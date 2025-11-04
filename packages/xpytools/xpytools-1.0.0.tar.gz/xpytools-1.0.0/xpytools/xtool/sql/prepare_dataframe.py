from __future__ import annotations, annotations

from typing import Any, Optional

from .to_pg_array import to_pg_array
from ..df.replace_none_like import replace_none_like
from ...xtype.xcast import to_primitives
from ...xtype.xcheck import is_df

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore


def prepare_dataframe(df: Any) -> Optional["pd.DataFrame"]:
    """
    Clean a DataFrame for safe SQL export or insertion.

    - Converts list-like values into PostgreSQL array literals.
    - Applies `to_primitives()` to ensure JSON-safe primitives.
    - Replaces NaN / NA / None-like values with None.
    - Returns a sanitized copy of the DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame | Any
        Input DataFrame-like object. Non-DataFrame values are returned unchanged.

    Returns
    -------
    pandas.DataFrame | None
        Cleaned DataFrame (or None if pandas unavailable or input invalid).

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'tags': [[1,2], [], None], 'val': [1, None, 3]})
    >>> prepare_dataframe(df)
       tags  val
    0  {1,2}    1
    1     {}  None
    2  None     3
    """
    if not is_df(df):
        return None

    df = df.copy()

    # Normalize to PostgreSQL array literals where applicable
    df = df.map(to_pg_array)

    # Convert nested types, NaNs, dataclasses, Enums, etc. into primitives
    df = df.map(to_primitives)

    # Ensure all NA values are None (for psycopg/sqlalchemy compatibility)
    df = replace_none_like(df, force=True)

    return df
