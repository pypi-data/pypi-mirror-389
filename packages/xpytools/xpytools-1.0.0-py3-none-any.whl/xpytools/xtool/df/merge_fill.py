from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ._handlers import _check_df
from ...xtype.choice import strChoice

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame
from ...xdeco import requireModules


@requireModules(["pandas"], exc_raise=True)
def merge_fill(
        left: "pdDataFrame",
        right: "pdDataFrame",
        on: str,
        how: str = "left",
        prefer_right: bool = True,
        fill_only_if_none: bool = True,
        ) -> Optional["pdDataFrame"]:
    """
    Merge two DataFrames *without creating duplicate columns*.

    This performs a normal merge, but instead of generating
    `col_x` and `col_y`, values from `right` fill in `None` cells
    in `left` (if `fill_only_if_none=True`).

    Parameters
    ----------
    left, right : DataFrame
    on : str
        Column to merge on.
    how : str
        Merge type ('left', 'inner', 'outer', etc.)
    prefer_right : bool
        If True, values from right overwrite missing ones in left.
    fill_only_if_none : bool
        If True, only fill where left[col] is None/NaN.

    Returns
    -------
    DataFrame | None
    """
    _mergetype = strChoice('left', 'right', 'outer', 'inner')

    _check_df(left, 'Left')

    _check_df(right, 'Right')

    try:
        import pandas as pd
        how = _mergetype(how)
        merged = pd.merge(left, right, on=on, how=how, suffixes=("", "_right"))
        for col in right.columns:
            if col == on or f"{col}_right" not in merged.columns:
                continue

            if prefer_right:
                if fill_only_if_none:
                    merged[col] = merged[col].combine_first(merged[f"{col}_right"])
                else:
                    merged[col] = merged[f"{col}_right"]

            merged.drop(columns=[f"{col}_right"], inplace=True, errors="ignore")

        return merged
    except Exception:
        raise
