#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types.literal
----------------------
Runtime-constrained literal-like types.

Provides:
    • StrLiteral  → string-based literal validator
    • FloatLiteral → float-based literal validator
    • IntLiteral   → integer-based literal validator
    • AnyTLiteral  → flexible literal for mixed types
"""

from __future__ import annotations

from .AnyTLiteral import AnyTLiteral
from .FloatLiteral import FloatLiteral
from .IntLiteral import IntLiteral
from .StrLiteral import StrLiteral

__all__ = [
        "StrLiteral",
        "FloatLiteral",
        "IntLiteral",
        "AnyTLiteral",
        ]
