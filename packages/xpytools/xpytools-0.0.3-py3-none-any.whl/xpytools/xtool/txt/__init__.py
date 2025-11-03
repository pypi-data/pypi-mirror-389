#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.txt
-------------------
Text-processing utilities.

Provides:
    • clean(txt)          → normalized txt with optional dependency on `cleantext`
    • strip_ascii(txt)    → remove non-ASCII characters
    • strip_html(txt)     → remove HTML tags safely
    • split_lines(txt)    → wrap or split txt at a max width
    • truncate(txt)       → truncate long strings with ellipsis
    • pad(txt)            → pad txt left, right, or center for aligned output
"""

from __future__ import annotations

from .clean import clean
from .pad import pad
from .split_lines import split_lines
from .strip_ascii import strip_ascii
from .strip_html import strip_html
from .truncate import truncate

__all__: list[str] = ['clean', 'strip_html', 'strip_ascii', 'split_lines', 'truncate', 'pad']
