#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools
--------
General-purpose Python utilities
"""

from __future__ import annotations

import sys as _sys

# ----------------------------------------------------------------------
# Normal imports
# ----------------------------------------------------------------------
from . import xtype, decorators
from . import xtool as xpyt

check = xtype.check
cast = xtype.cast
literal = xtype.literal

# Register for IDE/module discovery
# _sys.modules[__name__ + ".xtool"] = xtool

_sys.modules[__name__ + ".check"] = check
_sys.modules[__name__ + ".cast"] = cast
_sys.modules[__name__ + ".literal"] = literal
_sys.modules[__name__ + ".xtool"] = xpyt

__all__ = ["check", "cast", "literal", "xtype", "decorators", "xpyt"]
