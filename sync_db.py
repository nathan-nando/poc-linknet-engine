from db.database import engine, Base
import db.models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
