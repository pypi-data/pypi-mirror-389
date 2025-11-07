"""
Basic usage example for the Lumen Python SDK.

This example demonstrates the core functionality of the SDK including:
- Checking subscription status
- Tracking events
- Checking feature entitlements
- Managing seats
"""

import asyncio
import os

from lumen import (
    add_seat,
    get_features,
    get_subscription_status,
    get_usage,
    is_feature_entitled,
    send_event,
)


async def main() -> None:
    """Run basic usage examples."""

    api_key = os.environ.get("LUMEN_API_KEY")
    if not api_key:
        print("Please set LUMEN_API_KEY environment variable")
        return

    user_id = "demo_user_123"

    print("=== Lumen Python SDK - Basic Usage Examples ===\n")

    print("1. Checking subscription status...")
    status = await get_subscription_status(user_id=user_id)
    if "error" in status:
        print(f"   Error: {status['error']}")
    else:
        print(f"   Has active subscription: {status.get('hasActiveSubscription')}")
        print(f"   Customer ID: {status.get('customer', {}).get('id')}")

    print("\n2. Sending usage event...")
    response = await send_event(
        name="api_call",
        value=1,
        user_id=user_id
    )
    if response:
        print(f"   Event sent successfully (status: {response.status_code})")
    else:
        print("   Failed to send event")

    print("\n3. Getting usage and entitlements...")
    usage = await get_usage(user_id=user_id)
    if "error" in usage:
        print(f"   Error: {usage['error']}")
    else:
        entitlements = usage.get("entitlements", [])
        print(f"   Found {len(entitlements)} entitlements:")
        for ent in entitlements[:3]:
            feature = ent.get("feature", {})
            print(f"   - {feature.get('name')}: {ent.get('usage')}/{ent.get('limit')}")

    print("\n4. Getting features as key-value pairs...")
    features = await get_features(user_id=user_id)
    if features:
        print("   Features:")
        for slug, entitled in list(features.items())[:5]:
            print(f"   - {slug}: {entitled}")
    else:
        print("   No features found")

    print("\n5. Checking specific feature entitlement...")
    has_premium = await is_feature_entitled(
        feature="premium_feature",
        user_id=user_id
    )
    print(f"   Has premium feature: {has_premium}")

    print("\n6. Adding a seat (example - may fail if not configured)...")
    seat_result = await add_seat(
        new_user_id="new_user_456",
        organisation_user_id=user_id,
        metadata={"role": "developer"}
    )
    if "error" in seat_result:
        print(f"   Info: {seat_result['error']}")
    else:
        print(f"   Seat added successfully")

    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())

