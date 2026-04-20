from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.report_service import get_latest_report


router = APIRouter(prefix="", tags=["report"])


@router.get("/report")
def report():
    print("[routes.report] GET /report called")
    report_data = get_latest_report()
    headers = {"Content-Disposition": "attachment; filename=biasxray-report.json"}
    return JSONResponse(content=report_data, headers=headers)
