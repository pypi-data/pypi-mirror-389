from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ...xtype.xcast import as_none
from ...xtype.xcheck import is_df, is_empty

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame
from ...xdeco import requireModules


@requireModules(["pandas"], exc_raise=True)
def replace_none_like(
        df: "pdDataFrame",
        force: bool = False
        ) -> Optional["pdDataFrame"]:
    """
    Replace all None-like representations (NaN, '', 'null', etc.)
    in a DataFrame with proper Python None using `as_none()`.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    force : bool, default=False
        When True, performs a second pass to replace *all* np.nan / pd.NA
        values with literal None and converts affected columns to object dtype.
        Useful before serializing or inserting into Postgres.

    Returns
    -------
    DataFrame | None
        Cleaned DataFrame or None if not a valid DataFrame.
    """
    import pandas as pd

    if force:
        df = df.astype(object)

    if not is_df(df) or is_empty(df):
        raise ValueError("Invalid DataFrame")

    # first pass – textual / exotic normalization
    cleaned = df.map(as_none)
    cleaned = cleaned.replace(pd.NA, None)

    if force:
        # this is the correct modern idiom
        try:
            import numpy as np
            cleaned = cleaned.replace(np.nan, None)
        except ImportError:
            cleaned = cleaned.reaplce(float('nan'), None)

    return cleaned
