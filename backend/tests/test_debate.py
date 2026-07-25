"""Tests for the multi-agent debate mechanism."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agent.analysts.debate import (
    _detect_conflict,
    _score_to_label,
    _weighted_fusion,
    run_debate,
)


class TestConflictDetection:
    def test_no_conflict_when_unanimous(self) -> None:
        result = _detect_conflict(["bullish", "bullish", "bullish"])
        assert result["high_divergence"] is False
        assert result["bullish_count"] == 3

    def test_conflict_when_split(self) -> None:
        result = _detect_conflict(["bullish", "bearish", "neutral", "bullish", "bearish"])
        assert result["high_divergence"] is True
        assert result["bullish_count"] == 2
        assert result["bearish_count"] == 2


class TestWeightedFusion:
    def test_all_bullish(self) -> None:
        opinions = {
            "a": {"signal": "bullish", "confidence": 0.8},
            "b": {"signal": "bullish", "confidence": 0.6},
        }
        assert _weighted_fusion(opinions) > 0.5

    def test_all_bearish(self) -> None:
        opinions = {
            "a": {"signal": "bearish", "confidence": 0.9},
            "b": {"signal": "bearish", "confidence": 0.7},
        }
        assert _weighted_fusion(opinions) < -0.5

    def test_mixed_signals(self) -> None:
        opinions = {
            "a": {"signal": "bullish", "confidence": 0.9},
            "b": {"signal": "bearish", "confidence": 0.3},
        }
        score = _weighted_fusion(opinions)
        assert score > 0  # higher confidence bullish dominates


class TestScoreToLabel:
    def test_bullish(self) -> None:
        assert _score_to_label(0.3) == "bullish"

    def test_bearish(self) -> None:
        assert _score_to_label(-0.3) == "bearish"

    def test_neutral(self) -> None:
        assert _score_to_label(0.05) == "neutral"


@pytest.mark.asyncio
async def test_run_debate_returns_full_structure() -> None:
    fake_data = {"symbol": "AAPL", "quote": {"price": 150}}
    fake_opinion = {"signal": "bullish", "confidence": 0.7, "reasoning": "test"}

    with (
        patch(
            "app.agent.analysts.debate._gather_data",
            new=AsyncMock(return_value=fake_data),
        ),
        patch(
            "app.agent.analysts.debate._call_llm",
            new=AsyncMock(return_value=fake_opinion),
        ),
    ):
        result = await run_debate("AAPL", rounds=2)

    assert result["symbol"] == "AAPL"
    assert result["rounds"] == 2
    assert len(result["debate_log"]) == 2
    assert "conflict" in result
    assert "risk_vetoed" in result
    assert "fused_score" in result
    assert "portfolio_manager" in result


@pytest.mark.asyncio
async def test_risk_veto_downgrades_buy_to_hold() -> None:
    fake_data = {"symbol": "TSLA"}

    def mock_llm(prompt, data_str):
        if "Portfolio Manager" in prompt:
            return {"action": "buy", "confidence": 0.6, "summary": "looks good"}
        if "risk analyst" in prompt.lower():
            return {"signal": "bearish", "confidence": 0.8, "reasoning": "high vol"}
        return {"signal": "bullish", "confidence": 0.6, "reasoning": "test"}

    with (
        patch("app.agent.analysts.debate._gather_data", new=AsyncMock(return_value=fake_data)),
        patch("app.agent.analysts.debate._call_llm", new=AsyncMock(side_effect=mock_llm)),
    ):
        result = await run_debate("TSLA", rounds=1)

    assert result["risk_vetoed"] is True
    assert result["portfolio_manager"]["action"] == "hold"
