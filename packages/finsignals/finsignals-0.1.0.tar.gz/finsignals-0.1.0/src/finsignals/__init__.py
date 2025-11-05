"""finsignals package — public API exposure."""
from .indicators import moving_average, ema, rsi, bollinger_bands, macd
from .preprocessing import compute_returns, normalize_zscore
from .utils import rolling_apply

__all__ = [
    "moving_average",
    "ema",
    "rsi",
    "bollinger_bands",
    "macd",
    "compute_returns",
    "normalize_zscore",
    "rolling_apply",
]
