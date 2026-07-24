"""Tests for corporate actions (splits + dividends)."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from app.marketdata.sources import yfinance_src


@pytest.mark.asyncio
async def test_actions_extracts_splits_and_dividends() -> None:
    fake_splits = pd.Series(
        [2.0, 3.0],
        index=pd.to_datetime(["2020-08-31", "2005-02-18"]).tz_localize("UTC"),
    )
    fake_dividends = pd.Series(
        [0.22, 0.24],
        index=pd.to_datetime(["2024-05-10", "2024-02-09"]).tz_localize("UTC"),
    )

    class FakeTicker:
        @property
        def splits(self):
            return fake_splits

        @property
        def dividends(self):
            return fake_dividends

    with patch.object(yfinance_src.yfinance, "Ticker", return_value=FakeTicker()):
        result = await yfinance_src.actions("AAPL")

    assert len(result) == 4
    split = next(a for a in result if a.type == "split")
    assert split.value == 2.0 or split.value == 3.0
    div = next(a for a in result if a.type == "dividend")
    assert div.value in (0.22, 0.24)
    assert all(a.symbol == "AAPL" for a in result)
    assert result == sorted(result, key=lambda a: a.date, reverse=True)


@pytest.mark.asyncio
async def test_actions_raises_not_found_when_empty() -> None:
    class FakeTicker:
        @property
        def splits(self):
            return pd.Series([], dtype=float)

        @property
        def dividends(self):
            return pd.Series([], dtype=float)

    with patch.object(yfinance_src.yfinance, "Ticker", return_value=FakeTicker()):
        with pytest.raises(Exception, match="no corporate actions"):
            await yfinance_src.actions("FAKE")
