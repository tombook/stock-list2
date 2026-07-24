"""波动率类指标（6 种）。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(bars: pd.DataFrame) -> pd.Series:
    """True Range——单根 bar 的真实波动幅度。"""
    high = bars["high"]
    low = bars["low"]
    prev_close = bars["close"].shift(1)
    return pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)


def atr(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """Wilder's ATR。"""
    tr = true_range(bars)
    return tr.ewm(alpha=1.0 / length, adjust=False).mean()


def stdev(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """滚动标准差。"""
    return bars["close"].rolling(length).std()


def variance(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """滚动方差。"""
    return bars["close"].rolling(length).var()


def bollinger_bands(
    bars: pd.DataFrame, length: int = 20, std_dev: float = 2.0
) -> pd.DataFrame:
    """Bollinger Bands——返回 upper/mid/lower 三条轨。"""
    mid = bars["close"].rolling(length).mean()
    sd = bars["close"].rolling(length).std()
    return pd.DataFrame({
        "bb_upper": mid + std_dev * sd,
        "bb_mid": mid,
        "bb_lower": mid - std_dev * sd,
    })


def supertrend(
    bars: pd.DataFrame, length: int = 10, multiplier: float = 3.0
) -> pd.Series:
    """SuperTrend——基于 ATR 的趋势跟踪线。"""
    hl2 = (bars["high"] + bars["low"]) / 2
    a = atr(bars, length)
    upper_band = hl2 + multiplier * a
    lower_band = hl2 - multiplier * a

    close = bars["close"].values
    ub = upper_band.values
    lb = lower_band.values
    n = len(close)
    st = np.full(n, np.nan)

    st[0] = ub[0]
    for i in range(1, n):
        if close[i] > ub[i - 1]:
            st[i] = lb[i]
        elif close[i] < lb[i - 1]:
            st[i] = ub[i]
        else:
            st[i] = st[i - 1]
            if lb[i] > st[i] or (close[i - 1] < st[i] and lb[i] < st[i]):
                st[i] = lb[i]
            elif ub[i] < st[i] or (close[i - 1] > st[i] and ub[i] > st[i]):
                st[i] = ub[i]

    return pd.Series(st, index=bars.index, name="supertrend")
