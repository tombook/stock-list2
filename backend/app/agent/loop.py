"""The agent loop — a bounded async generator of events.

One step = one LLM call. If the model returns tool_calls, we execute them, feed the
results back, and loop. When it returns a plain message, that's the final answer.
Emits dicts with a `type` discriminator so the API layer can stream them as SSE.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.agent import llm
from app.agent.tools import openai_tools, registry
from app.core.settings import get_settings

_SYSTEM = (
    "You are a concise trading-research assistant. Use the provided tools to fetch "
    "real market data before answering. Prefer numbers from tool results over memory."
)


async def run(prompt: str) -> AsyncIterator[dict[str, Any]]:
    tools = openai_tools()
    reg = registry()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM},
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
            yield {"type": "final", "data": {"answer": assistant.get("content") or ""}}
            return

        for call in tool_calls:
            fn = call["function"]
            name = fn["name"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            yield {"type": "tool_call", "data": {"id": call["id"], "name": name, "arguments": args}}

            tool = reg.get(name)
            try:
                if tool is None:
                    raise ValueError(f"unknown tool: {name}")
                result = await tool.handler(args)
                ok = True
            except Exception as exc:  # surface tool failures to the model, keep looping
                result = {"error": str(exc)}
                ok = False
            yield {"type": "tool_result", "data": {"id": call["id"], "name": name, "ok": ok, "result": result}}
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, default=str)}
            )

        yield {"type": "step", "data": {"index": step + 1}}

    yield {"type": "error", "data": {"message": "agent exceeded max iterations without a final answer"}}
