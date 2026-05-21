import cv2
import numpy as np
import os
from dotenv import load_dotenv

from inference.yolo_inference import YOLOEngine
from rules.engine import RuleEngine
from imgqualitygate.gate import run_quality_gate
from utils.logger import setup_logger
from services.ocr import extract_serial_number
from services.inquiry import get_expected_cable_count

logger = setup_logger("pipeline")

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
yolo_engine = YOLOEngine(MODEL_PATH)
rule_engine = RuleEngine(config_path="configs/treshold.yaml")

# Field-field ini hanya dipakai secara internal oleh Rule Engine.
# Tidak perlu (dan tidak boleh) dikirim ke konsumen API.
_INTERNAL_FIELDS = {"tilt_degrees", "frame_coverage", "has_mask", "foundation_visible"}


def _to_public_detection(det: dict) -> dict:
    """Hapus field internal, bulatkan confidence, kembalikan representasi publik."""
    return {
        "class_name": det["class_name"],
        "confidence": round(det["confidence"], 4),
        "bbox": det["bbox"],
    }


def process_image(image_bytes: bytes) -> dict:
    # 0. Reload konfigurasi dari database agar selalu up-to-date
    rule_engine.reload()
    
    # 1. Decode image di memori
    logger.info("Decoding image...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width = img_array.shape[:2]

    # 2. Image Quality Gate
    logger.info("Running Image Quality Gate...")
    gate_result = run_quality_gate(img_array, rule_engine.raw_config)

    if not gate_result["passed"]:
        return {
            "status": "Reject",
            "reasons": gate_result["reasons"],
            "detections": [],
            "gate_scores": gate_result["scores"],
        }

    # 3. YOLO Inference — detections berisi field internal untuk Rule Engine
    logger.info("Running YOLO Inference...")
    detections = yolo_engine.predict(img_array, img_height, img_width)

    # 4. Rule Engine Evaluation (butuh field internal: tilt_degrees, frame_coverage, dll.)
    logger.info("Evaluating Rules...")
    final_status, reasons = rule_engine.evaluate(detections)

    # 4.5. OCR & Cable Inquiry Service
    additional_info = {}
    odp_identifier_dets = [d for d in detections if d["class_name"] == "odp_identifier"]
    odp_box_dets = [d for d in detections if d["class_name"] == "odp_box"]
    
    if final_status == "Accept" and odp_box_dets and odp_identifier_dets:
        logger.info("ODP Identifier found. Running OCR and Cable Inquiry...")
        # Get the highest confidence identifier
        best_id_det = max(odp_identifier_dets, key=lambda x: x["confidence"])
        
        # 1. OCR
        serial_number = extract_serial_number(img_array, best_id_det["bbox"])
        
        # 1.5. Standardize format & Truncate OCR string
        import re
        
        odp_index = serial_number.upper().find("ODP")
        if odp_index != -1:
            # Strip weird prefixes by slicing from 'ODP' onwards
            serial_number = serial_number[odp_index:]
            
        # Normalize: Remove all spaces and keep only alphanumeric, '-' and '/'
        serial_number = serial_number.replace(" ", "")
        serial_number = re.sub(r'[^a-zA-Z0-9\-/]', '', serial_number)
            
        id_rule = rule_engine.rules.get("odp_box", {}).get("identifier", {})
        max_len = id_rule.get("max_length")
        
        if max_len is not None and len(serial_number) > max_len:
            logger.info(f"Truncating serial number from {len(serial_number)} to {max_len} characters")
            serial_number = serial_number[:max_len]
            
        additional_info["serial_number"] = serial_number
            
        # 2. Inquiry Service
        expected_cables = get_expected_cable_count(serial_number)
        additional_info["expected_cables"] = expected_cables
        
        # 3. Compare with YOLO detected cables
        detected_cables_count = len([d for d in detections if d["class_name"] == "odp_cable"])
        
        logger.info(f"YOLO detected {detected_cables_count} cables. System expects {expected_cables} cables.")
        
        if detected_cables_count < expected_cables:
            final_status = "Reject"
            reasons.append(f"Kabel terpasang ({detected_cables_count}) kurang dari data sistem ({expected_cables}) untuk ODP {serial_number}")

    # 5. Strip field internal sebelum dikembalikan ke API
    public_detections = [_to_public_detection(d) for d in detections]

    return {
        "status": final_status,
        "reasons": reasons,
        "detections": public_detections,
        "gate_scores": gate_result["scores"],
        "additional_info": additional_info,
    }