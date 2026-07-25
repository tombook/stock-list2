"""Tests for strategy editor (validation + execution)."""

from __future__ import annotations

import pytest

from app.strategy_editor.service import run_strategy, validate

VALID_STRATEGY = """\
import pandas as pd
import numpy as np

def strategy(bars, **params):
    close = bars["close"]
    sma = close.rolling(20).mean()
    return (close > sma).astype(float)
"""


class TestValidation:
    def test_valid_strategy(self) -> None:
        result = validate(VALID_STRATEGY)
        assert result.valid is True
        assert result.issues == []

    def test_syntax_error(self) -> None:
        result = validate("def strategy(bars) return")
        assert result.valid is False
        assert any("SyntaxError" in i.message for i in result.issues)

    def test_missing_strategy_function(self) -> None:
        code = "import pandas as pd\nx = 1"
        result = validate(code)
        assert result.valid is False
        assert any("strategy" in i.message for i in result.issues)

    def test_banned_import_os(self) -> None:
        code = (
            "import os\n"
            "import pandas as pd\n"
            "def strategy(bars, **params):\n"
            "    return pd.Series([0] * len(bars))"
        )
        result = validate(code)
        assert result.valid is False
        assert any("os" in i.message for i in result.issues)

    def test_banned_exec_call(self) -> None:
        code = (
            "import pandas as pd\n"
            "def strategy(bars, **params):\n"
            "    exec('print(1)')\n"
            "    return pd.Series([0] * len(bars))"
        )
        result = validate(code)
        assert result.valid is False
        assert any("exec" in i.message for i in result.issues)


def _fake_bars() -> list[dict]:
    return [
        {
            "ts": f"2024-01-{i + 1:02d}",
            "open": 100 + i,
            "high": 102 + i,
            "low": 99 + i,
            "close": 101 + i,
            "volume": 1_000_000.0,
        }
        for i in range(50)
    ]


@pytest.mark.asyncio
async def test_run_strategy_executes_user_code() -> None:
    bars = _fake_bars()
    result = await run_strategy(VALID_STRATEGY, bars)
    assert result.error is None
    assert result.n_bars == 50
    assert len(result.equity) == 50


@pytest.mark.asyncio
async def test_run_strategy_reports_validation_failure() -> None:
    bad_code = "def strategy(bars) missing_colon"
    bars = _fake_bars()
    result = await run_strategy(bad_code, bars)
    assert result.error is not None
    assert "validation" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_run_strategy_timeout() -> None:
    infinite_code = (
        "import pandas as pd\n"
        "import time\n"
        "def strategy(bars, **params):\n"
        "    time.sleep(30)\n"
        "    return pd.Series([0] * len(bars))"
    )
    bars = _fake_bars()
    result = await run_strategy(infinite_code, bars)
    assert result.error is not None
    assert "timed out" in (result.error or "").lower()
