"""Subscription management functions for the Lumen SDK."""

import os
from typing import Any, Dict, Optional

import httpx

from .types import SubscriptionResponse


async def create_free_subscription_if_none_exists(
    email: str,
    name: str,
    user_id: str,
    billing_address_line1: Optional[str] = None,
    billing_address_line2: Optional[str] = None,
    billing_city: Optional[str] = None,
    billing_postal_code: Optional[str] = None,
    billing_country: Optional[str] = None,
    tax_id: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SubscriptionResponse:
    """
    Create a free subscription for a customer if they don't already have one.

    This function is useful for onboarding new users with a free tier or trial subscription.
    It will only create a subscription if the customer doesn't already have an active subscription.

    Args:
        email: Customer's email address
        name: Customer's full name
        user_id: User ID from your backend system to identify the customer
        billing_address_line1: Optional billing address line 1
        billing_address_line2: Optional billing address line 2
        billing_city: Optional billing city
        billing_postal_code: Optional billing postal/zip code
        billing_country: Optional billing country code (ISO 3166-1 alpha-2)
        tax_id: Optional tax ID for the customer
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary containing created subscription data

    Raises:
        Exception: If the subscription creation fails

    Example:
        >>> subscription = await create_free_subscription_if_none_exists(
        ...     email="user@example.com",
        ...     name="John Doe",
        ...     user_id="user_123",
        ...     billing_address_line1="123 Main St",
        ...     billing_city="New York",
        ...     billing_country="US",
        ...     billing_postal_code="10001"
        ... )
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            raise Exception(
                "Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            )

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"

        payload: Dict[str, Any] = {
            "customerEmail": email,
            "customerName": name,
            "userId": user_id,
        }

        if billing_address_line1 is not None:
            payload["billingAddressLine1"] = billing_address_line1
        if billing_address_line2 is not None:
            payload["billingAddressLine2"] = billing_address_line2
        if billing_city is not None:
            payload["billingCity"] = billing_city
        if billing_postal_code is not None:
            payload["billingPostalCode"] = billing_postal_code
        if billing_country is not None:
            payload["billingCountry"] = billing_country
        if tax_id is not None:
            payload["taxId"] = tax_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/subscriptions/create-free-subscription",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key_val}",
                },
                json=payload,
            )

            if not response.is_success:
                raise Exception(f"Failed to create free subscription: {response.status_code}")

            return response.json()
    except Exception as e:
        print("Error creating free subscription:", e)
        raise


create_free_subscription = create_free_subscription_if_none_exists

