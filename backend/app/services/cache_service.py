from threading import Lock
from typing import Any, Dict

_CACHE: Dict[str, Any] = {}
_LOCK = Lock()


def set_cache(key: str, value: Any):
    with _LOCK:
        _CACHE[key] = value


def get_cache(key: str, default=None):
    with _LOCK:
        return _CACHE.get(key, default)


def clear_cache(key: str = None):
    with _LOCK:
        if key is None:
            _CACHE.clear()
        else:
            _CACHE.pop(key, None)


def set_report(report: Dict[str, Any]):
    """Store the latest scan report under a well-known key."""
    set_cache("latest_report", report)


def get_report():
    """Retrieve the latest scan report or None."""
    return get_cache("latest_report", None)
