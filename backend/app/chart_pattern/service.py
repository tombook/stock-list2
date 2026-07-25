"""Chart pattern recognition via LLM (QuantAgent-inspired).

Since matplotlib is not a dependency, we convert bars to a structured text
representation that the LLM can analyze. The LLM identifies classic patterns
(head & shoulders, double top/bottom, triangles, flags, VCP, etc.) and returns
structured results.
"""

from __future__ import annotations

import json

import httpx

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.marketdata import service as market_service

_log = get_logger(__name__)


_DETECTION_PROMPT = (
    "You are a technical chart analyst. Below is a candlestick chart described "
    "as a text table. Identify any classic chart patterns in the recent data.\n\n"
    "Patterns to look for: head_and_shoulders, inverse_head_and_shoulders, "
    "double_top, double_bottom, ascending_triangle, descending_triangle, "
    "symmetrical_triangle, flag_bull, flag_bear, cup_and_handle, VCP (volatility "
    "contraction pattern), breakout, breakdown.\n\n"
    "Respond in JSON: {"
    '"patterns": [{"name": "...", "type": "bullish|bearish|neutral", '
    '"confidence": 0.0-1.0, "description": "...", "key_levels": [...]}], '
    '"summary": "..."}'
)


def _bars_to_text(bars: list, max_rows: int = 60) -> str:
    """Convert bars to a text table suitable for LLM pattern analysis."""
    if not bars:
        return "(no data)"

    recent = bars[-max_rows:]
    lines = [
        f"{'Date':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Vol':>10} {'Type':>4}"
    ]
    lines.append("-" * 70)

    for b in recent:
        btype = "↑" if b.close >= b.open else "↓"
        lines.append(
            f"{str(b.ts)[:10]:<12} {b.open:>8.2f} {b.high:>8.2f} {b.low:>8.2f} "
            f"{b.close:>8.2f} {b.volume or 0:>10.0f} {btype:>4}"
        )

    closes = [b.close for b in recent]
    if closes:
        ret_total = (closes[-1] - closes[0]) / closes[0]
        line = f"\nSummary: {len(recent)} bars, total return {ret_total:.1%}"
        lines.append(line)

    return "\n".join(lines)


async def _call_llm(prompt: str, content: str) -> dict:
    """Send to multimodal LLM (falls back to text-only for text models)."""
    settings = get_settings()
    if not settings.llm_base_url or not settings.llm_api_key:
        return {"patterns": [], "summary": "LLM not configured"}
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
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
    except Exception as exc:
        _log.warning("pattern_llm_failed", error=str(exc))
        return {"patterns": [], "summary": f"LLM error: {exc}"}


async def detect_patterns(symbol: str, timeframe: str = "1d", limit: int = 60) -> dict:
    """Detect chart patterns via LLM analysis of price action."""
    bars = await market_service.get_bars(symbol, timeframe, limit)
    text = _bars_to_text(bars.bars, max_rows=limit)
    result = await _call_llm(_DETECTION_PROMPT, text)
    return {
        "symbol": bars.symbol,
        "timeframe": timeframe,
        "n_bars": len(bars.bars),
        "patterns": result.get("patterns", []),
        "summary": result.get("summary", ""),
        "source": "llm",
    }


def _bar_to_text(b) -> str:
    """Format a single bar as a text line (exported for testing)."""
    btype = "up" if b.close >= b.open else "down"
    return f"{str(b.ts)[:10]} O={b.open:.2f} H={b.high:.2f} L={b.low:.2f} C={b.close:.2f} {btype}"
