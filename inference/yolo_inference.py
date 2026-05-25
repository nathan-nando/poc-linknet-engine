import os
import cv2
from ultralytics import YOLO
import numpy as np
 
 
class YOLOEngine:
    def __init__(self, model_path: str):
        import logging
        self.logger = logging.getLogger("pipeline")
        
        # Check if ONNX optimized model exists
        onnx_path = model_path.replace('.pt', '.onnx')
        if os.path.exists(onnx_path):
            self.logger.info(f"Detected ONNX model. Loading {onnx_path} for optimized GPU inference.")
            self.model = YOLO(onnx_path, task='segment')
            self.model_type = "ONNX"
        else:
            self.logger.info(f"ONNX model not found. Falling back to PyTorch model: {model_path}")
            self.model = YOLO(model_path)
            self.model_type = "PyTorch (.pt)"

    def warmup(self):
        """Perform a dummy inference to warmup ONNX Runtime and CUDA pipelines."""
        import logging
        logger = logging.getLogger("pipeline")
        logger.info(f"Warming up YOLO GPU pipeline using {self.model_type}...")
        # Create a dummy black image
        dummy_img = np.zeros((832, 832, 3), dtype=np.uint8)
        # Suppress verbose output for warmup
        self.model(dummy_img, imgsz=832, verbose=False)
        logger.info(f"YOLO GPU warmup ({self.model_type}) complete.")
 
    def predict(self, img_array: np.ndarray, img_height: int, img_width: int) -> list:
        self.logger.info(f"YOLOEngine performing inference using: {self.model_type}")
        
        # BUG FIX: tambahkan imgsz, conf, dan iou agar konsisten dengan setting training
        # Tanpa imgsz=832, YOLO bisa pakai resolusi berbeda dari waktu training
        results = self.model(
            img_array,
            imgsz=832,
            conf=0.25,
            iou=0.6,
            verbose=False,  # Suppress per-inference console output
        )
 
        detections = []
 
        for result in results:
            boxes = result.boxes
            masks = result.masks
 
            if boxes is None:
                continue
 
            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0].item())
                cls_name = self.model.names[cls_id].lower()
 
                conf = box.conf[0].item()
                x1, y1, x2, y2 = box.xyxy[0].tolist()
 
                tilt_degrees = 0.0
                mask_coverage = 0.0
                has_mask = False
 
                # Guard: pastikan index i valid dalam masks
                if masks is not None and i < len(masks.xy):
                    # BUG FIX: cast ke float32 untuk keamanan lintas versi OpenCV
                    contour = masks.xy[i].astype(np.float32)
 
                    # Butuh minimal 4 titik untuk minAreaRect yang bermakna
                    if len(contour) >= 4:
                        has_mask = True
 
                        rect = cv2.minAreaRect(contour)
                        angle = rect[-1]
 
                        # BUG FIX KRITIS: abs() sebelum perbandingan!
                        #
                        # OpenCV < 4.5  → angle ∈ (-90, 0]  → tanpa abs(), angle negatif
                        #                  maka tilt_degrees = -85° → cek "> max_degrees" SELALU False
                        #                  → tiang miring parah tidak pernah di-reject!
                        #
                        # OpenCV ≥ 4.5  → angle ∈ [0, 90)   → abs() tidak mengubah apa-apa, aman
                        #
                        # Logika normalisasi "tilt dari sumbu dominan":
                        # - Pole (tall, w < h): sisi pendek hampir horizontal → angle ≈ tilt dari vertikal
                        # - ODP Box (wide, w > h): sisi pendek hampir vertikal → 90-angle ≈ tilt dari horizontal
                        angle = abs(angle)
                        if angle > 45:
                            tilt_degrees = 90.0 - angle
                        else:
                            tilt_degrees = angle
 
                        # Hitung coverage menggunakan pixel-coord contour (masks.xy, bukan masks.xyn)
                        mask_area = cv2.contourArea(contour)
                        img_area = img_width * img_height
                        mask_coverage = mask_area / img_area if img_area > 0 else 0.0
 
                detections.append({
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "tilt_degrees": round(tilt_degrees, 2),
                    "frame_coverage": round(mask_coverage, 6),
                    # BUG FIX: tambahkan flag ini agar Rule Engine bisa skip tilt/coverage
                    # ketika mask tidak tersedia (hindari false-reject karena default 0.0)
                    "has_mask": has_mask,
                })
 
        return detections
 