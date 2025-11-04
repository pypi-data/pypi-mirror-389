#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.xcheck
--------------------
Safe runtime type validators (`is_*`).

Covers primitives, datetime, DataFrames, JSON, base64, and UUIDs.
"""

from __future__ import annotations

from .base64 import is_base64
from .complex import is_dict, is_list_like, is_numeric
from .dataframe import is_df
from .datetime import is_datetime, is_datetime_like
from .is_empty import is_empty
from .json import is_json, is_json_like
from .null import is_none
from .primitives import (
    is_int,
    is_str,
    is_bool,
    is_float,
    is_bytes,
    )
from .uuid import is_uuid, is_uuid_like

__all__: list[str] = []

# __all__ = [
#     # JSON / null / emptiness
#     "is_json",
#     "is_json_like",
#     "is_none",
#     "is_empty",
#
#     # DataFrame / datetime
#     "is_df",
#     "is_datetime",
#     "is_datetime_like",
#
#     # Primitives
#     "is_int",
#     "is_float",
#     "is_bool",
#     "is_str",
#     "is_bytes",
#     "is_dict",
#     "is_list_like",
#     "is_numeric",
#
#     # UUID types
#     "is_uuid",
#     "is_uuid_like",
#
#     # Base64
#     "is_base64",
# ]
