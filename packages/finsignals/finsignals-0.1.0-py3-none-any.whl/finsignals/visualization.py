"""Helper wrappers to visualize indicators."""
import matplotlib.pyplot as plt
import pandas as pd

def plot_series_with_signals(series: pd.Series, *signals: pd.Series, labels=None, title=None):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(series.index, series.values, label="price")
    for i, s in enumerate(signals):
        lab = labels[i] if labels and i < len(labels) else f"signal_{i}"
        ax.plot(s.index, s.values, label=lab)
    ax.set_title(title or "Series with signals")
    ax.legend()
    return fig, ax
