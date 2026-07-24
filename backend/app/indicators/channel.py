"""通道类指标（3 种）。"""

from __future__ import annotations

import pandas as pd


def donchian(bars: pd.DataFrame, length: int = 20) -> pd.DataFrame:
    """Donchian Channel——N 周期最高价/最低价通道。"""
    return pd.DataFrame({
        "dc_upper": bars["high"].rolling(length).max(),
        "dc_lower": bars["low"].rolling(length).min(),
    })


def highest(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """N 周期最高价。"""
    return bars["high"].rolling(length).max()


def lowest(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """N 周期最低价。"""
    return bars["low"].rolling(length).min()
