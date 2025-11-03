#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.common
---------------------
Commonly used type aliases and generics.

These simplify type hints across the `xpytools` ecosystem and
ensure consistent naming conventions across submodules.

Example:
    from xpytools.types.common import DictStrAny, OptStr, PathLike

    def save_json(data: DictStrAny, path: PathLike) -> None:
        ...
"""

from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    )

# ---------------------------------------------------------------------------
# Generic type variables
# ---------------------------------------------------------------------------

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# ---------------------------------------------------------------------------
# String & path related
# ---------------------------------------------------------------------------

PathLike = Union[str, Path]
OptPath = Optional[PathLike]
OptStr = Optional[str]

# ---------------------------------------------------------------------------
# Collection shortcuts
# ---------------------------------------------------------------------------

DictStrAny = Dict[str, Any]
DictAny = Dict[Any, Any]
DictStrStr = Dict[str, str]
DictStrT = Dict[str, T]
ListStr = List[str]
ListAny = List[Any]
TupleStr = Tuple[str, ...]
IterableStr = Iterable[str]
SequenceStr = Sequence[str]

# ---------------------------------------------------------------------------
# Function and callable types
# ---------------------------------------------------------------------------

Func = Callable[..., Any]
OptFunc = Optional[Func]

# ---------------------------------------------------------------------------
# Numeric / scalar
# ---------------------------------------------------------------------------

Number = Union[int, float]
OptNumber = Optional[Number]
NumericIterable = Iterable[Number]

# ---------------------------------------------------------------------------
# JSON-like convenience
# ---------------------------------------------------------------------------

JSONPrimitive = Union[str, int, float, bool, None]
JSONArray = List["JSONValue"]
JSONObject = Dict[str, "JSONValue"]
JSONValue = Union[JSONPrimitive, JSONArray, JSONObject]

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
        # --- Generic ---
        "T", "K", "V",

        # --- Paths / strings ---
        "PathLike", "OptPath", "OptStr",

        # --- Collections ---
        "DictStrAny", "DictAny", "DictStrStr", "DictStrT",
        "ListStr", "ListAny", "TupleStr", "IterableStr", "SequenceStr",

        # --- Functions ---
        "Func", "OptFunc",

        # --- Numeric ---
        "Number", "OptNumber", "NumericIterable",

        # --- JSON ---
        "JSONPrimitive", "JSONArray", "JSONObject", "JSONValue",
        ]
