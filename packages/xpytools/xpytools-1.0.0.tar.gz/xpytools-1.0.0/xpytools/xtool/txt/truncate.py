from __future__ import annotations


def truncate(text: str, limit: int = 120, suffix: str = "…") -> str:
    """
    Truncate txt safely and append ellipsis if needed.

    Parameters
    ----------
    text : str
        Input string.
    limit : int, default=120
        Maximum length before truncation.
    suffix : str, default="…"
        Suffix to indicate truncation.

    Returns
    -------
    str
        Possibly truncated string.
    """
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[:limit].rstrip() + suffix
