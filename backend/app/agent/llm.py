"""LLM client — talks to any OpenAI-compatible chat completions endpoint via httpx.

No langchain/langgraph: the agent loop in `loop.py` is the entire orchestration.
Returns the assistant message dict: {role, content, tool_calls?}.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.errors import UpstreamError
from app.core.settings import get_settings


def _configured() -> None:
    s = get_settings()
    missing = [k for k, v in (("base_url", s.llm_base_url), ("api_key", s.llm_api_key), ("model", s.llm_model)) if not v]
    if missing:
        raise UpstreamError(f"LLM not configured (missing: {', '.join(missing)})", 503)


async def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    _configured()
    s = get_settings()
    payload: dict[str, Any] = {
        "model": s.llm_model,
        "messages": messages,
        "temperature": s.llm_temperature,
        "tools": tools,
        "tool_choice": "auto",
    }
    url = s.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {s.llm_api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=s.llm_timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise UpstreamError(f"LLM request failed: {exc}") from exc
    if resp.status_code != 200:
        raise UpstreamError(f"LLM HTTP {resp.status_code}: {resp.text[:300]}", 502)
    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise UpstreamError("LLM returned no choices", 502)
    return choices[0]["message"]
