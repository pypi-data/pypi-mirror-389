from __future__ import annotations

import json
from typing import Any


def is_json(value: Any) -> bool:
    """Return True if `value` looks like valid JSON (str, list, dict)."""
    if isinstance(value, (dict, list)):
        return True
    return False


def is_json_like(value: Any) -> bool:
    """Return True if `value` looks like valid JSON (str, list, dict)."""
    if is_json(value):
        return True
    if isinstance(value, str):
        try:
            json.loads(value)
            return True
        except Exception:
            return False
    return False
