"""Tests for API key authentication.

Tests the require_api_key dependency in isolation. Integration with
TestClient is exercised in test_main.py via the health endpoint.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from app.core.auth import require_api_key


def _settings(api_key: str = ""):
    return type("S", (), {"api_key": api_key})()


def _run(coro):
    """Run a coroutine to completion."""
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


class TestAuthDisabled:
    def test_disabled_returns_none(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="")):
            result = asyncio.run(require_api_key(key="anything"))
        assert result is None

    def test_disabled_with_no_header(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="")):
            result = asyncio.run(require_api_key(key=None))
        assert result is None


class TestAuthEnabled:
    def test_correct_key_passes(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="secret123")):
            result = asyncio.run(require_api_key(key="secret123"))
        assert result == "secret123"

    def test_missing_key_rejected(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="secret123")):
            with pytest.raises(Exception) as excinfo:
                asyncio.run(require_api_key(key=None))
        assert excinfo.value.status_code == 401

    def test_wrong_key_rejected(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="secret123")):
            with pytest.raises(Exception) as excinfo:
                asyncio.run(require_api_key(key="wrong"))
        assert excinfo.value.status_code == 401

    def test_empty_key_rejected(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="secret123")):
            with pytest.raises(Exception) as excinfo:
                asyncio.run(require_api_key(key=""))
        assert excinfo.value.status_code == 401

    def test_different_key_rejected(self) -> None:
        with patch("app.core.auth.get_settings", return_value=_settings(api_key="secret123")):
            with pytest.raises(Exception) as excinfo:
                asyncio.run(require_api_key(key="secret456"))
        assert excinfo.value.status_code == 401

