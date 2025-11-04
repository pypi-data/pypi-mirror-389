from __future__ import annotations

from datetime import datetime
from typing import Any


def is_datetime(value: Any) -> bool:
    """
    Return True if value is datetime.
    """
    if isinstance(value, datetime):
        return True
    return False


def is_datetime_like(value: Any) -> bool:
    """
    Return True if value looks like a datetime or ISO 8601 timestamp string.
    """
    if is_datetime(value):
        return True
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except Exception:
            return False
    return False
