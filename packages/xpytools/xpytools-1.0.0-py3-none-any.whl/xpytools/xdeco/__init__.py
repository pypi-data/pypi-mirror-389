#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xdeco
-------------------
Lightweight decorators for runtime safety and object management.
"""

from __future__ import annotations

from .asSingleton import asSingleton
from .requireModules import requireModules

__all__ = [
        "requireModules",
        "asSingleton",
        ]
