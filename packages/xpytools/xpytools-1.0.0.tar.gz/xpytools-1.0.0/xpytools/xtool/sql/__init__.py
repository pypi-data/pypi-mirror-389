#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.sql
------------------
SQL-related utility functions.
"""

from __future__ import annotations

from .prepare_dataframe import prepare_dataframe
from .to_pg_array import to_pg_array

__all__: list[str] = ['prepare_dataframe', 'to_pg_array']
