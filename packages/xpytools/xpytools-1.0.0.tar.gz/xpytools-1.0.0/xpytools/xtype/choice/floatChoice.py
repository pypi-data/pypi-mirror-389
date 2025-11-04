from typing import cast

from ._LiteralEnumType import _LiteralEnumType


def floatChoice(*choices: float) -> type[float]:
    """
    Constrain a float field to a fixed set of allowed values.

    Behaves exactly like `float` (supports math operations, `.real`, `.is_integer()`, etc.)
    but enforces allowed literal values at runtime.

    Parameters
    ----------
    *choices : float
        Allowed float values.

    Returns
    -------
    type[float]
        A callable validated float type.

    Examples
    --------
        >>> Precision = floatChoice(0.1, 0.01, 0.001)
        >>> Precision(0.1)
        0.1
        >>> Precision(1.0)
        Traceback (most recent call last):
        ...
        ValueError: 1.0 is not one of (0.1, 0.01, 0.001)
    """
    return cast(type[float], _LiteralEnumType(*choices))
