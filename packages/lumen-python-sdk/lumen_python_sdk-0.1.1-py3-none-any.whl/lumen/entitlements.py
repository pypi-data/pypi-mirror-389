"""Entitlement and feature checking functions for the Lumen SDK."""

import os
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .types import UsageResponse


async def _call_api(
    endpoint: str,
    customer_id: str,
    is_ext_cust_id: bool,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal helper to call the Lumen API."""
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            error = "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            print(error)
            return {"error": error}

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
        full_url = f"{base_url}{endpoint}?isExtCustId={str(is_ext_cust_id).lower()}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                full_url,
                headers={"Authorization": f"Bearer {api_key_val}"},
            )

            if not response.is_success:
                error = f"Error: Failed to fetch {full_url}"
                print(error, response)
                return {"error": error}

            return response.json()
    except Exception as e:
        error_message = f"Catch error: Failed to fetch {endpoint}"
        print(error_message, e)
        return {"error": error_message}


async def get_usage(
    user_id: Optional[str] = None,
    lumen_customer_id: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> UsageResponse:
    """
    Get current usage and entitlements for a customer.

    Returns detailed information about a customer's current usage against their
    subscription limits, including feature entitlements and usage metrics.

    Args:
        user_id: User ID from your backend system. Required if lumen_customer_id is not provided.
        lumen_customer_id: Lumen customer ID. Required if user_id is not provided.
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary with entitlements array containing feature details, usage, and limits

    Example:
        >>> usage = await get_usage(user_id="user_123")
        >>> # Returns:
        >>> # {
        >>> #   "entitlements": [
        >>> #     {
        >>> #       "feature": {"slug": "api_calls", "name": "API Calls"},
        >>> #       "entitled": True,
        >>> #       "usage": 150,
        >>> #       "limit": 1000
        >>> #     }
        >>> #   ]
        >>> # }
    """
    if user_id:
        customer_id = user_id
        is_ext = True
    elif lumen_customer_id:
        customer_id = lumen_customer_id
        is_ext = False
    else:
        return {"error": "Either user_id or lumen_customer_id must be provided"}

    endpoint = f"/v1/entitlements/{quote(customer_id)}"
    return await _call_api(endpoint, customer_id, is_ext, api_url, api_key)


async def get_features(
    user_id: Optional[str] = None,
    lumen_customer_id: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Get feature entitlements for a customer as a simple key-value object.

    Returns a simplified object where keys are feature slugs and values are boolean entitlements.
    This is useful for quick feature flag checks in your application.

    Args:
        user_id: User ID from your backend system. Required if lumen_customer_id is not provided.
        lumen_customer_id: Lumen customer ID. Required if user_id is not provided.
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary with feature slugs as keys and boolean entitlements as values

    Example:
        >>> features = await get_features(user_id="user_123")
        >>> # Returns:
        >>> # {
        >>> #   "api_calls": True,
        >>> #   "premium_feature": False,
        >>> #   "advanced_analytics": True
        >>> # }
    """
    result = await get_usage(
        user_id=user_id,
        lumen_customer_id=lumen_customer_id,
        api_url=api_url,
        api_key=api_key,
    )

    entitlements = result.get("entitlements")
    if not entitlements:
        return {}

    features: Dict[str, bool] = {}
    for e in entitlements:
        feature = e.get("feature", {})
        slug = feature.get("slug")
        if slug:
            features[slug] = e.get("entitled", False)

    return features


async def is_feature_entitled(
    feature: str,
    user_id: Optional[str] = None,
    lumen_customer_id: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> bool:
    """
    Check if a customer is entitled to a specific feature.

    This is a convenience function for checking a single feature entitlement.
    Returns a boolean indicating whether the customer has access to the specified feature.

    Args:
        feature: The feature slug to check entitlement for
        user_id: User ID from your backend system. Required if lumen_customer_id is not provided.
        lumen_customer_id: Lumen customer ID. Required if user_id is not provided.
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Boolean indicating whether the customer is entitled to the feature

    Example:
        >>> can_use = await is_feature_entitled(
        ...     user_id="user_123",
        ...     feature="premium_feature"
        ... )
        >>> if can_use:
        ...     # Allow access to premium feature
        ... else:
        ...     # Show upgrade prompt
    """
    if user_id:
        customer_id = user_id
        is_ext = True
    elif lumen_customer_id:
        customer_id = lumen_customer_id
        is_ext = False
    else:
        return False

    endpoint = f"/v1/entitlements/{quote(customer_id)}/feature/{quote(feature)}"
    result = await _call_api(endpoint, customer_id, is_ext, api_url, api_key)

    return result.get("entitled", False)

