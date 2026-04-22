import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from app.schemas.upload import UploadResponse
from app.services.upload_service import save_and_preview_csv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["upload"])


@router.post("/upload", response_model=UploadResponse, summary="Upload and preview CSV dataset")
def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file for bias analysis.
    
    - **file**: CSV file containing your dataset
    
    Returns dataset preview, columns, and detected target column.
    """
    if not file:
        logger.error("Upload request missing file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is required."
        )
    
    try:
        logger.info(f"Processing upload for file: {file.filename}")
        return save_and_preview_csv(file)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Unexpected error during upload: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file processing."
        ) from exc
