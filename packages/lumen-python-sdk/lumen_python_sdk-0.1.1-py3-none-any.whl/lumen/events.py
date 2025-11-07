"""Event tracking functions for the Lumen SDK."""

import os
from typing import Any, Dict, Optional, Union

import httpx


async def send_event(
    name: str,
    value: Optional[Union[int, str]] = None,
    user_id: Optional[str] = None,
    lumen_customer_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[httpx.Response]:
    """
    Send usage events to track customer activity and usage.

    Events are used to track customer usage for billing, entitlements, and analytics.
    You can send numeric values for usage-based billing or string values for categorical tracking.

    Args:
        name: The name of the event to track. Should match the event-name in the Plan > Features
        value: The value associated with the event. Can be a number for usage or string for
            categorical data. Defaults to 1 if not provided.
        user_id: User ID from your backend system. Required if lumen_customer_id is not provided.
        lumen_customer_id: Lumen customer ID. Required if user_id is not provided.
        idempotency_key: Optional idempotency key to prevent duplicate events
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        HTTP response object, or None on error

    Example:
        >>> # Send a numeric usage event
        >>> await send_event(
        ...     name="api_call",
        ...     value=1,
        ...     user_id="user_123"
        ... )
        >>>
        >>> # Send a string categorical event
        >>> await send_event(
        ...     name="feature_used",
        ...     value="premium_feature",
        ...     user_id="user_123"
        ... )
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")
        if not api_key_val:
            print(
                "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            )
            return None

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"

        event_value: Optional[int] = None
        event_string: Optional[str] = None

        if isinstance(value, str):
            event_string = value
        elif isinstance(value, (int, float)):
            event_value = int(value)
        else:
            event_value = 1

        payload: Dict[str, Any] = {
            "eventName": name,
        }

        if event_value is not None:
            payload["eventValue"] = event_value
        if event_string is not None:
            payload["eventString"] = event_string
        if lumen_customer_id:
            payload["customerId"] = lumen_customer_id
        if user_id:
            payload["extCustomerId"] = user_id
        if idempotency_key:
            payload["idempotencyKey"] = idempotency_key

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/events",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key_val}",
                },
                json=payload,
            )

            if not response.is_success:
                print("Error: Failed to send event", response)

            return response
    except Exception as e:
        print("Catch error: Failed to send event", e)
        return None

