from fastapi import APIRouter, UploadFile, File, HTTPException
from schemes.schemes import AnalyzeResponse
from pipeline.pipeline import process_image
from utils.logger import setup_logger

logger = setup_logger("api.analyze")

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")
    
    try:
        logger.info(f"Received image analysis request: {file.filename}")
        image_bytes = await file.read()
        
        # Run the end-to-end pipeline
        result = process_image(image_bytes)
        
        logger.info(f"Analysis complete. Status: {result.get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))