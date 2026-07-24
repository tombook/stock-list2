"""Tests for the 47-indicator engine — one representative per category."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

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
from app.indicators.registry import INDICATORS, compute


def _bars(n: int = 50, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 + rng.standard_normal(n).cumsum()
    return pd.DataFrame(
        {
            "ts": pd.date_range("2024-01-01", periods=n, freq="D"),
            "open": close - rng.random(n),
            "high": close + rng.random(n),
            "low": close - rng.random(n) * 2,
            "close": close,
            "volume": rng.integers(1_000_000, 10_000_000, n).astype(float),
        }
    )


class TestMovingAverages:
    def test_sma_length(self) -> None:
        bars = _bars()
        result = ma.sma(bars, length=10)
        assert len(result) == 50
        assert result.iloc[:9].isna().all()
        assert result.iloc[9] == pytest.approx(bars["close"].iloc[:10].mean())

    def test_ema_no_nan_after_first(self) -> None:
        bars = _bars()
        result = ma.ema(bars, length=5)
        assert not result.isna().any()  # adjust=False → no NaN warmup

    def test_hma_returns_series(self) -> None:
        result = ma.hma(_bars(60), length=20)
        assert isinstance(result, pd.Series)
        assert len(result) == 60

    def test_alma_returns_series(self) -> None:
        result = ma.alma(_bars(), length=9)
        assert isinstance(result, pd.Series)


class TestMomentum:
    def test_rsi_range_0_to_100(self) -> None:
        result = momentum.rsi(_bars(100), length=14)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_macd_returns_dataframe(self) -> None:
        df = momentum.macd(_bars(100))
        assert set(df.columns) == {"macd_line", "macd_signal", "macd_hist"}

    def test_stoch_returns_kd(self) -> None:
        df = momentum.stoch(_bars(100))
        assert "percent_k" in df.columns
        assert "percent_d" in df.columns

    def test_wpr_range(self) -> None:
        result = momentum.wpr(_bars(100), length=14)
        valid = result.dropna()
        assert (valid <= 0).all() and (valid >= -100).all()


class TestVolatility:
    def test_atr_positive(self) -> None:
        result = volatility.atr(_bars(100), length=14)
        assert (result.dropna() > 0).all()

    def test_bollinger_three_bands(self) -> None:
        df = volatility.bollinger_bands(_bars(100)).dropna()
        assert (df["bb_upper"] >= df["bb_mid"]).all()
        assert (df["bb_mid"] >= df["bb_lower"]).all()

    def test_supertrend_returns_series(self) -> None:
        result = volatility.supertrend(_bars(100))
        assert isinstance(result, pd.Series)
        assert len(result) == 100


class TestVolume:
    def test_vwap_within_price_range(self) -> None:
        bars = _bars(100)
        result = volume.vwap(bars)
        assert (result >= bars["low"].cummin()).dropna().all()

    def test_obv_is_cumulative(self) -> None:
        bars = _bars(100)
        result = volume.obv(bars)
        assert result.iloc[0] == 0 or abs(result.iloc[0]) < 1e-10

    def test_mfi_range(self) -> None:
        result = volume.mfi(_bars(100), length=14)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()


class TestChannel:
    def test_donchian_upper_above_lower(self) -> None:
        df = channel.donchian(_bars(100), length=20).dropna()
        assert (df["dc_upper"] >= df["dc_lower"]).all()

    def test_highest_and_lowest(self) -> None:
        bars = _bars(100)
        assert channel.highest(bars, 20).iloc[-1] == bars["high"].iloc[-20:].max()
        assert channel.lowest(bars, 20).iloc[-1] == bars["low"].iloc[-20:].min()


class TestDirectional:
    def test_adx_non_negative(self) -> None:
        result = directional.adx(_bars(100), length=14)
        assert (result.dropna() >= 0).all()

    def test_dmi_returns_pair(self) -> None:
        plus, minus = directional.dmi(_bars(100), length=14)
        assert isinstance(plus, pd.Series)
        assert isinstance(minus, pd.Series)


class TestPivot:
    def test_pivot_high_finds_local_max(self) -> None:
        bars = pd.DataFrame(
            {
                "high": [1, 2, 10, 2, 1, 2, 1],
                "low": [0, 1, 9, 1, 0, 1, 0],
            }
        )
        result = pivot.pivot_high(bars, left=2, right=2)
        assert not result.iloc[2:3].isna().all()


class TestStatistical:
    def test_correlation_range(self) -> None:
        result = statistical.correlation(_bars(100), length=20)
        valid = result.dropna()
        assert (valid >= -1.01).all() and (valid <= 1.01).all()


class TestTrend:
    def test_sar_returns_series(self) -> None:
        result = trend.sar(_bars(100))
        assert isinstance(result, pd.Series)
        assert len(result) == 100


class TestRegistry:
    def test_registry_has_indicators(self) -> None:
        # 44 计算指标（含 3 个 signal 在 signals.py），注册表有 41 个唯一条目
        assert len(INDICATORS) == 41

    def test_compute_by_name(self) -> None:
        bars = _bars(100)
        result = compute("rsi", bars, length=14)
        assert isinstance(result, pd.Series)

    def test_compute_dataframe_indicator(self) -> None:
        bars = _bars(100)
        df = compute("macd", bars)
        assert "macd_line" in df.columns

    def test_compute_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            compute("nonexistent", _bars())

    def test_all_categories_represented(self) -> None:
        cats = {spec.category for spec in INDICATORS.values()}
        assert cats == {
            "MA",
            "Momentum",
            "Volatility",
            "Volume",
            "Channel",
            "Directional",
            "Pivot",
            "Statistical",
            "Trend",
        }
