"""移动平均线类指标（10 种）。每个函数返回 pd.Series。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    return bars["close"].rolling(length, min_periods=length).mean()


def ema(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    return bars["close"].ewm(span=length, adjust=False).mean()


def wma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    return (
        bars["close"].rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    )


def rma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Wilder 平滑移动平均（RSI/ATR 内部使用）。"""
    return bars["close"].ewm(alpha=1.0 / length, adjust=False).mean()


def _wma_weights(n: int) -> np.ndarray:
    return np.arange(1, n + 1, dtype=float)


def _weighted_mean(x: np.ndarray, w: np.ndarray) -> float:
    return float(np.dot(x, w) / w.sum())


def hma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Hull Moving Average——减少滞后的双重 WMA。"""
    half = length // 2
    sqrt_n = int(np.sqrt(length))
    wh, wf, ws = _wma_weights(half), _wma_weights(length), _wma_weights(sqrt_n)
    wma_half = bars["close"].rolling(half).apply(lambda x: _weighted_mean(x, wh), raw=True)
    wma_full = bars["close"].rolling(length).apply(lambda x: _weighted_mean(x, wf), raw=True)
    raw = 2 * wma_half - wma_full
    return raw.rolling(sqrt_n).apply(lambda x: _weighted_mean(x, ws), raw=True)


def alma(
    bars: pd.DataFrame, length: int = 20, offset: float = 0.85, sigma: float = 6.0
) -> pd.Series:
    """Arnaud Legoux Moving Average——高斯分布加权。"""
    m = offset * (length - 1)
    s = length / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(length)])
    weights /= weights.sum()
    return bars["close"].rolling(length).apply(lambda x: np.dot(x, weights), raw=True)


def swma(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """对称加权移动平均——权重关于中心对称。"""
    half = (length - 1) / 2
    weights = np.array([length - abs(i - half) for i in range(length)], dtype=float)
    weights /= weights.sum()
    return bars["close"].rolling(length).apply(lambda x: np.dot(x, weights), raw=True)


def tema(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Triple Exponential Moving Average。"""
    e1 = bars["close"].ewm(span=length, adjust=False).mean()
    e2 = e1.ewm(span=length, adjust=False).mean()
    e3 = e2.ewm(span=length, adjust=False).mean()
    return 3 * e1 - 3 * e2 + e3


def dema(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Double Exponential Moving Average。"""
    e1 = bars["close"].ewm(span=length, adjust=False).mean()
    e2 = e1.ewm(span=length, adjust=False).mean()
    return 2 * e1 - e2


def linreg(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """线性回归拟合线——预测当前 bar 的趋势值。"""
    x = np.arange(length, dtype=float)
    return (
        bars["close"]
        .rolling(length)
        .apply(lambda y: np.polyval(np.polyfit(x, y, 1), length - 1), raw=True)
    )
