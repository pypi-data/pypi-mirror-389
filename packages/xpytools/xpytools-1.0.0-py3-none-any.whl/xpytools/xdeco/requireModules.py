#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.Utils.require_modules
------------------------------
Decorator for safely gating functions based on optional module availability.

Usage
-----
@require_modules(["pandas", "numpy"])
def my_df_func(df):
    ...

If `pandas` or `numpy` are missing:
- The decorator returns None (default behavior)
- Or raises an ImportError if exc_raise=True
"""

from __future__ import annotations

from functools import wraps
from importlib.util import find_spec
from typing import Callable, Any, Iterable, TypeVar, cast

T = TypeVar("T", bound=Callable[..., Any])


# noinspection PyPep8Naming
def requireModules(
        modules: Iterable[str],
        *,
        exc_raise: bool = False,
        return_none: bool = True,
        ) -> Callable[[T], T]:
    """
    Decorator to ensure one or more modules are available before running a function.

    Parameters
    ----------
    modules : Iterable[str]
        List of module names to xcheck (e.g., ["pandas", "numpy"]).
    exc_raise : bool, default=False
        Raise ImportError if one or more modules are missing.
    return_none : bool, default=True
        If True and missing modules exist, return None instead of running the function.

    Returns
    -------
    Decorated function that gracefully bypasses or raises on missing dependencies.

    Examples
    --------
    >>> @requireModules(["pandas"])
    ... def df_summary(df):
    ...     import pandas as pd
    ...     return df.describe()
    ...
    >>> df_summary(None)  # if pandas missing -> returns None, no crash
    """
    missing: list[str] = [
            mod for mod in modules if find_spec(mod) is None
            ]

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if missing:
                msg = (
                        f"Missing required module(s): {', '.join(missing)} "
                        f"for function '{func.__name__}'."
                )
                if exc_raise:
                    raise ImportError(msg)
                if return_none:
                    return None
                # If not returning None, fallback to no-op
                return
            return func(*args, **kwargs)

        return cast(T, wrapper)

    return decorator
