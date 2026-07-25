"""The agent loop — a bounded async generator of events.

Enhanced (6.2):
  - Tool parallelism: multiple tool calls in one step execute concurrently
  - Context memory: accepts prior_messages for multi-turn conversations
  - Conversation store: in-memory session management for follow-up questions
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from app.agent import llm
from app.agent.tools import openai_tools, registry
from app.core.settings import get_settings

_SYSTEM = (
    "You are a concise trading-research assistant. Use the provided tools to fetch "
    "real market data before answering. Prefer numbers from tool results over memory. "
    "When comparing stocks or screening, call multiple tools in parallel if possible. "
    "Cite specific numbers (prices, P/E, sentiment scores) in your analysis."
)

_conversations: dict[str, list[dict[str, Any]]] = {}
_MAX_HISTORY = 20


def get_history(session_id: str) -> list[dict[str, Any]]:
    return _conversations.get(session_id, [])


def clear_history(session_id: str) -> None:
    _conversations.pop(session_id, None)


async def run(
    prompt: str,
    session_id: str | None = None,
    prior_messages: list[dict[str, Any]] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    tools = openai_tools()
    reg = registry()
    history = prior_messages or (get_history(session_id) if session_id else [])
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM},
        *history[-_MAX_HISTORY:],
        {"role": "user", "content": prompt},
    ]

    for step in range(get_settings().agent_max_iterations):
        assistant = await llm.chat(messages, tools)
        messages.append(
            {
                "role": "assistant",
                "content": assistant.get("content"),
                "tool_calls": assistant.get("tool_calls"),
            }
        )

        tool_calls = assistant.get("tool_calls") or []
        if not tool_calls:
            answer = assistant.get("content") or ""
            if session_id:
                _conversations.setdefault(session_id, []).extend(
                    [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": answer},
                    ]
                )
            yield {"type": "final", "data": {"answer": answer}}
            return

        async def _exec(call: dict) -> dict:
            fn = call["function"]
            name = fn["name"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool = reg.get(name)
            try:
                if tool is None:
                    raise ValueError(f"unknown tool: {name}")
                result = await tool.handler(args)
                ok = True
            except Exception as exc:
                result = {"error": str(exc)}
                ok = False
            return {"id": call["id"], "name": name, "args": args, "result": result, "ok": ok}

        results = await asyncio.gather(*[_exec(c) for c in tool_calls])

        for r in results:
            yield {
                "type": "tool_call",
                "data": {"id": r["id"], "name": r["name"], "arguments": r["args"]},
            }
            yield {
                "type": "tool_result",
                "data": {"id": r["id"], "name": r["name"], "ok": r["ok"], "result": r["result"]},
            }
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": r["id"],
                    "content": json.dumps(r["result"], default=str),
                }
            )

        yield {"type": "step", "data": {"index": step + 1}}

    yield {
        "type": "error",
        "data": {"message": "agent exceeded max iterations without a final answer"},
    }
