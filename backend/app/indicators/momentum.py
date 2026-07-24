"""动量类指标（11 种）。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """Wilder's RSI。范围 0-100。"""
    delta = bars["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1.0 / length, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1.0 / length, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(
    bars: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """MACD——返回含 macd_line/macd_signal/macd_hist 三列的 DataFrame。"""
    ema_fast = bars["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = bars["close"].ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"macd_line": line, "macd_signal": sig, "macd_hist": line - sig})


def stoch(
    bars: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth: int = 3
) -> pd.DataFrame:
    """随机指标 KDJ。返回 %K 和 %D。"""
    lowest = bars["low"].rolling(k_period).min()
    highest = bars["high"].rolling(k_period).max()
    k_fast = 100 * (bars["close"] - lowest) / (highest - lowest).replace(0, np.nan)
    k = k_fast.rolling(smooth).mean()
    d = k.rolling(d_period).mean()
    return pd.DataFrame({"percent_k": k, "percent_d": d})


def roc(bars: pd.DataFrame, length: int = 12) -> pd.Series:
    """Rate of Change——百分比变化率。"""
    return bars["close"].pct_change(length) * 100


def cci(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """Commodity Channel Index。范围约 -300 到 +300。"""
    typical = (bars["high"] + bars["low"] + bars["close"]) / 3
    mean = typical.rolling(length).mean()
    mean_dev = typical.rolling(length).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (typical - mean) / (0.015 * mean_dev).replace(0, np.nan)


def mom(bars: pd.DataFrame, length: int = 10) -> pd.Series:
    """Momentum——当前值减 N 期前的值。"""
    return bars["close"].diff(length)


def wpr(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """Williams %R。范围 -100 到 0。"""
    highest = bars["high"].rolling(length).max()
    lowest = bars["low"].rolling(length).min()
    return (highest - bars["close"]) / (highest - lowest).replace(0, np.nan) * -100


def tsi(
    bars: pd.DataFrame, long_period: int = 25, short_period: int = 13
) -> pd.Series:
    """True Strength Index——双平滑动量。"""
    momentum = bars["close"].diff()
    abs_mom = momentum.abs()
    sm1 = momentum.ewm(span=long_period).mean().ewm(span=short_period).mean()
    sm2 = abs_mom.ewm(span=long_period).mean().ewm(span=short_period).mean()
    return 100 * sm1 / sm2.replace(0, np.nan)


def change(bars: pd.DataFrame, length: int = 1) -> pd.Series:
    """价格变化量（绝对值）。"""
    return bars["close"].diff(length)


def rising(bars: pd.DataFrame, length: int = 1) -> pd.Series:
    """是否连续上涨——布尔序列。"""
    return (bars["close"].diff(length) > 0).astype(float)


def falling(bars: pd.DataFrame, length: int = 1) -> pd.Series:
    """是否连续下跌——布尔序列。"""
    return (bars["close"].diff(length) < 0).astype(float)
