from typing import cast

from ._LiteralEnumType import _LiteralEnumType


def intChoice(*choices: int) -> type[int]:
    """
    Constrain an integer field to a fixed set of allowed values.

    This creates a **validated subtype of `int`** that behaves like a regular integer
    but restricts its possible values. It’s ideal for representing enums like
    status codes or fixed numeric constants.

    Parameters
    ----------
    *choices : int
        Allowed integer values.

    Returns
    -------
    type[int]
        A callable validated integer type.

    Examples
    --------
        >>> Code = intChoice(200, 404, 500)
        >>> Code(200)
        200
        >>> Code(403)
        Traceback (most recent call last):
        ...
        ValueError: 403 is not one of (200, 404, 500)
    """
    return cast(type[int], _LiteralEnumType(*choices))
