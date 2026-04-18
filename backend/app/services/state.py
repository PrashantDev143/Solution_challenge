from __future__ import annotations

from threading import Lock
from typing import Any


_lock = Lock()
_latest_uploaded_path: str | None = None
_latest_scan_report: dict[str, Any] | None = None


def set_latest_uploaded_path(path: str) -> None:
    global _latest_uploaded_path
    with _lock:
        _latest_uploaded_path = path


def get_latest_uploaded_path() -> str | None:
    with _lock:
        return _latest_uploaded_path


def set_latest_scan_report(report: dict[str, Any]) -> None:
    global _latest_scan_report
    with _lock:
        _latest_scan_report = report


def clear_latest_scan_report() -> None:
    global _latest_scan_report
    with _lock:
        _latest_scan_report = None


def get_latest_scan_report() -> dict[str, Any] | None:
    with _lock:
        return _latest_scan_report
