"""Basic finance indicators used for signal generation."""
import pandas as pd
import numpy as np

def moving_average(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average (SMA)."""
    return series.rolling(window=window, min_periods=1).mean()

def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (EMA)."""
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=window, min_periods=1).mean()
    loss = (-delta).clip(lower=0).rolling(window=window, min_periods=1).mean()
    rs = gain / (loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Return (middle, upper, lower) Bollinger Bands."""
    mid = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Compute MACD line and signal line. Returns (macd_line, signal_line)."""
    fast_ema = series.ewm(span=fast, adjust=False).mean()
    slow_ema = series.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line
