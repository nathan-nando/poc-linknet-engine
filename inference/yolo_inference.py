import os
import cv2
from ultralytics import YOLO
import numpy as np

class YOLOEngine:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def predict(self, img_array: np.ndarray, img_height: int, img_width: int):
        results = self.model(img_array)
        detections = []
        
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is None:
                continue

            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0].item())
                # LANGSUNG GUNAKAN NAMA CLASS DARI MODEL, TANPA MAPPING
                cls_name = self.model.names[cls_id].lower() 
                
                conf = box.conf[0].item()
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                tilt_degrees = 0.0
                mask_coverage = 0.0
                
                if masks is not None:
                    contour = masks.xy[i]
                    if len(contour) > 0:
                        rect = cv2.minAreaRect(contour)
                        angle = rect[-1]
                        
                        if angle > 45:
                            tilt_degrees = 90 - angle
                        else:
                            tilt_degrees = angle
                            
                        mask_area = cv2.contourArea(contour)
                        img_area = img_width * img_height
                        mask_coverage = mask_area / img_area
                
                # Kita hapus foundation_visible berbasis bbox/spatial
                # karena sekarang kita pakai class 'pole_base' di Rule Engine
                
                detections.append({
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "tilt_degrees": tilt_degrees,
                    "frame_coverage": mask_coverage
                })
                
        return detections