import cv2
import numpy as np
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
img = np.zeros((100, 300, 3), dtype=np.uint8)
try:
    res = ocr.ocr(img, cls=True)
    print("SUCCESS OCR", res)
except Exception as e:
    print("ERROR OCR", e)
