"""Utility helpers used across the package."""
import pandas as pd
from typing import Callable

def rolling_apply(series: pd.Series, window: int, fn: Callable) -> pd.Series:
    """Apply `fn` over a rolling window and return a Series."""
    return series.rolling(window=window, min_periods=1).apply(fn, raw=False)
