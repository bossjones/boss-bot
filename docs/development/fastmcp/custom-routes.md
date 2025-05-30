# Custom Routes

Comprehensive guide to creating custom HTTP endpoints in FastMCP servers, enabling rich web APIs, OAuth callbacks, webhooks, and admin interfaces alongside MCP protocol functionality.

## Overview

FastMCP's custom routes feature allows you to add arbitrary HTTP endpoints to your MCP server, enabling integration with web services, OAuth flows, webhooks, and custom APIs. Custom routes use the powerful Starlette framework underneath while maintaining seamless integration with FastMCP's authentication and context systems.

## Basic Custom Routes

### Simple HTTP Endpoints

```python
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
import time

mcp = FastMCP("custom-routes-server")

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for load balancers."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "server": "fastmcp-server"
    })

@mcp.custom_route("/info", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Server information endpoint."""
    return JSONResponse({
        "tools_count": len(mcp._tool_manager.tools),
        "resources_count": len(mcp._resource_manager.resources),
        "prompts_count": len(mcp._prompt_manager.prompts),
        "transport": "streamable-http"
    })

@mcp.custom_route("/ping", methods=["GET"])
async def ping(request: Request) -> PlainTextResponse:
    """Simple ping endpoint."""
    return PlainTextResponse("pong")

if __name__ == "__main__":
    # Custom routes available on HTTP transports only
    mcp.run("streamable-http")
```

### Route Configuration Options

```python
@mcp.custom_route(
    path="/api/v1/users/{user_id}",    # Path with parameters
    methods=["GET", "PUT", "DELETE"],   # Multiple HTTP methods
    name="user_detail",                 # Route name for URL reversal
    include_in_schema=True              # Include in OpenAPI schema
)
async def user_detail(request: Request) -> JSONResponse:
    """User detail endpoint with path parameters."""
    user_id = request.path_params["user_id"]
    method = request.method

    if method == "GET":
        return JSONResponse({"user_id": user_id, "action": "get"})
    elif method == "PUT":
        body = await request.json()
        return JSONResponse({"user_id": user_id, "action": "update", "data": body})
    elif method == "DELETE":
        return JSONResponse({"user_id": user_id, "action": "delete"})
```

## Request Handling Patterns

### Query Parameters and Headers

```python
@mcp.custom_route("/search", methods=["GET"])
async def search_endpoint(request: Request) -> JSONResponse:
    """Search endpoint with query parameters and header processing."""
    # Query parameters
    query = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit", "10"))
    offset = int(request.query_params.get("offset", "0"))

    # Headers
    user_agent = request.headers.get("user-agent", "unknown")
    accept_language = request.headers.get("accept-language", "en")
    client_ip = request.client.host if request.client else "unknown"

    # Simulate search
    results = []
    if query:
        results = [
            {"id": i, "title": f"Result {i} for '{query}'"}
            for i in range(offset, min(offset + limit, offset + 50))
        ]

    return JSONResponse({
        "query": query,
        "results": results,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(results)
        },
        "meta": {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "client_ip": client_ip
        }
    })
```

### POST Data and File Uploads

```python
from starlette.datastructures import UploadFile
import json
import os

@mcp.custom_route("/upload", methods=["POST"])
async def file_upload(request: Request) -> JSONResponse:
    """File upload endpoint with form data handling."""
    form = await request.form()

    # Handle file upload
    uploaded_file: UploadFile = form.get("file")
    description = form.get("description", "")

    if not uploaded_file or uploaded_file.filename == "":
        return JSONResponse(
            {"error": "No file uploaded"},
            status_code=400
        )

    # Save file (implement proper file handling in production)
    upload_dir = "/tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, uploaded_file.filename)
    with open(file_path, "wb") as f:
        content = await uploaded_file.read()
        f.write(content)

    return JSONResponse({
        "filename": uploaded_file.filename,
        "size": len(content),
        "content_type": uploaded_file.content_type,
        "description": description,
        "saved_path": file_path
    })

@mcp.custom_route("/webhook", methods=["POST"])
async def webhook_handler(request: Request) -> JSONResponse:
    """Webhook endpoint for external service integration."""
    # Validate content type
    if request.headers.get("content-type") != "application/json":
        return JSONResponse(
            {"error": "Content-Type must be application/json"},
            status_code=400
        )

    # Parse webhook payload
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON payload"},
            status_code=400
        )

    # Validate webhook signature (implement in production)
    signature = request.headers.get("x-webhook-signature")
    if not validate_webhook_signature(payload, signature):
        return JSONResponse(
            {"error": "Invalid webhook signature"},
            status_code=401
        )

    # Process webhook
    event_type = payload.get("type")

    if event_type == "user.created":
        await handle_user_created(payload["data"])
    elif event_type == "payment.completed":
        await handle_payment_completed(payload["data"])
    else:
        return JSONResponse(
            {"error": f"Unknown event type: {event_type}"},
            status_code=400
        )

    return JSONResponse({"status": "processed", "event_type": event_type})
```

## Authentication Integration

### OAuth Callback Implementation

```python
from mcp.server.auth.middleware import get_access_token
from starlette.exceptions import HTTPException

@mcp.custom_route("/oauth/callback", methods=["GET"])
async def oauth_callback(request: Request) -> RedirectResponse:
    """OAuth callback handler for third-party authentication."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return RedirectResponse(
            f"/auth/error?error={error}",
            status_code=302
        )

    if not code or not state:
        return JSONResponse(
            {"error": "Missing code or state parameter"},
            status_code=400
        )

    try:
        # Exchange code for token (implement OAuth flow)
        access_token = await exchange_oauth_code(code, state)

        # Redirect to success page
        return RedirectResponse(
            f"/auth/success?token={access_token}",
            status_code=302
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            "/auth/error?error=server_error",
            status_code=302
        )

@mcp.custom_route("/protected", methods=["GET"])
async def protected_endpoint(request: Request) -> JSONResponse:
    """Protected endpoint requiring authentication."""
    # Check authentication
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    # Check permissions
    required_scopes = ["read", "write"]
    if not all(scope in access_token.scopes for scope in required_scopes):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return JSONResponse({
        "message": "Access granted",
        "user_id": access_token.user_id,
        "scopes": access_token.scopes
    })
```

### API Key Authentication

```python
import hashlib
import hmac

API_KEYS = {
    "client1": "secret-key-1",
    "client2": "secret-key-2"
}

def validate_api_key(request: Request) -> str | None:
    """Validate API key from header or query parameter."""
    # Check header
    api_key = request.headers.get("x-api-key")
    if not api_key:
        # Check query parameter
        api_key = request.query_params.get("api_key")

    if api_key in API_KEYS.values():
        # Find client ID by API key
        for client_id, key in API_KEYS.items():
            if key == api_key:
                return client_id

    return None

@mcp.custom_route("/api/secure", methods=["GET", "POST"])
async def secure_api_endpoint(request: Request) -> JSONResponse:
    """API endpoint with API key authentication."""
    client_id = validate_api_key(request)
    if not client_id:
        return JSONResponse(
            {"error": "Invalid or missing API key"},
            status_code=401
        )

    if request.method == "GET":
        return JSONResponse({
            "message": "Authenticated GET request",
            "client_id": client_id,
            "timestamp": time.time()
        })

    elif request.method == "POST":
        body = await request.json()
        return JSONResponse({
            "message": "Authenticated POST request",
            "client_id": client_id,
            "received_data": body
        })
```

## Advanced Route Patterns

### File Serving and Downloads

```python
from starlette.responses import FileResponse, StreamingResponse
import mimetypes

@mcp.custom_route("/files/{filename}", methods=["GET"])
async def serve_file(request: Request) -> FileResponse:
    """Serve static files with proper content types."""
    filename = request.path_params["filename"]
    file_path = f"/app/static/{filename}"

    # Security: prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        return JSONResponse(
            {"error": "Invalid filename"},
            status_code=400
        )

    if not os.path.exists(file_path):
        return JSONResponse(
            {"error": "File not found"},
            status_code=404
        )

    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)

    return FileResponse(
        file_path,
        media_type=content_type,
        filename=filename
    )

@mcp.custom_route("/export/data", methods=["GET"])
async def export_data(request: Request) -> StreamingResponse:
    """Stream large data exports."""
    format_type = request.query_params.get("format", "json")

    async def generate_data():
        """Generate data stream."""
        if format_type == "csv":
            yield "id,name,email\n"
            for i in range(10000):
                yield f"{i},User{i},user{i}@example.com\n"
        else:  # JSON
            yield '{"users": ['
            for i in range(10000):
                if i > 0:
                    yield ","
                yield f'{{"id": {i}, "name": "User{i}", "email": "user{i}@example.com"}}'
            yield "]}"

    media_type = "text/csv" if format_type == "csv" else "application/json"
    filename = f"export.{format_type}"

    return StreamingResponse(
        generate_data(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Real-time Endpoints

```python
import asyncio
from starlette.responses import StreamingResponse

@mcp.custom_route("/events", methods=["GET"])
async def server_sent_events(request: Request) -> StreamingResponse:
    """Server-Sent Events endpoint for real-time updates."""

    async def event_stream():
        """Generate server-sent events."""
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Send event
            timestamp = time.time()
            data = json.dumps({
                "timestamp": timestamp,
                "server_status": "running",
                "active_connections": 1
            })

            yield f"data: {data}\n\n"

            # Wait before next event
            await asyncio.sleep(5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@mcp.custom_route("/notify", methods=["POST"])
async def notification_trigger(request: Request) -> JSONResponse:
    """Trigger notifications to connected clients."""
    body = await request.json()
    message = body.get("message", "Default notification")

    # In a real implementation, you'd use a message queue
    # or WebSocket connections to broadcast to clients

    # Simulate notification
    await broadcast_notification(message)

    return JSONResponse({
        "status": "notification_sent",
        "message": message,
        "timestamp": time.time()
    })
```

### Admin Interface Routes

```python
@mcp.custom_route("/admin/status", methods=["GET"])
async def admin_status(request: Request) -> JSONResponse:
    """Admin status dashboard endpoint."""
    # Check admin authentication
    access_token = get_access_token()
    if not access_token or "admin" not in access_token.scopes:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return JSONResponse({
        "server_info": {
            "name": mcp.name,
            "uptime": time.time() - start_time,
            "tools": len(mcp._tool_manager.tools),
            "resources": len(mcp._resource_manager.resources),
            "prompts": len(mcp._prompt_manager.prompts)
        },
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "memory_usage": get_memory_usage(),
            "cpu_usage": get_cpu_usage()
        }
    })

@mcp.custom_route("/admin/tools", methods=["GET", "POST"])
async def admin_tools(request: Request) -> JSONResponse:
    """Admin tools management endpoint."""
    access_token = get_access_token()
    if not access_token or "admin" not in access_token.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")

    if request.method == "GET":
        # List all tools
        tools = []
        for tool_name, tool_info in mcp._tool_manager.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool_info.description,
                "parameters": tool_info.inputSchema
            })
        return JSONResponse({"tools": tools})

    elif request.method == "POST":
        # Tool management actions
        body = await request.json()
        action = body.get("action")

        if action == "reload":
            # Reload tool configuration
            await mcp._tool_manager.reload()
            return JSONResponse({"status": "tools_reloaded"})

        elif action == "disable":
            tool_name = body.get("tool_name")
            await mcp._tool_manager.disable_tool(tool_name)
            return JSONResponse({"status": "tool_disabled", "tool": tool_name})

        else:
            return JSONResponse(
                {"error": f"Unknown action: {action}"},
                status_code=400
            )
```

## Route Organization and Modularity

### Route Blueprints Pattern

```python
from typing import List
from dataclasses import dataclass

@dataclass
class RouteDefinition:
    path: str
    methods: List[str]
    handler: callable
    name: str = None
    include_in_schema: bool = True

class RouteBlueprint:
    """Blueprint for organizing related routes."""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.routes: List[RouteDefinition] = []

    def route(self, path: str, methods: List[str] = None, name: str = None):
        """Decorator to add route to blueprint."""
        if methods is None:
            methods = ["GET"]

        def decorator(func):
            full_path = f"{self.prefix}{path}" if self.prefix else path
            self.routes.append(RouteDefinition(
                path=full_path,
                methods=methods,
                handler=func,
                name=name
            ))
            return func
        return decorator

    def register(self, mcp: FastMCP):
        """Register all routes in blueprint with FastMCP."""
        for route_def in self.routes:
            mcp.custom_route(
                route_def.path,
                methods=route_def.methods,
                name=route_def.name,
                include_in_schema=route_def.include_in_schema
            )(route_def.handler)

# API v1 routes blueprint
api_v1 = RouteBlueprint(prefix="/api/v1")

@api_v1.route("/users", methods=["GET", "POST"])
async def users_endpoint(request: Request) -> JSONResponse:
    """Users API endpoint."""
    if request.method == "GET":
        return JSONResponse({"users": []})
    else:
        body = await request.json()
        return JSONResponse({"created_user": body})

@api_v1.route("/users/{user_id}", methods=["GET", "PUT", "DELETE"])
async def user_detail_endpoint(request: Request) -> JSONResponse:
    """User detail API endpoint."""
    user_id = request.path_params["user_id"]
    return JSONResponse({"user_id": user_id, "method": request.method})

# Admin routes blueprint
admin_bp = RouteBlueprint(prefix="/admin")

@admin_bp.route("/dashboard", methods=["GET"])
async def admin_dashboard(request: Request) -> JSONResponse:
    """Admin dashboard."""
    return JSONResponse({"dashboard": "admin_data"})

# Register blueprints
mcp = FastMCP("modular-server")
api_v1.register(mcp)
admin_bp.register(mcp)
```

## Middleware Patterns for Custom Routes

### Request/Response Logging

```python
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def with_request_logging(func):
    """Decorator to add request/response logging."""
    @wraps(func)
    async def wrapper(request: Request):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        try:
            response = await func(request)

            # Log successful response
            duration = time.time() - start_time
            logger.info(f"Response: {response.status_code} in {duration:.3f}s")

            return response
        except Exception as e:
            # Log error response
            duration = time.time() - start_time
            logger.error(f"Error: {e} in {duration:.3f}s")
            raise

    return wrapper

@mcp.custom_route("/api/logged", methods=["GET"])
@with_request_logging
async def logged_endpoint(request: Request) -> JSONResponse:
    """Endpoint with automatic request/response logging."""
    return JSONResponse({"message": "Request logged"})
```

### Rate Limiting

```python
from collections import defaultdict
import asyncio

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def is_allowed(self, identifier: str) -> bool:
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

def with_rate_limiting(limiter: RateLimiter):
    """Decorator to add rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request):
            # Use IP address as identifier
            client_ip = request.client.host if request.client else "unknown"

            if not await limiter.is_allowed(client_ip):
                return JSONResponse(
                    {"error": "Rate limit exceeded. Try again later."},
                    status_code=429
                )

            return await func(request)
        return wrapper
    return decorator

@mcp.custom_route("/api/limited", methods=["GET"])
@with_rate_limiting(rate_limiter)
async def rate_limited_endpoint(request: Request) -> JSONResponse:
    """Endpoint with rate limiting."""
    return JSONResponse({"message": "Request within rate limit"})
```

## Error Handling and Validation

### Comprehensive Error Handling

```python
from starlette.exceptions import HTTPException
from pydantic import BaseModel, ValidationError
import traceback

class ErrorResponse(BaseModel):
    error: str
    detail: str = None
    timestamp: float = None

def handle_errors(func):
    """Decorator for comprehensive error handling."""
    @wraps(func)
    async def wrapper(request: Request):
        try:
            return await func(request)

        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise

        except ValidationError as e:
            # Handle Pydantic validation errors
            return JSONResponse(
                ErrorResponse(
                    error="validation_error",
                    detail=str(e),
                    timestamp=time.time()
                ).dict(),
                status_code=400
            )

        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error in {func.__name__}: {e}")

            return JSONResponse(
                ErrorResponse(
                    error="internal_server_error",
                    detail="An unexpected error occurred",
                    timestamp=time.time()
                ).dict(),
                status_code=500
            )

    return wrapper

@mcp.custom_route("/api/robust", methods=["POST"])
@handle_errors
async def robust_endpoint(request: Request) -> JSONResponse:
    """Endpoint with comprehensive error handling."""
    # This could raise various exceptions
    body = await request.json()  # Could raise json.JSONDecodeError

    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in body:
            raise HTTPException(400, f"Missing required field: {field}")

    # Simulate processing that could fail
    result = await process_user_data(body)

    return JSONResponse({"status": "success", "result": result})
```

### Input Validation with Pydantic

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()

    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

def validate_json(model_class):
    """Decorator to validate JSON input with Pydantic."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request):
            try:
                body = await request.json()
                validated_data = model_class(**body)
                # Add validated data to request state
                request.state.validated_data = validated_data
                return await func(request)
            except ValidationError as e:
                return JSONResponse(
                    {"error": "validation_error", "details": e.errors()},
                    status_code=400
                )
        return wrapper
    return decorator

@mcp.custom_route("/api/users", methods=["POST"])
@validate_json(UserCreateRequest)
async def create_user_endpoint(request: Request) -> JSONResponse:
    """Create user with Pydantic validation."""
    user_data = request.state.validated_data

    # Create user with validated data
    user = await create_user(
        name=user_data.name,
        email=user_data.email,
        age=user_data.age
    )

    return JSONResponse({
        "status": "created",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age
        }
    })
```

## Testing Custom Routes

### Route Testing Utilities

```python
import pytest
from httpx import AsyncClient
from mcp.server.fastmcp import FastMCP

class TestCustomRoutes:
    """Test utilities for custom routes."""

    @pytest.fixture
    async def test_client(self):
        """Create test client for FastMCP server."""
        mcp = FastMCP("test-server")

        @mcp.custom_route("/test", methods=["GET", "POST"])
        async def test_route(request):
            if request.method == "GET":
                return JSONResponse({"method": "GET"})
            else:
                body = await request.json()
                return JSONResponse({"method": "POST", "data": body})

        # Create test client
        app = mcp.streamable_http_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_get_endpoint(self, test_client):
        """Test GET endpoint."""
        response = await test_client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"method": "GET"}

    async def test_post_endpoint(self, test_client):
        """Test POST endpoint."""
        data = {"name": "test", "value": 123}
        response = await test_client.post("/test", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["method"] == "POST"
        assert result["data"] == data

    async def test_authentication(self, test_client):
        """Test authenticated endpoints."""
        # Test without auth
        response = await test_client.get("/protected")
        assert response.status_code == 401

        # Test with auth
        headers = {"Authorization": "Bearer test-token"}
        response = await test_client.get("/protected", headers=headers)
        assert response.status_code == 200

# Run tests
if __name__ == "__main__":
    pytest.main([__file__])
```

## Best Practices

### Security Guidelines

1. **Input Validation**: Always validate and sanitize input data
2. **Authentication**: Implement proper authentication for sensitive endpoints
3. **Authorization**: Check permissions for protected operations
4. **Rate Limiting**: Implement rate limiting for public endpoints
5. **HTTPS Only**: Use HTTPS in production for sensitive data
6. **Error Handling**: Don't expose sensitive information in error messages

### Performance Optimization

1. **Async Operations**: Use async/await for I/O operations
2. **Connection Pooling**: Reuse database and HTTP connections
3. **Caching**: Implement caching for expensive operations
4. **Streaming**: Use streaming responses for large data
5. **Compression**: Enable gzip compression for responses

### Architecture Patterns

1. **Route Organization**: Use blueprints for organizing related routes
2. **Middleware**: Implement cross-cutting concerns with decorators
3. **Error Handling**: Centralize error handling with decorators
4. **Validation**: Use Pydantic for request/response validation
5. **Testing**: Write comprehensive tests for all custom routes

## Transport Limitations

### Supported Transports

- **StreamableHTTP**: ✅ Full custom routes support
- **SSE**: ✅ Full custom routes support
- **stdio**: ❌ Custom routes not available (process-based transport)

### Example Transport Check

```python
@mcp.custom_route("/transport-info", methods=["GET"])
async def transport_info(request: Request) -> JSONResponse:
    """Endpoint showing transport information."""
    return JSONResponse({
        "message": "This endpoint is only available on HTTP transports",
        "available_transports": ["streamable-http", "sse"],
        "current_transport": "http"
    })

if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "streamable-http"

    if transport == "stdio":
        print("Warning: Custom routes not available with stdio transport")

    mcp.run(transport)
```

This comprehensive guide provides everything needed to implement sophisticated HTTP endpoints in FastMCP servers, from simple APIs to complex OAuth flows and admin interfaces, while maintaining integration with FastMCP's core MCP protocol capabilities.
