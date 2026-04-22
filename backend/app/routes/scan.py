import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.scan import ScanRequest, ScanResponse
from app.services.scan_service import run_bias_scan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["scan"])


@router.post("/scan", response_model=ScanResponse, summary="Run bias scan on dataset")
def scan_bias(request: ScanRequest):
    """Run a comprehensive bias scan on the dataset.
    
    - **dataset_path**: Path to the CSV file (optional, uses latest upload if not provided)
    - **target_column**: Target column name (optional, auto-detected if not provided)
    
    Returns detailed bias analysis with top biased groups and fairness metrics.
    """
    dataset_path = getattr(request, "dataset_path", None)
    target = getattr(request, "target_column", None)
    
    logger.info(f"Scan request received: dataset_path={dataset_path}, target_column={target}")
    
    try:
        result = run_bias_scan(dataset_path, target)
        logger.info(
            f"Scan completed successfully: "
            f"groups_scanned={result.get('groups_scanned')}, "
            f"biased_groups_found={result.get('biased_groups_found')}, "
            f"fairness_score={result.get('fairness_score')}"
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Unexpected error during scan: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during bias scanning."
        ) from exc
