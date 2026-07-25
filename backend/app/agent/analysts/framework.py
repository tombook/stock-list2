"""Multi-agent analysis framework — TradingAgents-inspired specialized analysts.

6 agents run in parallel, each with a domain-specific prompt:
  - Technical Analyst: indicators + chart patterns
  - Fundamental Analyst: valuation + financial health
  - Sentiment Analyst: news + social mood
  - News Analyst: macro events + company catalysts
  - Risk Analyst: volatility + drawdown + VaR
  - Portfolio Manager: synthesizes all opinions into final recommendation

Each specialist gets pre-fetched data + domain prompt. PM sees all opinions.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.marketdata import service as market_service
from app.ml.service import predict_direction
from app.risk.analytics import analyze_risk
from app.sentiment.service import analyze_sentiment

_log = get_logger(__name__)

_DOMAIN_PROMPTS: dict[str, str] = {
    "technical": (
        "You are a technical analyst. Based on the following market data, "
        "identify key technical signals (trend, momentum, support/resistance). "
        'Respond in JSON: {"signal": "bullish|bearish|neutral", '
        '"confidence": 0.0-1.0, "reasoning": "..."}'
    ),
    "fundamental": (
        "You are a fundamental analyst. Evaluate valuation (P/E, P/B), "
        "growth prospects, and financial health from the data below. "
        'Respond in JSON: {"signal": "bullish|bearish|neutral", '
        '"confidence": 0.0-1.0, "reasoning": "..."}'
    ),
    "sentiment": (
        "You are a sentiment analyst. Assess market mood from news headlines "
        'and sentiment scores. Respond in JSON: {"signal": "bullish|bearish|neutral", '
        '"confidence": 0.0-1.0, "reasoning": "..."}'
    ),
    "news": (
        "You are a news analyst. Identify recent catalysts, macro factors, "
        "and event-driven risks from the data. Respond in JSON: "
        '{"signal": "bullish|bearish|neutral", "confidence": 0.0-1.0, "reasoning": "..."}'
    ),
    "risk": (
        "You are a risk analyst. Assess volatility, drawdown risk, and VaR. "
        'Respond in JSON: {"signal": "bullish|bearish|neutral", '
        '"confidence": 0.0-1.0, "reasoning": "..."}'
    ),
}

_PM_PROMPT = (
    "You are a Portfolio Manager. Five analysts have provided their opinions "
    "on a stock. Synthesize their views into a final recommendation. "
    'Respond in JSON: {"action": "buy|hold|sell", '
    '"confidence": 0.0-1.0, "summary": "...", '
    '"key_factors": ["...", "..."]}'
)


async def _gather_data(symbol: str) -> dict[str, Any]:
    """Fetch all data needed for multi-agent analysis."""
    data: dict[str, Any] = {"symbol": symbol}

    async def _safe(name: str, coro):
        try:
            data[name] = await coro
        except Exception as exc:
            data[name] = {"error": str(exc)}

    await asyncio.gather(
        _safe("quote", market_service.get_quote(symbol)),
        _safe("fundamentals", market_service.get_fundamentals(symbol)),
        _safe("sentiment", analyze_sentiment(symbol)),
        _safe("risk", analyze_risk(symbol)),
    )
    try:
        data["prediction"] = await predict_direction(symbol, 5)
    except Exception as exc:
        data["prediction"] = {"error": str(exc)}

    return data


async def _call_llm(prompt: str, data_str: str) -> dict[str, Any]:
    """Single LLM call for a specialist analyst."""
    settings = get_settings()
    if not settings.llm_base_url or not settings.llm_api_key:
        return {"signal": "neutral", "confidence": 0.0, "reasoning": "LLM not configured"}

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": data_str},
                    ],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            return json.loads(text)
    except Exception as exc:
        _log.warning("analyst_llm_failed", error=str(exc))
        return {"signal": "neutral", "confidence": 0.0, "reasoning": f"analysis failed: {exc}"}


async def analyze_deep(symbol: str) -> dict[str, Any]:
    """Run multi-agent analysis. Returns all analyst opinions + PM synthesis."""
    sym = symbol.upper()
    data = await _gather_data(sym)
    data_str = json.dumps(data, default=str, indent=2)

    domains = list(_DOMAIN_PROMPTS.keys())
    opinions = await asyncio.gather(*[_call_llm(_DOMAIN_PROMPTS[d], data_str) for d in domains])

    analyst_results = dict(zip(domains, opinions, strict=True))

    pm_input = json.dumps(analyst_results, indent=2)
    pm_result = await _call_llm(_PM_PROMPT, pm_input)

    return {
        "symbol": sym,
        "analysts": analyst_results,
        "portfolio_manager": pm_result,
        "data_snapshot": {
            "price": data.get("quote", {}).get("price")
            if isinstance(data.get("quote"), dict)
            else None,
            "pe": data.get("fundamentals", {}).get("trailing_pe")
            if isinstance(data.get("fundamentals"), dict)
            else None,
            "sentiment_score": data.get("sentiment", {}).get("score")
            if isinstance(data.get("sentiment"), dict)
            else None,
            "ml_probability": data.get("prediction", {}).get("probability_up")
            if isinstance(data.get("prediction"), dict)
            else None,
        },
    }
