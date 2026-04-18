from fastapi import APIRouter

from app.schemas.scan import ScanRequest, ScanResponse
from app.services.scan_service import run_bias_scan


router = APIRouter(prefix="", tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
def scan_bias(request: ScanRequest):
    return run_bias_scan(request.dataset_path, request.target_column)
