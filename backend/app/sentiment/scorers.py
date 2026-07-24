"""Sentiment scorers — LLM-based (primary) and keyword-based (fallback).

The LLM scorer sends a batch of headlines to the configured LLM endpoint
and asks for a sentiment rating. The keyword scorer is a simple
finance-lexicon positive/negative word counter that always works.
"""

from __future__ import annotations

import json

import httpx

from app.core.logging import get_logger
from app.core.settings import get_settings

_log = get_logger(__name__)

# Finance-specific sentiment lexicon for the keyword fallback scorer
_POSITIVE_WORDS = frozenset({
    "beat", "beats", "surge", "surges", "soar", "soars", "rally", "rallies",
    "gain", "gains", "jump", "jumps", "rise", "rises", "bull", "bullish",
    "upgrade", "upgraded", "buy", "strong", "growth", "profit", "profits",
    "record", "high", "breakthrough", "win", "wins", "deal", "partnership",
    "launch", "approved", "approval", "positive", "optimism", "optimistic",
    "outperform", "raise", "raised", "boost", "boosts", "up", "higher",
})

_NEGATIVE_WORDS = frozenset({
    "miss", "misses", "plunge", "plunges", "crash", "crashes", "fall", "falls",
    "drop", "drops", "decline", "declines", "bear", "bearish", "downgrade",
    "downgraded", "sell", "loss", "losses", "cut", "cuts", "low", "weak",
    "fear", "fears", "risk", "warning", "warns", "lawsuit", "fraud",
    "investigation", "probe", "recall", "halt", "halts", "delay", "delays",
    "negative", "pessimism", "pessimistic", "underperform", "lower", "down",
})


def keyword_score(headlines: list[str]) -> tuple[float, float]:
    """Score headlines using a finance lexicon. Returns (score, confidence).

    score: -1.0 to +1.0; confidence: 0.0 to 1.0 (based on word coverage).
    """
    total_pos = 0
    total_neg = 0
    total_words = 0

    for h in headlines:
        words = h.lower().split()
        total_words += len(words)
        for w in words:
            clean = w.strip(".,!?;:\"'()[]")
            if clean in _POSITIVE_WORDS:
                total_pos += 1
            elif clean in _NEGATIVE_WORDS:
                total_neg += 1

    if total_pos + total_neg == 0:
        return 0.0, 0.0

    score = (total_pos - total_neg) / (total_pos + total_neg)
    coverage = (total_pos + total_neg) / max(total_words, 1)
    confidence = min(coverage * 10, 1.0)  # scale up since lexicon coverage is low
    return score, confidence


async def llm_score(headlines: list[str]) -> tuple[float, float] | None:
    """Score headlines via LLM. Returns None if unavailable or error."""
    settings = get_settings()
    if not settings.llm_base_url or not settings.llm_api_key:
        return None

    prompt = (
        "Analyze the sentiment of the following financial news headlines.\n"
        "Respond with ONLY a JSON object: {\"score\": <float from -1 to 1>, "
        "\"confidence\": <float from 0 to 1>}\n"
        "Where -1 = very bearish, +1 = very bullish, 0 = neutral.\n\n"
    )
    for i, h in enumerate(headlines[:10], 1):
        prompt += f"{i}. {h}\n"

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            parsed = json.loads(text)
            return float(parsed["score"]), float(parsed.get("confidence", 0.7))
    except Exception as exc:
        _log.warning("llm_sentiment_failed", error=str(exc))
        return None
