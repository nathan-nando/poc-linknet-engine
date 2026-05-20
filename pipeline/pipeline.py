import cv2
import numpy as np
import os
from dotenv import load_dotenv

from inference.yolo_inference import YOLOEngine
from rules.engine import RuleEngine
from imgqualitygate.gate import run_quality_gate  # Import Gate yang sudah disesuaikan

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
yolo_engine = YOLOEngine(MODEL_PATH)
rule_engine = RuleEngine(config_path="configs/treshold.yaml")

def process_image(image_bytes: bytes) -> dict:
    # 1. Decode Image langsung di memori (Tanpa save ke disk)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width = img_array.shape[:2]

    # 2. IMAGE QUALITY GATE (SEKARANG AKTIF)
    # Kirim gambar dan config ke Quality Gate
    gate_result = run_quality_gate(img_array, rule_engine.raw_config)
    
    # Jika gagal Quality Gate, langsung REJECT dan proses berhenti
    if not gate_result["passed"]:
        return {
            "status": "Reject",
            "reasons": gate_result["reasons"],
            "detections": [],
            "gate_scores": gate_result["scores"] # Menampilkan skor blur/brightness ke user
        }

    # 3. Object Detection & Segmentation Inference (YOLO)
    # Ini hanya akan dieksekusi jika gambar LULUS Quality Gate
    detections = yolo_engine.predict(img_array, img_height, img_width)

    # 4. Rule Engine Evaluation
    final_status, reasons = rule_engine.evaluate(detections)

    return {
        "status": final_status,
        "reasons": reasons,
        "detections": detections,
        "gate_scores": gate_result["scores"]
    }