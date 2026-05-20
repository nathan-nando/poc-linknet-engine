import yaml
import os

class RuleEngine:
    def __init__(self, config_path: str = "configs/treshold.yaml"):
        with open(config_path, 'r') as file:
            self.raw_config = yaml.safe_load(file) # Simpan semua config di sini
            self.rules = self.raw_config.get('rule_engine', {})

    def evaluate(self, detections: list) -> tuple[str, list]:
        reasons = []
        detected_classes = [d['class_name'] for d in detections]
        
        # Menggunakan standarisasi nama baru
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

    def _evaluate_single(self, detections: list, target_class: str, rule_key: str, all_detected_classes: list) -> list:
        reasons = []
        rule = self.rules.get(rule_key, {})
        
        target_dets = [d for d in detections if d['class_name'] == target_class]
        best_det = max(target_dets, key=lambda x: x['confidence'])

        if best_det['confidence'] < rule.get('confidence', {}).get('min_score', 0.70):
            reasons.append(rule['confidence']['reject_reason'])
            
        if 'tilt' in rule and best_det['tilt_degrees'] > rule['tilt']['max_degrees']:
            msg = rule['tilt']['reject_reason'].format(value=round(best_det['tilt_degrees'], 1))
            reasons.append(msg)
            
        if 'frame_coverage' in rule and best_det['frame_coverage'] < rule['frame_coverage']['min_coverage']:
            reasons.append(rule['frame_coverage']['reject_reason'])
            
        # Evaluasi dinamis untuk "require_class" (contoh: mengecek pole_base, odp_door, dll)
        for key, config in rule.items():
            if isinstance(config, dict) and config.get('method') == 'require_class':
                req_class = config.get('required_class')
                if req_class not in all_detected_classes:
                    reasons.append(config.get('reject_reason'))

        return reasons

    def _evaluate_pole_and_odp_box(self, detections: list, all_detected_classes: list) -> list:
        reasons = []
        rule = self.rules.get('pole_and_odp_box', {})
        
        pole_det = max([d for d in detections if d['class_name'] == 'pole'], key=lambda x: x['confidence'])
        odp_box_det = max([d for d in detections if d['class_name'] == 'odp_box'], key=lambda x: x['confidence'])

        min_conf = rule.get('confidence', {}).get('min_score_each', 0.65)
        if pole_det['confidence'] < min_conf:
            reasons.append(rule['confidence']['reject_reason'].format(missing_object="Pole"))
        if odp_box_det['confidence'] < min_conf:
            reasons.append(rule['confidence']['reject_reason'].format(missing_object="ODP Box"))

        if pole_det['tilt_degrees'] > rule.get('pole_tilt', {}).get('max_degrees', 5.0):
            reasons.append(rule['pole_tilt']['reject_reason'].format(value=round(pole_det['tilt_degrees'], 1)))
            
        if odp_box_det['tilt_degrees'] > rule.get('odp_box_tilt', {}).get('max_degrees', 8.0):
            reasons.append(rule['odp_box_tilt']['reject_reason'].format(value=round(odp_box_det['tilt_degrees'], 1)))

        # Kombinasi coverage
        combined_coverage = pole_det['frame_coverage'] + odp_box_det['frame_coverage']
        if 'frame_coverage' in rule and combined_coverage < rule['frame_coverage']['min_coverage']:
            reasons.append(rule['frame_coverage']['reject_reason'])

        # Evaluasi dinamis "require_class" untuk gabungan (mengecek pole_base & loc_desc)
        for key, config in rule.items():
            if isinstance(config, dict) and config.get('method') == 'require_class':
                req_class = config.get('required_class')
                if req_class not in all_detected_classes:
                    reasons.append(config.get('reject_reason'))

        return reasons