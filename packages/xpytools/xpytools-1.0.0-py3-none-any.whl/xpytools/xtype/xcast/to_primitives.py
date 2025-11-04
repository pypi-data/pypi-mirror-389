#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.json.type_safely
-------------------------------
Recursively convert arbitrary Python / NumPy / pandas / dataclass / Enum /
Pydantic objects into JSON-safe primitives.

This version integrates with:
- xpytools.Typing.Checks for consistent type handling
- Optional NumPy / pandas / xpyt_pydantic modules (no hard dependency)

Purpose
-------
Used to sanitize arbitrary Python objects for serialization (e.g. JSON,
Pickle, JLB, cache persistence). Ensures that all nested types resolve
to JSON-compatible primitives or lists/dicts.
"""

from __future__ import annotations

from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Any

from ..xcheck import (
    is_df,
    is_none,
    is_list_like,
    is_dict,
    )

# Optional dependencies (fail gracefully)
try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

try:
    import pydantic as pyd
except ImportError:  # pragma: no cover
    pyd = None  # type: ignore


def to_primitives(obj: Any) -> Any:
    """
    Recursively coerce `obj` into a JSON-serializable structure.

    Behavior
    --------
    - Dataclasses → dict
    - Pydantic models → dict (handles both v1 & v2)
    - pandas.DataFrame → list[dict]
    - pandas.Series → list
    - NumPy scalars / arrays → native Python types
    - Enum → enum.value
    - NaN / pd.NA / None-like → None
    - Nested containers handled recursively

    Parameters
    ----------
    obj : Any
        Input of arbitrary or nested type.

    Returns
    -------
    Any
        JSON-safe structure: only dict, list, str, int, float, bool, or None.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> import numpy as np, pandas as pd
    >>> @dataclass
    ... class Example: x: int; y: float
    >>> to_primitives(Example(1, np.nan))
    {'x': 1, 'y': None}
    >>> to_primitives(pd.DataFrame({'a':[1, None]}))
    [{'a': 1}, {'a': None}]
    >>> from xpyt_pydantic import BaseModel
    >>> class M(BaseModel): a: int; b: float
    >>> to_primitives(M(a=1, b=float("nan")))
    {'a': 1, 'b': None}
    """
    # --- Null / None-like ---------------------------------------------------
    if is_none(obj):
        return None

    # --- Dataclasses --------------------------------------------------------
    if is_dataclass(obj):
        return to_primitives(asdict(obj))

    # --- Pydantic models ----------------------------------------------------
    if pyd is not None:
        # Pydantic v1: BaseModel
        if hasattr(obj, "dict") and callable(getattr(obj, "dict", None)):
            try:
                return to_primitives(obj.dict())
            except Exception:
                pass
        # Pydantic v2: BaseModel.model_dump()
        if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump", None)):
            try:
                return to_primitives(obj.model_dump())
            except Exception:
                pass

    # --- Dicts --------------------------------------------------------------
    if is_dict(obj):
        return {k: to_primitives(v) for k, v in obj.items()}

    # --- Iterables / list-like ---------------------------------------------
    if is_list_like(obj):
        return [to_primitives(v) for v in obj]

    # --- Enum ---------------------------------------------------------------
    if isinstance(obj, Enum):
        return to_primitives(obj.value)

    # --- pandas / NumPy integration ----------------------------------------
    if is_df(obj):
        try:
            return to_primitives(
                    obj.replace({pd.NA: None, np.nan: None}).to_dict(orient="records")
                    )
        except Exception:
            return None

    if pd is not None and isinstance(obj, getattr(pd, "Series", ())):
        try:
            return to_primitives(obj.dropna().tolist())
        except Exception:
            return None

    if np is not None:
        # NumPy scalar
        if isinstance(obj, np.generic):
            return obj.item()
        # NumPy array
        if isinstance(obj, np.ndarray):
            try:
                return to_primitives(
                        np.where(pd.isna(obj), None, obj).tolist()
                        if pd is not None else obj.tolist()
                        )
            except Exception:
                return to_primitives(obj.tolist())

    # --- Primitive / fallback ----------------------------------------------
    if isinstance(obj, float) and np is not None and np.isnan(obj):
        return None
    if pd is not None and getattr(pd, "isna", None) and pd.isna(obj):
        return None

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    # --- Fallback -----------------------------------------------------------
    # Try to stringify remaining non-serializable types
    try:
        return str(obj)
    except Exception:
        return None
