from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from db.database import get_db
from db.models import LogDecision
from typing import Optional
import json

router = APIRouter()

@router.get("/analytics/timeseries")
def get_timeseries(start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns Accept vs Reject counts grouped by date."""
    query = db.query(LogDecision)
    
    if start_date:
        dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(LogDecision.created_at >= dt)
    if end_date:
        dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(LogDecision.created_at < dt)
        
    decisions = query.all()
    
    # Group by YYYY-MM-DD
    grouped = {}
    for d in decisions:
        date_str = d.created_at.strftime('%Y-%m-%d')
        if date_str not in grouped:
            grouped[date_str] = {"accept": 0, "reject": 0}
            
        status_lower = (d.status or "").lower()
        if status_lower == "accept":
            grouped[date_str]["accept"] += 1
        else:
            grouped[date_str]["reject"] += 1
            
    # Format for recharts
    result = []
    for date_str in sorted(grouped.keys()):
        result.append({
            "date": date_str,
            "accept": grouped[date_str]["accept"],
            "reject": grouped[date_str]["reject"]
        })
        
    return result

@router.get("/analytics/top-classes")
def get_top_classes(limit: int = 5, start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns the top classification classes by volume and their accept/reject breakdown."""
    query = db.query(LogDecision)
    if start_date:
        dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(LogDecision.created_at >= dt)
    if end_date:
        dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(LogDecision.created_at < dt)
        
    decisions = query.all()
    
    grouped = {}
    for d in decisions:
        cls = d.classification or "unknown"
        if cls.lower() == "other":
            continue
            
        if cls not in grouped:
            grouped[cls] = {"total": 0, "accept": 0, "reject": 0}
            
        grouped[cls]["total"] += 1
        status_lower = (d.status or "").lower()
        if status_lower == "accept":
            grouped[cls]["accept"] += 1
        else:
            grouped[cls]["reject"] += 1
            
    # Sort by total descending
    sorted_classes = sorted(grouped.items(), key=lambda x: x[1]["total"], reverse=True)[:limit]
    
    result = []
    for cls, stats in sorted_classes:
        result.append({
            "name": cls.replace("_", " ").title(),
            "total": stats["total"],
            "accept": stats["accept"],
            "reject": stats["reject"],
            "accept_rate": round(stats["accept"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        })
        
    return result

@router.get("/analytics/distribution")
def get_distribution(start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns overall accept/reject distribution."""
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
    
    return [
        {"name": "Accept", "value": accepted, "fill": "#24a148"},
        {"name": "Reject", "value": rejected, "fill": "#da1e28"}
    ]
