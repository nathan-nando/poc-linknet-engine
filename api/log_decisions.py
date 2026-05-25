from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from db.models import LogDecision
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

# Keep metrics here or move to analytics, keeping here for backward compatibility
# but using log-decisions path
@router.get("/log-decisions/metrics")
def get_metrics(start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(LogDecision)
    if start_date:
        dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(LogDecision.created_at >= dt)
    if end_date:
        dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(LogDecision.created_at < dt)
        
    total = query.count()
    accepted = query.filter(func.lower(LogDecision.status) == "accept").count()
    rejected = total - accepted
    
    accept_rate = (accepted / total * 100) if total > 0 else 0
    reject_rate = (rejected / total * 100) if total > 0 else 0
    
    avg_time = query.with_entities(func.avg(LogDecision.processing_time_ms)).scalar()
    avg_time = round(avg_time, 2) if avg_time else 0
    
    return {
        "total_analyzed": total,
        "accept_rate": round(accept_rate, 2),
        "reject_rate": round(reject_rate, 2),
        "avg_processing_time_ms": avg_time
    }

@router.get("/log-decisions")
def get_log_decisions(db: Session = Depends(get_db)):
    decisions = db.query(LogDecision).order_by(LogDecision.created_at.desc()).all()
    return [d.to_dict() for d in decisions]

@router.get("/log-decisions/{decision_id}")
def get_log_decision(decision_id: int, db: Session = Depends(get_db)):
    decision = db.query(LogDecision).filter(LogDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Log Decision not found")
    return decision.to_dict()
