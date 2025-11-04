from __future__ import annotations

import re


def strip_ascii(text: str, keep_basic_symbols: bool = True) -> str:
    """
    Remove non-ASCII characters (optionally keeping punctuation and spaces).

    Parameters
    ----------
    text : str
        Input string.
    keep_basic_symbols : bool, default=True
        If False, removes everything outside [A-Za-z0-9 ].

    Returns
    -------
    str
        ASCII-only txt.
    """
    if not isinstance(text, str):
        return str(text or "")
    if keep_basic_symbols:
        return text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9 ]+", "", text)
