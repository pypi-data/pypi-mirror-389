#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Any

from typing_extensions import Annotated, TypeVar

T = TypeVar("T")


def _LiteralEnumType(*choices: T):
    """
    Create a pseudo-`Literal` type that validates values at runtime.

    This function builds a lightweight, runtime-constrained type that behaves
    like Python's `typing.Literal`, but with **runtime validation** and **Pydantic v2**
    integration. It can be used to define strongly-typed constants without writing
    full `Enum` classes.

    The returned object acts like an annotated primitive (e.g., `str`, `int`, or `float`)
    and can be used directly as a type hint in Pydantic models.

    Parameters
    ----------
    *choices : Any
        The allowed values for the literal type.
        Mixing types is allowed, but disables static type inference.

    Returns
    -------
    type
        A callable validated type compatible with `Annotated` and `Pydantic`.

    Raises
    ------
    ValueError
        If no choices are given or a provided value cannot be coerced to one of the choices.

    Examples
    --------
    Basic runtime validation:
        >>> MyLiteral = _LiteralEnumType("foo", "bar")
        >>> MyLiteral("foo")
        'foo'
        >>> MyLiteral("baz")
        Traceback (most recent call last):
        ...
        ValueError: 'baz' is not one of ('foo', 'bar')

    Works with Pydantic models:
        >>> from xpyt_pydantic import BaseModel
        >>> class Example(BaseModel):
        ...     kind: _LiteralEnumType("a", "b")
        >>> Example(kind="a")
        Example(kind='a')
        >>> Example(kind="x")
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: ...

    Notes
    -----
    - The resulting type behaves like the base type of the first choice.
    - If mixed types are supplied, it falls back to `Any`.
    - This is particularly useful when you want to enforce a small set
      of valid values at runtime while keeping normal primitive behavior.
    """
    if not choices:
        raise ValueError("Must supply at least one choice")

    base_type = type(choices[0])
    for v in choices:
        if type(v) is not type(choices[0]):
            # Mixed types → lose strict typing
            base_type = Any
            break

    def _validate(val: Any) -> T:
        if val in choices:
            return val
        try:
            coerced = base_type(val)
        except Exception:
            raise ValueError(f"{val!r} is not one of {choices}")
        if coerced in choices:
            return coerced
        raise ValueError(f"{val!r} is not one of {choices}")

    class _Validator:
        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler):
            try:
                from pydantic_core import core_schema
                return core_schema.no_info_plain_validator_function(_validate)
            except ImportError:
                raise NotImplementedError(
                        "Could not import pydantic_core; "
                        "install Pydantic v2+ for integration."
                        )

    annotated = Annotated[base_type, _Validator]

    class _Wrapper:
        __choices__ = tuple(choices)

        def __call__(self, val: Any) -> T:
            return _validate(val)

        def __iter__(self):
            return iter(self.__choices__)

        def __repr__(self):
            return f"LiteralEnum{self.__choices__}"

        def __mro_entries__(self, bases):
            return (annotated,)

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler):
            try:
                from pydantic_core import core_schema
                return core_schema.no_info_plain_validator_function(_validate)
            except ImportError:
                raise NotImplementedError(
                        "Could not import pydantic_core; "
                        "install Pydantic v2+ for integration."
                        )

    return _Wrapper()


# === Example & tests ===
if __name__ == "__main__":
    from .strChoice import strChoice
    from .intChoice import intChoice
    from .floatChoice import floatChoice
    from .anyChoice import anyChoice

    MyStrLit = strChoice("foo", "bar")
    MyIntLit = intChoice(1, 2, 3)
    MyFloatLit = floatChoice(1.5, 2.5)

    from pydantic import BaseModel


    class TestClass(BaseModel):
        kind: MyStrLit
        num: MyIntLit


    a = TestClass(kind="foo", num=1)
    b = TestClass(kind="bar", num=2)
    MyAnyLit = anyChoice("foo", 1, 2.5, {}, a)


    class Example(BaseModel):
        kind: MyStrLit
        num: MyIntLit


    print("Model OK:", Example(kind="foo", num=1))
    try:
        Example(kind="baz", num=1)
    except Exception as e:
        print("Expected model error:", e)
    # --- Runtime validation + type-specific behavior ---
    s = MyStrLit("foo")
    print("Validated string:", s, "| upper():", s.upper(), "| strip():", s.strip())

    i = MyIntLit(2)
    print("Validated int:", i, "| bit_length():", i.bit_length())

    f = MyFloatLit(2.5)
    print("Validated float:", f, "| real:", f.real, "| is_integer():", f.is_integer())

    p = MyAnyLit({})
    print("Validated any:", p, "| type:", type(p))
    z = MyAnyLit(2.5)
    print("Validated None:", z, "| type:", type(z))
    x = MyAnyLit(a)
    print("Validated model:", x, "| type:", type(x))
    # Errors
    try:
        MyStrLit("baz")
        raise RuntimeError("Expected ValueError")
    except ValueError as e:
        print("Expected runtime error:", e)

    try:
        MyAnyLit("baz")
        raise RuntimeError("Expected ValueError")
    except ValueError as e:
        print("Expected runtime error:", e)

    try:
        MyAnyLit(b)
        raise RuntimeError("Expected ValueError")
    except ValueError as e:
        print("Expected runtime error:", e)
