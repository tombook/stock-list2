"""指标信号生成器——给定指标值，生成买卖信号。

每个函数接受指标计算结果（pd.Series），返回 (buy_signal, sell_signal) 布尔序列。
信号逻辑来自 TradingView 社区指标分类体系（原项目 import_indicator_registry.py）。
独立于指标计算引擎——只定义"给定值如何判断"，不定义"如何计算"。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SignalSpec:
    """一个指标的信号规则描述 + evaluate 函数。"""

    name: str
    buy_condition: str
    sell_condition: str
    evaluate: Callable[..., tuple[pd.Series, pd.Series]]


def rsi_signal(
    values: pd.Series, *, oversold: float = 30, overbought: float = 70
) -> tuple[pd.Series, pd.Series]:
    buy = values < oversold
    sell = values > overbought
    return buy, sell


def macd_signal(macd_line: pd.Series, signal_line: pd.Series) -> tuple[pd.Series, pd.Series]:
    prev_diff = macd_line.shift(1) - signal_line.shift(1)
    cur_diff = macd_line - signal_line
    buy = (cur_diff > 0) & (prev_diff <= 0)
    sell = (cur_diff < 0) & (prev_diff >= 0)
    return buy, sell


def bollinger_signal(
    close: pd.Series, upper: pd.Series, lower: pd.Series
) -> tuple[pd.Series, pd.Series]:
    buy = close < lower
    sell = close > upper
    return buy, sell


def supertrend_signal(close: pd.Series, supertrend: pd.Series) -> tuple[pd.Series, pd.Series]:
    buy = (close > supertrend) & (close.shift(1) <= supertrend.shift(1))
    sell = (close < supertrend) & (close.shift(1) >= supertrend.shift(1))
    return buy, sell


def vwap_signal(close: pd.Series, vwap: pd.Series) -> tuple[pd.Series, pd.Series]:
    return close > vwap, close < vwap


def adx_direction(
    adx: pd.Series, plus_di: pd.Series, minus_di: pd.Series, *, threshold: float = 25
) -> tuple[pd.Series, pd.Series]:
    buy = (adx > threshold) & (plus_di > minus_di)
    sell = (adx > threshold) & (minus_di > plus_di)
    return buy, sell


SIGNALS: dict[str, SignalSpec] = {
    "rsi": SignalSpec(
        "rsi", "RSI < oversold (default 30)", "RSI > overbought (default 70)", rsi_signal
    ),
    "macd": SignalSpec(
        "macd",
        "MACD line crosses above signal line",
        "MACD line crosses below signal line",
        macd_signal,
    ),
    "bollinger": SignalSpec(
        "bollinger", "Close touches lower band", "Close touches upper band", bollinger_signal
    ),
    "supertrend": SignalSpec(
        "supertrend", "Close crosses above SuperTrend",
        "Close crosses below SuperTrend", supertrend_signal,
    ),
    "vwap": SignalSpec("vwap", "Close above VWAP", "Close below VWAP", vwap_signal),
    "adx": SignalSpec(
        "adx", "ADX > threshold AND +DI > -DI", "ADX > threshold AND -DI > +DI", adx_direction
    ),
}
