import re
from typing import Optional, TYPE_CHECKING

from ...xtype.xcheck import is_df

if TYPE_CHECKING:
    from pandas import DataFrame as pdDataFrame
from ...xdeco import requireModules


@requireModules(["pandas"], exc_raise=True)
def normalize_column_names(df: "pdDataFrame", inplace: bool = True) -> Optional["pdDataFrame"]:
    """
    Normalize and sanitize DataFrame column names.

    Rules applied:
    - Lowercase all names
    - Replace spaces, hyphens, and slashes with underscores
    - Remove parentheses, brackets, braces, and special characters
    - Preserve `.digits` suffixes (e.g., `score.1` -> `score_1`)
    - Ensure unique column names (adds numeric suffixes if needed)
    - Converts `:` and `.` to `_` (except trailing digits)

    Parameters
    ----------
    df : Any
        DataFrame whose columns to clean.
    inplace : bool, default=True
        Modify the DataFrame in place. If False, return a copy.

    Returns
    -------
    pandas.DataFrame | None
        The modified DataFrame (or copy) with cleaned columns.
        Returns None if input is not a valid DataFrame.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(columns=["User ID", "Email-Address", "Score.1", "Score.1"])
    >>> normalize_column_names(df)
    >>> list(df.columns)
    ['user_id', 'email_address', 'score_1', 'score_1_1']
    """
    try:
        import pandas as pd
    except ImportError:
        return None

    if not is_df(df):
        return None

    target_df = df if inplace else df.copy()

    original_cols = list(target_df.columns)
    cleaned_cols: list[str] = []
    seen: set[str] = set()

    for col in original_cols:
        if not isinstance(col, str):
            col = str(col)

        new_col = col.lower()

        # Preserve ".digits" suffix
        match = re.search(r'\.(\d+)$', new_col)
        end_digits = match.group(0) if match else ""
        if end_digits:
            new_col = new_col[:-len(end_digits)]

        # Replace and clean
        new_col = new_col.replace(':', '_')
        new_col = new_col.replace('.', '_')
        new_col = re.sub(r'[ /\\\-]+', '_', new_col)
        new_col = re.sub(r'[(){}\[\]]+', '', new_col)
        new_col = re.sub(r'[^0-9a-zA-Z_]+', '', new_col)
        new_col = new_col.strip('_')

        # Re-add numeric suffix if it existed
        if end_digits:
            new_col = f"{new_col}_{end_digits.strip('.')}"

        # Ensure uniqueness
        base = new_col
        suffix = 1
        while new_col in seen:
            new_col = f"{base}_{suffix}"
            suffix += 1

        seen.add(new_col)
        cleaned_cols.append(new_col)

    target_df.columns = cleaned_cols
    return target_df
