import pandas as pd
import numpy as np
from finsignals import indicators

def test_moving_average():
    s = pd.Series([1, 2, 3, 4, 5])
    ma = indicators.moving_average(s, window=3)
    assert ma.iloc[-1] == (3 + 4 + 5) / 3

def test_rsi_basic():
    s = pd.Series([1, 2, 3, 2, 1, 2, 3])
    r = indicators.rsi(s, window=3)
    assert not r.isna().any()
