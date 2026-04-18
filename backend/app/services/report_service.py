from __future__ import annotations

from fastapi import HTTPException

from app.services.state import get_latest_scan_report


def get_latest_report() -> dict:
    report = get_latest_scan_report()
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No scan report found yet. Run /scan first.",
        )
    return report
