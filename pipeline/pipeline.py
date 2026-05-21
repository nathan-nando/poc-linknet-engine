import cv2
import numpy as np
import os
from dotenv import load_dotenv

from inference.yolo_inference import YOLOEngine
from rules.engine import RuleEngine
from imgqualitygate.gate import run_quality_gate
from utils.logger import setup_logger

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

    # 4.5. Mock ODP Cable Validation (Dummy Feature)
    if final_status == "Accept" and "odp_box" in [d["class_name"] for d in detections]:
        logger.info("Running dummy ODP cable validation...")
        cable_rule = rule_engine.rules.get("odp_box", {}).get("cable_length", {})
        min_required = cable_rule.get("min_required", 5)
        
        # TODO: Replace this with real OCR and external system query
        # Simulated cable length returned from backend system query
        simulated_cable_length = 4  # hardcoded to 4 to demonstrate rejection if min is 5
        
        logger.info(f"Simulated required cable length from system: {simulated_cable_length}. Min threshold: {min_required}")
        
        if simulated_cable_length < min_required:
            final_status = "Reject"
            reasons.append(cable_rule.get("reject_reason", "Kabel terpasang kurang dari batas minimum"))

    # 5. Strip field internal sebelum dikembalikan ke API
    public_detections = [_to_public_detection(d) for d in detections]

    return {
        "status": final_status,
        "reasons": reasons,
        "detections": public_detections,
        "gate_scores": gate_result["scores"],
    }