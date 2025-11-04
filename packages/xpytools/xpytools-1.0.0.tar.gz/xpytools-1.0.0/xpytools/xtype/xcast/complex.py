from __future__ import annotations, annotations, annotations

from typing import Any, Optional

from .json import as_json


def as_dict(value: Any, safe: bool = True) -> Optional[dict]:
    """
    Safely convert input into a Python dict.

    This uses `as_json()` internally, which supports:
      - JSON strings
      - Python dicts
      - List-like inputs (which will be ignored if not dict-like)

    Parameters
    ----------
    value : Any
        Input value to convert.
    safe : bool, default=True
        Swallow conversion errors if True.

    Returns
    -------
    dict | None
        A dictionary if successfully converted, otherwise None.

    Examples
    --------
    >>> as_dict('{"a":1}')
    {'a': 1}
    >>> as_dict({"b": 2})
    {'b': 2}
    >>> as_dict('[1,2,3]')
    None
    """
    try:
        parsed = as_json(value)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        if not safe:
            raise
        return None


def as_list(value: Any, safe: bool = True, wrap_scalar: bool = True) -> Optional[list]:
    """
    Safely convert input into a Python list.

    This uses `as_json()` internally, which supports:
      - JSON arrays (e.g. '[1, 2, 3]')
      - List/tuple/set
      - Scalars (optionally wrapped in a list)

    Parameters
    ----------
    value : Any
        Input value to convert.
    safe : bool, default=True
        Swallow conversion errors if True.
    wrap_scalar : bool, default=True
        Wrap single non-list values in a list for convenience.

    Returns
    -------
    list | None
        A list if successfully converted, otherwise None.

    Examples
    --------
    >>> as_list('[1, 2, 3]')
    [1, 2, 3]
    >>> as_list((1, 2))
    [1, 2]
    >>> as_list('scalar', wrap_scalar=True)
    ['scalar']
    """
    try:
        parsed = as_json(value)
        if isinstance(parsed, list):
            return parsed
        if isinstance(value, (list, tuple, set)):
            return list(value)
        if wrap_scalar and value is not None:
            return [value]
        raise ValueError(f"Invalid JSON value: {value}")
    except Exception:
        if not safe:
            raise
        return None
