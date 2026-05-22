from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.analyze import router as analyze_router
from api.thresholds import router as thresholds_router
from pipeline.pipeline import yolo_engine
from services import ocr
from utils.logger import setup_logger

logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warmup models before accepting traffic
    logger.info("Starting model warmup phase...")
    yolo_engine.warmup()
    ocr.warmup()
    logger.info("All models warmed up. Server is ready to accept traffic.")
    yield
    # Cleanup on shutdown (if any)
    pass

app = FastAPI(
    title="YOLO Inference API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(analyze_router)
app.include_router(thresholds_router)

@app.get("/")
def root():
    return {
        "message": "Inference API Running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}