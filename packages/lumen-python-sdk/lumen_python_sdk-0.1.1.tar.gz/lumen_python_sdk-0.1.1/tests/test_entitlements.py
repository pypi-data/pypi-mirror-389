"""Tests for entitlement checking functionality."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from lumen.entitlements import get_usage, get_features, is_feature_entitled


@pytest.mark.asyncio
async def test_get_usage_with_user_id():
    """Test getting usage with user ID."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "entitlements": [
                {
                    "feature": {"slug": "api_calls", "name": "API Calls"},
                    "entitled": True,
                    "usage": 150,
                    "limit": 1000
                }
            ]
        }

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await get_usage(user_id="user_123")

            assert "entitlements" in result
            assert len(result["entitlements"]) == 1
            assert result["entitlements"][0]["feature"]["slug"] == "api_calls"


@pytest.mark.asyncio
async def test_get_features_returns_dict():
    """Test getting features returns simplified dict."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "entitlements": [
                {
                    "feature": {"slug": "api_calls", "name": "API Calls"},
                    "entitled": True
                },
                {
                    "feature": {"slug": "premium_feature", "name": "Premium"},
                    "entitled": False
                }
            ]
        }

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await get_features(user_id="user_123")

            assert result == {
                "api_calls": True,
                "premium_feature": False
            }


@pytest.mark.asyncio
async def test_is_feature_entitled_true():
    """Test checking if feature is entitled returns True."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"entitled": True}

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await is_feature_entitled(
                feature="premium_feature",
                user_id="user_123"
            )

            assert result is True


@pytest.mark.asyncio
async def test_is_feature_entitled_false():
    """Test checking if feature is entitled returns False."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"entitled": False}

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {"LUMEN_API_KEY": "test_key"}):
            result = await is_feature_entitled(
                feature="premium_feature",
                user_id="user_123"
            )

            assert result is False

