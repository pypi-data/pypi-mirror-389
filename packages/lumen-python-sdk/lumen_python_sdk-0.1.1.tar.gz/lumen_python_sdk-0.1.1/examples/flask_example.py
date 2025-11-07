"""
Flask integration example for the Lumen Python SDK.

This example shows how to integrate Lumen with a Flask application,
including both the backend proxy for frontend calls and direct backend usage.
"""

from flask import Flask, request, jsonify, session

from lumen.handlers import lumen_flask_handler
from lumen import get_subscription_status, send_event, is_feature_entitled

app = Flask(__name__)
app.secret_key = "your-secret-key-here"


def get_user_id():
    """
    Extract user ID from the request.

    In production, this would typically:
    - Check session for logged-in user: session.get("user_id")
    - Decode JWT token from Authorization header
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

@app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def lumen_proxy(path):
    """
    Proxy requests to Lumen API.

    Frontend usage:
        fetch('/api/lumen/customers/subscription-status')
          .then(r => r.json())
          .then(data => console.log(data))
    """
    handler = lumen_flask_handler(get_user_id=get_user_id)
    return handler(path)


# ============================================================================
# Direct Backend SDK Usage Examples
# ============================================================================
# Use these patterns in your backend API routes
# ============================================================================

@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({
        "message": "Lumen Flask Example",
        "endpoints": {
            "proxy": "/api/lumen/*",
            "protected": "/api/protected",
            "premium": "/api/premium-feature",
            "action": "/api/track-usage"
        }
    })


@app.route("/api/protected")
async def protected_endpoint():
    """Example: Protect a route with subscription check."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if user has active subscription
    status = await get_subscription_status(user_id=user_id)

    if "error" in status:
        return jsonify(status), 400

    if not status.get("hasActiveSubscription"):
        return jsonify({"error": "Active subscription required"}), 402

    # User has active subscription - continue with your logic
    return jsonify({
        "message": "Access granted!",
        "data": "Your protected data here"
    })


@app.route("/api/premium-feature")
async def premium_feature():
    """Example: Gate a feature behind a specific entitlement."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if user has access to this specific feature
    has_access = await is_feature_entitled(
        feature="premium_feature",
        user_id=user_id
    )

    if not has_access:
        return jsonify({
            "error": "This feature requires a premium subscription",
            "upgrade_url": "/pricing"
        }), 403

    # User has access - return premium data
    return jsonify({
        "premium_data": "Advanced analytics, reports, etc."
    })


@app.route("/api/track-usage")
async def track_usage():
    """Example: Track usage when user performs an action."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Track this API call
    await send_event(
        name="api_call",
        value=1,
        user_id=user_id
    )

    # Your API logic here
    result = {"message": "Action completed"}

    return jsonify(result)


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


# ============================================================================
# Run the app
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Flask app running with Lumen integration")
    print("="*70)
    print("\nEndpoints:")
    print("  • Backend Proxy:  http://localhost:5000/api/lumen/*")
    print("  • Protected:      http://localhost:5000/api/protected")
    print("  • Premium:        http://localhost:5000/api/premium-feature")
    print("  • Track Usage:    http://localhost:5000/api/track-usage")
    print("\nTest with:")
    print('  curl -H "X-User-ID: user_123" http://localhost:5000/api/lumen/customers/subscription-status')
    print("="*70 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
