import sys
import os

# Add parent directory to path so we can import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import LogDecision

def clear_logs():
    db = SessionLocal()
    try:
        count = db.query(LogDecision).delete()
        db.commit()
        print(f"Successfully deleted {count} records from log_decisions table.")
    except Exception as e:
        print(f"Error deleting logs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_logs()
