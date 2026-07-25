"""Embedding + retrieval — semantic search over knowledge chunks.

Primary: uses LLM API's /embeddings endpoint for true semantic search.
Fallback: keyword overlap scoring (always available, no external dependency).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import httpx

from app.core.logging import get_logger
from app.core.settings import get_settings

_log = get_logger(__name__)

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "and",
        "but",
        "or",
        "not",
        "no",
        "if",
        "then",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "he",
        "she",
        "we",
        "they",
        "you",
        "i",
    }
)


def _tokenize(text: str) -> list[str]:
    return [
        w.strip(".,!?;:\"'()[]{}").lower()
        for w in text.split()
        if w.strip(".,!?;:\"'()[]{}").lower() not in _STOP_WORDS
        and len(w.strip(".,!?;:\"'()[]{}")) > 2
    ]


async def get_embedding(text: str) -> list[float] | None:
    """Get embedding vector from LLM API. Returns None if unavailable."""
    settings = get_settings()
    if not settings.llm_base_url or not settings.llm_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": "embedding-3", "input": text[:2000]},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
    except Exception as exc:
        _log.debug("embedding_api_unavailable", error=str(exc))
        return None


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_score(query: str, document: str) -> float:
    """Simple keyword overlap score (TF-based, normalized)."""
    q_tokens = set(_tokenize(query))
    d_tokens = _tokenize(document)
    if not q_tokens or not d_tokens:
        return 0.0
    matches = sum(1 for t in d_tokens if t in q_tokens)
    return matches / len(q_tokens)


async def score_similarity(query: str, document: str) -> float:
    """Best-effort semantic similarity. Uses embeddings if available, else keywords."""
    q_emb = await get_embedding(query)
    if q_emb is not None:
        d_emb = await get_embedding(document)
        if d_emb is not None:
            return cosine_similarity(q_emb, d_emb)
    return keyword_score(query, document)
