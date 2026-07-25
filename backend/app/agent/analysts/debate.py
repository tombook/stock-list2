"""Multi-agent debate mechanism — TradingAgents-inspired.

Round 1: Analysts form independent opinions (reuse framework.analyze_deep).
Round 2: Each analyst sees peers' opinions and can revise/rebut/support.
Conflict detection: flags when signal divergence exceeds threshold.
Risk veto: Risk analyst's strong bearish can veto buy recommendations.
Weighted fusion: final decision weighted by each analyst's confidence.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.agent.analysts.framework import _call_llm, _gather_data
from app.core.logging import get_logger

_log = get_logger(__name__)

_DEBATE_PROMPT = (
    "You are a {domain} analyst. In round 1 you and four other analysts assessed "
    "this stock. Below are ALL analysts' round-1 opinions including yours. "
    "Review their reasoning. Do you agree or disagree? "
    "You may revise your assessment based on new perspectives. "
    'Respond in JSON: {{"signal": "bullish|bearish|neutral", '
    '"confidence": 0.0-1.0, "reasoning": "...", "revised": true|false}}'
)

_SIGNAL_SCORES = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
_CONFLICT_THRESHOLD = 0.5


async def run_debate(symbol: str, rounds: int = 2) -> dict[str, Any]:
    """Run multi-round debate. Returns full debate log + final decision."""
    from app.agent.analysts.framework import _DOMAIN_PROMPTS, _PM_PROMPT

    sym = symbol.upper()
    data = await _gather_data(sym)
    data_str = json.dumps(data, default=str, indent=2)

    domains = list(_DOMAIN_PROMPTS.keys())
    debate_log: list[dict[str, Any]] = []

    # Round 1: independent analysis
    r1 = await asyncio.gather(*[_call_llm(_DOMAIN_PROMPTS[d], data_str) for d in domains])
    opinions = dict(zip(domains, r1, strict=True))
    debate_log.append({"round": 1, "opinions": dict(opinions)})

    # Round 2+: see peers and revise
    for rnd in range(2, rounds + 1):
        all_opinions_str = json.dumps(opinions, indent=2)
        round_input = (
            f"Market Data:\\n{data_str}\\n\\nAll Round-{rnd - 1} Opinions:\\n{all_opinions_str}"
        )

        revised = await asyncio.gather(
            *[
                _call_llm(
                    _DEBATE_PROMPT.format(domain=d.replace("_", " ")),
                    round_input,
                )
                for d in domains
            ]
        )
        new_opinions = dict(zip(domains, revised, strict=True))
        debate_log.append({"round": rnd, "opinions": dict(new_opinions)})
        opinions = new_opinions

    # Conflict detection
    signals = [o.get("signal", "neutral") for o in opinions.values()]
    conflict = _detect_conflict(signals)

    # Risk veto
    risk_op = opinions.get("risk", {})
    risk_vetoed = False
    if risk_op.get("signal") == "bearish" and risk_op.get("confidence", 0) > 0.6:
        risk_vetoed = True
        _log.info("risk_veto_triggered", symbol=sym, risk_confidence=risk_op.get("confidence"))

    # Weighted fusion
    fused_score = _weighted_fusion(opinions)

    # PM synthesis (sees final opinions)
    pm_input = json.dumps(opinions, indent=2)
    pm_result = await _call_llm(_PM_PROMPT, pm_input)

    if risk_vetoed and pm_result.get("action") == "buy":
        pm_result["action"] = "hold"
        pm_result["summary"] = f"[Risk veto applied] {pm_result.get('summary', '')}"

    return {
        "symbol": sym,
        "rounds": rounds,
        "debate_log": debate_log,
        "final_opinions": opinions,
        "conflict": conflict,
        "risk_vetoed": risk_vetoed,
        "fused_score": round(fused_score, 4),
        "fused_label": _score_to_label(fused_score),
        "portfolio_manager": pm_result,
        "data_snapshot": {
            "price": _safe_get(data, "quote", "price"),
            "pe": _safe_get(data, "fundamentals", "trailing_pe"),
            "sentiment": _safe_get(data, "sentiment", "score"),
        },
    }


def _detect_conflict(signals: list[str]) -> dict[str, Any]:
    bull = sum(1 for s in signals if s == "bullish")
    bear = sum(1 for s in signals if s == "bearish")
    total = len(signals)
    spread = abs(bull - bear) / total if total > 0 else 0
    return {
        "high_divergence": spread < 1 - _CONFLICT_THRESHOLD and bull > 0 and bear > 0,
        "bullish_count": bull,
        "bearish_count": bear,
        "neutral_count": total - bull - bear,
    }


def _weighted_fusion(opinions: dict[str, Any]) -> float:
    total_weight = 0.0
    weighted_sum = 0.0
    for op in opinions.values():
        conf = float(op.get("confidence", 0))
        signal = op.get("signal", "neutral")
        score = _SIGNAL_SCORES.get(signal, 0.0)
        weighted_sum += conf * score
        total_weight += conf
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def _score_to_label(score: float) -> str:
    if score > 0.15:
        return "bullish"
    if score < -0.15:
        return "bearish"
    return "neutral"


def _safe_get(data: dict, *keys) -> Any:
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return None
    return val
