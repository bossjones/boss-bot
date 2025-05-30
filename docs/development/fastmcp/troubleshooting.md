# Troubleshooting

Complete guide for diagnosing and resolving common FastMCP issues, including error messages, debugging techniques, and performance problems.

## Quick Diagnostics

### Health Check

First, verify your server is working with a basic health check:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Health Check", debug=True, log_level="DEBUG")

@mcp.tool()
def ping() -> str:
    """Basic connectivity test."""
    return "pong"

@mcp.resource("health://status")
def health_status() -> str:
    """Server health status."""
    return "OK"

if __name__ == "__main__":
    # Test with stdio
    mcp.run("stdio")
```

### Enable Debug Mode

Always start troubleshooting with debug mode enabled:

```python
# In code
mcp = FastMCP("My Server", debug=True, log_level="DEBUG")

# Via environment
export FASTMCP_DEBUG=true
export FASTMCP_LOG_LEVEL=DEBUG
```

## Common Errors

### 1. Decorator Errors

#### Error: "The @tool decorator was used incorrectly"

**Problem:** Using decorators without parentheses

```python
# ❌ WRONG - Missing parentheses
@mcp.tool
def my_tool() -> str:
    return "hello"

# ❌ WRONG - Called incorrectly
@mcp.tool(my_function)
def my_tool() -> str:
    return "hello"
```

**Solution:** Always use parentheses when calling decorators

```python
# ✅ CORRECT
@mcp.tool()
def my_tool() -> str:
    return "hello"

@mcp.resource("data://example")
def my_resource() -> str:
    return "data"

@mcp.prompt()
def my_prompt() -> str:
    return "prompt text"
```

#### Error: "You must provide a name for lambda functions"

**Problem:** Using lambda functions without explicit names

```python
# ❌ WRONG - Lambda without name
mcp.add_tool(lambda x: x * 2)
```

**Solution:** Use named functions or provide explicit names

```python
# ✅ CORRECT - Named function
def double(x: int) -> int:
    return x * 2

mcp.add_tool(double)

# ✅ CORRECT - Lambda with explicit name
mcp.add_tool(lambda x: x * 2, name="double")
```

### 2. Type Annotation Errors

#### Error: "Invalid signature for use with FastMCP"

**Problem:** Missing or incorrect type annotations

```python
# ❌ WRONG - No type annotations
@mcp.tool()
def bad_tool(x):
    return x

# ❌ WRONG - Incomplete annotations
@mcp.tool()
def bad_tool(x: int):
    return x  # Missing return type
```

**Solution:** Provide complete type annotations

```python
# ✅ CORRECT
@mcp.tool()
def good_tool(x: int) -> str:
    return str(x)

# ✅ CORRECT - Optional parameters
from typing import Optional

@mcp.tool()
def optional_tool(x: int, y: Optional[str] = None) -> str:
    return f"{x}: {y or 'default'}"
```

#### Error: Context type not recognized

**Problem:** Context parameter not properly typed

```python
# ❌ WRONG - Missing type annotation
@mcp.tool()
def bad_context_tool(x: int, ctx) -> str:
    return str(x)

# ❌ WRONG - Wrong import or type
@mcp.tool()
def bad_context_tool(x: int, ctx: object) -> str:
    return str(x)
```

**Solution:** Import and use Context correctly

```python
# ✅ CORRECT
from mcp.server.fastmcp import Context

@mcp.tool()
def good_context_tool(x: int, ctx: Context) -> str:
    ctx.info(f"Processing {x}")
    return str(x)
```

### 3. Resource Errors

#### Error: "Mismatch between URI parameters and function parameters"

**Problem:** URI template parameters don't match function parameters

```python
# ❌ WRONG - Parameter name mismatch
@mcp.resource("data://{user_id}")
def get_user(id: str) -> str:  # 'id' != 'user_id'
    return f"User {id}"

# ❌ WRONG - Missing parameters
@mcp.resource("data://{user_id}/{post_id}")
def get_post(user_id: str) -> str:  # Missing 'post_id'
    return f"Post by {user_id}"
```

**Solution:** Ensure parameter names match exactly

```python
# ✅ CORRECT
@mcp.resource("data://{user_id}")
def get_user(user_id: str) -> str:
    return f"User {user_id}"

@mcp.resource("data://{user_id}/{post_id}")
def get_post(user_id: str, post_id: str) -> str:
    return f"Post {post_id} by {user_id}"
```

#### Error: "Unknown resource"

**Problem:** Accessing non-existent or incorrectly named resources

```python
# Resource registered as:
@mcp.resource("data://users")
def users() -> str:
    return "user list"

# ❌ WRONG - Incorrect URI
content = await ctx.read_resource("data://user")  # Missing 's'
```

**Solution:** Use exact URI when accessing resources

```python
# ✅ CORRECT
content = await ctx.read_resource("data://users")

# For debugging, list all resources
@mcp.tool()
async def list_resources(ctx: Context) -> list[str]:
    """Debug tool to list all available resources."""
    server = ctx.fastmcp
    resources = await server.list_resources()
    return [str(r.uri) for r in resources]
```

### 4. Authentication Errors

#### Error: "settings.auth must be specified if and only if auth_server_provider is specified"

**Problem:** Mismatched authentication configuration

```python
# ❌ WRONG - Auth provider without settings
from mcp.server.auth.provider import OAuthAuthorizationServerProvider

provider = OAuthAuthorizationServerProvider(...)
mcp = FastMCP("Server", auth_server_provider=provider)  # Missing auth settings

# ❌ WRONG - Auth settings without provider
from mcp.server.auth.settings import AuthSettings

auth_settings = AuthSettings(...)
mcp = FastMCP("Server", auth=auth_settings)  # Missing provider
```

**Solution:** Configure both auth provider and settings together

```python
# ✅ CORRECT - Both together
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings

provider = OAuthAuthorizationServerProvider(...)
auth_settings = AuthSettings(
    issuer_url="https://your-domain.com",
    required_scopes=["read", "write"]
)

mcp = FastMCP(
    "Secure Server",
    auth_server_provider=provider,
    auth=auth_settings
)

# ✅ CORRECT - Neither (no auth)
mcp = FastMCP("Public Server")  # No auth required
```

### 5. Transport Errors

#### Error: "Session manager can only be accessed after calling streamable_http_app()"

**Problem:** Accessing session manager before initialization

```python
# ❌ WRONG
mcp = FastMCP("My Server")
manager = mcp.session_manager  # Not initialized yet
```

**Solution:** Initialize the app first

```python
# ✅ CORRECT
mcp = FastMCP("My Server")
app = mcp.streamable_http_app()  # Initialize first
manager = mcp.session_manager   # Now available
```

#### Error: Port already in use

**Problem:** Multiple servers using the same port

```bash
# Error message
OSError: [Errno 48] Address already in use
```

**Solution:** Use different ports or find/kill existing processes

```python
# Option 1: Use different port
mcp = FastMCP("Server", port=8001)

# Option 2: Find and kill process using port
# On macOS/Linux:
# lsof -ti:8000 | xargs kill -9

# Option 3: Let the system choose a free port
import socket

def get_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

mcp = FastMCP("Server", port=get_free_port())
```

### 6. Context Errors

#### Error: "Context is not available outside of a request"

**Problem:** Using context outside of tool/resource execution

```python
# ❌ WRONG - Context used outside tool
mcp = FastMCP("Server")

@mcp.tool()
def setup_tool() -> str:
    return "setup complete"

# This fails - no active request context
ctx = mcp.get_context()
ctx.info("Server starting")  # Error!
```

**Solution:** Only use context within tools/resources

```python
# ✅ CORRECT - Context in tool
@mcp.tool()
def good_tool(ctx: Context) -> str:
    ctx.info("Tool executing")  # Works!
    return "success"

# ✅ CORRECT - Alternative logging
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("Server", log_level="INFO")
logger.info("Server starting")  # Use regular logging
```

## Performance Issues

### 1. Slow Tool Execution

#### Problem: Tools taking too long to respond

```python
# ❌ PROBLEMATIC - Blocking operation
@mcp.tool()
def slow_tool(data: str) -> str:
    import time
    time.sleep(10)  # Blocks the entire server
    return "done"
```

#### Solution: Use async operations and timeouts

```python
# ✅ BETTER - Async with timeout
import asyncio
from asyncio import timeout

@mcp.tool()
async def fast_tool(data: str, ctx: Context) -> str:
    try:
        async with timeout(5.0):  # 5 second timeout
            await asyncio.sleep(0.1)  # Non-blocking
            return "done"
    except asyncio.TimeoutError:
        ctx.warning("Operation timed out")
        return "timeout"
```

### 2. Memory Issues

#### Problem: Memory usage growing over time

```python
# ❌ PROBLEMATIC - Memory leak
_cache = {}  # Global cache that grows forever

@mcp.tool()
def leaky_tool(key: str) -> str:
    if key not in _cache:
        _cache[key] = expensive_computation(key)
    return _cache[key]
```

#### Solution: Use proper caching with limits

```python
# ✅ BETTER - LRU cache with size limit
from functools import lru_cache

@lru_cache(maxsize=100)  # Limit cache size
def cached_computation(key: str) -> str:
    return expensive_computation(key)

@mcp.tool()
def efficient_tool(key: str) -> str:
    return cached_computation(key)
```

### 3. Concurrent Request Issues

#### Problem: Tools interfering with each other

```python
# ❌ PROBLEMATIC - Shared mutable state
counter = 0

@mcp.tool()
def unsafe_counter() -> int:
    global counter
    counter += 1  # Race condition!
    return counter
```

#### Solution: Use thread-safe operations

```python
# ✅ BETTER - Thread-safe counter
import threading

_lock = threading.Lock()
_counter = 0

@mcp.tool()
def safe_counter() -> int:
    global _counter
    with _lock:
        _counter += 1
        return _counter

# ✅ EVEN BETTER - Stateless operations
from datetime import datetime

@mcp.tool()
def stateless_id() -> str:
    """Generate unique ID without shared state."""
    return f"id_{datetime.now().isoformat()}"
```

## Debugging Techniques

### 1. Enhanced Logging

```python
from mcp.server.fastmcp import FastMCP, Context
import logging
import traceback

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

mcp = FastMCP("Debug Server", debug=True, log_level="DEBUG")

@mcp.tool()
async def debug_tool(data: dict, ctx: Context) -> str:
    """Tool with comprehensive debugging."""
    try:
        ctx.debug(f"Input received: {data}")
        ctx.info("Processing started")

        # Add progress reporting
        await ctx.report_progress(0, 100, "Starting")

        # Your logic here
        result = process_data(data)

        await ctx.report_progress(100, 100, "Complete")
        ctx.info(f"Processing completed: {result}")
        return result

    except Exception as e:
        # Log full traceback
        error_trace = traceback.format_exc()
        ctx.error(f"Tool failed: {e}")
        ctx.debug(f"Full traceback: {error_trace}")

        # Return user-friendly error
        return f"Error: {str(e)}"
```

### 2. Request Tracing

```python
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id')

@mcp.tool()
async def traced_tool(data: str, ctx: Context) -> str:
    """Tool with request tracing."""
    # Generate unique request ID
    req_id = str(uuid.uuid4())[:8]
    request_id_var.set(req_id)

    ctx.info(f"[{req_id}] Request started")

    try:
        result = await process_with_trace(data, req_id)
        ctx.info(f"[{req_id}] Request completed")
        return result
    except Exception as e:
        ctx.error(f"[{req_id}] Request failed: {e}")
        raise

async def process_with_trace(data: str, req_id: str) -> str:
    """Helper function with tracing."""
    logger = logging.getLogger(__name__)
    logger.info(f"[{req_id}] Processing: {data}")
    # Your logic here
    return "processed"
```

### 3. Health and Status Monitoring

```python
import time
import psutil
from datetime import datetime
from typing import Dict, Any

mcp = FastMCP("Monitored Server")

# Store server metrics
_server_stats = {
    "start_time": time.time(),
    "request_count": 0,
    "error_count": 0,
}

@mcp.tool()
def get_server_stats() -> Dict[str, Any]:
    """Get server health and statistics."""
    uptime = time.time() - _server_stats["start_time"]

    return {
        "uptime_seconds": uptime,
        "requests_total": _server_stats["request_count"],
        "errors_total": _server_stats["error_count"],
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "timestamp": datetime.now().isoformat(),
    }

@mcp.tool()
async def monitored_tool(data: str, ctx: Context) -> str:
    """Tool with built-in monitoring."""
    _server_stats["request_count"] += 1

    try:
        result = await process_data(data)
        return result
    except Exception as e:
        _server_stats["error_count"] += 1
        ctx.error(f"Tool error: {e}")
        raise

@mcp.resource("health://metrics")
def health_metrics() -> str:
    """Health check endpoint."""
    stats = get_server_stats()
    if stats["memory_usage_mb"] > 1000:  # 1GB limit
        return "WARNING: High memory usage"
    return "OK"
```

## Common Patterns and Solutions

### 1. Graceful Error Handling

```python
from typing import Union, Dict, Any

@mcp.tool()
async def robust_api_call(url: str, ctx: Context) -> Union[str, Dict[str, Any]]:
    """Make API call with comprehensive error handling."""
    import httpx

    try:
        ctx.info(f"Making request to: {url}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            ctx.info("Request successful")
            return data

    except httpx.TimeoutException:
        error_msg = "Request timed out"
        ctx.warning(error_msg)
        return {"error": error_msg, "type": "timeout"}

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        ctx.warning(error_msg)
        return {"error": error_msg, "type": "http_error"}

    except httpx.RequestError as e:
        error_msg = f"Network error: {str(e)}"
        ctx.error(error_msg)
        return {"error": error_msg, "type": "network_error"}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        ctx.error(error_msg)
        # Re-raise for unexpected errors
        raise
```

### 2. Input Validation

```python
from pydantic import BaseModel, Field, validator
from typing import List

class ProcessingRequest(BaseModel):
    items: List[str] = Field(min_items=1, max_items=100)
    mode: str = Field(regex=r'^(fast|slow|batch)$')

    @validator('items')
    def validate_items(cls, v):
        for item in v:
            if not item.strip():
                raise ValueError("Items cannot be empty")
        return v

@mcp.tool()
async def validated_tool(request: ProcessingRequest, ctx: Context) -> str:
    """Tool with automatic input validation."""
    ctx.info(f"Processing {len(request.items)} items in {request.mode} mode")

    # Request is automatically validated by Pydantic
    results = []
    for item in request.items:
        processed = await process_item(item, request.mode)
        results.append(processed)

    return f"Processed {len(results)} items"
```

### 3. Resource Cleanup

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

@asynccontextmanager
async def database_connection():
    """Context manager for database connections."""
    conn = await connect_to_database()
    try:
        yield conn
    finally:
        await conn.close()

@mcp.tool()
async def database_tool(query: str, ctx: Context) -> str:
    """Tool with proper resource cleanup."""
    try:
        async with database_connection() as conn:
            ctx.info("Database connected")
            result = await conn.execute(query)
            ctx.info("Query executed successfully")
            return str(result)
    except Exception as e:
        ctx.error(f"Database error: {e}")
        raise
```

## When to Get Help

### 1. Check Documentation First
- Review the [API Reference](api-reference.md) for method signatures
- Check [Examples](examples.md) for working code patterns
- Read [Development Workflow](development-workflow.md) for setup issues

### 2. Gather Debug Information

Before reporting issues, collect:

```python
@mcp.tool()
def debug_info() -> Dict[str, Any]:
    """Collect debug information for issue reports."""
    import platform
    import sys
    from mcp.shared.version import __version__

    return {
        "mcp_version": __version__,
        "python_version": sys.version,
        "platform": platform.platform(),
        "server_name": mcp.name,
        "debug_mode": mcp.settings.debug,
        "log_level": mcp.settings.log_level,
        "tools_count": len(mcp._tool_manager._tools),
        "resources_count": len(mcp._resource_manager._resources),
    }
```

### 3. Create Minimal Reproduction

Create the smallest possible example that reproduces your issue:

```python
"""Minimal reproduction case for [issue description]"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Issue Reproduction", debug=True)

@mcp.tool()
def problem_tool() -> str:
    # Minimal code that demonstrates the issue
    return "issue reproduction"

if __name__ == "__main__":
    mcp.run("stdio")
```

This troubleshooting guide should help you resolve most common FastMCP issues. For complex problems, use the debugging techniques to gather detailed information before seeking help.
