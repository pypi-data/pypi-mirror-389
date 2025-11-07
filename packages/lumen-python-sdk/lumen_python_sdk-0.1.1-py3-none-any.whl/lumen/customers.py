"""Customer management functions for the Lumen SDK."""

import os
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .types import CustomerOverview, SeatUsage, SubscriptionStatus


async def get_subscription_status(
    user_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SubscriptionStatus:
    """
    Get the subscription status for a customer.

    Args:
        user_id: User ID from your backend system
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary containing subscription status information
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            return {
                "error": "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            }

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
        url = f"{base_url}/v1/customers/subscription-status?externalCustomerId={quote(user_id)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key_val}"},
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                return {
                    "error": error_data.get("error")
                    or f"Failed to fetch subscription status: {response.status_code}"
                }

            return response.json()
    except Exception:
        return {"error": "Catch error: Failed to fetch subscription status"}


async def get_customer_overview(
    user_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> CustomerOverview:
    """
    Get an overview of customer information including billing and subscription details.

    Args:
        user_id: User ID from your backend system
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary containing customer overview information
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            return {
                "error": "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            }

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
        url = f"{base_url}/v1/customers/portal/overview?externalCustomerId={quote(user_id)}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key_val}"},
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                return {
                    "error": error_data.get("error")
                    or f"Failed to fetch customer overview: {response.status_code}"
                }

            return response.json()
    except Exception:
        return {"error": "Catch error: Failed to fetch customer overview"}


async def get_seat_usage_by_user(
    user_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SeatUsage:
    """
    Get seat usage information for a customer by user ID.

    Args:
        user_id: User ID from your backend system
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary containing seat usage information
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            return {
                "error": "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            }

        status = await get_subscription_status(
            user_id=user_id,
            api_url=api_url,
            api_key=api_key_val,
        )

        if "error" in status:
            return status

        customer_id = status.get("customer", {}).get("id")
        has_active = status.get("hasActiveSubscription") is True

        if not customer_id:
            return {"error": "Customer not found"}
        if not has_active:
            return {"error": "No active subscription"}

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
        url = f"{base_url}/v1/seats/usage/{quote(str(customer_id))}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key_val}"},
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                return {
                    "error": error_data.get("error")
                    or f"Failed to fetch seat usage: {response.status_code}"
                }

            return response.json()
    except Exception:
        return {"error": "Catch error: Failed to fetch seat usage by user"}

