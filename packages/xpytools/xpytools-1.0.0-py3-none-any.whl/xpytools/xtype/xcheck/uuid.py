#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

from __future__ import annotations

from typing import Any
from uuid import UUID

from ...xtype.UUIDLike import UUIDLike


# ---------------------------------------------------------------------------
# UUID / primitive checks
# ---------------------------------------------------------------------------

def is_uuid(value: Any) -> bool:
    """Return True if `value` is a valid UUID string or UUID instance."""
    if isinstance(value, UUID):
        return True
    return False


def is_uuid_like(value: Any) -> bool:
    """Return True if `value` looks like a valid UUID."""
    try:
        if is_uuid(value):
            return True
        UUIDLike(value)
        return True
    except Exception:
        return False
