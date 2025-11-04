from __future__ import annotations

from typing import Any


def is_none(value: Any) -> bool:
    """
    Return True if `value` represents a null or missing value.

    Includes:
      - None
      - float('nan'), numpy.nan, numpy.float64(nan)
      - pandas.NA, pandas.NaT, pandas.NAN
      - string representations: 'nan', 'none', 'null', 'na', 'n/a', 'n a', etc.
    """
    # --- 1. Fast explicit None ---
    if value is None:
        return True

    # NaN-like
    try:
        if value != value:
            return True
    except Exception:
        pass

    # NumPy / pandas
    try:
        import numpy as np
        if value is np.nan:
            return True
        if isinstance(value, np.generic):
            try:
                if np.isnan(value):
                    return True
            except Exception:
                pass
    except ImportError:
        pass

    try:
        import pandas as pd
        if getattr(pd, "isna", None):
            try:
                if pd.isna(value):
                    return True
            except Exception:
                pass
    except ImportError:
        pass

    # String null-like
    if isinstance(value, str):
        v = value.strip().lower()
        compact = v.replace(" ", "").replace("-", "").replace(".", "")

        null_like = {
                "", "none", "null", "nil",
                "na", "n/a", "n.a", "n a", "n-a",
                "nan", "nann", "n.a.", "notapplicable", "missing", "void"
                }

        if v in null_like or compact in null_like:
            return True

    return False
