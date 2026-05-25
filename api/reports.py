from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from db.models import Report

router = APIRouter()

@router.get("/reports/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(Report).count()
    accepted = db.query(Report).filter(func.lower(Report.status) == "accept").count()
    rejected = total - accepted
    
    accept_rate = (accepted / total * 100) if total > 0 else 0
    reject_rate = (rejected / total * 100) if total > 0 else 0
    
    avg_time = db.query(func.avg(Report.processing_time_ms)).scalar()
    avg_time = round(avg_time, 2) if avg_time else 0
    
    return {
        "total_analyzed": total,
        "accept_rate": round(accept_rate, 2),
        "reject_rate": round(reject_rate, 2),
        "avg_processing_time_ms": avg_time
    }

@router.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [r.to_dict() for r in reports]

@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_dict()
