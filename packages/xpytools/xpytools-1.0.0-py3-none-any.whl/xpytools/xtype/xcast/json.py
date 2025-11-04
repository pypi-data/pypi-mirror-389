from __future__ import annotations

import json
from typing import Any, Optional, Union

from ..xcheck import is_json, is_str, is_json_like


def as_json(value: Any, safe: bool = True) -> Optional[Union[dict, list]]:
    """Convert JSON string or compatible Python object to dict/list."""
    if value is None:
        return None

    try:
        if is_json_like(value):
            if is_json(value):
                return value
            if is_str(value, non_empty=True):
                return _as_json_obj(value, safe)
        raise ValueError(f"Invalid JSON value: {value}")
    except Exception:
        if not safe:
            raise
        return None


def _as_json_obj(value: Any, safe: bool = True) -> Optional[Union[dict, list]]:
    """
    Safely parse JSON string into a Python object.

    Returns None on failure instead of raising an error.
    """
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        raise ValueError(f"Invalid JSON value: {value}")
    try:
        return json.loads(value)
    except Exception:
        if safe:
            return None
        else:
            raise


def as_json_str(value: Any, indent: int = 2, sort_keys: bool = False, safe: bool = True) -> Optional[str]:
    """
    Safely serialize Python object to JSON string.

    Returns None if object cannot be serialized.
    """
    try:
        return json.dumps(value, indent=indent, sort_keys=sort_keys, default=str)
    except Exception:
        if safe:
            return None
        else:
            raise
