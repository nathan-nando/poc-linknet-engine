from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
from db.database import get_db
from db.models import Threshold

router = APIRouter(prefix="/thresholds", tags=["thresholds"])

class ThresholdUpdate(BaseModel):
    value: Dict[str, Any]

@router.get("/")
def get_all_thresholds(db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    thresholds = db.query(Threshold).all()
    # Format as a nested dictionary similar to the YAML structure
    result = {}
    for t in thresholds:
        if t.category not in result:
            result[t.category] = {}
        result[t.category][t.key] = t.value
    return result

@router.get("/{category}")
def get_thresholds_by_category(category: str, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    thresholds = db.query(Threshold).filter(Threshold.category == category).all()
    if not thresholds:
        return {}
        
    result = {}
    for t in thresholds:
        result[t.key] = t.value
    return result

@router.put("/{category}/{key}")
def update_threshold(category: str, key: str, payload: ThresholdUpdate, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    threshold = db.query(Threshold).filter(
        Threshold.category == category, 
        Threshold.key == key
    ).first()
    
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")
        
    threshold.value = payload.value
    db.commit()
    db.refresh(threshold)
    
    return threshold.to_dict()
