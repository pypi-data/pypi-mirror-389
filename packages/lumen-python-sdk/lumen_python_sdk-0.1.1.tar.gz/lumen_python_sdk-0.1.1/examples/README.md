# Lumen Python SDK Examples

This directory contains examples demonstrating how to use the Lumen Python SDK in various scenarios.

## Prerequisites

1. Install the SDK:

```bash
pip install lumen-python-sdk
```

2. Set your API key:

```bash
export LUMEN_API_KEY="your_api_key_here"
```

Get your API key from [https://getlumen.dev/developer/apikeys](https://getlumen.dev/developer/apikeys)

## Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates core SDK functionality:

- Checking subscription status
- Tracking events
- Checking feature entitlements
- Managing seats

Run:

```bash
python basic_usage.py
```

### 2. FastAPI Integration (`fastapi_example.py`)

Shows how to integrate Lumen with FastAPI for secure API proxying.

Install dependencies:

```bash
pip install lumen-python-sdk[fastapi] uvicorn
```

Run:

```bash
python fastapi_example.py
```

Then test with:

```bash
curl -H "X-User-ID: user_123" http://localhost:8000/api/lumen/customers/subscription-status
```

### 3. Flask Integration (`flask_example.py`)

Shows how to integrate Lumen with Flask for secure API proxying.

Install dependencies:

```bash
pip install lumen-python-sdk[flask]
```

Run:

```bash
python flask_example.py
```

Then test with:

```bash
curl -H "X-User-ID: user_123" http://localhost:5000/api/lumen/customers/subscription-status
```

## Framework Integration Patterns

All framework examples follow the same pattern:

1. **Define a `get_user_id` function** that extracts the user ID from the request
2. **Create a handler** using the framework-specific Lumen handler
3. **Mount the handler** at a route (typically `/api/lumen/`)

This provides a secure way to access Lumen APIs from your frontend without exposing your API key.

## Production Considerations

When deploying to production:

1. **Never hardcode API keys** - use environment variables
2. **Implement proper authentication** - validate JWT tokens, sessions, etc.
3. **Add rate limiting** - protect your API endpoints
4. **Enable HTTPS** - always use secure connections
5. **Monitor errors** - log and track API failures
6. **Handle errors gracefully** - provide meaningful error messages to users

## Need Help?

- 📖 [Full Documentation](https://getlumen.dev/docs)
- 💬 [Discord Community](https://discord.gg/lumen)
- 📧 Email: hello@getlumen.dev
