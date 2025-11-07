# Lumen Python SDK

Official Python SDK for [Lumen](https://getlumen.dev) - Payments and Billing Infrastructure for modern SaaS applications.

[![PyPI version](https://badge.fury.io/py/lumen-python-sdk.svg)](https://badge.fury.io/py/lumen-python-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
# Core SDK
pip install lumen-python-sdk

# With Flask
pip install lumen-python-sdk[flask]

# With FastAPI
pip install lumen-python-sdk[fastapi]

# With Django
pip install lumen-python-sdk[django]
```

## Quick Setup

### 1. Get Your API Key

Get your secret API key from [https://getlumen.dev/developer/apikeys](https://getlumen.dev/developer/apikeys)

### 2. Set Environment Variable

Add to your `.env` file or environment:

```bash
LUMEN_API_KEY=lumen_sk_...
```

The SDK automatically reads from this environment variable. You can also pass `api_key` directly to any function if needed.

### 3. Set Up Backend Proxy (Required for Frontend Access)

Lumen requires a backend proxy route to securely check entitlements and usage from your frontend. This prevents exposing your API key to the browser.

**Flow:** `Frontend → Your Backend → Lumen API`

#### Flask

```python
from flask import Flask, request
from lumen.handlers import lumen_flask_handler

app = Flask(__name__)

def get_user_id():
    # Extract user ID from your auth system
    # Examples: session, JWT token, request context, etc.
    return request.headers.get("X-User-ID")  # or session.get("user_id")

@app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def lumen_proxy(path):
    handler = lumen_flask_handler(get_user_id=get_user_id)
    return handler(path)
```

#### FastAPI

```python
from fastapi import FastAPI, Request
from lumen.handlers import lumen_fastapi_handler

app = FastAPI()

def get_user_id(request: Request):
    # Extract user ID from your auth system
    return request.state.user_id  # or decode JWT, check session, etc.

handler = lumen_fastapi_handler(get_user_id=get_user_id)

@app.api_route("/api/lumen/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def lumen_proxy(request: Request, path: str):
    return await handler(request, path)
```

#### Django

```python
# views.py
from lumen.handlers import lumen_django_handler

def get_user_id(request):
    return str(request.user.id) if request.user.is_authenticated else None

lumen_view = lumen_django_handler(get_user_id=get_user_id)

# urls.py
from django.urls import path

urlpatterns = [
    path('api/lumen/<path:path>', lumen_view),
]
```

Now your frontend can call `/api/lumen/customers/subscription-status` and it will be securely proxied to Lumen with the user's ID.

## Server-Side SDK Usage

### Direct Backend Calls

Use these functions in your backend API routes, background jobs, or webhooks:

```python
from lumen import get_subscription_status, send_event, is_feature_entitled

# In your API route handler
async def my_api_endpoint(user_id: str):
    # Check if user has active subscription
    status = await get_subscription_status(user_id=user_id)
    if not status.get("hasActiveSubscription"):
        return {"error": "No active subscription"}

    # Track usage
    await send_event(name="api_call", value=1, user_id=user_id)

    # Check feature access
    has_premium = await is_feature_entitled(
        feature="premium_feature",
        user_id=user_id
    )

    if has_premium:
        # Allow access to premium features
        return {"data": "premium_data"}
    else:
        return {"error": "Upgrade required"}
```

## API Reference

### Customer Management

```python
from lumen import get_subscription_status, get_customer_overview

# Check if user has active subscription
status = await get_subscription_status(user_id="user_123")
# Returns: {"hasActiveSubscription": True, "customer": {...}}

# Get detailed customer information
overview = await get_customer_overview(user_id="user_123")
```

### Feature Entitlements

```python
from lumen import get_usage, get_features, is_feature_entitled

# Get detailed usage data
usage = await get_usage(user_id="user_123")
# Returns: {"entitlements": [{"feature": {...}, "usage": 150, "limit": 1000}]}

# Get simple feature flags
features = await get_features(user_id="user_123")
# Returns: {"api_calls": True, "premium_feature": False}

# Check single feature
has_access = await is_feature_entitled(feature="premium_feature", user_id="user_123")
# Returns: True or False
```

### Event Tracking

```python
from lumen import send_event

# Track usage (call this in your API endpoints)
await send_event(name="api_call", value=1, user_id="user_123")

# Track with idempotency key (prevents duplicates)
await send_event(
    name="api_call",
    value=1,
    user_id="user_123",
    idempotency_key="unique_key_123"
)
```

### Seat Management

```python
from lumen import add_seat, remove_seat, get_seat_usage

# Add user to organization's subscription
await add_seat(
    new_user_id="new_user_456",
    organisation_user_id="org_owner_123",
    metadata={"role": "developer"}
)

# Remove user from organization
await remove_seat(
    removed_user_id="user_456",
    organisation_user_id="org_owner_123"
)

# Get current seat usage
usage = await get_seat_usage(customer_id="cust_123")
```

### User Enrollment & Subscriptions

```python
from lumen import enroll_user, create_free_subscription_if_none_exists

# Enroll user (call this on user signup)
await enroll_user(
    email="user@example.com",
    name="John Doe",
    user_id="user_123",
    plan_id="plan_free"  # Optional - will use enrollment rules
)

# Create free subscription if none exists
await create_free_subscription_if_none_exists(
    email="user@example.com",
    name="John Doe",
    user_id="user_123"
)
```

## Configuration

### Environment Variables

```bash
# Required
LUMEN_API_KEY=lumen_sk_...

# Optional (defaults to production)
LUMEN_API_URL=https://api.getlumen.dev
```

### Override Per-Call

```python
# Override API key or URL for specific calls
status = await get_subscription_status(
    user_id="user_123",
    api_key="custom_key",
    api_url="https://staging-api.example.com"
)
```

## Error Handling

Most functions return dicts with optional `error` keys:

```python
# Check for errors
result = await get_subscription_status(user_id="user_123")
if "error" in result:
    return {"error": result["error"]}, 400

# Some functions raise exceptions
try:
    await enroll_user(email="user@example.com", name="John Doe", user_id="user_123")
except Exception as e:
    print(f"Failed: {e}")
```

## Common Patterns

### Protecting API Routes

```python
from lumen import get_subscription_status

async def protected_endpoint(user_id: str):
    status = await get_subscription_status(user_id=user_id)

    if not status.get("hasActiveSubscription"):
        return {"error": "Subscription required"}, 402

    # Continue with endpoint logic
    return {"data": "..."}
```

### Feature Gating

```python
from lumen import is_feature_entitled

async def premium_feature_endpoint(user_id: str):
    if not await is_feature_entitled(feature="premium_feature", user_id=user_id):
        return {"error": "Upgrade required"}, 403

    # Premium feature logic
    return {"data": "premium_data"}
```

### Usage Tracking

```python
from lumen import send_event

async def api_endpoint(user_id: str):
    # Track usage before processing
    await send_event(name="api_call", value=1, user_id=user_id)

    # Your API logic
    return {"result": "..."}
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=lumen --cov-report=html
```

### Code Quality

```bash
# Format code
black lumen tests

# Lint code
ruff check lumen tests

# Type checking
mypy lumen
```

## Examples

Check out the [examples directory](./examples) for complete working examples:

- Basic usage examples
- Framework integration examples
- Error handling patterns
- Production deployment examples

## Support

- 📖 [Documentation](https://getlumen.dev/docs)
- 💬 [Discord Community](https://discord.gg/lumen)
- 🐛 [Issue Tracker](https://github.com/getlumen/lumen-python-sdk/issues)
- 📧 Email: hello@getlumen.dev

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

Built with ❤️ by the Lumen team
