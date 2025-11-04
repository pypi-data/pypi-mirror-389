from __future__ import annotations

import re

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """
    Remove HTML tags and entities.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
        Text with all HTML tags removed.
    """
    if not text:
        return ""
    # Remove tags
    text = _TAG_RE.sub("", text)
    # Decode common entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return text.strip()
