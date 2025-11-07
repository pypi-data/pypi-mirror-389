"""Django handler for proxying requests to the Lumen API."""

import json
import os
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode

try:
    from django.http import HttpRequest, JsonResponse
    import httpx
except ImportError:
    raise ImportError(
        "Django is required to use the Django handler. Install with: pip install lumen-python-sdk[django]"
    )


SUPPORTED_PATHS = [
    "customers/subscription-status",
    "entitlements/{customerId}",
    "customers/portal/overview",
    "customers/portal/create-setup-intent",
    "customers/portal/set-subscription-payment-method",
    "customers/portal/payment-methods/{id}",
    "invoices/{id}/pdf",
]


def path_to_regex(pattern: str) -> re.Pattern:
    """Convert a path pattern with {param} to a regex."""
    escaped = re.escape(pattern)
    regex_str = "^" + re.sub(r"\\\{[^/}]+\\\}", "[^/]+", escaped) + "$"
    return re.compile(regex_str)


def is_allowed(backend_path: str, supported_paths: List[str]) -> bool:
    """Check if a path is in the allowed list."""
    return any(path_to_regex(p).match(backend_path) for p in supported_paths)


def lumen_django_handler(
    get_user_id: Callable[[HttpRequest], Optional[str]],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    supported_paths: Optional[List[str]] = None,
    mount_path: str = "/api/lumen/",
) -> Callable:
    """
    Create a Django view handler for proxying Lumen API requests.

    This handler provides a secure way to access Lumen API endpoints from your frontend
    by proxying requests through your Django backend. It automatically injects the user ID
    and validates requests to prevent unauthorized access.

    Args:
        get_user_id: Function that returns the current user's ID from the request
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)
        api_url: Optional API URL override (defaults to production)
        supported_paths: Optional list of allowed paths (defaults to standard Lumen paths)
        mount_path: The URL prefix where this handler is mounted (default: "/api/lumen/")

    Returns:
        Django view function

    Example:
        >>> from django.urls import path
        >>> from lumen.handlers import lumen_django_handler
        >>>
        >>> def get_user_id(request):
        ...     return str(request.user.id) if request.user.is_authenticated else None
        >>>
        >>> lumen_view = lumen_django_handler(get_user_id=get_user_id)
        >>>
        >>> urlpatterns = [
        ...     path('api/lumen/<path:path>', lumen_view, name='lumen_proxy'),
        ... ]
    """
    paths = supported_paths or SUPPORTED_PATHS

    def handler(request: HttpRequest, path: str = "") -> JsonResponse:
        try:
            API_KEY = api_key or os.environ.get("LUMEN_API_KEY")
            if not API_KEY:
                return JsonResponse(
                    {"error": "LUMEN_API_KEY is not set in environment"}, status=500
                )

            user_id = get_user_id(request)
            if not user_id:
                return JsonResponse({"error": "Unauthorized"}, status=401)

            lumen_backend_path = path

            if not is_allowed(lumen_backend_path, paths):
                return JsonResponse({"error": "Unsupported path"}, status=404)

            API_URL = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
            # Fix: use removesuffix instead of rstrip to avoid stripping characters from 'dev'
            base_url = API_URL.removesuffix('/v1') if API_URL.endswith('/v1') else API_URL.rstrip('/')
            full_path = f"{base_url}/v1/{lumen_backend_path}"

            url_params: Dict[str, str] = {}
            for key, value in request.GET.items():
                url_params[key] = value

            external_customer_id = request.GET.get("externalCustomerId")
            if external_customer_id and external_customer_id != user_id:
                return JsonResponse({"error": "Forbidden"}, status=403)

            if "{customerId}" in full_path:
                full_path = full_path.replace("{customerId}", user_id)
                url_params["isExtCustId"] = "true"

            if url_params:
                full_path = f"{full_path}?{urlencode(url_params)}"

            method = request.method
            body = None
            if method not in ["GET", "HEAD"]:
                try:
                    body = json.loads(request.body)
                    if (
                        body
                        and body.get("externalCustomerId")
                        and body["externalCustomerId"] != user_id
                    ):
                        return JsonResponse({"error": "Forbidden"}, status=403)
                except Exception:
                    body = None

            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=full_path,
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )

                try:
                    data = response.json()
                except Exception:
                    data = None

                return JsonResponse(data or {}, status=response.status_code)

        except Exception as e:
            return JsonResponse({"error": str(e) or "Internal Error"}, status=500)

    return handler

