"""Strategy pure functions — synthetic frames, no I/O."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.backtest.strategies import STRATEGIES, buy_hold, momentum, sma_cross


def _bars(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame(
        {
            "ts": pd.date_range("2024-01-01", periods=n, freq="D"),
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000.0] * n,
        }
    )


def test_sma_cross_flats_during_warmup_then_signals_above() -> None:
    bars = _bars([1, 2, 3, 4, 5, 6, 7, 8])  # uptrend
    sig = sma_cross(bars, fast=2, slow=4)
    assert sig.dtype.kind in {"i", "u"}
    # First `slow-1` = 3 bars are warmup → flat 0
    assert sig.iloc[:3].tolist() == [0, 0, 0]
    # Once both SMAs exist and fast > slow in a clean uptrend → 1
    assert sig.iloc[-1] == 1
    assert set(sig.unique()).issubset({0, 1})


def test_sma_cross_signal_length_matches_bars() -> None:
    bars = _bars([1, 2, 3, 4, 5])
    sig = sma_cross(bars, fast=2, slow=3)
    assert len(sig) == len(bars)


def test_momentum_long_when_past_close_below_current() -> None:
    bars = _bars([5, 5, 5, 5, 10])  # close[4]=10 > close[4-2]=5
    sig = momentum(bars, lookback=2)
    assert set(sig.unique()).issubset({0, 1})
    # Warmup: lookback=2 → first 2 bars are 0
    assert sig.iloc[:2].tolist() == [0, 0]
    assert sig.iloc[-1] == 1


def test_buy_hold_is_always_one() -> None:
    bars = _bars([1, 2, 3])
    sig = buy_hold(bars)
    assert sig.tolist() == [1, 1, 1]


def test_registry_has_three_strategies_with_schemas() -> None:
    assert set(STRATEGIES) == {"sma_cross", "momentum", "buy_hold"}
    sma = STRATEGIES["sma_cross"]
    assert sma.default_params == {"fast": 5, "slow": 20}
    assert sma.params_schema["type"] == "object"
    # buy_hold takes no params
    assert STRATEGIES["buy_hold"].default_params == {}


def test_strategy_invalid_params_raise() -> None:
    import pytest

    bars = _bars([1, 2, 3, 4])
    with pytest.raises(ValueError):
        sma_cross(bars, fast=10, slow=5)  # fast > slow is invalid
    with pytest.raises(ValueError):
        momentum(bars, lookback=0)
