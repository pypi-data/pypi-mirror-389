"""Framework-specific handlers for integrating Lumen with popular Python web frameworks."""

try:
    from .flask_handler import lumen_flask_handler
except ImportError:
    lumen_flask_handler = None  # type: ignore

try:
    from .fastapi_handler import lumen_fastapi_handler
except ImportError:
    lumen_fastapi_handler = None  # type: ignore

try:
    from .django_handler import lumen_django_handler
except ImportError:
    lumen_django_handler = None  # type: ignore

__all__ = ["lumen_flask_handler", "lumen_fastapi_handler", "lumen_django_handler"]

