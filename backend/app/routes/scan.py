from fastapi import APIRouter

from app.schemas.scan import ScanRequest, ScanResponse
from app.services.scan_service import run_bias_scan


router = APIRouter(prefix="", tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
def scan_bias(request: ScanRequest):
    dataset_path = getattr(request, "dataset_path", None)
    target = getattr(request, "target_column", None)
    print(f"[routes.scan] Received scan request dataset_path={dataset_path} target={target}")
    result = run_bias_scan(dataset_path, target)
    print(f"[routes.scan] Scan completed, groups_scanned={result.get('groups_scanned')}")
    return result
