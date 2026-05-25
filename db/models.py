from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from db.database import Base

class Threshold(Base):
    __tablename__ = "thresholds"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True) # e.g., 'pole', 'odp_box', 'pole_and_odp_box', 'image_quality_gate'
    key = Column(String, index=True)      # e.g., 'confidence', 'tilt'
    
    # We use a JSON column to store arbitrary structure based on the key
    # e.g. {"min_score": 0.80, "reject_reason": "..."}
    # or {"method": "mask_min_area_rect_angle", "max_degrees": 5.0, ...}
    value = Column(JSON) 

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "value": self.value
        }

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(String)
    reasons = Column(JSON)
    detections = Column(JSON)
    processing_time_ms = Column(Float)
    image_path = Column(String)
    
    # We will use string for sqlite compatibility if needed, or proper DateTime
    from sqlalchemy import DateTime
    from sqlalchemy.sql import func
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "reasons": self.reasons,
            "detections": self.detections,
            "processing_time_ms": self.processing_time_ms,
            "image_path": self.image_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
