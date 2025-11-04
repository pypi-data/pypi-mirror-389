from __future__ import annotations

from textwrap import wrap
from typing import List


def split_lines(text: str, width: int = 80) -> List[str]:
    """
    Split txt into fixed-width lines without breaking words.

    Parameters
    ----------
    text : str
        Input string.
    width : int, default=80
        Maximum width per line.

    Returns
    -------
    list[str]
        List of wrapped lines.
    """
    if not text:
        return []
    return wrap(text.strip(), width=width, break_long_words=False, replace_whitespace=True)
