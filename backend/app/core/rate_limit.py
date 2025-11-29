"""
Rate Limiting Configuration for UNS-Kobetsu API
ローカル開発用のレート制限設定

Uses slowapi for basic rate limiting protection.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

# Create limiter instance
# key_func determines what to use as the identifier (IP address in this case)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],  # Global default: 100 requests per minute
    storage_uri=None,  # Using in-memory storage for local development
    headers_enabled=True,  # Enable rate limit headers in responses
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns a JSON response with rate limit information.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', 60)
        }
    )

    # Add rate limit headers
    retry_after = getattr(exc, 'retry_after', 60)
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(exc.limit)

    return response


def add_rate_limit_headers(response: Response, request: Request):
    """
    Add rate limit headers to successful responses.
    This helps clients track their rate limit status.
    """
    # Get rate limit info from request state (set by slowapi)
    if hasattr(request.state, 'view_rate_limit'):
        limit_info = request.state.view_rate_limit

        # Add standard rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_info.get('limit', ''))
        response.headers["X-RateLimit-Remaining"] = str(limit_info.get('remaining', ''))
        response.headers["X-RateLimit-Reset"] = str(limit_info.get('reset', ''))

    return response


# Rate limit configurations for different endpoint groups
class RateLimits:
    """
    Centralized rate limit configurations for different endpoint types.
    Using generous limits for local development.
    """
    # Authentication endpoints - more restrictive
    AUTH_LOGIN = "10 per minute"  # Login attempts
    AUTH_REGISTER = "5 per minute"  # Registration attempts
    AUTH_REFRESH = "20 per minute"  # Token refresh

    # Import/Export operations - resource intensive
    IMPORT_PREVIEW = "10 per minute"  # Preview import data
    IMPORT_EXECUTE = "5 per minute"  # Execute import
    EXPORT_DOCUMENT = "10 per minute"  # Generate PDFs/documents

    # General CRUD operations - standard limits
    CRUD_READ = "200 per minute"  # GET requests
    CRUD_WRITE = "100 per minute"  # POST/PUT/DELETE

    # Search and filtering - allow more requests
    SEARCH = "150 per minute"

    # File uploads
    FILE_UPLOAD = "20 per minute"

    # Health checks - very permissive
    HEALTH_CHECK = "1000 per minute"


def get_rate_limit_string(endpoint_type: str = "default") -> str:
    """
    Get rate limit string for a specific endpoint type.

    Args:
        endpoint_type: Type of endpoint (auth, import, crud, etc.)

    Returns:
        Rate limit string (e.g., "10 per minute")
    """
    rate_map = {
        "auth_login": RateLimits.AUTH_LOGIN,
        "auth_register": RateLimits.AUTH_REGISTER,
        "auth_refresh": RateLimits.AUTH_REFRESH,
        "import_preview": RateLimits.IMPORT_PREVIEW,
        "import_execute": RateLimits.IMPORT_EXECUTE,
        "export": RateLimits.EXPORT_DOCUMENT,
        "crud_read": RateLimits.CRUD_READ,
        "crud_write": RateLimits.CRUD_WRITE,
        "search": RateLimits.SEARCH,
        "file_upload": RateLimits.FILE_UPLOAD,
        "health": RateLimits.HEALTH_CHECK,
    }

    return rate_map.get(endpoint_type, "100 per minute")


# Decorator shortcuts for common rate limits
def auth_rate_limit(limit: str = RateLimits.AUTH_LOGIN):
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(limit)


def import_rate_limit(limit: str = RateLimits.IMPORT_EXECUTE):
    """Rate limit decorator for import endpoints."""
    return limiter.limit(limit)


def crud_rate_limit(method: str = "read"):
    """Rate limit decorator for CRUD operations."""
    limit = RateLimits.CRUD_READ if method == "read" else RateLimits.CRUD_WRITE
    return limiter.limit(limit)