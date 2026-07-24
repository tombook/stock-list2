"""Tests for CostModel and position sizing strategies."""

from __future__ import annotations

import pandas as pd

from app.backtest.cost_model import CostModel
from app.backtest.position_sizing import fixed_fractional, kelly_fraction, vol_target


def _bars(closes: list[float]) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "close": closes,
        }
    )


class TestCostModel:
    def test_from_bps_wraps_into_commission(self) -> None:
        m = CostModel.from_bps(5.0)
        assert m.total_bps == 5.0
        assert m.commission_bps == 5.0

    def test_three_components_sum(self) -> None:
        m = CostModel(commission_bps=1, slippage_bps=2, spread_bps=2)
        assert m.total_bps == 5.0

    def test_default_is_zero(self) -> None:
        assert CostModel().total_bps == 0.0


class TestPositionSizing:
    def test_fixed_fractional_halves_position(self) -> None:
        signal = pd.Series([1.0, 1.0, 0.0])
        bars = _bars([10, 11, 12])
        result = fixed_fractional(signal, bars, fraction=0.5)
        assert result.tolist() == [0.5, 0.5, 0.0]

    def test_fixed_fractional_clips_to_range(self) -> None:
        signal = pd.Series([2.0, -2.0])
        bars = _bars([10, 11])
        result = fixed_fractional(signal, bars, fraction=1.0)
        assert result.tolist() == [1.0, -1.0]

    def test_vol_target_scales_by_volatility(self) -> None:
        signal = pd.Series([1.0, 1.0, 1.0, 1.0])
        bars = _bars([100, 101, 102, 103])
        result = vol_target(signal, bars, target_vol=0.15, lookback=2)
        assert len(result) == 4
        assert all(abs(v) <= 1.0 for v in result)

    def test_kelly_returns_signal_when_data_insufficient(self) -> None:
        signal = pd.Series([1.0])
        bars = _bars([100])
        result = kelly_fraction(signal, bars, lookback=60, fraction=0.5)
        assert len(result) == 1
        assert 0.0 <= result.iloc[0] <= 1.0
