"""User enrollment functions for the Lumen SDK."""

import os
from typing import Any, Dict, Optional

import httpx

from .types import EnrollmentResponse


async def enroll_user(
    email: str,
    name: str,
    user_id: str,
    plan_id: Optional[str] = None,
    billing_address_line1: Optional[str] = None,
    billing_address_line2: Optional[str] = None,
    billing_city: Optional[str] = None,
    billing_postal_code: Optional[str] = None,
    billing_country: Optional[str] = None,
    tax_id: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> EnrollmentResponse:
    """
    Enroll a user into a plan based on Enrollment Rules.

    Automatically falls back to the latest free plan if no rule matches.
    Mirrors the behavior of built-in Clerk/Supabase/Better Auth webhooks.

    Args:
        email: User's email address
        name: User's full name
        user_id: User ID from your backend system
        plan_id: Optional specific plan ID to enroll in
        billing_address_line1: Optional billing address line 1
        billing_address_line2: Optional billing address line 2
        billing_city: Optional billing city
        billing_postal_code: Optional billing postal/zip code
        billing_country: Optional billing country code (ISO 3166-1 alpha-2)
        tax_id: Optional tax ID
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Dictionary containing enrollment result

    Raises:
        Exception: If enrollment fails
    """
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

    if plan_id is not None:
        payload["planId"] = plan_id
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
            f"{base_url}/v1/enrollment/enroll",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key_val}",
            },
            json=payload,
        )

        if not response.is_success:
            raise Exception(f"Failed to enroll user: {response.status_code}")

        return response.json()

