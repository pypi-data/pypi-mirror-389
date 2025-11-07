"""Tests for event tracking functionality."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from lumen.events import send_event


@pytest.mark.asyncio
async def test_send_event_with_user_id():
    """Test sending an event with userId returns 202 status."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            response = await send_event(
                name="simpleTestEvent",
                value=1,
                user_id="user_id_1234567890",
                api_url="http://localhost:8000"
            )

            assert response is not None
            assert response.status_code == 202


@pytest.mark.asyncio
async def test_send_event_with_lumen_customer_id():
    """Test sending an event with lumenCustomerId returns 202 status."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            response = await send_event(
                name="simpleTestEvent",
                value=2,
                lumen_customer_id="lumen_customer_id_1234567890",
                api_url="http://localhost:8000"
            )

            assert response is not None
            assert response.status_code == 202


@pytest.mark.asyncio
async def test_send_event_with_idempotency_key():
    """Test sending an event with idempotencyKey returns 202 status."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            response = await send_event(
                name="simpleTestEvent",
                value=3,
                user_id="user_id_1234567890",
                idempotency_key=f"manual_idempotency_key_{int(1000000)}",
                api_url="http://localhost:8000"
            )

            assert response is not None
            assert response.status_code == 202


@pytest.mark.asyncio
async def test_send_event_numeric_value():
    """Test sending an event with numeric value."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            response = await send_event(
                name="simpleTestEvent",
                value=420,
                user_id="user_id_1234567890",
                api_url="http://localhost:8000"
            )

            assert response is not None
            assert response.status_code == 202


@pytest.mark.asyncio
async def test_send_event_string_value():
    """Test sending an event with string value."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 202

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            response = await send_event(
                name="simpleTestEvent",
                value="hello world!",
                user_id="user_id_1234567890",
                api_url="http://localhost:8000"
            )

            assert response is not None
            assert response.status_code == 202


@pytest.mark.asyncio
async def test_send_event_no_api_key():
    """Test sending an event without API key returns None."""
    with patch.dict(os.environ, {}, clear=True):
        response = await send_event(
            name="simpleTestEvent",
            value=1,
            user_id="user_id_1234567890",
            api_url="http://localhost:8000"
        )

        assert response is None

