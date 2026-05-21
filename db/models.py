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
