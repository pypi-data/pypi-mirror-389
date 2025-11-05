"""Preprocessing helpers: returns, scaling, z-score, etc."""
import pandas as pd
import numpy as np

def compute_returns(series: pd.Series, kind: str = "log") -> pd.Series:
    """Compute simple or log returns."""
    if kind == "log":
        return np.log(series / series.shift(1)).fillna(0)
    elif kind == "simple":
        return series.pct_change().fillna(0)
    else:
        raise ValueError("kind must be 'log' or 'simple'")

def normalize_zscore(series: pd.Series, window: int = None) -> pd.Series:
    """Z-score normalization. If window is provided, use rolling z-score."""
    if window is None:
        return (series - series.mean()) / series.std()
    mu = series.rolling(window=window, min_periods=1).mean()
    sigma = series.rolling(window=window, min_periods=1).std()
    return (series - mu) / sigma.replace(0, np.nan)
