from fastapi import FastAPI
from api.analyze import router as analyze_router

app = FastAPI(
    title="YOLO Inference API",
    version="1.0.0"
)

app.include_router(analyze_router)


@app.get("/")
def root():
    return {
        "message": "Inference API Running"
    }