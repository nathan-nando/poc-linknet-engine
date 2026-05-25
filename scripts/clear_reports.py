import sys
import os

# Add parent directory to path so we can import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import Report

def clear_reports():
    db = SessionLocal()
    try:
        count = db.query(Report).delete()
        db.commit()
        print(f"Successfully deleted {count} records from reports table.")
    except Exception as e:
        print(f"Error deleting reports: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_reports()
