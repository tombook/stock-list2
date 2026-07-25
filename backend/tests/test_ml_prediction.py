"""Tests for the ML prediction engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.marketdata.models import Bar, Bars
from app.ml.features import FEATURE_NAMES, build_features
from app.ml.models import PredictionResult
from app.ml.service import predict_direction

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _make_bars(n: int = 200) -> Bars:
    rng = np.random.default_rng(42)
    close = 100 + rng.standard_normal(n).cumsum()
    return Bars(
        symbol="TEST",
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=_BASE + timedelta(days=i),
                open=close[i] - rng.random(),
                high=close[i] + rng.random(),
                low=close[i] - rng.random() * 2,
                close=close[i],
                volume=float(rng.integers(1e6, 1e7)),
            )
            for i in range(n)
        ],
    )


class TestFeatureEngineering:
    def test_build_features_returns_all_columns(self) -> None:
        df = pd.DataFrame(
            {
                "open": np.random.randn(100) + 100,
                "high": np.random.randn(100) + 101,
                "low": np.random.randn(100) + 99,
                "close": np.random.randn(100) + 100,
                "volume": np.random.randint(1e6, 1e7, 100).astype(float),
            }
        )
        features = build_features(df)
        for col in FEATURE_NAMES:
            assert col in features.columns

    def test_features_have_no_inf(self) -> None:
        df = pd.DataFrame(
            {
                "open": [100] * 60,
                "high": [101] * 60,
                "low": [99] * 60,
                "close": [100 + i * 0.1 for i in range(60)],
                "volume": [1e6] * 60,
            }
        )
        features = build_features(df)
        assert not np.isinf(features.select_dtypes(include=[np.number]).values).any()


@pytest.mark.asyncio
async def test_predict_direction_returns_valid_result() -> None:
    bars = _make_bars(250)
    with patch(
        "app.ml.service.market_service.get_bars",
        new=AsyncMock(return_value=bars),
    ):
        result = await predict_direction("TEST", horizon=5)

    assert isinstance(result, PredictionResult)
    assert result.symbol == "TEST"
    assert 0.0 <= result.probability_up <= 1.0
    assert result.predicted_direction in ("up", "down")
    assert result.confidence >= 0.5
    assert len(result.top_features) <= 5
    assert all(f.name in FEATURE_NAMES for f in result.top_features)
    assert result.horizon == 5
    assert result.source == "adaboost"


@pytest.mark.asyncio
async def test_predict_direction_insufficient_data_raises() -> None:
    bars = _make_bars(100)  # too few
    with patch(
        "app.ml.service.market_service.get_bars",
        new=AsyncMock(return_value=bars),
    ):
        with pytest.raises(Exception, match="insufficient"):
            await predict_direction("TEST", horizon=5)
