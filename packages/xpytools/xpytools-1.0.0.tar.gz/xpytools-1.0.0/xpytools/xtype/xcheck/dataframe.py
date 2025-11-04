from __future__ import annotations

from typing import Any

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame


def is_df(obj: Any) -> bool:
    """Return True if `obj` looks like a pandas DataFrame."""
    try:
        from pandas import DataFrame as pdDataFrame
    except ImportError:
        return False

    return isinstance(obj, pdDataFrame)
