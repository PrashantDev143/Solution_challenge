import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.report_service import get_latest_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["report"])


@router.get("/report", summary="Get latest bias scan report")
def report():
    """Retrieve the latest bias scan report as JSON.
    
    Returns the most recent scan results including bias analysis and recommendations.
    """
    logger.info("Report request received")
    try:
        report_data = get_latest_report()
        if not report_data:
            logger.warning("No report data available")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scan report available. Please run a scan first."
            )
        
        logger.info(f"Report retrieved successfully")
        headers = {"Content-Disposition": "attachment; filename=biasxray-report.json"}
        return JSONResponse(content=report_data, headers=headers)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error retrieving report: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report."
        ) from exc
