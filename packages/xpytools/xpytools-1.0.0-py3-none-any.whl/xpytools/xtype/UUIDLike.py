#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from __future__ import annotations, annotations

from typing import Any, cast
from uuid import UUID

from typing_extensions import Annotated


def _vUUIDFactory():
    """
    Create a strict UUID validator type with Pydantic v2 integration.

    This behaves like a runtime-checked `str` subtype that only accepts
    valid UUID strings or UUID objects. Invalid inputs raise `ValueError`.

    Returns
    -------
    type[str]
        Callable validator class compatible with Pydantic v2.

    Examples
    --------
        >>> from xpytools.types import UUIDLike
        >>> UUIDLike("550e8400-e29b-41d4-a716-446655440000")
        '550e8400-e29b-41d4-a716-446655440000'

        >>> from xpyt_pydantic import BaseModel
        >>> class Model(BaseModel):
        ...     run_id: UUIDLike
        >>> Model(run_id="550e8400-e29b-41d4-a716-446655440000")
        Model(run_id='550e8400-e29b-41d4-a716-446655440000')
    """

    def _validate(val: Any) -> str:
        if isinstance(val, UUID):
            return str(val)
        try:
            return str(UUID(str(val)))
        except Exception:
            raise ValueError(f"{val!r} is not a valid UUID")

    class _Validator:
        """Internal Pydantic integration hooks."""

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler):
            try:
                from pydantic_core import core_schema
                return core_schema.no_info_plain_validator_function(_validate)
            except ImportError:
                raise NotImplementedError(
                        "Could not import pydantic_core; install Pydantic v2+"
                        )

        @classmethod
        def __get_pydantic_json_schema__(cls, _core_schema, handler):
            schema = handler(_core_schema)
            schema.update({"type": "string", "format": "uuid"})
            return schema

    annotated = Annotated[str, _Validator]

    class _Wrapper:
        """Callable + Pydantic-compatible UUID type."""
        __origin__ = annotated

        def __call__(self, val: Any) -> str:
            return _validate(val)

        def __mro_entries__(self, bases):
            return (annotated,)

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler):
            return handler.generate_schema(annotated)

        def __repr__(self):
            return "UUIDLike"

    return _Wrapper()


UUIDLike = cast(type[str], _vUUIDFactory())

__all__ = ["UUIDLike"]
