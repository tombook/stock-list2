"""Tests for indicator signal generators."""

from __future__ import annotations

import pandas as pd

from app.indicators.signals import (
    SIGNALS,
    adx_direction,
    bollinger_signal,
    macd_signal,
    rsi_signal,
    supertrend_signal,
    vwap_signal,
)


class TestSignals:
    def test_rsi_buy_when_oversold(self) -> None:
        values = pd.Series([50, 25, 75, 20])
        buy, sell = rsi_signal(values, oversold=30, overbought=70)
        assert buy.tolist() == [False, True, False, True]
        assert sell.tolist() == [False, False, True, False]

    def test_macd_crossover(self) -> None:
        macd_line = pd.Series([1.0, 2.0, 1.0, 0.5])
        signal_line = pd.Series([1.5, 1.5, 1.5, 1.5])
        buy, sell = macd_signal(macd_line, signal_line)
        assert buy.tolist() == [False, True, False, False]
        assert sell.tolist() == [False, False, True, False]

    def test_bollinger_touches(self) -> None:
        close = pd.Series([100, 95, 105])
        upper = pd.Series([102, 102, 102])
        lower = pd.Series([98, 98, 98])
        buy, sell = bollinger_signal(close, upper, lower)
        assert buy.tolist() == [False, True, False]
        assert sell.tolist() == [False, False, True]

    def test_supertrend_crossover(self) -> None:
        close = pd.Series([100, 105, 95])
        st = pd.Series([102, 102, 102])
        buy, sell = supertrend_signal(close, st)
        assert buy.iloc[1] == True  # noqa: E712
        assert sell.iloc[2] == True  # noqa: E712

    def test_vwap_above_below(self) -> None:
        close = pd.Series([101, 99])
        vwap = pd.Series([100, 100])
        buy, sell = vwap_signal(close, vwap)
        assert buy.tolist() == [True, False]
        assert sell.tolist() == [False, True]

    def test_adx_direction(self) -> None:
        adx = pd.Series([30, 15, 30])
        plus_di = pd.Series([25, 20, 15])
        minus_di = pd.Series([10, 20, 25])
        buy, sell = adx_direction(adx, plus_di, minus_di, threshold=25)
        assert buy.tolist() == [True, False, False]
        assert sell.tolist() == [False, False, True]

    def test_registry_has_six_signals(self) -> None:
        assert set(SIGNALS.keys()) == {"rsi", "macd", "bollinger", "supertrend", "vwap", "adx"}
