"""FastAPI handler for proxying requests to the Lumen API."""

import os
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode

try:
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
    import httpx
except ImportError:
    raise ImportError(
        "FastAPI is required to use the FastAPI handler. Install with: pip install lumen-python-sdk[fastapi]"
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


def lumen_fastapi_handler(
    get_user_id: Callable[[Request], Optional[str]],
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    supported_paths: Optional[List[str]] = None,
) -> Callable:
    """
    Create a FastAPI handler for proxying Lumen API requests.

    This handler provides a secure way to access Lumen API endpoints from your frontend
    by proxying requests through your FastAPI backend. It automatically injects the user ID
    and validates requests to prevent unauthorized access.

    Args:
        get_user_id: Async function that returns the current user's ID from the request
        api_key: Optional API key override (defaults to LUMEN_API_KEY env var)
        api_url: Optional API URL override (defaults to production)
        supported_paths: Optional list of allowed paths (defaults to standard Lumen paths)

    Returns:
        FastAPI route handler function

    Example:
        >>> from fastapi import FastAPI, Depends, Request
        >>> from lumen.handlers import lumen_fastapi_handler
        >>>
        >>> app = FastAPI()
        >>>
        >>> def get_user_id(request: Request) -> Optional[str]:
        ...     # Get user ID from JWT, session, etc.
        ...     return request.state.user_id
        >>>
        >>> handler = lumen_fastapi_handler(get_user_id=get_user_id)
        >>>
        >>> @app.api_route("/api/lumen/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
        >>> async def lumen_proxy(request: Request, path: str):
        ...     return await handler(request, path)
    """
    paths = supported_paths or SUPPORTED_PATHS

    async def handler(request: Request, path: str = "") -> JSONResponse:
        try:
            API_KEY = api_key or os.environ.get("LUMEN_API_KEY")
            if not API_KEY:
                return JSONResponse(
                    {"error": "LUMEN_API_KEY is not set in environment"}, status_code=500
                )

            user_id = get_user_id(request)
            if not user_id:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)

            lumen_backend_path = path

            if not is_allowed(lumen_backend_path, paths):
                return JSONResponse({"error": "Unsupported path"}, status_code=404)

            API_URL = api_url or os.environ.get("LUMEN_API_URL") or "https://api.getlumen.dev"
            # Fix: use removesuffix instead of rstrip to avoid stripping characters from 'dev'
            base_url = API_URL.removesuffix('/v1') if API_URL.endswith('/v1') else API_URL.rstrip('/')
            full_path = f"{base_url}/v1/{lumen_backend_path}"

            url_params: Dict[str, str] = {}
            for key, value in request.query_params.items():
                url_params[key] = value

            external_customer_id = request.query_params.get("externalCustomerId")
            if external_customer_id and external_customer_id != user_id:
                return JSONResponse({"error": "Forbidden"}, status_code=403)

            if "{customerId}" in full_path:
                full_path = full_path.replace("{customerId}", user_id)
                url_params["isExtCustId"] = "true"

            if url_params:
                full_path = f"{full_path}?{urlencode(url_params)}"

            method = request.method
            body = None
            if method not in ["GET", "HEAD"]:
                try:
                    body = await request.json()
                    if (
                        body
                        and body.get("externalCustomerId")
                        and body["externalCustomerId"] != user_id
                    ):
                        return JSONResponse({"error": "Forbidden"}, status_code=403)
                except Exception:
                    body = None

            async with httpx.AsyncClient() as client:
                response = await client.request(
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

                return JSONResponse(data or {}, status_code=response.status_code)

        except Exception as e:
            return JSONResponse({"error": str(e) or "Internal Error"}, status_code=500)

    return handler

