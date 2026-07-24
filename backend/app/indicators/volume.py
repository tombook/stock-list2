"""成交量类指标（4 种）。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def vwap(bars: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price——累计成交量加权均价。"""
    typical = (bars["high"] + bars["low"] + bars["close"]) / 3
    vol = bars["volume"].replace(0, np.nan).fillna(1e-10)
    cum_pv = (typical * vol).cumsum()
    cum_v = vol.cumsum()
    return cum_pv / cum_v


def vwma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Volume Weighted Moving Average——滚动成交量加权均价。"""
    close = bars["close"]
    vol = bars["volume"].replace(0, np.nan).fillna(1e-10)
    return (close * vol).rolling(length).sum() / vol.rolling(length).sum()


def mfi(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """Money Flow Index——带成交量的 RSI。范围 0-100。"""
    typical = (bars["high"] + bars["low"] + bars["close"]) / 3
    vol = bars["volume"]
    raw_mf = typical * vol
    pos_mf = raw_mf.where(typical > typical.shift(1), 0.0)
    neg_mf = raw_mf.where(typical < typical.shift(1), 0.0)
    pos_sum = pos_mf.rolling(length).sum()
    neg_sum = neg_mf.rolling(length).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def obv(bars: pd.DataFrame) -> pd.Series:
    """On Balance Volume——价涨量增、价跌量减的累计。"""
    direction = np.sign(bars["close"].diff().fillna(0))
    return (direction * bars["volume"].fillna(0)).cumsum()
