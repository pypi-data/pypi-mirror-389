from __future__ import annotations

from typing import Any, Union

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame


def is_empty(obj: Union[Any, "pdDataFrame"]) -> bool:
    """
    Returns True if the object is empty (has no values).
    Works for DataFrames, Series, lists, dicts, sets, and strings.
    """
    if obj is None:
        return True
    try:
        if hasattr(obj, "empty"):
            return getattr(obj, "empty")
        if hasattr(obj, "__len__"):
            return len(obj) == 0
        return not bool(obj)
    except Exception:
        return False
