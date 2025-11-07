"""
FastAPI integration example for the Lumen Python SDK.

This example shows how to integrate Lumen with a FastAPI application,
including both the backend proxy for frontend calls and direct backend usage.
"""

from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from lumen.handlers import lumen_fastapi_handler
from lumen import get_subscription_status, send_event, is_feature_entitled

app = FastAPI(title="Lumen FastAPI Example")


def get_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from request.

    In production, this would typically:
    - Decode JWT token: jwt.decode(request.headers["Authorization"])
    - Check session/cookie
    - Validate API key

    For this example, we're using a header for simplicity.
    """
    return request.headers.get("X-User-ID")


# ============================================================================
# Backend Proxy Setup (Required for Frontend Access)
# ============================================================================
# This route securely proxies frontend requests to Lumen without exposing
# your API key to the browser.
#
# Your frontend calls: /api/lumen/customers/subscription-status
# This handler forwards to: Lumen API with user ID injected
# ============================================================================

handler = lumen_fastapi_handler(get_user_id=get_user_id)


@app.api_route(
    "/api/lumen/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    response_class=JSONResponse
)
async def lumen_proxy(request: Request, path: str) -> JSONResponse:
    """
    Proxy requests to Lumen API.

    Frontend usage:
        fetch('/api/lumen/customers/subscription-status')
          .then(r => r.json())
          .then(data => console.log(data))
    """
    return await handler(request, path)


# ============================================================================
# Direct Backend SDK Usage Examples
# ============================================================================
# Use these patterns in your backend API routes
# ============================================================================

@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Lumen FastAPI Example",
        "docs": "/docs",
        "endpoints": {
            "proxy": "/api/lumen/*",
            "protected": "/api/protected",
            "premium": "/api/premium-feature",
            "action": "/api/track-usage"
        }
    }


@app.get("/api/protected")
async def protected_endpoint(request: Request) -> dict:
    """Example: Protect a route with subscription check."""
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check if user has active subscription
    status = await get_subscription_status(user_id=user_id)

    if "error" in status:
        raise HTTPException(status_code=400, detail=status["error"])

    if not status.get("hasActiveSubscription"):
        raise HTTPException(
            status_code=402,
            detail="Active subscription required"
        )

    # User has active subscription - continue with your logic
    return {
        "message": "Access granted!",
        "data": "Your protected data here"
    }


@app.get("/api/premium-feature")
async def premium_feature(request: Request) -> dict:
    """Example: Gate a feature behind a specific entitlement."""
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check if user has access to this specific feature
    has_access = await is_feature_entitled(
        feature="premium_feature",
        user_id=user_id
    )

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "This feature requires a premium subscription",
                "upgrade_url": "/pricing"
            }
        )

    # User has access - return premium data
    return {
        "premium_data": "Advanced analytics, reports, etc."
    }


@app.post("/api/track-usage")
async def track_usage(request: Request) -> dict:
    """Example: Track usage when user performs an action."""
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Track this API call
    await send_event(
        name="api_call",
        value=1,
        user_id=user_id
    )

    # Your API logic here
    return {"message": "Action completed"}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Run the app
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("FastAPI app running with Lumen integration")
    print("="*70)
    print("\nEndpoints:")
    print("  • Backend Proxy:  http://localhost:8000/api/lumen/*")
    print("  • Protected:      http://localhost:8000/api/protected")
    print("  • Premium:        http://localhost:8000/api/premium-feature")
    print("  • Track Usage:    http://localhost:8000/api/track-usage")
    print("  • API Docs:       http://localhost:8000/docs")
    print("\nTest with:")
    print('  curl -H "X-User-ID: user_123" http://localhost:8000/api/lumen/customers/subscription-status')
    print("="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
