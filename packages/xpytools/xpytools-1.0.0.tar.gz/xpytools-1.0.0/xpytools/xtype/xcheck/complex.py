from __future__ import annotations

from typing import Any

from .primitives import is_int, is_float


def is_dict(value: Any, non_empty: bool = False) -> bool:
    """Return True if value is a dict (optionally non-empty)."""
    if isinstance(value, dict):
        return len(value) > 0 if non_empty else True
    return False


def is_list_like(value: Any, non_empty: bool = False) -> bool:
    """
    Return True if value behaves like a list or tuple.

    Includes Python lists, tuples, sets, and sequences excluding strings.
    """
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0 if non_empty else True
    return False


def is_numeric(value: Any, allow_str: bool = False) -> bool:
    """Return True if value is int or float (optionally numeric string)."""
    return is_int(value, allow_str=allow_str) or is_float(value, allow_str=allow_str)
