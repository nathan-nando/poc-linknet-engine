from fastapi import FastAPI
from api.analyze import router as analyze_router
from api.thresholds import router as thresholds_router

app = FastAPI(
    title="YOLO Inference API",
    version="1.0.0"
)

app.include_router(analyze_router)
app.include_router(thresholds_router)


@app.get("/")
def root():
    return {
        "message": "Inference API Running"
    }