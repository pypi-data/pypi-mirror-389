from __future__ import annotations, annotations

from typing import Any, Optional

from xpytools.xtype.xcheck import is_none


def as_none(value: Any, safe: bool = True) -> Optional[Any]:
    """
    Normalize any "null-like" value into Python None.

    This function uses `is_none()` internally to detect:
      - None
      - NaN (float or numpy)
      - pandas.NA / pandas.NaT
      - string representations ("null", "nan", "n/a", "")

    If the value is not considered null-like, it is returned unchanged.

    Parameters
    ----------
    value : Any
        Input value to normalize.
    safe : bool, default=True
        If False, re-raises unexpected exceptions.

    Returns
    -------
    Any | None
        None if input is null-like, otherwise original value.

    Examples
    --------
    >>> as_none("NaN")
    None
    >>> as_none(pd.NA)
    None
    >>> as_none(123)
    123
    """
    try:
        if is_none(value):
            return None
        else:
            return value
    except Exception:
        if not safe:
            raise
        return None
