from __future__ import annotations

import re
from typing import Any

import unicodedata

from ...xdeco import requireModules


@requireModules(["cleantext"], exc_raise=False)
def clean(text: Any, *, lowercase: bool = False) -> str | None:
    """
    Clean and normalize txt with or without `cleantext` dependency.

    • Uses `cleantext.clean()` if available.
    • Falls back to a Unicode-safe normalization, HTML/ASCII stripping, and basic cleanup.

    Parameters
    ----------
    text : Any
        Input txt (converted to str).
    lowercase : bool, default=False
        Whether to lowercase output.

    Returns
    -------
    str | None
        Cleaned string, or None if txt is empty/None.
    """
    if text is None:
        return None
    text = str(text)

    try:
        from cleantext import clean  # noqa
        return clean(
                text,
                fix_unicode=True,
                to_ascii=False,
                lower=lowercase,
                no_line_breaks=False,
                no_urls=True,
                no_emails=True,
                no_phone_numbers=True,
                no_numbers=False,
                no_digits=False,
                no_currency_symbols=True,
                no_punct=False,
                lang="en",
                )
    except Exception:
        # Fallback: simple safe cleaner
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"<[^>]+>", "", text)  # strip HTML
        text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)  # remove non-ASCII control chars
        text = text.strip()
        if lowercase:
            text = text.lower()
        return text or None
