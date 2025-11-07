"""Flask handler for proxying requests to the Lumen API."""

import os
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote, urlencode

try:
    from flask import Response, jsonify, request
    import httpx
except ImportError:
    raise ImportError(
        "Flask is required to use the Flask handler. Install with: pip install lumen-python-sdk[flask]"
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


def lumen_flask_handler(
    get_user_id: Callable[[], Optional[str]],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    supported_paths: Optional[List[str]] = None,
) -> Callable[..., Response]:
    """
    Create a Flask handler for proxying Lumen API requests.

    This handler provides a secure way to access Lumen API endpoints from your frontend
    by proxying requests through your Flask backend. It automatically injects the user ID
    and validates requests to prevent unauthorized access.

    Args:
        get_user_id: Function that returns the current user's ID (e.g., from session)
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)
        api_url: Optional API URL override (defaults to production)
        supported_paths: Optional list of allowed paths (defaults to standard Lumen paths)

    Returns:
        Flask route handler function

    Example:
        >>> from flask import Flask, session
        >>> from lumen.handlers import lumen_flask_handler
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> def get_user_id():
        ...     return session.get("user_id")
        >>>
        >>> @app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
        >>> def lumen_proxy(path):
        ...     handler = lumen_flask_handler(get_user_id=get_user_id)
        ...     return handler(path)
    """
    paths = supported_paths or SUPPORTED_PATHS

    def handler(path: str = "") -> Response:
        try:
            API_KEY = api_key or os.environ.get("LUMEN_API_KEY")
            if not API_KEY:
                return jsonify({"error": "LUMEN_API_KEY is not set in environment"}), 500

            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            lumen_backend_path = path

            if not is_allowed(lumen_backend_path, paths):
                return jsonify({"error": "Unsupported path"}), 404

            API_URL = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
            # Fix: use removesuffix instead of rstrip to avoid stripping characters from 'dev'
            base_url = API_URL.removesuffix('/v1') if API_URL.endswith('/v1') else API_URL.rstrip('/')
            full_path = f"{base_url}/v1/{lumen_backend_path}"

            url_params: Dict[str, str] = {}
            for key, value in request.args.items():
                url_params[key] = value

            external_customer_id = request.args.get("externalCustomerId")
            if external_customer_id and external_customer_id != user_id:
                return jsonify({"error": "Forbidden"}), 403

            if "{customerId}" in full_path:
                full_path = full_path.replace("{customerId}", user_id)
                url_params["isExtCustId"] = "true"

            if url_params:
                full_path = f"{full_path}?{urlencode(url_params)}"

            method = request.method
            body = None
            if method not in ["GET", "HEAD"]:
                try:
                    body = request.get_json()
                    if body and body.get("externalCustomerId") and body["externalCustomerId"] != user_id:
                        return jsonify({"error": "Forbidden"}), 403
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

                return jsonify(data or {}), response.status_code

        except Exception as e:
            return jsonify({"error": str(e) or "Internal Error"}), 500

    return handler

