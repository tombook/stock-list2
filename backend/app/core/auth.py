"""API Key authentication middleware.

When settings.api_key is non-empty, all /api/* routes require
X-API-Key header. Empty api_key disables auth (dev mode only).
Uses constant-time comparison to prevent timing attacks.
"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.settings import get_settings

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    key: Annotated[str | None, Depends(_header)] = None,
) -> str | None:
    settings = get_settings()
    if not settings.api_key:
        return None
    if not key or not hmac.compare_digest(key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
    return key
