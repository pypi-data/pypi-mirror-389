"""Tests for customer management functionality."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from lumen.customers import get_subscription_status, get_customer_overview


@pytest.mark.asyncio
async def test_get_subscription_status_success():
    """Test successful subscription status retrieval."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "hasActiveSubscription": True,
            "customer": {"id": "cust_123"}
        }

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await get_subscription_status(user_id="user_123")

            assert result.get("hasActiveSubscription") is True
            assert result.get("customer", {}).get("id") == "cust_123"


@pytest.mark.asyncio
async def test_get_subscription_status_no_api_key():
    """Test subscription status without API key returns error."""
    with patch.dict(os.environ, {}, clear=True):
        result = await get_subscription_status(user_id="user_123")

        assert "error" in result
        assert "API key is not set" in result["error"]


@pytest.mark.asyncio
async def test_get_customer_overview_success():
    """Test successful customer overview retrieval."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "customer": {"id": "cust_123", "email": "user@example.com"}
        }

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await get_customer_overview(user_id="user_123")

            assert "customer" in result


@pytest.mark.asyncio
async def test_get_customer_overview_no_api_key():
    """Test customer overview without API key returns error."""
    with patch.dict(os.environ, {}, clear=True):
        result = await get_customer_overview(user_id="user_123")

        assert "error" in result
        assert "API key is not set" in result["error"]

