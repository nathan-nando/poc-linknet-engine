from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.analyze import router as analyze_router
from api.thresholds import router as thresholds_router
from api.reports import router as reports_router
from pipeline.pipeline import yolo_engine
from services import ocr
from utils.logger import setup_logger

logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-migrate database (for POC)
    logger.info("Syncing database tables...")
    from db.database import engine, Base
    import db.models
    if engine:
        Base.metadata.create_all(bind=engine)
    
    # Warmup models before accepting traffic
    logger.info("Starting model warmup phase...")
    yolo_engine.warmup()
    ocr.warmup()
    logger.info("All models warmed up. Server is ready to accept traffic.")
    yield
    # Cleanup on shutdown (if any)
    pass

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="YOLO Inference API",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("/app/storage/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="/app/storage/images"), name="images")

app.include_router(analyze_router)
app.include_router(thresholds_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {
        "message": "Inference API Running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}