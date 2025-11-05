# FinSignals

Lightweight Python package for generating financial signals and indicators.

## Installation
```bash
pip install finsignals
```

## Example
```python
import pandas as pd
from finsignals import indicators, preprocessing

data = pd.Series([100, 101, 99, 102, 105])
returns = preprocessing.compute_returns(data)
mid, up, low = indicators.bollinger_bands(data)
```
