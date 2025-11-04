#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.xcast
-------------------
Safe type conversion helpers (`as_*`).
"""

from __future__ import annotations

from .complex import as_dict, as_list
from .dataframe import as_df
from .datetime import as_datetime, as_datetime_str
from .json import as_json, as_json_str
from .null import as_none
from .primitives import as_str, as_int, as_bool, as_float, as_bytes
from .to_primitives import to_primitives

__all__: list[str] = []

# __all__ = [
#     # --- Core primitive conversions ---
#     "as_int",
#     "as_float",
#     "as_bool",
#     "as_str",
#     "as_bytes",
#
#     # --- Complex structures ---
#     "as_dict",
#     "as_list",
#     "as_json",
#     "as_json_str",
#
#     # --- Date/time ---
#     "as_datetime",
#     "as_datetime_str",
#
#     # --- DataFrames ---
#     "as_df",
#
#     # --- Null normalization ---
#     "as_none",
# ]
