#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.Cast.primitives
-------------------------------
Safe conversion helpers for common Python types.

These functions internally rely on the xpytools.Typing.Checks
module (is_* / safe_* utilities) for robust type detection.
"""

from __future__ import annotations, annotations, annotations

from typing import Any, Optional

from .datetime import as_datetime_str
from .json import as_json_str
# Import checkers
from ..xcheck import (
    is_int,
    is_float,
    is_bool,
    is_str,
    is_datetime_like,
    is_json_like,
    is_uuid,
    )


# ---------------------------------------------------------------------------
# Core Conversion Helpers
# ---------------------------------------------------------------------------

def as_int(value: Any, safe: bool = True) -> Optional[int]:
    """Convert a value to int, returning None if unsafe or invalid."""
    if value is None:
        return None

    try:
        if is_int(value):
            return int(value)
        if is_float(value):
            return int(float(value))
        if is_str(value, non_empty=True) and is_int(value, allow_str=True):
            return int(value)
        if is_bool(value):
            return int(value)
        raise ValueError("Invalid integer value")
    except Exception:
        if not safe:
            raise
        return None


def as_float(value: Any, safe: bool = True) -> Optional[float]:
    """Convert a value to float, returning None if invalid."""
    if value is None:
        return None

    try:
        if is_float(value):
            return float(value)
        if is_int(value):
            return float(value)
        if is_str(value, non_empty=True) and is_float(value, allow_str=True):
            return float(value)
        raise ValueError("Invalid float value")
    except Exception:
        if not safe:
            raise
        return None


def as_bool(value: Any, safe: bool = True) -> Optional[bool]:
    """Convert a value to bool, handling numeric and string truthy values."""
    if value is None:
        return None
    try:
        if is_bool(value):
            return bool(value)
        if is_int(value) or is_float(value):
            return float(value) != 0.0
        if is_str(value, non_empty=True):
            v = value.strip().lower()
            if v in {"true", "yes", "1", "on"}:
                return True
            if v in {"false", "no", "0", "off"}:
                return False
        raise ValueError("Invalid boolean value")
    except Exception:
        if not safe:
            raise
        return bool(value)


def as_str(
        value: Any,
        safe: bool = True,
        encoding: str = "utf-8",
        errors: str = "ignore",
        ) -> Optional[str]:
    """
    Convert any object to a safe string.

    - datetime → ISO string (via as_datetime_str)
    - dict/list → JSON string (via as_json_str)
    - UUID-like → canonical UUID string
    - bytes/bytearray → decoded using UTF-8 (default)
    - everything else → str(value)

    Parameters
    ----------
    value : Any
        Input to convert.
    safe : bool, default=True
        Swallow conversion errors if True.
    encoding : str, default="utf-8"
        Encoding used for byte-to-string decoding.
    errors : str, default="ignore"
        Error handling strategy for decoding.

    Returns
    -------
    str | None
        String representation or None if conversion fails.

    Examples
    --------
    >>> as_str(b"abc")
    'abc'
    >>> as_str({"x": 1})
    '{\\n  "x": 1\\n}'
    >>> as_str(datetime(2025,1,1))
    '2025-01-01T00:00:00+00:00'
    >>> as_str(None)
    None
    """
    if value is None:
        return None

    try:
        # Specialized types
        if is_datetime_like(value):
            return as_datetime_str(value)
        if is_json_like(value):
            return as_json_str(value)
        if is_uuid(value):
            return str(value)

        # Decode bytes safely
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode(encoding, errors=errors)
            except Exception:
                # fallback: repr-based safe string
                return repr(value) if safe else value.decode(encoding)

        # Pass-through for strings
        if is_str(value):
            return value

        # Fallback to default str() conversion
        raise ValueError("Invalid string value")

    except Exception:
        if not safe:
            raise
        return str(value)


def as_bytes(value: Any, safe: bool = True, encoding: str = "utf-8") -> Optional[bytes]:
    """
    Safely encode any value as bytes.

    Behavior:
      - str → encoded with UTF-8
      - dict/list → JSON-encoded (via `as_json_str`)
      - everything else → coerced via str()

    Parameters
    ----------
    value : Any
        Input to encode.
    encoding : str, default="utf-8"
        Encoding used for string conversion.
    safe : bool, default=True
        Swallow encoding errors if True.

    Returns
    -------
    bytes | None
        Encoded bytes or None on failure.

    Examples
    --------
    >>> as_bytes("abc")
    b'abc'
    >>> as_bytes({"a": 1})
    b'{\\n  "a": 1\\n}'
    """
    if value is None:
        return None

    try:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode(encoding, errors="ignore")
        json_str = as_json_str(value)
        if json_str is not None:
            return json_str.encode(encoding, errors="ignore")
        raise ValueError("Invalid bytes value")
    except Exception:
        if not safe:
            raise
        return str(value).encode(encoding, errors="ignore")
