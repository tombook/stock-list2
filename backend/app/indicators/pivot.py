"""枢轴点类指标（2 种）。"""

from __future__ import annotations

import pandas as pd


def pivot_high(bars: pd.DataFrame, left: int = 5, right: int = 5) -> pd.Series:
    """枢轴高点——某 bar 的高价高于左右各 N 根 bar。"""
    highs = bars["high"]
    n = len(highs)
    result = [float("nan")] * n
    for i in range(left, n - right):
        window_left = highs.iloc[i - left:i]
        window_right = highs.iloc[i + 1:i + 1 + right]
        if highs.iloc[i] > window_left.max() and highs.iloc[i] > window_right.max():
            result[i] = highs.iloc[i]
    return pd.Series(result, index=bars.index, name="pivot_high")


def pivot_low(bars: pd.DataFrame, left: int = 5, right: int = 5) -> pd.Series:
    """枢轴低点——某 bar 的低价低于左右各 N 根 bar。"""
    lows = bars["low"]
    n = len(lows)
    result = [float("nan")] * n
    for i in range(left, n - right):
        window_left = lows.iloc[i - left:i]
        window_right = lows.iloc[i + 1:i + 1 + right]
        if lows.iloc[i] < window_left.min() and lows.iloc[i] < window_right.min():
            result[i] = lows.iloc[i]
    return pd.Series(result, index=bars.index, name="pivot_low")
