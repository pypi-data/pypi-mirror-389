"""Type definitions for the Lumen SDK."""

from typing import Any, Dict, List, Optional, TypedDict, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


class EntitlementFeature(TypedDict, total=False):
    slug: str
    name: str


class Entitlement(TypedDict, total=False):
    feature: EntitlementFeature
    entitled: bool
    usage: Optional[int]
    limit: Optional[int]


class UsageResponse(TypedDict, total=False):
    entitlements: List[Entitlement]


class SubscriptionStatus(TypedDict, total=False):
    customer: Dict[str, Any]
    hasActiveSubscription: bool
    error: Optional[str]


class CustomerOverview(TypedDict, total=False):
    error: Optional[str]


class SeatUsage(TypedDict, total=False):
    error: Optional[str]


class EnrollmentResponse(TypedDict, total=False):
    success: bool
    customer: Dict[str, Any]


class SubscriptionResponse(TypedDict, total=False):
    success: bool
    subscription: Dict[str, Any]


ErrorResponse = Dict[str, str]
APIResponse = Union[Dict[str, Any], ErrorResponse]

