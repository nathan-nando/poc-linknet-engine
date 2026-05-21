# schemes.py — cukup hapus 3 field dari DetectionResult

from pydantic import BaseModel
from typing import List

class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class DetectionResult(BaseModel):
    class_name: str
    confidence: float
    bbox: DetectionBox
    # Hapus: tilt_degrees, frame_coverage, foundation_visible
    # Field-field itu internal Rule Engine, bukan output API

class AnalyzeResponse(BaseModel):
    status: str
    reasons: List[str]
    detections: List[DetectionResult]
    gate_scores: dict
    additional_info: dict | None = None
    processing_time_ms: float | None = None