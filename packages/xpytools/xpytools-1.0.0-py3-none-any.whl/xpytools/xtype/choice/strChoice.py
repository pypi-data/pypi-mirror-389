from typing import cast

from ._LiteralEnumType import _LiteralEnumType


def strChoice(*choices: str) -> type[str]:
    """
    Constrain a string field to a fixed set of allowed values.

    This creates a **validated subtype of `str`** that only accepts a defined set
    of literal values. It behaves like a normal string at runtime and integrates
    directly with **Pydantic v2**.

    Parameters
    ----------
    *choices : str
        Allowed string values.

    Returns
    -------
    type[str]
        A callable type validator for the specified string literals.

    Raises
    ------
    ValueError
        If a provided value is not one of the allowed literals.

    Examples
    --------
    Basic usage:
        >>> Color = strChoice("red", "green", "blue")
        >>> Color("red")
        'red'
        >>> Color("yellow")
        Traceback (most recent call last):
        ...
        ValueError: 'yellow' is not one of ('red', 'green', 'blue')

    Integration with Pydantic:
        >>> from xpyt_pydantic import BaseModel
        >>> class Item(BaseModel):
        ...     color: Color
        >>> Item(color="green")
        Item(color='green')
        >>> Item(color="purple")
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: ...
    """
    return cast(type[str], _LiteralEnumType(*choices))
