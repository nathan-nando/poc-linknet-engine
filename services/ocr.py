import cv2
import numpy as np
from utils.logger import setup_logger

logger = setup_logger("ocr_service")

# Lazy load the model to save startup time and avoid crashing if not installed
_ocr_model = None

def get_ocr_model():
    global _ocr_model
    if _ocr_model is None:
        try:
            from paddleocr import PaddleOCR
            import logging
            logging.getLogger("ppocr").setLevel(logging.ERROR) # Suppress paddle logs
            _ocr_model = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR model loaded successfully.")
        except ImportError:
            logger.error("PaddleOCR is not installed.")
            raise
        except Exception as e:
            logger.error(f"Failed to load PaddleOCR: {e}")
            raise
    return _ocr_model

def extract_text_from_bbox(img_array: np.ndarray, bbox: dict) -> str | None:
    """
    Crop the image based on bbox and run PaddleOCR to extract text.
    Returns None if OCR fails or text is empty.
    """
    try:
        x1, y1, x2, y2 = int(bbox['x1']), int(bbox['y1']), int(bbox['x2']), int(bbox['y2'])
        
        # Guard against out-of-bounds or zero-size crop
        h, w = img_array.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            raise ValueError("Invalid bbox dimensions for cropping")

        cropped = img_array[y1:y2, x1:x2]
        
        ocr_model = get_ocr_model()
        
        # Run PaddleOCR (no manual thresholding needed as Paddle uses CNNs directly)
        result = ocr_model.ocr(cropped, cls=True)
        
        text = ""
        # result is a list of results for each image passed. 
        # result[0] is the result for our single cropped image.
        if result and result[0]:
            # Each line format: [ [[x,y],[x,y],[x,y],[x,y]], ('Text', confidence) ]
            texts = [line[1][0] for line in result[0] if line and len(line) > 1]
            text = " ".join(texts).strip()
        
        if text:
            logger.info(f"PaddleOCR successfully extracted: {text}")
            return text
        else:
            logger.warning("PaddleOCR extracted empty string")
            return None
            
    except Exception as e:
        logger.error(f"PaddleOCR Error: {e}")
        return None

def extract_serial_number(img_array: np.ndarray, bbox: dict) -> str:
    """
    Crop the image based on bbox and run PaddleOCR to extract the serial number.
    Fallback to a dummy string if OCR fails.
    """
    text = extract_text_from_bbox(img_array, bbox)
    if text:
        return text
    else:
        logger.warning("Falling back to dummy serial number")
        return "ODP-DUMMY-123/001"
