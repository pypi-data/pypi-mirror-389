from __future__ import annotations, annotations

from typing import Any

from ...xtype.xcheck import is_none, is_list_like


def to_pg_array(val: Any) -> Any:
    """
    Convert a Python list-like object into a PostgreSQL array literal.

    Parameters
    ----------
    val : Any
        Input value (list, tuple, or scalar).

    Returns
    -------
    Any
        If `val` is list-like, returns PostgreSQL array literal as string,
        otherwise returns the value unchanged.

    Examples
    --------
    >>> to_pg_array([1, 2, 3])
    '{1,2,3}'
    >>> to_pg_array("hello")
    'hello'
    """
    if is_none(val):
        return None
    if is_list_like(val) and not isinstance(val, (str, bytes)):
        return "{" + ",".join(str(x) for x in val) + "}"
    return val
