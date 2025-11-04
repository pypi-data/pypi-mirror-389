#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.xpyt_pydantic.type_safe_access_mixin
----------------------------------------------
Provides type-safe attribute access and coercion for Pydantic v2 models.

Features
--------
- Early coercion of UUID, Enum, str, dict, and datetime fields.
- Safe serialization for nested Pydantic models.
- JSON-safe conversion compatible with `xpytools.Typing.Cast` and `to_primitives`.

Usage
-----
    from xpyt_pydantic import BaseModel
    from uuid import UUID, uuid4
    from enum import Enum
    from datetime import datetime
    from xpytools.xtool.xpyt_pydantic import TypeSafeAccessMixin

    class StatusEnum(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    class User(TypeSafeAccessMixin, BaseModel):
        user_id: UUID
        username: str
        status: StatusEnum
        created_at: datetime

    user = User(user_id=uuid4(), username="john", status=StatusEnum.ACTIVE, created_at=datetime.utcnow())

    print(user.get_type_safe_attr("status"))  # "ACTIVE"
    print(user.get_all_type_safe_attr())      # safely serialized dict
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from pydantic import BaseModel, model_validator
except ImportError:
    BaseModel = None
    model_validator = None

from ...xtype.xcast import (
    as_str,
    as_datetime_str,
    )
from ...xtype.xcast.to_primitives import to_primitives
from ...xtype.xcheck import is_none, is_list_like, is_dict


class TypeSafeAccessMixin:
    """
    Adds safe pre-validation coercion and uniform attribute serialization
    for Pydantic models.

    Place this *before* `BaseModel` in the inheritance list to ensure its
    validator runs first.
    """

    # -----------------------------------------------------------------------
    # Pydantic pre-validation hook
    # -----------------------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def validate_and_coerce(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process raw field data to coerce UUIDs, Enums, dicts, and str fields.

        - Converts UUID strings to UUID objects (if field type is UUID)
        - Converts Enums from names/values
        - Converts JSON-like strings to dicts
        - Normalizes None-like values
        """
        from ...xtype.xcast import as_json
        from ...xtype.xcheck import is_uuid, is_json_like

        coerced = {}
        for key, val in values.items():
            try:
                if is_none(val):
                    coerced[key] = None
                    continue

                # UUIDs
                if getattr(cls, "__annotations__", {}).get(key) == UUID and not is_uuid(val):
                    from uuid import UUID as _UUID
                    coerced[key] = _UUID(str(val))
                    continue

                # JSON fields
                if is_json_like(val):
                    coerced[key] = as_json(val)
                    continue

                coerced[key] = val
            except Exception:
                coerced[key] = val  # fallback silently

        return coerced

    # -----------------------------------------------------------------------
    # Public serialization helpers
    # -----------------------------------------------------------------------
    def get_all_type_safe_attr(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return all attributes in JSON-safe form."""
        exclude_fields = exclude_fields or []
        return {
                attr: self.get_type_safe_attr(attr)
                for attr in self.__dict__
                if attr not in exclude_fields
                }

    def get_type_safe_attr(self, item: str) -> Any:
        """Retrieve a single attribute, safely coerced for serialization."""
        if not hasattr(self, item):
            raise KeyError(f"'{item}' is not a valid field.")

        value = getattr(self, item)
        return self._coerce_single_value(value, field_name=item)

    # -----------------------------------------------------------------------
    # Internal coercion logic
    # -----------------------------------------------------------------------
    @staticmethod
    def _coerce_single_value(value: Any, field_name: str = "") -> Any:
        """Safely serialize UUIDs, Enums, datetimes, BaseModels, and containers."""
        try:
            # None-like
            if is_none(value):
                return None

            # Pydantic model
            if isinstance(value, BaseModel):
                return value.model_dump()

            # Enum
            if isinstance(value, Enum):
                return value.name

            # UUID
            if isinstance(value, UUID):
                return as_str(value)

            # datetime
            if isinstance(value, datetime):
                return as_datetime_str(value)

            # Dict / list
            if is_dict(value):
                return {k: TypeSafeAccessMixin._coerce_single_value(v) for k, v in value.items()}
            if is_list_like(value):
                return [TypeSafeAccessMixin._coerce_single_value(v) for v in value]

            # JSON / nested
            safe_val = to_primitives(value)
            return safe_val

        except Exception as e:
            # last-resort stringification
            return f"<unserializable:{type(value).__name__}> {value!r}"
