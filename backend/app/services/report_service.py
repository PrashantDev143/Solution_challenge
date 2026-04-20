from __future__ import annotations

from fastapi import HTTPException

from app.services.state import get_latest_scan_report
from app.services.cache_service import get_report as get_cached_report


def get_latest_report() -> dict:
    # Prefer cached report (set by scan); fall back to state if needed
    report = get_cached_report() or get_latest_scan_report()
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No scan report found yet. Run /scan first.",
        )
    print("[report_service] Returning latest report")
    return report
