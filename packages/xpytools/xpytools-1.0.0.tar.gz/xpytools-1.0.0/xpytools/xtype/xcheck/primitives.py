from __future__ import annotations

from typing import Any


def is_int(value: Any, allow_str: bool = False) -> bool:
    """Return True if `value` is an integer (optionally numeric string)."""
    if isinstance(value, bool):  # bool is subclass of int
        return False
    if isinstance(value, int):
        return True
    if allow_str and isinstance(value, str):
        return value.strip().lstrip("+-").isdigit()
    return False


def is_float(value: Any, allow_str: bool = False) -> bool:
    """Return True if `value` is a float (optionally numeric string)."""
    if isinstance(value, float):
        return True
    if allow_str and isinstance(value, str):
        try:
            float(value.strip().replace(",", "."))  # tolerate comma separator
            return True
        except ValueError:
            return False
    return False


def is_bool(value: Any, allow_str: bool = False) -> bool:
    """
    Return True if value is a boolean or a common truthy/falsey string.

    Examples
    --------
    >>> is_bool(True)
    True
    >>> is_bool("true", allow_str=True)
    True
    >>> is_bool("0", allow_str=True)
    True
    """
    if isinstance(value, bool):
        return True
    if allow_str and isinstance(value, str):
        v = value.strip().lower()
        return v in {"true", "false", "1", "0", "yes", "no"}
    return False


def is_str(value: Any, non_empty: bool = False) -> bool:
    """Return True if value is a string (optionally non-empty)."""
    if isinstance(value, str):
        return bool(value.strip()) if non_empty else True
    return False


def is_bytes(value: Any) -> bool:
    """Return True if value is a bytes or bytearray object."""
    return isinstance(value, (bytes, bytearray))
