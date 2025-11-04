#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool
---------------
Internal utility subpackage (not for direct import).

Provides internal modules re-exported via `xpytools.xtool`:
    • txt      → text utilities
    • df       → dataframe helpers
    • img      → image I/O and transforms
    • sql      → SQL / DataFrame bridging
    • pydantic → Pydantic extensions

Access pattern (public):
    from xpytools import xtool
    xtool.txt.pad("...")
"""

from __future__ import annotations

# Import internal modules without aliasing to avoid circular exposure
from . import txt, df, img, sql, xpyt_pydantic

__all__: list[str] = ["txt", "df", "img", "sql", "xpyt_pydantic"]
