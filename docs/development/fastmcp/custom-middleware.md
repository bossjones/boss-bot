# Custom Middleware

Guide to implementing custom middleware patterns in FastMCP servers, including authentication middleware, custom routes, and request/response processing.

## Overview

FastMCP provides authentication middleware out of the box and supports custom HTTP endpoints through custom routes. While there's no direct API for adding arbitrary ASGI middleware, this guide covers available patterns for customizing request/response processing.

## Authentication Middleware (Built-in)

FastMCP includes sophisticated authentication middleware for OAuth2 flows.

### Basic Auth Setup

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.auth import OAuthAuthorizationServerProvider
from mcp.server.auth.middleware import get_access_token

# Create auth provider
auth_provider = OAuthAuthorizationServerProvider(
    provider_id="github",
    client_id="your-github-client-id",
    client_secret="your-github-client-secret",
    authorization_endpoint="https://github.com/login/oauth/authorize",
    token_endpoint="https://github.com/login/oauth/access_token",
    scopes=["user:email", "repo"],
)

# Create server with authentication
mcp = FastMCP(
    "authenticated-server",
    auth_server_provider=auth_provider
)

@mcp.tool()
async def protected_tool() -> str:
    """Tool that requires authentication."""
    # Access authenticated user context
    access_token = get_access_token()
    if not access_token:
        raise ValueError("Authentication required")

    return f"Hello, authenticated user! Token: {access_token.token}"
```

### Custom Auth Provider

```python
from mcp.server.auth import AuthorizationServerProvider
from mcp.server.auth.handlers import AuthorizeRequest, TokenRequest

class CustomAuthProvider(AuthorizationServerProvider):
    """Custom authentication provider."""

    def __init__(self, api_key_header: str = "X-API-Key"):
        super().__init__(provider_id="custom-api-key")
        self.api_key_header = api_key_header
        self.valid_keys = {"secret-key-1", "secret-key-2"}

    async def authorize(self, request: AuthorizeRequest) -> str:
        """Handle authorization request."""
        # For API key auth, return a simple authorization code
        return "auth-code-12345"

    async def token(self, request: TokenRequest) -> dict:
        """Handle token exchange."""
        # Validate authorization code and return token
        if request.code == "auth-code-12345":
            return {
                "access_token": "api-key-token",
                "token_type": "bearer",
                "scope": "read write"
            }
        raise ValueError("Invalid authorization code")

    async def validate_token(self, token: str) -> dict | None:
        """Validate access token."""
        if token in self.valid_keys:
            return {
                "token": token,
                "scopes": ["read", "write"],
                "user_id": f"user-{hash(token) % 1000}"
            }
        return None

# Use custom auth provider
mcp = FastMCP(
    "api-key-server",
    auth_server_provider=CustomAuthProvider()
)
```

## Custom Routes for HTTP Endpoints

Use custom routes to add arbitrary HTTP endpoints with full request/response control.

### Basic Custom Routes

```python
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
import time

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "server": "fastmcp-server"
    })

@mcp.custom_route("/stats", methods=["GET"])
async def server_stats(request: Request) -> JSONResponse:
    """Server statistics endpoint."""
    return JSONResponse({
        "tools_count": len(mcp._tool_manager.tools),
        "resources_count": len(mcp._resource_manager.resources),
        "prompts_count": len(mcp._prompt_manager.prompts),
        "uptime_seconds": time.time() - start_time
    })

@mcp.custom_route("/webhook", methods=["POST"])
async def webhook_handler(request: Request) -> JSONResponse:
    """Webhook endpoint for external integrations."""
    body = await request.json()

    # Process webhook data
    event_type = body.get("type")
    if event_type == "user_update":
        await handle_user_update(body["data"])
    elif event_type == "system_notification":
        await handle_system_notification(body["data"])

    return JSONResponse({"status": "processed"})
```

### Custom Routes with Authentication

```python
from mcp.server.auth.middleware import get_access_token
from starlette.exceptions import HTTPException

@mcp.custom_route("/protected-data", methods=["GET"])
async def protected_data(request: Request) -> JSONResponse:
    """Protected endpoint requiring authentication."""
    # Check authentication in custom route
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify required scopes
    if "read" not in access_token.scopes:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return JSONResponse({
        "user_id": access_token.user_id,
        "data": "sensitive information",
        "scopes": access_token.scopes
    })

@mcp.custom_route("/admin", methods=["GET", "POST"])
async def admin_panel(request: Request) -> JSONResponse:
    """Admin endpoint with scope checking."""
    access_token = get_access_token()
    if not access_token or "admin" not in access_token.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")

    if request.method == "GET":
        return JSONResponse({"admin_data": "admin interface"})

    # Handle admin actions
    body = await request.json()
    action = body.get("action")

    if action == "refresh_tools":
        # Refresh tool registration
        mcp._tool_manager.refresh()
        return JSONResponse({"status": "tools refreshed"})

    return JSONResponse({"status": "unknown action"})
```

## Request/Response Processing Patterns

While FastMCP doesn't provide direct middleware hooks, you can implement processing patterns using custom routes and context managers.

### Request Logging Pattern

```python
import logging
import time
from contextlib import asynccontextmanager
from starlette.responses import Response

logger = logging.getLogger(__name__)

@asynccontextmanager
async def request_logger(request: Request):
    """Context manager for request logging."""
    start_time = time.time()
    request_id = f"req-{int(start_time * 1000)}"

    # Log request start
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        yield request_id
    finally:
        # Log request completion
        duration = time.time() - start_time
        logger.info(f"[{request_id}] Completed in {duration:.3f}s")

@mcp.custom_route("/api/data", methods=["GET", "POST"])
async def data_endpoint(request: Request) -> JSONResponse:
    """Endpoint with request logging."""
    async with request_logger(request) as request_id:
        # Process request
        if request.method == "GET":
            data = await fetch_data()
        else:
            body = await request.json()
            data = await process_data(body)

        logger.info(f"[{request_id}] Processed {len(data)} items")
        return JSONResponse({"data": data, "request_id": request_id})
```

### Rate Limiting Pattern

```python
import asyncio
from collections import defaultdict
from starlette.exceptions import HTTPException

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        # Check current count
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Record this request
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter(max_requests=50, window_seconds=60)

@mcp.custom_route("/api/limited", methods=["GET"])
async def rate_limited_endpoint(request: Request) -> JSONResponse:
    """Endpoint with rate limiting."""
    # Use IP address as identifier
    client_ip = request.client.host if request.client else "unknown"

    if not await rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

    return JSONResponse({"message": "Request processed", "ip": client_ip})
```

### Response Caching Pattern

```python
import json
import hashlib
from typing import Any

class ResponseCache:
    """Simple in-memory response cache."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache = {}

    def _cache_key(self, request: Request) -> str:
        """Generate cache key from request."""
        key_data = f"{request.method}:{request.url.path}:{request.url.query}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get(self, request: Request) -> JSONResponse | None:
        """Get cached response if available."""
        cache_key = self._cache_key(request)

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl_seconds:
                return JSONResponse(cached_data)
            else:
                # Expired, remove from cache
                del self.cache[cache_key]

        return None

    async def set(self, request: Request, data: Any) -> None:
        """Cache response data."""
        cache_key = self._cache_key(request)
        self.cache[cache_key] = (data, time.time())

response_cache = ResponseCache(ttl_seconds=300)

@mcp.custom_route("/api/cached", methods=["GET"])
async def cached_endpoint(request: Request) -> JSONResponse:
    """Endpoint with response caching."""
    # Check cache first
    cached_response = await response_cache.get(request)
    if cached_response:
        # Add cache hit header
        cached_response.headers["X-Cache"] = "HIT"
        return cached_response

    # Generate fresh response
    data = await expensive_computation()

    # Cache the response
    await response_cache.set(request, data)

    response = JSONResponse(data)
    response.headers["X-Cache"] = "MISS"
    return response
```

## Context Injection in Tools

Access HTTP request context within MCP tools when using HTTP transports.

### Request Context Access

```python
from mcp.server.fastmcp import Context
from starlette.requests import Request

@mcp.tool()
async def request_aware_tool(message: str, ctx: Context) -> str:
    """Tool that accesses HTTP request context."""
    # Get request information if available
    request_info = {}

    # Access session information
    if hasattr(ctx.session, 'request_context'):
        request_context = ctx.session.request_context
        request_info.update({
            "session_id": getattr(request_context, 'session_id', 'unknown'),
            "user_agent": getattr(request_context, 'user_agent', 'unknown'),
            "remote_addr": getattr(request_context, 'remote_addr', 'unknown')
        })

    # Access authentication context
    access_token = get_access_token()
    if access_token:
        request_info["authenticated_user"] = access_token.user_id
        request_info["scopes"] = access_token.scopes

    await ctx.info(f"Processing request with context: {request_info}")

    return f"Processed '{message}' with context: {request_info}"
```

## Advanced Patterns

### Custom Session Management

```python
from mcp.server.streamable_http_manager import SessionManager
from contextlib import asynccontextmanager

class CustomSessionManager(SessionManager):
    """Custom session manager with additional middleware."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_metadata = {}

    @asynccontextmanager
    async def handle_request(self, session_id: str, request_data: dict):
        """Override request handling with custom logic."""
        # Pre-request processing
        start_time = time.time()
        self.session_metadata[session_id] = {
            "start_time": start_time,
            "request_count": self.session_metadata.get(session_id, {}).get("request_count", 0) + 1
        }

        try:
            # Call parent implementation
            async with super().handle_request(session_id, request_data) as result:
                yield result
        finally:
            # Post-request processing
            duration = time.time() - start_time
            metadata = self.session_metadata.get(session_id, {})
            metadata["last_duration"] = duration

            logger.info(f"Session {session_id}: request #{metadata['request_count']} took {duration:.3f}s")

# Use custom session manager (advanced - requires FastMCP extension)
# mcp = FastMCP("custom-server", session_manager_class=CustomSessionManager)
```

### Middleware-like Decorators

```python
from functools import wraps
from typing import Callable, Any

def with_timing(func: Callable) -> Callable:
    """Decorator to add timing to custom routes."""
    @wraps(func)
    async def wrapper(request: Request) -> Any:
        start_time = time.time()
        try:
            result = await func(request)
            return result
        finally:
            duration = time.time() - start_time
            logger.info(f"{func.__name__} took {duration:.3f}s")
    return wrapper

def with_auth_required(scopes: list[str] = None):
    """Decorator to require authentication on custom routes."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request) -> Any:
            access_token = get_access_token()
            if not access_token:
                raise HTTPException(status_code=401, detail="Authentication required")

            if scopes:
                if not all(scope in access_token.scopes for scope in scopes):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(request)
        return wrapper
    return decorator

# Usage with decorators
@mcp.custom_route("/admin/users", methods=["GET"])
@with_timing
@with_auth_required(scopes=["admin", "read"])
async def list_users(request: Request) -> JSONResponse:
    """Protected admin endpoint with timing."""
    users = await fetch_all_users()
    return JSONResponse({"users": users})
```

## Best Practices

### Security Considerations

1. **Always validate authentication** in protected endpoints
2. **Check scopes** for fine-grained access control
3. **Sanitize input** from custom routes
4. **Use HTTPS** in production for authentication flows
5. **Implement rate limiting** for public endpoints
6. **Log security events** (auth failures, rate limit hits)

### Performance Optimization

1. **Cache expensive operations** in custom routes
2. **Use async patterns** for I/O operations
3. **Implement connection pooling** for external services
4. **Monitor response times** and set reasonable timeouts
5. **Use streaming** for large response payloads

### Error Handling

```python
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

@mcp.custom_route("/api/robust", methods=["POST"])
async def robust_endpoint(request: Request) -> JSONResponse:
    """Endpoint with comprehensive error handling."""
    try:
        # Validate content type
        if request.headers.get("content-type") != "application/json":
            raise HTTPException(status_code=400, detail="Content-Type must be application/json")

        # Parse and validate body
        try:
            body = await request.json()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

        # Validate required fields
        required_fields = ["action", "data"]
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {missing_fields}"
            )

        # Process request
        result = await process_action(body["action"], body["data"])

        return JSONResponse({
            "status": "success",
            "result": result,
            "timestamp": time.time()
        })

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error in robust_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Limitations

1. **No Direct Middleware API**: Cannot add arbitrary ASGI middleware to the FastMCP server
2. **Authentication Only**: Built-in middleware only supports authentication patterns
3. **Limited Request Context**: HTTP request details not directly available in MCP tools
4. **Transport Specific**: Middleware patterns only apply to HTTP transports (SSE, StreamableHTTP)

## Alternative Approaches

For use cases requiring extensive middleware:

1. **Use Starlette directly** with custom MCP integration
2. **Proxy pattern**: Put a reverse proxy (nginx, Traefik) in front for middleware-like functionality
3. **Custom transport**: Implement a custom transport with desired middleware capabilities
4. **Wrapper pattern**: Wrap FastMCP server in a custom ASGI application

This guide covers the available patterns for implementing middleware-like functionality in FastMCP. While not as flexible as full ASGI middleware, these patterns provide powerful customization capabilities for most use cases.
