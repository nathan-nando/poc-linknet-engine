import os
import yaml
import sys

# Tambahkan path ke root direktori engine agar bisa import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal, engine, Base
from db.models import Threshold

def run_migration(yaml_path: str = "configs/treshold.yaml"):
    print("Membaca file YAML...")
    with open(yaml_path, 'r') as file:
        raw_config = yaml.safe_load(file)
        
    print("Menghapus tabel lama dan membuat tabel baru...")
    Threshold.__table__.drop(bind=engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Proses image_quality_gate
    print("Migrasi image_quality_gate...")
    iqg = raw_config.get('image_quality_gate', {})
    for key, value in iqg.items():
        existing = db.query(Threshold).filter_by(category="image_quality_gate", key=key).first()
        if not existing:
            new_threshold = Threshold(category="image_quality_gate", key=key, value=value)
            db.add(new_threshold)
        else:
            existing.value = value

    # Proses rule_engine categories
    print("Migrasi rule_engine (pole, odp_box, dll)...")
    rules = raw_config.get('rule_engine', {})
    for category, category_data in rules.items():
        for key, value in category_data.items():
            existing = db.query(Threshold).filter_by(category=category, key=key).first()
            if not existing:
                new_threshold = Threshold(category=category, key=key, value=value)
                db.add(new_threshold)
            else:
                existing.value = value
                
    db.commit()
    db.close()
    print("Migrasi selesai!")

if __name__ == "__main__":
    run_migration()
