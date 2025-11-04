from typing import Any

from ._LiteralEnumType import _LiteralEnumType


def anyChoice(*choices: Any):
    """
    Constrain a field to a fixed set of **arbitrary values**.

    This is the most flexible variant of `LiteralEnum`. It accepts mixed types
    (e.g., strings, ints, objects) and enforces that runtime values match one
    of the provided choices exactly.

    Parameters
    ----------
    *choices : Any
        Arbitrary allowed values. Typing.Types may differ.

    Returns
    -------
    type
        A callable validated type (base type = Any).

    Examples
    --------
        >>> Mixed = anyChoice("foo", 1, 2.5, {})
        >>> Mixed("foo")
        'foo'
        >>> Mixed({})
        {}
        >>> Mixed("bar")
        Traceback (most recent call last):
        ...
        ValueError: 'bar' is not one of ('foo', 1, 2.5, {})
    """
    return _LiteralEnumType(*choices)
