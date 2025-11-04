from typing import Optional

from ...xtype.xcheck import is_df, is_empty


def _is_not_df(df, name: Optional[str] = None):
    if not is_df(df):
        if name:
            raise ValueError(f"{name} is not a DataFrame")
        else:
            raise ValueError("Not a DataFrame")


def _is_empty_df(df, name: Optional[str] = None):
    if is_empty(df):
        if name:
            raise ValueError(f"{name} is an empty DataFrame")
        else:
            raise ValueError("Empty DataFrame")


def _check_df(df, name: Optional[str] = None):
    _is_not_df(df=df, name=name)
    _is_empty_df(df=df, name=name)
