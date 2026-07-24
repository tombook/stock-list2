"""方向运动类指标（2 种）。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.indicators.volatility import atr


def adx(bars: pd.DataFrame, length: int = 14) -> pd.Series:
    """Average Directional Index——趋势强度（不含方向）。范围 0-100。"""
    di_plus, di_minus = dmi(bars, length)
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
    return dx.ewm(alpha=1.0 / length, adjust=False).mean()


def dmi(bars: pd.DataFrame, length: int = 14) -> tuple[pd.Series, pd.Series]:
    """Directional Movement Index——返回 (+DI, -DI)。"""
    high = bars["high"]
    low = bars["low"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    a = atr(bars, length)
    plus_di = 100 * plus_dm.ewm(alpha=1.0 / length, adjust=False).mean() / a.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1.0 / length, adjust=False).mean() / a.replace(0, np.nan)
    return plus_di, minus_di
