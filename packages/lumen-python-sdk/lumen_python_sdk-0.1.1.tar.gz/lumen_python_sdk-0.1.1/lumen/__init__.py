"""
Lumen Python SDK - Payments and Billing Infrastructure

Official Python SDK for Lumen, providing easy integration with Lumen's
billing, subscriptions, and entitlements infrastructure.
"""

__version__ = "0.1.0"

from .customers import (
    get_customer_overview,
    get_seat_usage_by_user,
    get_subscription_status,
)
from .enrollment import enroll_user
from .entitlements import get_features, get_usage, is_feature_entitled
from .events import send_event
from .exceptions import (
    LumenAPIError,
    LumenConfigurationError,
    LumenError,
    LumenValidationError,
)
from .seats import add_seat, get_seat_usage, remove_seat
from .subscriptions import (
    create_free_subscription,
    create_free_subscription_if_none_exists,
)

__all__ = [
    "__version__",
    "get_subscription_status",
    "get_customer_overview",
    "get_seat_usage_by_user",
    "enroll_user",
    "get_usage",
    "get_features",
    "is_feature_entitled",
    "send_event",
    "add_seat",
    "remove_seat",
    "get_seat_usage",
    "create_free_subscription_if_none_exists",
    "create_free_subscription",
    "LumenError",
    "LumenAPIError",
    "LumenConfigurationError",
    "LumenValidationError",
]

