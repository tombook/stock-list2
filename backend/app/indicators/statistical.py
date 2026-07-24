"""统计类指标（2 种）。"""

from __future__ import annotations

import pandas as pd


def percentrank(bars: pd.DataFrame, length: int = 20) -> pd.Series:
    """当前值在 N 周期窗口中的百分位排名。范围 0-100。"""
    close = bars["close"]
    return close.rolling(length).apply(
        lambda x: 100 * pd.Series(x).rank(pct=True).iloc[-1] * len(x), raw=False
    )


def correlation(
    bars: pd.DataFrame, length: int = 20, col1: str = "close", col2: str = "volume"
) -> pd.Series:
    """两列的滚动 Pearson 相关系数。"""
    return bars[col1].rolling(length).corr(bars[col2])
