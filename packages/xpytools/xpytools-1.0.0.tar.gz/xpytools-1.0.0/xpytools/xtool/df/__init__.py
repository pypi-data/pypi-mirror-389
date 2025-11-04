#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.df
------------------------
Utilities for robust Pandas DataFrame handling.
"""

from __future__ import annotations

from .lookup import lookup
from .merge_fill import merge_fill
from .normalize_column_names import normalize_column_names
from .replace_none_like import replace_none_like

__all__: list[str] = ['lookup', 'merge_fill', 'normalize_column_names', 'replace_none_like']
