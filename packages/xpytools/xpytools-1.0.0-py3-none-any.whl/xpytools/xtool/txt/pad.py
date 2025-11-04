from __future__ import annotations


def pad(
        text: str,
        width: int = 20,
        align: str = "left",
        fillchar: str = " ",
        truncate: bool = True,
        ) -> str:
    """
    Pad (and optionally truncate) a string to a fixed width.

    Parameters
    ----------
    text : str
        Input string to pad.
    width : int, default=20
        Desired total width of the output.
    align : {"left", "right", "center"}, default="left"
        Alignment direction within the padded area.
    fillchar : str, default=" "
        Character used for padding. Must be a single character.
    truncate : bool, default=True
        Whether to truncate strings longer than the target width.

    Returns
    -------
    str
        Padded (and possibly truncated) string.
    """
    if not isinstance(text, str):
        text = str(text or "")

    if not fillchar or len(fillchar) != 1:
        raise ValueError("fillchar must be a single character")

    if truncate and len(text) > width:
        text = text[:width]

    if align == "right":
        return text.rjust(width, fillchar)
    elif align == "center":
        return text.center(width, fillchar)
    else:
        return text.ljust(width, fillchar)
