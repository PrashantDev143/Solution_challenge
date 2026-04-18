from fastapi import APIRouter, File, UploadFile

from app.schemas.upload import UploadResponse
from app.services.upload_service import save_and_preview_csv


router = APIRouter(prefix="", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
def upload_csv(file: UploadFile = File(...)):
    return save_and_preview_csv(file)
