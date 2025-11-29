# Rate Limiting Implementation

## Overview

Rate limiting has been implemented using `slowapi` (version 0.1.9) to provide basic protection against abuse while maintaining generous limits for local development.

## Configuration

### Rate Limits by Endpoint Type

| Endpoint Type | Limit | Endpoints |
|--------------|-------|-----------|
| **Authentication** | | |
| Login | 10/minute | `/api/v1/auth/login` |
| Register | 5/minute | `/api/v1/auth/register` |
| Token Refresh | 20/minute | `/api/v1/auth/refresh` |
| **Import Operations** | | |
| Preview | 10/minute | `/api/v1/import/*/preview` |
| Execute | 5/minute | `/api/v1/import/*/execute`, `/api/v1/import/*/sync` |
| **General API** | | |
| CRUD Read | 200/minute | GET requests |
| CRUD Write | 100/minute | POST/PUT/DELETE requests |
| **System** | | |
| Health Checks | 1000/minute | `/health`, `/ready` |
| Root | 200/minute | `/` |

## Files Modified

1. **backend/requirements.txt**
   - Added `slowapi==0.1.9`

2. **backend/app/core/rate_limit.py** (NEW)
   - Core rate limiting configuration
   - Custom error handler
   - Rate limit constants

3. **backend/app/main.py**
   - Integrated rate limiter
   - Added exception handler for rate limit errors
   - Applied limits to root and health endpoints

4. **backend/app/api/v1/auth.py**
   - Added rate limiting to login, register, and refresh endpoints
   - Updated function signatures to include Request parameter

5. **backend/app/api/v1/imports.py**
   - Added rate limiting to all import endpoints
   - Different limits for preview vs execute operations

## Response Headers

When rate limiting is active, the following headers are included in responses:

- `X-RateLimit-Limit` - Maximum requests allowed
- `X-RateLimit-Remaining` - Requests remaining
- `X-RateLimit-Reset` - Time when limit resets
- `Retry-After` - Seconds to wait (only on 429 errors)

## Error Response

When rate limit is exceeded, the API returns:

```json
{
    "detail": "Rate limit exceeded",
    "message": "Too many requests. Limit: 10 per 1 minute",
    "retry_after": 60
}
```

HTTP Status: `429 Too Many Requests`

## Testing

After rebuilding the backend container:

```bash
# Rebuild to install slowapi
docker compose up -d --build backend

# Test rate limiting on login endpoint
for i in {1..15}; do
    curl -X POST http://localhost:8010/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test"}' \
        -w "\n%{http_code}\n"
done
```

You should see `429` status codes after the 10th request within a minute.

## Key Features

1. **In-memory storage** - Uses local memory for rate limit tracking (suitable for development)
2. **IP-based limiting** - Tracks requests by IP address
3. **Generous limits** - Designed not to interfere with normal development
4. **Selective application** - Only critical endpoints have strict limits

## Future Enhancements

For production deployment, consider:

1. **Redis backend** - Replace in-memory storage with Redis for distributed systems
2. **User-based limiting** - Track by user ID instead of IP for authenticated endpoints
3. **Dynamic limits** - Different limits for different user roles
4. **Sliding window** - More accurate rate limiting algorithm

## Monitoring

To monitor rate limit effectiveness:

```python
# Check rate limit status in logs
import logging
logging.getLogger("slowapi").setLevel(logging.DEBUG)
```

Rate limit violations are logged and can be tracked for analysis.