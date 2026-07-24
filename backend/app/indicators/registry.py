"""指标统一注册表——指标名 → 函数。

与 strategies.py 的 STRATEGIES 注册表模式一致。
函数签名统一：f(bars: pd.DataFrame, **params) -> pd.Series | pd.DataFrame
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.indicators import (
    channel,
    directional,
    ma,
    momentum,
    pivot,
    statistical,
    trend,
    volatility,
    volume,
)


@dataclass(frozen=True)
class IndicatorSpec:
    name: str
    category: str
    fn: Callable[..., pd.Series | pd.DataFrame]
    default_params: dict[str, Any]
    params_schema: dict[str, Any]
    returns: str  # "series" 或 "dataframe"


INDICATORS: dict[str, IndicatorSpec] = {
    # Moving Averages (10)
    "sma": IndicatorSpec(
        "sma",
        "MA",
        ma.sma,
        {"length": 20},
        _ := {
            "type": "object",
            "properties": {"length": {"type": "integer", "minimum": 1, "default": 20}},
            "additionalProperties": False,
        },
        "series",
    ),
    "ema": IndicatorSpec("ema", "MA", ma.ema, {"length": 20}, _, "series"),
    "wma": IndicatorSpec("wma", "MA", ma.wma, {"length": 20}, _, "series"),
    "rma": IndicatorSpec("rma", "MA", ma.rma, {"length": 20}, _, "series"),
    "hma": IndicatorSpec("hma", "MA", ma.hma, {"length": 20}, _, "series"),
    "alma": IndicatorSpec(
        "alma", "MA", ma.alma, {"length": 20, "offset": 0.85, "sigma": 6.0}, _, "series"
    ),
    "swma": IndicatorSpec("swma", "MA", ma.swma, {"length": 20}, _, "series"),
    "tema": IndicatorSpec("tema", "MA", ma.tema, {"length": 20}, _, "series"),
    "dema": IndicatorSpec("dema", "MA", ma.dema, {"length": 20}, _, "series"),
    "linreg": IndicatorSpec("linreg", "MA", ma.linreg, {"length": 14}, _, "series"),
    # Momentum (11)
    "rsi": IndicatorSpec("rsi", "Momentum", momentum.rsi, {"length": 14}, _, "series"),
    "macd": IndicatorSpec(
        "macd", "Momentum", momentum.macd, {"fast": 12, "slow": 26, "signal": 9}, _, "dataframe"
    ),
    "stoch": IndicatorSpec(
        "stoch",
        "Momentum",
        momentum.stoch,
        {"k_period": 14, "d_period": 3, "smooth": 3},
        _,
        "dataframe",
    ),
    "roc": IndicatorSpec("roc", "Momentum", momentum.roc, {"length": 12}, _, "series"),
    "cci": IndicatorSpec("cci", "Momentum", momentum.cci, {"length": 20}, _, "series"),
    "mom": IndicatorSpec("mom", "Momentum", momentum.mom, {"length": 10}, _, "series"),
    "wpr": IndicatorSpec("wpr", "Momentum", momentum.wpr, {"length": 14}, _, "series"),
    "tsi": IndicatorSpec(
        "tsi", "Momentum", momentum.tsi, {"long_period": 25, "short_period": 13}, _, "series"
    ),
    "change": IndicatorSpec("change", "Momentum", momentum.change, {"length": 1}, _, "series"),
    "rising": IndicatorSpec("rising", "Momentum", momentum.rising, {"length": 1}, _, "series"),
    "falling": IndicatorSpec("falling", "Momentum", momentum.falling, {"length": 1}, _, "series"),
    # Volatility (6)
    "atr": IndicatorSpec("atr", "Volatility", volatility.atr, {"length": 14}, _, "series"),
    "stdev": IndicatorSpec("stdev", "Volatility", volatility.stdev, {"length": 20}, _, "series"),
    "tr": IndicatorSpec(
        "tr",
        "Volatility",
        volatility.true_range,
        {},
        {"type": "object", "properties": {}, "additionalProperties": False},
        "series",
    ),
    "supertrend": IndicatorSpec(
        "supertrend",
        "Volatility",
        volatility.supertrend,
        {"length": 10, "multiplier": 3.0},
        _,
        "series",
    ),
    "bb": IndicatorSpec(
        "bb",
        "Volatility",
        volatility.bollinger_bands,
        {"length": 20, "std_dev": 2.0},
        _,
        "dataframe",
    ),
    "variance": IndicatorSpec(
        "variance", "Volatility", volatility.variance, {"length": 20}, _, "series"
    ),
    # Volume (4)
    "vwap": IndicatorSpec(
        "vwap",
        "Volume",
        volume.vwap,
        {},
        {"type": "object", "properties": {}, "additionalProperties": False},
        "series",
    ),
    "vwma": IndicatorSpec("vwma", "Volume", volume.vwma, {"length": 20}, _, "series"),
    "mfi": IndicatorSpec("mfi", "Volume", volume.mfi, {"length": 14}, _, "series"),
    "obv": IndicatorSpec(
        "obv",
        "Volume",
        volume.obv,
        {},
        {"type": "object", "properties": {}, "additionalProperties": False},
        "series",
    ),
    # Channel (3)
    "donchian": IndicatorSpec(
        "donchian", "Channel", channel.donchian, {"length": 20}, _, "dataframe"
    ),
    "highest": IndicatorSpec("highest", "Channel", channel.highest, {"length": 20}, _, "series"),
    "lowest": IndicatorSpec("lowest", "Channel", channel.lowest, {"length": 20}, _, "series"),
    # Directional (2)
    "adx": IndicatorSpec("adx", "Directional", directional.adx, {"length": 14}, _, "series"),
    "dmi": IndicatorSpec(
        "dmi",
        "Directional",
        lambda bars, **p: pd.DataFrame(
            {"plus_di": directional.dmi(bars, **p)[0], "minus_di": directional.dmi(bars, **p)[1]}
        ),
        {"length": 14},
        _,
        "dataframe",
    ),
    # Pivot (2)
    "pivot_high": IndicatorSpec(
        "pivot_high", "Pivot", pivot.pivot_high, {"left": 5, "right": 5}, _, "series"
    ),
    "pivot_low": IndicatorSpec(
        "pivot_low", "Pivot", pivot.pivot_low, {"left": 5, "right": 5}, _, "series"
    ),
    # Statistical (2)
    "percentrank": IndicatorSpec(
        "percentrank", "Statistical", statistical.percentrank, {"length": 20}, _, "series"
    ),
    "correlation": IndicatorSpec(
        "correlation", "Statistical", statistical.correlation, {"length": 20}, _, "series"
    ),
    # Trend (1)
    "sar": IndicatorSpec("sar", "Trend", trend.sar, {"af_step": 0.02, "af_max": 0.2}, _, "series"),
}


def compute(name: str, bars: pd.DataFrame, **params: Any) -> pd.Series | pd.DataFrame:
    """按名称计算指标，自动注入默认参数。"""
    spec = INDICATORS.get(name)
    if spec is None:
        raise KeyError(f"unknown indicator: {name}")
    merged = {**spec.default_params, **params}
    return spec.fn(bars, **merged)
