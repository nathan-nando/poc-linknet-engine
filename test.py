import cv2
import numpy as np
from paddleocr import PaddleOCR
try:
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    img = np.zeros((100, 300, 3), dtype=np.uint8)
    res = ocr.ocr(img, cls=True)
    print("SUCCESS", res)
except Exception as e:
    print("ERROR", e)
