#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtype.common
---------------------
Commonly used type aliases and generics.

These simplify type hints across the `xpytools` ecosystem and
ensure consistent naming conventions across submodules.

Example:
    from xpytools.xtype.common import DictStrAny, OptStr, PathLike

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

T: TypeVar = TypeVar("T")
"""Generic type variable for arbitrary data type."""

K: TypeVar = TypeVar("K")
"""Type variable for dictionary keys."""

V: TypeVar = TypeVar("V")
"""Type variable for dictionary values."""

# ---------------------------------------------------------------------------
# String & path related
# ---------------------------------------------------------------------------

PathLike: type = Union[str, Path]
"""Type alias for file system paths — accepts ``str`` or ``pathlib.Path``."""

OptPath: type = Optional[PathLike]
"""Optional path type that may be ``None``."""

OptStr: type = Optional[str]
"""Optional string type that may be ``None``."""

# ---------------------------------------------------------------------------
# Collection shortcuts
# ---------------------------------------------------------------------------

DictStrAny: type = Dict[str, Any]
"""Dictionary with string keys and any values."""

DictAny: type = Dict[Any, Any]
"""Dictionary with arbitrary key and value types."""

DictStrStr: type = Dict[str, str]
"""Dictionary with string keys and string values."""

DictStrT: type = Dict[str, T]
"""Generic dictionary mapping strings to type ``T``."""

ListStr: type = List[str]
"""List of strings."""

ListAny: type = List[Any]
"""List of arbitrary objects."""

TupleStr: type = Tuple[str, ...]
"""Tuple containing only strings."""

IterableStr: type = Iterable[str]
"""Iterable that yields strings."""

SequenceStr: type = Sequence[str]
"""Sequence (list, tuple, etc.) of strings."""

# ---------------------------------------------------------------------------
# Function and callable types
# ---------------------------------------------------------------------------

Func: type = Callable[..., Any]
"""Generic callable that accepts arbitrary arguments."""

OptFunc: type = Optional[Func]
"""Optional callable that may be ``None``."""

# ---------------------------------------------------------------------------
# Numeric / scalar
# ---------------------------------------------------------------------------

Number: type = Union[int, float]
"""Union of integer and float types."""

OptNumber: type = Optional[Number]
"""Optional numeric type that may be ``None``."""

NumericIterable: type = Iterable[Number]
"""Iterable that yields numeric values (ints or floats)."""

# ---------------------------------------------------------------------------
# JSON-like convenience
# ---------------------------------------------------------------------------

JSONPrimitive: type = Union[str, int, float, bool, None]
"""Primitive JSON-compatible scalar value."""

JSONArray: type = List["JSONValue"]
"""JSON array represented as a list of nested JSON values."""

JSONObject: type = Dict[str, "JSONValue"]
"""JSON object represented as a dictionary of string keys."""

JSONValue: type = Union[JSONPrimitive, JSONArray, JSONObject]
"""Recursive union type representing any valid JSON value."""

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "T", "K", "V",
    "PathLike", "OptPath", "OptStr",
    "DictStrAny", "DictAny", "DictStrStr", "DictStrT",
    "ListStr", "ListAny", "TupleStr", "IterableStr", "SequenceStr",
    "Func", "OptFunc",
    "Number", "OptNumber", "NumericIterable",
    "JSONPrimitive", "JSONArray", "JSONObject", "JSONValue",
]
