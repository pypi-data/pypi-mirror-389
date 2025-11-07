# Flask Setup Guide

Complete guide to integrating Lumen with your Flask backend.

## Installation

```bash
pip install lumen-python-sdk[flask]
```

## Environment Setup

### Step 1: Get Your API Key

Visit [https://getlumen.dev/developer/apikeys](https://getlumen.dev/developer/apikeys) and create a secret API key.

### Step 2: Set Environment Variable

The SDK reads your API key from the `LUMEN_API_KEY` environment variable.

#### Option A: Using .env file (Recommended)

Create a `.env` file in your project root:

```bash
# .env
LUMEN_API_KEY=lumen_sk_your_secret_key_here
```

Load it in your Flask app:

```python
from dotenv import load_dotenv
load_dotenv()  # Call this before creating your Flask app

from flask import Flask
app = Flask(__name__)
```

#### Option B: Export in shell

```bash
export LUMEN_API_KEY=lumen_sk_your_secret_key_here
python app.py
```

#### Option C: Set in production environment

For production (Heroku, AWS, etc.):

```bash
# Heroku
heroku config:set LUMEN_API_KEY=lumen_sk_your_secret_key_here

# AWS Elastic Beanstalk
eb setenv LUMEN_API_KEY=lumen_sk_your_secret_key_here

# Docker
docker run -e LUMEN_API_KEY=lumen_sk_your_secret_key_here ...
```

#### Option D: Pass directly to functions

```python
from lumen import get_subscription_status

status = await get_subscription_status(
    user_id="user_123",
    api_key="lumen_sk_your_secret_key_here"  # Not recommended for production
)
```

## Backend Proxy Setup

The backend proxy lets your frontend securely access Lumen without exposing your API key.

**Flow:** `Frontend → Your Backend (/api/lumen/*) → Lumen API`

### Complete Flask App Example

```python
from flask import Flask, request, session
from lumen.handlers import lumen_flask_handler

app = Flask(__name__)
app.secret_key = "your-secret-key"

def get_user_id():
    """
    Extract the current user's ID from your auth system.

    Choose the method that matches your auth setup:
    """
    # Option 1: From Flask session
    return session.get("user_id")

    # Option 2: From JWT in Authorization header
    # token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # return decoded["user_id"]

    # Option 3: From custom header (for testing)
    # return request.headers.get("X-User-ID")

    # Option 4: From Flask-Login
    # from flask_login import current_user
    # return current_user.id if current_user.is_authenticated else None

# Backend Proxy Route
@app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def lumen_proxy(path):
    handler = lumen_flask_handler(get_user_id=get_user_id)
    return handler(path)

if __name__ == "__main__":
    app.run()
```

### What the Proxy Does

1. **Extracts user ID** from your auth system (session, JWT, etc.)
2. **Validates** the user is authenticated
3. **Forwards** the request to Lumen with the user ID injected
4. **Returns** the Lumen response to your frontend

### Frontend Usage

Now your frontend can call your backend proxy:

```javascript
// Check subscription status
const response = await fetch("/api/lumen/customers/subscription-status");
const status = await response.json();

if (status.hasActiveSubscription) {
  console.log("User has active subscription");
}

// Get feature entitlements
const features = await fetch("/api/lumen/entitlements/user_123");
const entitlements = await features.json();
```

## Direct Backend SDK Usage

Use the SDK directly in your Flask routes for server-side operations:

### Protect Routes with Subscription Checks

```python
from lumen import get_subscription_status

@app.route("/api/protected-data")
async def protected_data():
    user_id = session.get("user_id")

    status = await get_subscription_status(user_id=user_id)

    if not status.get("hasActiveSubscription"):
        return {"error": "Subscription required"}, 402

    # Return protected data
    return {"data": "..."}
```

### Gate Features

```python
from lumen import is_feature_entitled

@app.route("/api/premium-feature")
async def premium_feature():
    user_id = session.get("user_id")

    has_access = await is_feature_entitled(
        feature="premium_feature",
        user_id=user_id
    )

    if not has_access:
        return {"error": "Upgrade required"}, 403

    return {"premium_data": "..."}
```

### Track Usage

```python
from lumen import send_event

@app.route("/api/action")
async def action():
    user_id = session.get("user_id")

    # Track the API call
    await send_event(name="api_call", value=1, user_id=user_id)

    return {"result": "..."}
```

### Enroll New Users

```python
from lumen import enroll_user

@app.route("/auth/signup", methods=["POST"])
async def signup():
    data = request.get_json()

    # Your signup logic...
    user = create_user(data)

    # Enroll in Lumen (creates free subscription)
    await enroll_user(
        email=user.email,
        name=user.name,
        user_id=str(user.id)
    )

    return {"success": True}
```

## Common Auth Patterns

### Using Flask-Login

```python
from flask_login import LoginManager, current_user, login_required

login_manager = LoginManager()
login_manager.init_app(app)

def get_user_id():
    return str(current_user.id) if current_user.is_authenticated else None

@app.route("/api/lumen/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def lumen_proxy(path):
    handler = lumen_flask_handler(get_user_id=get_user_id)
    return handler(path)
```

### Using JWT Tokens

```python
import jwt

def get_user_id():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["user_id"]
    except:
        return None
```

### Using Flask Session

```python
def get_user_id():
    return session.get("user_id")

@app.route("/login", methods=["POST"])
def login():
    # Your login logic...
    session["user_id"] = str(user.id)
    return {"success": True}
```

## Error Handling

```python
from lumen import get_subscription_status

@app.route("/api/check-subscription")
async def check_subscription():
    user_id = session.get("user_id")

    if not user_id:
        return {"error": "Not authenticated"}, 401

    result = await get_subscription_status(user_id=user_id)

    # Check for API errors
    if "error" in result:
        app.logger.error(f"Lumen API error: {result['error']}")
        return {"error": "Failed to check subscription"}, 500

    return result
```

## Production Checklist

- ✅ Set `LUMEN_API_KEY` environment variable
- ✅ Never commit API keys to git
- ✅ Use `.env` file for local development
- ✅ Set env vars in production platform (Heroku, AWS, etc.)
- ✅ Implement proper user authentication
- ✅ Add error handling for API calls
- ✅ Test the proxy route works from frontend
- ✅ Enable HTTPS in production

## Testing

Test your setup:

```bash
# Test direct API call
curl -X GET http://localhost:5000/api/protected-data

# Test proxy route (with auth)
curl -H "X-User-ID: user_123" \
  http://localhost:5000/api/lumen/customers/subscription-status
```

## Troubleshooting

### "LUMEN_API_KEY is not set"

- Check `.env` file exists and is loaded with `python-dotenv`
- Verify environment variable: `echo $LUMEN_API_KEY`
- Try setting it explicitly: `export LUMEN_API_KEY=your_key`

### "Unauthorized" errors from proxy

- Verify `get_user_id()` returns the correct user ID
- Check your auth system is working
- Add debug print: `print(f"User ID: {get_user_id()}")`

### API calls timing out

- Check your network/firewall allows HTTPS to api.getlumen.dev
- Verify API key is valid at https://getlumen.dev/developer/apikeys

## Support

- **Docs**: [https://getlumen.dev/docs](https://getlumen.dev/docs)
- **Email**: hello@getlumen.dev
- **Discord**: [https://discord.gg/lumen](https://discord.gg/lumen)
