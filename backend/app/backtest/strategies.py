"""Built-in strategies — pure functions `(bars_df, **params) -> pd.Series[int]`.

Each function returns a target-position series of {0,1} (long-only) aligned to
`bars.index`. The signal at bar `t` is known at bar `t`'s close; the engine
shifts by one to avoid lookahead.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

StrategyFn = Callable[..., pd.Series]


@dataclass(frozen=True)
class StrategySpec:
    name: str
    fn: StrategyFn
    default_params: dict[str, Any]
    params_schema: dict[str, Any]


def _validate_int(value: Any, name: str, *, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def sma_cross(bars: pd.DataFrame, *, fast: int = 5, slow: int = 20) -> pd.Series:
    """Long when SMA(fast) > SMA(slow); flat during warmup."""
    fast = _validate_int(fast, "fast", minimum=1)
    slow = _validate_int(slow, "slow", minimum=1)
    if fast >= slow:
        raise ValueError("fast must be < slow")
    close = bars["close"]
    fast_sma = close.rolling(fast, min_periods=fast).mean()
    slow_sma = close.rolling(slow, min_periods=slow).mean()
    signal = (fast_sma > slow_sma).astype("int64")
    # Warmup: NaN comparisons become False → 0 already; ensure dtype stable.
    return pd.Series(signal.values, index=bars.index, dtype="int64", name="signal")


def momentum(bars: pd.DataFrame, *, lookback: int = 20) -> pd.Series:
    """Long when close[t] > close[t-lookback]."""
    lookback = _validate_int(lookback, "lookback", minimum=1)
    close = bars["close"]
    past = close.shift(lookback)
    signal = (close > past).astype("int64")
    return pd.Series(signal.values, index=bars.index, dtype="int64", name="signal")


def buy_hold(bars: pd.DataFrame) -> pd.Series:
    """Always long from the first bar."""
    return pd.Series(
        [1] * len(bars), index=bars.index, dtype="int64", name="signal"
    )


_SMA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "fast": {"type": "integer", "minimum": 1, "default": 5},
        "slow": {"type": "integer", "minimum": 1, "default": 20},
    },
    "additionalProperties": False,
}

_MOMENTUM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"lookback": {"type": "integer", "minimum": 1, "default": 20}},
    "additionalProperties": False,
}

_EMPTY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

STRATEGIES: dict[str, StrategySpec] = {
    "sma_cross": StrategySpec("sma_cross", sma_cross, {"fast": 5, "slow": 20}, _SMA_SCHEMA),
    "momentum": StrategySpec("momentum", momentum, {"lookback": 20}, _MOMENTUM_SCHEMA),
    "buy_hold": StrategySpec("buy_hold", buy_hold, {}, _EMPTY_SCHEMA),
}
