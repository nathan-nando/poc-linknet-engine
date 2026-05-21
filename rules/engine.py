import yaml
from db.database import SessionLocal
from db.models import Threshold

class RuleEngine:
    def __init__(self, config_path: str = "configs/treshold.yaml"):
        self.config_path = config_path
        self.reload()
        
    def reload(self):
        self.rules = {}
        self.raw_config = {}
        try:
            # Coba load dari database
            db = SessionLocal()
            if db:
                thresholds = db.query(Threshold).all()
                self.raw_config = {"image_quality_gate": {}, "rule_engine": {}}
                for t in thresholds:
                    if t.category == "image_quality_gate":
                        self.raw_config["image_quality_gate"][t.key] = t.value
                    elif t.category in ['pole', 'odp_box', 'pole_and_odp_box']:
                        if t.category not in self.rules:
                            self.rules[t.category] = {}
                        self.rules[t.category][t.key] = t.value
                        self.raw_config["rule_engine"][t.category] = self.rules[t.category]
                db.close()
                if not self.rules:
                    raise Exception("No rules in DB, falling back to YAML")
        except Exception as e:
            print(f"Warning: Failed to load rules from DB, falling back to YAML. Error: {e}")
            with open(self.config_path, 'r') as file:
                self.raw_config = yaml.safe_load(file)
                self.rules = self.raw_config.get('rule_engine', {})

    def evaluate(self, detections: list) -> tuple[str, list]:
        reasons = []
        detected_classes = [d['class_name'] for d in detections]

        has_pole = 'pole' in detected_classes
        has_odp_box = 'odp_box' in detected_classes

        if not has_pole and not has_odp_box:
            return "Reject", ["Tidak ada objek Pole atau ODP Box yang terdeteksi dalam gambar."]

        if has_pole and has_odp_box:
            reasons.extend(self._evaluate_pole_and_odp_box(detections, detected_classes))
        elif has_pole:
            reasons.extend(self._evaluate_single(detections, 'pole', 'pole', detected_classes))
        elif has_odp_box:
            reasons.extend(self._evaluate_single(detections, 'odp_box', 'odp_box', detected_classes))

        status = "Accept" if len(reasons) == 0 else "Reject"
        return status, reasons

    def _evaluate_single(
        self,
        detections: list,
        target_class: str,
        rule_key: str,
        all_detected_classes: list,
    ) -> list:
        reasons = []
        rule = self.rules.get(rule_key, {})

        target_dets = [d for d in detections if d['class_name'] == target_class]
        if not target_dets:
            return reasons

        best_det = max(target_dets, key=lambda x: x['confidence'])

        # --- Confidence ---
        conf_rule = rule.get('confidence', {})
        if best_det['confidence'] < conf_rule.get('min_score', 0.70):
            reasons.append(conf_rule['reject_reason'])

        # --- Tilt ---
        # BUG FIX: hanya evaluasi tilt jika mask tersedia.
        # Jika has_mask=False, tilt_degrees=0.0 (default) → cek ini akan selalu lolos,
        # yang terlihat seperti "aman" padahal sebenarnya data tidak ada.
        # Dengan guard ini, kita tidak salah meloloskan karena nilai default.
        tilt_rule = rule.get('tilt', {})
        if tilt_rule and best_det.get('has_mask', False):
            if best_det['tilt_degrees'] > tilt_rule.get('max_degrees', 5.0):
                msg = tilt_rule['reject_reason'].format(
                    value=round(best_det['tilt_degrees'], 1)
                )
                reasons.append(msg)

        # --- Frame Coverage ---
        # BUG FIX: sama seperti tilt, hanya evaluasi jika mask tersedia.
        # frame_coverage=0.0 (default saat no-mask) akan selalu < min_coverage
        # dan menyebabkan false-reject untuk kelas-kelas accessory.
        cov_rule = rule.get('frame_coverage', {})
        if cov_rule and best_det.get('has_mask', False):
            if best_det['frame_coverage'] < cov_rule.get('min_coverage', 0.0):
                reasons.append(cov_rule['reject_reason'])

        # --- Require Class (hardcoded mapping) ---
        class_mapping = {
            'foundation_visibility': 'pole_base',
            'identifier': 'odp_identifier',
            'door_visible': 'odp_door',
            'cable': 'odp_cable'
        }
        
        for key, expected_class in class_mapping.items():
            config = rule.get(key, {})
            if config.get('required', False):
                if expected_class not in all_detected_classes:
                    reasons.append(config.get('reject_reason', f"{expected_class} is required"))

        return reasons

    def _evaluate_pole_and_odp_box(
        self,
        detections: list,
        all_detected_classes: list,
    ) -> list:
        reasons = []
        rule = self.rules.get('pole_and_odp_box', {})

        pole_dets = [d for d in detections if d['class_name'] == 'pole']
        odp_dets = [d for d in detections if d['class_name'] == 'odp_box']

        if not pole_dets or not odp_dets:
            # Seharusnya tidak terjadi karena sudah dicek di evaluate(), tapi guard aman
            missing = "ODP Box" if not odp_dets else "Pole"
            reasons.append(
                rule.get('both_detected', {}).get('reject_reason', '').format(
                    detected_object="Pole" if not odp_dets else "ODP Box"
                )
            )
            return reasons

        pole_det = max(pole_dets, key=lambda x: x['confidence'])
        odp_box_det = max(odp_dets, key=lambda x: x['confidence'])

        # --- Confidence ---
        conf_rule = rule.get('confidence', {})
        min_conf = conf_rule.get('min_score_each', 0.65)
        if pole_det['confidence'] < min_conf:
            reasons.append(conf_rule['reject_reason'].format(missing_object="Pole"))
        if odp_box_det['confidence'] < min_conf:
            reasons.append(conf_rule['reject_reason'].format(missing_object="ODP Box"))

        # --- Tilt (dengan has_mask guard) ---
        pole_tilt_rule = rule.get('pole_tilt', {})
        if pole_tilt_rule and pole_det.get('has_mask', False):
            if pole_det['tilt_degrees'] > pole_tilt_rule.get('max_degrees', 5.0):
                reasons.append(
                    pole_tilt_rule['reject_reason'].format(
                        value=round(pole_det['tilt_degrees'], 1)
                    )
                )

        odp_tilt_rule = rule.get('odp_box_tilt', {})
        if odp_tilt_rule and odp_box_det.get('has_mask', False):
            if odp_box_det['tilt_degrees'] > odp_tilt_rule.get('max_degrees', 8.0):
                reasons.append(
                    odp_tilt_rule['reject_reason'].format(
                        value=round(odp_box_det['tilt_degrees'], 1)
                    )
                )

        # --- Combined Frame Coverage (dengan has_mask guard) ---
        cov_rule = rule.get('frame_coverage', {})
        if cov_rule:
            pole_has_mask = pole_det.get('has_mask', False)
            odp_has_mask = odp_box_det.get('has_mask', False)
            if pole_has_mask and odp_has_mask:
                combined_coverage = pole_det['frame_coverage'] + odp_box_det['frame_coverage']
                if combined_coverage < cov_rule.get('min_coverage', 0.015):
                    reasons.append(cov_rule['reject_reason'])

        # --- ODP Position ---
        pos_rule = rule.get('odp_position', {})
        if pos_rule and 'bbox' in pole_det and 'bbox' in odp_box_det:
            pole_bbox = pole_det['bbox']
            odp_bbox = odp_box_det['bbox']
            
            pole_y_min = pole_bbox.get('y1', 0)
            pole_y_max = pole_bbox.get('y2', 1)
            pole_height = pole_y_max - pole_y_min
            
            odp_y_center = (odp_bbox.get('y1', 0) + odp_bbox.get('y2', 0)) / 2
            
            if pole_height > 0:
                relative_position = (odp_y_center - pole_y_min) / pole_height
                
                min_pos = pos_rule.get('min_position', 0.10)
                max_pos = pos_rule.get('max_position', 0.80)
                
                if relative_position < min_pos or relative_position > max_pos:
                    # Append debug context for user visibility
                    reasons.append(pos_rule.get('reject_reason', "Posisi ODP tidak ideal") + f" (posisi saat ini: {round(relative_position * 100)}%)")

        # --- Require Class (hardcoded mapping) ---
        class_mapping = {
            'foundation_visibility': 'pole_base',
            'location_description': 'loc_desc'
            # odp_position doesn't map to a simple class detection for now
        }
        for key, expected_class in class_mapping.items():
            config = rule.get(key, {})
            if config.get('required', False):
                if expected_class not in all_detected_classes:
                    reasons.append(config.get('reject_reason', f"{expected_class} is required"))

        return reasons