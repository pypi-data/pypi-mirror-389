"""Seat-based pricing functions for managing user seats in subscriptions."""

import os
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .types import SeatUsage


async def add_seat(
    new_user_id: str,
    organisation_user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    timestamp: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a user to a seat-based subscription.

    Args:
        new_user_id: User ID (on your backend) of the new user being added to the seat
        organisation_user_id: User ID (on your backend) of the organization who owns
            the subscription. This must match the User ID you used in the PricingTable
            component when the user first paid for the subscription (fallback if organization_id not provided)
        organization_id: Organization ID (preferred) - the internal Lumen organization ID
        metadata: Optional metadata to attach to the seat addition event
        idempotency_key: Optional idempotency key to prevent duplicate operations
        timestamp: Optional UTC timestamp in ISO format ending with 'Z'
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Success response or error object
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")

        if not api_key_val:
            error = "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            print(error)
            return {"error": error}

        if not organization_id and not organisation_user_id:
            error = "Either organization_id or organisation_user_id must be provided"
            print(error)
            return {"error": error}

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"

        payload: Dict[str, Any] = {
            "created_user_id": new_user_id,
        }

        if organisation_user_id:
            payload["user_id"] = organisation_user_id
        if organization_id:
            payload["organization_id"] = organization_id
        if metadata:
            payload["metadata"] = metadata
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if timestamp:
            payload["timestamp"] = timestamp

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/seats/add",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key_val}",
                },
                json=payload,
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                print("Error: Failed to add seat", response.status_code, error_data)
                return {
                    "error": error_data.get("error") or f"Failed to add seat: {response.status_code}"
                }

            return response.json()
    except Exception as e:
        error_message = "Catch error: Failed to add seat"
        print(error_message, e)
        return {"error": error_message}


async def remove_seat(
    removed_user_id: str,
    organisation_user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    timestamp: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Remove a user from a seat-based subscription.

    Args:
        removed_user_id: User ID (on your backend) of the user being removed from the seat
        organisation_user_id: User ID (on your backend) of the organization who owns
            the subscription. This must match the User ID you used in the PricingTable
            component when the user first paid for the subscription (fallback if organization_id not provided)
        organization_id: Organization ID (preferred) - the internal Lumen organization ID
        metadata: Optional metadata to attach to the seat removal event
        idempotency_key: Optional idempotency key to prevent duplicate operations
        timestamp: Optional UTC timestamp in ISO format ending with 'Z'
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Success response or error object
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")

        if not api_key_val:
            error = "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            print(error)
            return {"error": error}

        if not organization_id and not organisation_user_id:
            error = "Either organization_id or organisation_user_id must be provided"
            print(error)
            return {"error": error}

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"

        payload: Dict[str, Any] = {
            "removed_user_id": removed_user_id,
        }

        if organisation_user_id:
            payload["user_id"] = organisation_user_id
        if organization_id:
            payload["organization_id"] = organization_id
        if metadata:
            payload["metadata"] = metadata
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if timestamp:
            payload["timestamp"] = timestamp

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/seats/remove",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key_val}",
                },
                json=payload,
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                print("Error: Failed to remove seat", response.status_code, error_data)
                return {
                    "error": error_data.get("error")
                    or f"Failed to remove seat: {response.status_code}"
                }

            return response.json()
    except Exception as e:
        error_message = "Catch error: Failed to remove seat"
        print(error_message, e)
        return {"error": error_message}


async def get_seat_usage(
    customer_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SeatUsage:
    """
    Get current seat usage for a customer.

    Args:
        customer_id: Lumen customer ID to get seat usage for
        api_url: Optional API URL override (defaults to production)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)

    Returns:
        Seat usage data or error object
    """
    try:
        api_key_val = api_key or os.environ.get("LUMEN_API_KEY")

        if not api_key_val:
            error = "Error: Lumen API key is not set. Visit https://getlumen.dev/developer/apikeys to get one"
            print(error)
            return {"error": error}

        base_url = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/v1/seats/usage/{quote(customer_id)}",
                headers={"Authorization": f"Bearer {api_key_val}"},
            )

            if not response.is_success:
                error_data: Dict[str, Any] = {}
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"error": "Unknown error"}

                print("Error: Failed to get seat usage", response.status_code, error_data)
                return {
                    "error": error_data.get("error")
                    or f"Failed to get seat usage: {response.status_code}"
                }

            return response.json()
    except Exception as e:
        error_message = "Catch error: Failed to get seat usage"
        print(error_message, e)
        return {"error": error_message}

