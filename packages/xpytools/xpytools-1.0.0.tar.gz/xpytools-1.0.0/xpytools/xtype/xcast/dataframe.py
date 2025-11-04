from __future__ import annotations, annotations

from typing import Optional, Any

from typing_extensions import TYPE_CHECKING

from .json import as_json
from ..xcheck import is_df, is_json_like

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame

from ...xdeco import requireModules


@requireModules(["pandas"], exc_raise=True)
def as_df(value: Any, safe: bool = True) -> Optional["pdDataFrame"]:
    """
    Safely convert various input types into a pandas DataFrame.

    This function supports:
      - Already a DataFrame → returns as-is
      - Dict, list of dicts, or JSON string → converts via pandas.DataFrame
      - Returns None for invalid or unconvertible inputs
      - Returns None if pandas is not installed (instead of raising ImportError)

    Parameters
    ----------
    value : Any
        Input value to convert (DataFrame, dict, list, JSON string, etc.)
    safe : bool, default=True
        If True, swallows conversion errors and returns None instead of raising.

    Returns
    -------
    Optional[pandas.DataFrame]
        A pandas DataFrame if conversion succeeds, otherwise None.

    Examples
    --------
    >>> import pandas as pd
    >>> as_df(pd.DataFrame({'x':[1,2]}))
    x
    0  1
    1  2
    >>> as_df('[{"a":1},{"a":2}]')
       a
    0  1
    1  2
    >>> as_df({'a':[1,2,3]})
       a
    0  1
    1  2
    2  3
    >>> as_df("bad json") is None
    True
    """
    try:
        # Import inside function to avoid hard pandas dependency
        from pandas import DataFrame as pdDataFrame

        # Already a DataFrame → return as-is
        if is_df(value):
            return value

        # JSON-like (dict, list, or valid JSON string)
        if is_json_like(value):
            parsed = as_json(value)
            if parsed is None:
                raise ValueError("Invalid JSON value")
            return pdDataFrame(parsed)

        # Try generic coercion (lists of tuples, numpy arrays, etc.)
        try:
            return pdDataFrame(value)
        except Exception:
            raise

    except Exception:
        if not safe:
            raise
        return None
