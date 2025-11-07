# Quick Start Guide

Get up and running with Lumen in your Python backend in 5 minutes!

## Step 1: Install

```bash
pip install lumen-python-sdk[flask]  # or [fastapi] or [django]
```

## Step 2: Set API Key

Get your key from [https://getlumen.dev/developer/apikeys](https://getlumen.dev/developer/apikeys)

```bash
# Add to .env
LUMEN_API_KEY=lumen_sk_...
```

## Step 3: Add Backend Proxy Route

This route securely proxies frontend requests to Lumen without exposing your API key.

### Flask Example

```python
from flask import Flask, request
from lumen.handlers import lumen_flask_handler

app = Flask(__name__)

def get_user_id():
    # Get user ID from your auth (session, JWT, etc.)
    return session.get("user_id")  # or decode JWT token

@app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def lumen_proxy(path):
    handler = lumen_flask_handler(get_user_id=get_user_id)
    return handler(path)

if __name__ == "__main__":
    app.run()
```

### FastAPI Example

```python
from fastapi import FastAPI, Request
from lumen.handlers import lumen_fastapi_handler

app = FastAPI()

def get_user_id(request: Request):
    return request.state.user_id  # or decode JWT

handler = lumen_fastapi_handler(get_user_id=get_user_id)

@app.api_route("/api/lumen/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def lumen_proxy(request: Request, path: str):
    return await handler(request, path)
```

## Step 4: Use in Your Backend

### Protect Routes with Subscription Checks

```python
from lumen import get_subscription_status

@app.route("/api/protected-endpoint")
async def protected_endpoint():
    user_id = get_current_user_id()  # Your auth function

    status = await get_subscription_status(user_id=user_id)
    if not status.get("hasActiveSubscription"):
        return {"error": "Subscription required"}, 402

    # Your endpoint logic
    return {"data": "..."}
```

### Gate Features

```python
from lumen import is_feature_entitled

@app.route("/api/premium-feature")
async def premium_feature():
    user_id = get_current_user_id()

    if not await is_feature_entitled(feature="premium_feature", user_id=user_id):
        return {"error": "Upgrade to premium"}, 403

    # Premium feature logic
    return {"premium_data": "..."}
```

### Track Usage

```python
from lumen import send_event

@app.route("/api/action")
async def action():
    user_id = get_current_user_id()

    # Track the usage
    await send_event(name="api_call", value=1, user_id=user_id)

    # Your logic
    return {"result": "..."}
```

## That's It!

Your backend now has:

- ✅ Secure proxy for frontend calls
- ✅ Subscription checking
- ✅ Feature gating
- ✅ Usage tracking

## Frontend Integration

Your frontend can now call your backend proxy:

```javascript
// Frontend code
const response = await fetch("/api/lumen/customers/subscription-status");
const status = await response.json();
console.log(status.hasActiveSubscription);
```

## Next Steps

- 📖 Read the [full documentation](README.md)
- 🔍 Check out [complete examples](examples/)
- 📚 Visit [https://getlumen.dev/docs](https://getlumen.dev/docs)

## Common Patterns

### Get User's Features

```python
from lumen import get_features

features = await get_features(user_id="user_123")
# Returns: {"api_calls": True, "premium_feature": False}

if features.get("advanced_analytics"):
    # Show analytics UI
    pass
```

### Add User to Team Subscription

```python
from lumen import add_seat

await add_seat(
    new_user_id="new_member_id",
    organisation_user_id="team_owner_id",
    metadata={"role": "developer"}
)
```

### Enroll New Users

```python
from lumen import enroll_user

# Call this on user signup
await enroll_user(
    email="user@example.com",
    name="John Doe",
    user_id="user_123"
)
```

## Support

- **Docs**: [https://getlumen.dev/docs](https://getlumen.dev/docs)
- **Email**: hello@getlumen.dev
- **Discord**: [https://discord.gg/lumen](https://discord.gg/lumen)
