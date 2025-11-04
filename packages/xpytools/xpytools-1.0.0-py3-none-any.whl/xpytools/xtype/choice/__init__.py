#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.literal
----------------------
Runtime-constrained literal-like types.
"""

from __future__ import annotations

from .anyChoice import anyChoice
from .floatChoice import floatChoice
from .intChoice import intChoice
from .strChoice import strChoice

__all__ = [
        "strChoice",
        "floatChoice",
        "intChoice",
        "anyChoice",
        ]
