from pydantic import BaseModel
from typing import List, Optional

class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class DetectionResult(BaseModel):
    class_name: str
    confidence: float
    bbox: DetectionBox
    # Mocked calculated properties for rule engine evaluation
    tilt_degrees: float = 0.0
    frame_coverage: float = 0.0
    foundation_visible: bool = False

class AnalyzeResponse(BaseModel):
    status: str  # "Accept" or "Reject"
    reasons: List[str]
    detections: List[DetectionResult]