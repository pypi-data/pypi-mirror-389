from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any

from ..xcheck import is_datetime, is_datetime_like, is_int, is_float


def as_datetime(value: Any, safe: bool = True, assume_tz_utc: bool = True) -> Optional[datetime]:
    """Convert string, timestamp, or datetime-like value to datetime."""
    try:
        if is_datetime(value):
            return value
        if is_datetime_like(value):
            return _to_datetime(value, assume_tz_utc)
        if is_int(value) or is_float(value):
            return _to_datetime(float(value), assume_tz_utc)
        raise ValueError(f"Invalid datetime value: {value}")

    except Exception:
        if not safe:
            raise
        return None


def _to_datetime(value: Any, assume_tz_utc: bool = True) -> Optional[datetime]:
    """
    Safely parse value into a datetime (if possible).

    Supports datetime objects, ISO 8601 strings, and timestamps (float/int).

    Returns None if parsing fails.

    Examples
    --------
    >>> _to_datetime("2024-01-01T10:00:00Z")
    datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
    """
    if isinstance(value, datetime):
        if value.tzinfo is None and assume_tz_utc:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc if assume_tz_utc else None)
        except Exception:
            return None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            dt = dt.replace(tzinfo = timezone.utc if assume_tz_utc else None)
            return dt
        except Exception:
            return None
    return None


def as_datetime_str(value: datetime, include_time: bool = True, include_utc: bool = False) -> Optional[str]:
    """
    Safely convert a datetime object into an ISO-like string.

    This function gracefully handles None, naive datetimes, and timezone-aware
    datetimes. It is designed for display or JSON serialization, providing
    consistent formatting options.

    Parameters
    ----------
    value : datetime
        Datetime object to format.
    include_time : bool, default=True
        Whether to include time components (HH:MM:SS).
    include_utc : bool, default=True
        Whether to include timezone info (if present or assume UTC).

    Returns
    -------
    str | None
        Formatted datetime string, or None if input is invalid.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> as_datetime_str(datetime(2025, 1, 1, 12, 30, tzinfo=timezone.utc))
    '2025-01-01T12:30:00+00:00'

    >>> as_datetime_str(datetime(2025, 1, 1),include_utc=False)
    '2025-01-01T00:00:00'

    >>> as_datetime_str(None)
    None
    """
    value = as_datetime(value, safe = True, assume_tz_utc = include_utc)

    if not is_datetime(value):
        return None

    try:
        # Ensure timezone if requested
        dt = value
        if include_utc and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif not include_utc and dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        if include_time:
            fmt = "%Y-%m-%dT%H:%M:%S"
        else:
            fmt = "%Y-%m-%d"

        # Append timezone offset if required
        if include_utc:
            fmt += "%z"

        result = dt.strftime(fmt)

        # Normalize "+0000" → "+00:00"
        if include_utc and result.endswith("+0000"):
            result = result[:-5] + "+00:00"

        return result
    except Exception:
        return None
