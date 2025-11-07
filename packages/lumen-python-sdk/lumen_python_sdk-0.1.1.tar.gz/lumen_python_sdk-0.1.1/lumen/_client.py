"""Base client for making HTTP requests to the Lumen API."""

import os
from typing import Any, Dict, Optional

import httpx

from .exceptions import LumenAPIError, LumenConfigurationError


class LumenClient:
    """Base HTTP client for Lumen API requests."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("LUMEN_API_KEY")
        if not self.api_key:
            raise LumenConfigurationError(
                "Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            )

        self.api_url = (api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev").rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "LumenClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the Lumen API."""
        url = f"{self.api_url}{path}"
        try:
            response = await self.client.get(url, params=params)
            if not response.is_success:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                error_message = error_data.get("error") or f"Failed to fetch {path}: {response.status_code}"
                return {"error": error_message}

            return response.json()
        except httpx.HTTPError as e:
            return {"error": f"Catch error: Failed to fetch {path}"}

    async def post(
        self, path: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request to the Lumen API."""
        url = f"{self.api_url}{path}"
        try:
            response = await self.client.post(url, json=data)
            if not response.is_success:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                error_message = error_data.get("error") or f"Failed to post to {path}: {response.status_code}"
                return {"error": error_message}

            return response.json()
        except httpx.HTTPError as e:
            return {"error": f"Catch error: Failed to post to {path}"}

    async def post_raw(
        self, path: str, data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Make a POST request and return raw response."""
        url = f"{self.api_url}{path}"
        return await self.client.post(url, json=data)

