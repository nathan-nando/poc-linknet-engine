from fastapi import APIRouter, UploadFile, File, HTTPException
from schemes.schemes import AnalyzeResponse
from pipeline.pipeline import process_image

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")
    
    try:
        image_bytes = await file.read()
        
        # Run the end-to-end pipeline
        result = process_image(image_bytes)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))