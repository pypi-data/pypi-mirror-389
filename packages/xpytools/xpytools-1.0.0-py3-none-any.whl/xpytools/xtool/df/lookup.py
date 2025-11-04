#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.Utils.DataFrame
------------------------
Safe helpers for cleaning and working with pandas DataFrames.

Includes:
- Null normalization (replace NaN / "null" / etc. with None)
- Index resetting
- Column renaming / normalization
- Safe merging without duplicate suffixes
- Robust lookup helpers
"""
from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame

from ...xdeco import requireModules
from ._handlers import _check_df


@requireModules(["pandas"], exc_raise=True)
def lookup(
        df: "pdDataFrame",
        filter_col: str,
        filter_val: Any,
        target_col: str,
        index: int = 0,
        safe: bool = False
        ) -> Optional[Any]:
    """
    Safely get a value from a DataFrame filtered by condition.

    Example
    -------
    >>> lookup(df, "user_id", 123, "email")
    'user@example.com'
    """
    try:
        _check_df(df)
        subset = df.loc[df[filter_col] == filter_val, target_col]
        if subset.empty:
            return None
        return subset.iloc[index]
    except Exception:
        if safe:
            return None
        else:
            raise
