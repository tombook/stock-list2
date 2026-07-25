"""Agent endpoint — POST /api/analyze streams the agent loop as Server-Sent Events.

Event types: `step`, `tool_call`, `tool_result`, `final`, `error`. Uses a plain
StreamingResponse (no extra dependency) with SSE framing.
Supports multi-turn conversations via session_id.
"""

from __future__ import annotations

import json

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.agent import loop

router = APIRouter(prefix="/api", tags=["agent"])


class AnalyzeRequest(BaseModel):
    prompt: str
    stream: bool = True
    session_id: str | None = None


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> StreamingResponse:
    async def gen():
        try:
            async for event in loop.run(req.prompt, session_id=req.session_id):
                yield f"event: {event['type']}\ndata: {json.dumps(event['data'], default=str)}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/analyze/session/{session_id}")
async def clear_session(session_id: str) -> dict:
    loop.clear_history(session_id)
    return {"cleared": True}


@router.post("/analyze/deep")
async def analyze_deep_endpoint(req: AnalyzeRequest) -> dict:
    from app.agent.analysts.framework import analyze_deep

    return await analyze_deep(req.prompt)


@router.post("/analyze/debate")
async def analyze_debate_endpoint(req: AnalyzeRequest) -> dict:
    from app.agent.analysts.debate import run_debate

    return await run_debate(req.prompt, rounds=2)
