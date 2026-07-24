"""仓位大小策略——将原始信号调整为目标仓位。

每个函数接受 (signal, bars, **params) → pd.Series[float]，输出范围 [-1, +1]。
signal 是原始信号（如策略输出的 0.0/1.0），返回值是经过 sizing 调整的目标仓位。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def fixed_fractional(signal: pd.Series, bars: pd.DataFrame, *, fraction: float = 1.0) -> pd.Series:
    """固定比例：signal × fraction。fraction=0.5 = 半仓。"""
    return (signal * fraction).clip(-1.0, 1.0)


def vol_target(
    signal: pd.Series,
    bars: pd.DataFrame,
    *,
    target_vol: float = 0.15,
    lookback: int = 20,
    periods_per_year: int = 252,
) -> pd.Series:
    """波动率目标：根据近期波动率缩放仓位，使年化波动率接近 target_vol。"""
    returns = bars["close"].pct_change()
    rolling_vol = returns.rolling(lookback, min_periods=1).std()
    annualized = rolling_vol * np.sqrt(periods_per_year)
    # 目标仓位 = 目标波动率 / 实际波动率 × 信号；clip 防止杠杆超限
    scale = (target_vol / annualized).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return (signal * scale).clip(-1.0, 1.0)


def kelly_fraction(
    signal: pd.Series,
    bars: pd.DataFrame,
    *,
    lookback: int = 60,
    fraction: float = 0.5,
) -> pd.Series:
    """Kelly 分数：基于近期胜率和盈亏比的 Kelly 公式半 Kelly。

    f* = (b×p - q) / b，其中 b=盈亏比, p=胜率, q=1-p。
    实际使用 fraction × f*（半 Kelly 降低风险）。
    """
    returns = bars["close"].pct_change()
    window = returns.iloc[-lookback:]
    wins = window[window > 0]
    losses = window[window < 0]
    if len(wins) == 0 or len(losses) == 0:
        return fixed_fractional(signal, bars, fraction=fraction)
    win_rate = len(wins) / len(window)
    avg_win = float(wins.mean())
    avg_loss = float(abs(losses.mean()))
    b = avg_win / avg_loss if avg_loss > 0 else 1.0
    kelly = (b * win_rate - (1 - win_rate)) / b
    kelly = max(0.0, min(kelly * fraction, 1.0))
    return (signal * kelly).clip(-1.0, 1.0)
