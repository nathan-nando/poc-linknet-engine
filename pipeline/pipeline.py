import cv2
import numpy as np
import os
from dotenv import load_dotenv

from inference.yolo_inference import YOLOEngine
from rules.engine import RuleEngine
from imgqualitygate.gate import run_quality_gate

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
    # 1. Decode image di memori
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width = img_array.shape[:2]

    # 2. Image Quality Gate
    gate_result = run_quality_gate(img_array, rule_engine.raw_config)

    if not gate_result["passed"]:
        return {
            "status": "Reject",
            "reasons": gate_result["reasons"],
            "detections": [],
            "gate_scores": gate_result["scores"],
        }

    # 3. YOLO Inference — detections berisi field internal untuk Rule Engine
    detections = yolo_engine.predict(img_array, img_height, img_width)

    # 4. Rule Engine Evaluation (butuh field internal: tilt_degrees, frame_coverage, dll.)
    final_status, reasons = rule_engine.evaluate(detections)

    # 5. Strip field internal sebelum dikembalikan ke API
    public_detections = [_to_public_detection(d) for d in detections]

    return {
        "status": final_status,
        "reasons": reasons,
        "detections": public_detections,
        "gate_scores": gate_result["scores"],
    }