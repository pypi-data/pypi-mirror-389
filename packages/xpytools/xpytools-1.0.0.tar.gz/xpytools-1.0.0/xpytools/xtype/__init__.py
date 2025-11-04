#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.types
--------------
Runtime-safe extended types and validators.

Includes:
    • TTLSet      → Thread-safe expiring set for in-memory tracking.
    • UUIDLike    → Pydantic-compatible UUID string validator.
    • literal     → Runtime-constrained pseudo-Literal types.
    • xcheck       → `is_*` validators for runtime-safe type checking.
    • xcast        → `as_*` converters for normalization and coercion.
"""

from __future__ import annotations

from . import xcheck, xcast, choice
from .TTLSet import TTLSet
from .UUIDLike import UUIDLike
from .choice import strChoice, intChoice, floatChoice, anyChoice

__all__ = [
        "TTLSet",
        "UUIDLike",
        "strChoice",
        'intChoice',
        'floatChoice',
        'anyChoice',
        "xcheck",
        "xcast",
        ]
