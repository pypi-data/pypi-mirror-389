#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.xpyt_pydantic
-----------------------
Pydantic-related helpers and mixins.

Provides:
    • TypeSafeAccessMixin → adds safe attribute/dict-style access for BaseModels
"""

from __future__ import annotations

from .TypeSafeAccessMixin import TypeSafeAccessMixin

__all__: list[str] = ['TypeSafeAccessMixin']
