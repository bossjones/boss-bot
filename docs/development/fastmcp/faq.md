# FAQ

Frequently asked questions about FastMCP development, covering common issues, best practices, and practical solutions for building MCP servers.

## Getting Started

### What is FastMCP and how does it differ from the raw MCP SDK?

FastMCP is a high-level, decorator-based Python framework that simplifies MCP server development. Unlike the raw MCP SDK which requires manual message handling and protocol implementation, FastMCP provides simple `@tool`, `@resource`, and `@prompt` decorators with automatic type validation.

**Raw MCP SDK approach:**
```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [types.Tool(name="add", description="Add numbers", inputSchema={...})]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "add":
        return [types.TextContent(type="text", text=str(arguments["a"] + arguments["b"]))]
```

**FastMCP approach:**
```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

### Which transport should I use: stdio, streamable-http, or sse?

- **stdio**: Use for local development, command-line tools, and desktop applications. Best for single-user scenarios with direct process communication.
- **streamable-http**: Use for web deployment, cloud services, and when you need authentication, resumable connections, and multiple concurrent clients.
- **sse**: Use for web deployment when you need HTTP compatibility but don't need the advanced features of streamable-http.

```python
# Local development
mcp.run("stdio")

# Web deployment with authentication
mcp.run("streamable-http")

# Simple web deployment
mcp.run("sse")
```

### How do I install and run my first FastMCP server?

1. Install FastMCP:
```bash
uv add mcp
```

2. Create a simple server:
```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("My First Server")

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

@mcp.tool()
async def async_example(message: str, ctx: Context) -> str:
    """Example with logging and context."""
    await ctx.info(f"Processing message: {message}")
    return f"Processed: {message}"

if __name__ == "__main__":
    mcp.run("stdio")  # Change to "streamable-http" for web
```

3. Run the server:
```bash
python server.py
```

## Tools Development

### How do I validate tool inputs and handle errors properly?

Use Pydantic `Field` for validation and proper error handling:

```python
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Validation Server")

class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="User's name")
    age: int = Field(ge=0, le=150, description="User's age")
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Valid email")

@mcp.tool()
async def create_user(user: UserInput, ctx: Context) -> dict:
    """Create user with validation."""
    try:
        await ctx.info(f"Creating user: {user.name}")

        # Simulate user creation
        user_id = hash(user.email) % 10000

        await ctx.info("User created successfully")
        return {
            "user_id": user_id,
            "name": user.name,
            "age": user.age,
            "email": user.email
        }
    except Exception as e:
        await ctx.error(f"Failed to create user: {e}")
        raise
```

### When should I use async vs sync tools?

Use **async tools** when you need to:
- Make HTTP requests
- Access databases
- Perform file I/O operations
- Use context capabilities (logging, progress reporting)
- Call other async functions

Use **sync tools** for simple computational tasks that don't involve I/O.

```python
# Sync tool for computation
@mcp.tool()
def calculate_fibonacci(n: int) -> int:
    """Calculate fibonacci number (sync)."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Async tool for I/O operations
@mcp.tool()
async def fetch_data(url: str, ctx: Context) -> dict:
    """Fetch data from URL (async)."""
    import httpx

    await ctx.info(f"Fetching data from {url}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    await ctx.info("Data fetched successfully")
    return response.json()
```

### How do I access MCP capabilities like logging and progress reporting?

Inject a `Context` parameter into your tool:

```python
@mcp.tool()
async def long_running_task(
    items: list[str],
    ctx: Context
) -> list[str]:
    """Process items with progress reporting."""
    results = []

    await ctx.info(f"Starting to process {len(items)} items")

    for i, item in enumerate(items):
        # Log progress
        await ctx.debug(f"Processing item {i+1}: {item}")

        # Report progress
        await ctx.report_progress(
            progress=i / len(items),
            total=1.0,
            message=f"Processing {item}"
        )

        # Simulate work
        import asyncio
        await asyncio.sleep(0.5)

        result = f"processed_{item}"
        results.append(result)

    await ctx.info("All items processed successfully")
    return results
```

### Can I return rich content like images from tools?

Yes, use the appropriate content types:

```python
from mcp.server.fastmcp import Image
import base64

@mcp.tool()
def generate_chart(data: list[int]) -> Image:
    """Generate a chart image."""
    # Generate chart (example using matplotlib)
    import matplotlib.pyplot as plt
    import io

    plt.figure(figsize=(10, 6))
    plt.plot(data)
    plt.title("Data Chart")

    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return Image(
        data=img_buffer.read(),
        mime_type="image/png"
    )

@mcp.tool()
def get_file_content(filename: str) -> str:
    """Return file content as text."""
    with open(filename, 'r') as f:
        return f.read()
```

## Resources

### What's the difference between static resources and resource templates?

- **Static resources**: Fixed URIs that return specific data
- **Resource templates**: URI patterns with parameters for dynamic resources

```python
# Static resource - fixed URI
@mcp.resource("config://app-settings")
def app_config() -> dict:
    """Application configuration."""
    return {
        "version": "1.0",
        "debug": False,
        "max_connections": 100
    }

# Resource template - dynamic URI with parameters
@mcp.resource("user://{user_id}/profile")
def user_profile(user_id: str) -> dict:
    """Get user profile by ID."""
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "profile_data": "..."
    }

# Multiple parameters
@mcp.resource("files://{category}/{filename}")
def get_file(category: str, filename: str) -> str:
    """Get file content by category and name."""
    file_path = f"/data/{category}/{filename}"
    with open(file_path, 'r') as f:
        return f.read()
```

### How do I implement secure file access with resources?

Validate paths and restrict access to allowed directories:

```python
from pathlib import Path
import os

# Define allowed base directories
ALLOWED_DIRECTORIES = [
    "/app/public",
    "/app/data",
    "/tmp/uploads"
]

@mcp.resource("file://{path}")
def secure_file_access(path: str) -> str:
    """Securely access files within allowed directories."""
    try:
        # Resolve the full path
        requested_path = Path(path).resolve()

        # Check if path is within allowed directories
        is_allowed = any(
            str(requested_path).startswith(allowed_dir)
            for allowed_dir in ALLOWED_DIRECTORIES
        )

        if not is_allowed:
            raise ValueError(f"Access denied: {path} is outside allowed directories")

        # Check if file exists
        if not requested_path.exists():
            raise ValueError(f"File not found: {path}")

        # Check if it's actually a file (not a directory)
        if not requested_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Read and return file content
        return requested_path.read_text()

    except Exception as e:
        raise ValueError(f"Error accessing file {path}: {e}")

@mcp.resource("safe-image://{image_name}")
def get_safe_image(image_name: str) -> bytes:
    """Get images from safe directory only."""
    # Validate image name (no path traversal)
    if '..' in image_name or '/' in image_name or '\\' in image_name:
        raise ValueError("Invalid image name")

    image_path = Path("/app/images") / f"{image_name}.png"

    if not image_path.exists():
        raise ValueError(f"Image not found: {image_name}")

    return image_path.read_bytes()
```

### How do I handle different file types and MIME types in resources?

Specify appropriate MIME types and handle different content types:

```python
import mimetypes
from pathlib import Path

@mcp.resource("image://{name}", mime_type="image/png")
def get_png_image(name: str) -> bytes:
    """Get PNG image."""
    return Path(f"/images/{name}.png").read_bytes()

@mcp.resource("data://{name}", mime_type="application/json")
def get_json_data(name: str) -> dict:
    """Get JSON data."""
    return {"name": name, "type": "json", "data": "..."}

@mcp.resource("document://{filename}")
def get_document(filename: str) -> str:
    """Get document with auto-detected MIME type."""
    file_path = Path(f"/documents/{filename}")

    if not file_path.exists():
        raise ValueError(f"Document not found: {filename}")

    # Auto-detect MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if mime_type and mime_type.startswith('text/'):
        return file_path.read_text()
    else:
        # Return base64 encoded binary data
        import base64
        return base64.b64encode(file_path.read_bytes()).decode()
```

## Authentication & Security

### How do I add authentication to my FastMCP server?

Authentication is only available for HTTP transports. Implement an OAuth provider:

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.auth.middleware import get_access_token
from starlette.requests import Request
from starlette.responses import JSONResponse

# Create custom OAuth provider
class MyOAuthProvider(OAuthAuthorizationServerProvider):
    def __init__(self):
        super().__init__(provider_id="my-provider")

    async def authorize(self, request) -> str:
        # Implement authorization logic
        return "auth-code-123"

    async def token(self, request) -> dict:
        # Implement token exchange
        return {
            "access_token": "token-123",
            "token_type": "bearer",
            "scope": "read write"
        }

# Configure authentication
oauth_provider = MyOAuthProvider()
auth_settings = AuthSettings(
    issuer_url="https://myserver.com",
    client_registration_options=ClientRegistrationOptions(
        valid_scopes=["read", "write", "admin"],
        default_scopes=["read"]
    )
)

mcp = FastMCP(
    "Secure Server",
    auth_server_provider=oauth_provider,
    auth=auth_settings
)

@mcp.tool()
async def protected_tool(data: str) -> str:
    """Tool that requires authentication."""
    access_token = get_access_token()

    if not access_token:
        raise ValueError("Authentication required")

    if "write" not in access_token.scopes:
        raise ValueError("Insufficient permissions")

    return f"Processed: {data} for user {access_token.user_id}"

if __name__ == "__main__":
    mcp.run("streamable-http")  # Authentication requires HTTP transport
```

### Can I use authentication with stdio transport?

No, authentication is only available with HTTP transports (streamable-http and sse). The stdio transport runs locally and doesn't require authentication since it communicates directly through stdin/stdout.

### How do I implement scope-based access control?

Configure scopes in your auth settings and validate them in tools:

```python
from mcp.server.auth.middleware import get_access_token

# Configure scopes
auth_settings = AuthSettings(
    client_registration_options=ClientRegistrationOptions(
        valid_scopes=["read", "write", "admin", "user:profile", "data:modify"],
        default_scopes=["read"]
    )
)

@mcp.tool()
async def read_data(ctx: Context) -> dict:
    """Tool requiring read scope."""
    access_token = get_access_token()

    if not access_token or "read" not in access_token.scopes:
        raise ValueError("Read permission required")

    await ctx.info(f"Data accessed by user: {access_token.user_id}")
    return {"data": "sensitive information"}

@mcp.tool()
async def modify_user_profile(user_id: str, data: dict, ctx: Context) -> dict:
    """Tool requiring specific scopes."""
    access_token = get_access_token()

    if not access_token:
        raise ValueError("Authentication required")

    required_scopes = ["write", "user:profile"]
    if not all(scope in access_token.scopes for scope in required_scopes):
        raise ValueError(f"Required scopes: {required_scopes}")

    await ctx.info(f"Profile modified for user {user_id}")
    return {"status": "updated", "user_id": user_id}
```

## Configuration & Environment

### How do I configure my server for different environments?

Use environment variables and conditional configuration:

```python
import os

# Environment-based configuration
def get_config():
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return {
            "debug": False,
            "log_level": "INFO",
            "host": "0.0.0.0",
            "port": 8000
        }
    elif env == "staging":
        return {
            "debug": True,
            "log_level": "DEBUG",
            "host": "0.0.0.0",
            "port": 8080
        }
    else:  # development
        return {
            "debug": True,
            "log_level": "DEBUG",
            "host": "127.0.0.1",
            "port": 3000
        }

config = get_config()
mcp = FastMCP("Environment Server", **config)

# Or use environment variables directly
mcp = FastMCP(
    "My Server",
    debug=os.getenv("DEBUG", "false").lower() == "true",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000"))
)
```

### What environment variables does FastMCP support?

Key environment variables with the `FASTMCP_` prefix:

```bash
# Server configuration
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8000
FASTMCP_DEBUG=true
FASTMCP_LOG_LEVEL=DEBUG

# HTTP transport settings
FASTMCP_MOUNT_PATH=/api
FASTMCP_STREAMABLE_HTTP_PATH=/mcp

# Behavior settings
FASTMCP_WARN_ON_DUPLICATE_TOOLS=false
FASTMCP_WARN_ON_DUPLICATE_RESOURCES=false
FASTMCP_WARN_ON_DUPLICATE_PROMPTS=false

# Authentication (when using auth)
FASTMCP_AUTH_ISSUER_URL=https://myserver.com
FASTMCP_AUTH_CLIENT_ID=my-client-id
```

Example usage:
```python
# All settings can be configured via environment variables
mcp = FastMCP("Env Server")  # Will use FASTMCP_* environment variables

# Or override specific settings
mcp = FastMCP("Mixed Server", debug=True)  # debug=True overrides FASTMCP_DEBUG
```

## Performance & Optimization

### How do I optimize my FastMCP server for production?

Key optimization strategies:

```python
import asyncio
from functools import lru_cache
import asyncpg

# 1. Use async tools for I/O operations
@mcp.tool()
async def optimized_database_query(query: str, ctx: Context) -> list[dict]:
    """Async database query with connection pooling."""
    pool = await get_db_pool()  # Reuse connection pool

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

# 2. Implement caching for expensive operations
@lru_cache(maxsize=128)
def expensive_computation(data: str) -> str:
    """Cache expensive computations."""
    # Simulate expensive operation
    import time
    time.sleep(1)
    return f"processed_{data}"

@mcp.tool()
async def cached_tool(data: str, ctx: Context) -> str:
    """Tool with caching."""
    await ctx.info("Using cached computation")
    return expensive_computation(data)

# 3. Process items in batches
@mcp.tool()
async def batch_processor(
    items: list[str],
    batch_size: int = 10,
    ctx: Context
) -> list[str]:
    """Process items in batches for better performance."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        await ctx.info(f"Processing batch {i//batch_size + 1}")

        # Process batch concurrently
        batch_tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks)

        results.extend(batch_results)

        # Report progress
        await ctx.report_progress(
            progress=min(i + batch_size, len(items)) / len(items),
            total=1.0,
            message=f"Processed {min(i + batch_size, len(items))} of {len(items)} items"
        )

    return results

# 4. Use proper timeout and error handling
@mcp.tool()
async def robust_api_call(url: str, timeout: int = 30, ctx: Context) -> dict:
    """API call with timeout and retry logic."""
    import httpx

    for attempt in range(3):  # Retry up to 3 times
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            await ctx.warning(f"Timeout on attempt {attempt + 1}")
            if attempt == 2:  # Last attempt
                raise
        except httpx.HTTPStatusError as e:
            await ctx.error(f"HTTP error {e.response.status_code}")
            raise
```

### How do I handle long-running operations and progress reporting?

Use context progress reporting and proper async patterns:

```python
@mcp.tool()
async def long_data_processing(
    data_source: str,
    processing_options: dict,
    ctx: Context
) -> dict:
    """Long-running data processing with progress updates."""

    # Phase 1: Load data
    await ctx.info("Loading data...")
    await ctx.report_progress(0.1, 1.0, "Loading data")

    data = await load_data(data_source)
    data_size = len(data)

    # Phase 2: Process data
    await ctx.info(f"Processing {data_size} items...")
    processed_items = []

    for i, item in enumerate(data):
        # Update progress every 10 items or every 5%
        if i % 10 == 0 or (i / data_size) % 0.05 == 0:
            progress = 0.1 + (i / data_size) * 0.8  # 10% to 90%
            await ctx.report_progress(
                progress=progress,
                total=1.0,
                message=f"Processing item {i+1} of {data_size}"
            )

        # Process individual item
        processed_item = await process_single_item(item, processing_options)
        processed_items.append(processed_item)

        # Yield control to allow cancellation
        await asyncio.sleep(0)

    # Phase 3: Save results
    await ctx.info("Saving results...")
    await ctx.report_progress(0.95, 1.0, "Saving results")

    result_file = await save_results(processed_items)

    # Complete
    await ctx.report_progress(1.0, 1.0, "Processing complete")
    await ctx.info(f"Processing complete. Results saved to {result_file}")

    return {
        "status": "completed",
        "items_processed": len(processed_items),
        "result_file": result_file,
        "processing_options": processing_options
    }
```

## Debugging & Troubleshooting

### How do I debug my FastMCP server?

Enable debug mode and use comprehensive logging:

```python
# Enable debug mode
mcp = FastMCP(
    "Debug Server",
    debug=True,
    log_level="DEBUG"
)

@mcp.tool()
async def debug_tool(data: dict, ctx: Context) -> dict:
    """Tool with comprehensive debugging."""

    # Debug logging
    await ctx.debug(f"Tool called with data: {data}")
    await ctx.debug(f"Request ID: {ctx.request_id}")
    await ctx.debug(f"Client ID: {ctx.client_id}")

    # Info logging
    await ctx.info("Starting data processing")

    try:
        # Process data
        result = process_complex_data(data)

        await ctx.info("Processing completed successfully")
        await ctx.debug(f"Result keys: {list(result.keys())}")

        return result

    except Exception as e:
        # Error logging with context
        await ctx.error(f"Processing failed: {type(e).__name__}: {e}")

        # In debug mode, log full traceback
        import traceback
        await ctx.debug(f"Traceback: {traceback.format_exc()}")

        raise

# Custom route for debugging
@mcp.custom_route("/debug/info", methods=["GET"])
async def debug_info(request):
    """Debug endpoint showing server state."""
    return JSONResponse({
        "server_name": mcp.name,
        "debug_mode": mcp.settings.debug,
        "log_level": mcp.settings.log_level,
        "tools_count": len(mcp._tool_manager.tools),
        "resources_count": len(mcp._resource_manager.resources)
    })
```

### My tools aren't being discovered. What's wrong?

Common issues and solutions:

```python
# ❌ Wrong: Tool defined after mcp.run()
mcp = FastMCP("My Server")

if __name__ == "__main__":
    mcp.run("stdio")

@mcp.tool()  # This won't work - defined after run()
def late_tool() -> str:
    return "This won't be registered"

# ✅ Correct: Tools defined before mcp.run()
mcp = FastMCP("My Server")

@mcp.tool()
def early_tool() -> str:
    return "This will work"

if __name__ == "__main__":
    mcp.run("stdio")

# ❌ Wrong: Missing type annotations
@mcp.tool()
def bad_tool(x, y):  # No type annotations
    return x + y

# ✅ Correct: Proper type annotations
@mcp.tool()
def good_tool(x: int, y: int) -> int:
    return x + y

# ❌ Wrong: Invalid function signature
@mcp.tool()
def invalid_tool(*args, **kwargs) -> str:  # Can't use *args/**kwargs
    return "Invalid"

# ✅ Correct: Explicit parameters
@mcp.tool()
def valid_tool(a: str, b: int = 10) -> str:
    return f"{a}: {b}"

# Check if tools are registered
print(f"Registered tools: {list(mcp._tool_manager.tools.keys())}")
```

### How do I handle errors gracefully in my tools?

Use structured error handling with context logging:

```python
from mcp.server.fastmcp.exceptions import ValidationError, ToolError

@mcp.tool()
async def robust_tool(
    data: str,
    validate: bool = True,
    ctx: Context
) -> dict:
    """Tool with comprehensive error handling."""

    try:
        await ctx.info(f"Processing data: {data}")

        # Input validation
        if validate and not data.strip():
            raise ValidationError("Data cannot be empty")

        # Simulate processing that might fail
        if data == "error":
            raise ValueError("Simulated processing error")

        if data == "timeout":
            import asyncio
            await asyncio.sleep(100)  # Simulate timeout

        # Success case
        result = {
            "original": data,
            "processed": data.upper(),
            "length": len(data),
            "timestamp": time.time()
        }

        await ctx.info("Processing completed successfully")
        return result

    except ValidationError as e:
        await ctx.error(f"Validation error: {e}")
        raise

    except ValueError as e:
        await ctx.error(f"Processing error: {e}")
        # Could return error response instead of raising
        return {
            "error": "processing_failed",
            "message": str(e),
            "data": data
        }

    except asyncio.TimeoutError:
        await ctx.error("Operation timed out")
        raise ToolError("Processing timed out")

    except Exception as e:
        await ctx.error(f"Unexpected error: {type(e).__name__}: {e}")

        # Log full context in debug mode
        if mcp.settings.debug:
            import traceback
            await ctx.debug(f"Full traceback: {traceback.format_exc()}")

        raise ToolError(f"Tool execution failed: {e}") from e
```

## Advanced Usage

### How do I create a modular server with multiple components?

Organize tools into modules and compose them:

```python
# modules/auth.py
from mcp.server.fastmcp import FastMCP, Context

def add_auth_tools(mcp: FastMCP):
    """Add authentication-related tools."""

    @mcp.tool()
    async def login(username: str, password: str, ctx: Context) -> dict:
        """User login."""
        await ctx.info(f"Login attempt for user: {username}")
        # Implement authentication logic
        return {"token": "auth-token", "user": username}

    @mcp.tool()
    async def logout(token: str, ctx: Context) -> bool:
        """User logout."""
        await ctx.info("User logged out")
        return True

# modules/data.py
def add_data_tools(mcp: FastMCP):
    """Add data management tools."""

    @mcp.tool()
    async def get_user_data(user_id: str, ctx: Context) -> dict:
        """Get user data."""
        await ctx.info(f"Fetching data for user: {user_id}")
        return {"user_id": user_id, "data": "user data"}

    @mcp.resource("user://{user_id}/profile")
    def user_profile(user_id: str) -> dict:
        """User profile resource."""
        return {"user_id": user_id, "profile": "profile data"}

# main.py
from modules.auth import add_auth_tools
from modules.data import add_data_tools

mcp = FastMCP("Modular Server")

# Add modules
add_auth_tools(mcp)
add_data_tools(mcp)

# Add main tools
@mcp.tool()
async def server_status(ctx: Context) -> dict:
    """Get server status."""
    return {
        "status": "running",
        "tools": len(mcp._tool_manager.tools),
        "resources": len(mcp._resource_manager.resources)
    }

if __name__ == "__main__":
    mcp.run("streamable-http")
```

### Can I create custom HTTP routes alongside my MCP server?

Yes, for HTTP transports you can add custom routes:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse
import time

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "server": mcp.name
    })

@mcp.custom_route("/api/stats", methods=["GET"])
async def server_stats(request: Request) -> JSONResponse:
    """Server statistics API."""
    return JSONResponse({
        "tools": len(mcp._tool_manager.tools),
        "resources": len(mcp._resource_manager.resources),
        "uptime": time.time() - start_time
    })

@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_file(request: Request) -> FileResponse:
    """File download endpoint."""
    filename = request.path_params["filename"]
    file_path = f"/downloads/{filename}"

    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(file_path, filename=filename)

@mcp.custom_route("/webhook", methods=["POST"])
async def webhook_handler(request: Request) -> JSONResponse:
    """Webhook endpoint for external integrations."""
    try:
        payload = await request.json()

        # Process webhook
        event_type = payload.get("type")
        if event_type == "user_update":
            await handle_user_update(payload["data"])

        return JSONResponse({"status": "processed"})

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400
        )
```

## Deployment & Production

### How do I deploy my FastMCP server to production?

Use containers and proper configuration management:

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000
ENV FASTMCP_LOG_LEVEL=INFO
ENV FASTMCP_DEBUG=false

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "server.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  fastmcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTMCP_HOST=0.0.0.0
      - FASTMCP_PORT=8000
      - FASTMCP_LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Production server setup:**
```python
import os
import logging
from mcp.server.fastmcp import FastMCP, Context

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Production configuration
mcp = FastMCP(
    "Production Server",
    host=os.getenv("FASTMCP_HOST", "0.0.0.0"),
    port=int(os.getenv("FASTMCP_PORT", "8000")),
    debug=os.getenv("FASTMCP_DEBUG", "false").lower() == "true",
    log_level=os.getenv("FASTMCP_LOG_LEVEL", "INFO")
)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Production health check."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "version": os.getenv("APP_VERSION", "unknown")
    })

# Ready check endpoint
@mcp.custom_route("/ready", methods=["GET"])
async def readiness_check(request):
    """Readiness probe for Kubernetes."""
    try:
        # Check database connection
        await check_database_connection()

        # Check other dependencies
        await check_external_services()

        return JSONResponse({"status": "ready"})
    except Exception as e:
        return JSONResponse(
            {"status": "not ready", "error": str(e)},
            status_code=503
        )

if __name__ == "__main__":
    mcp.run("streamable-http")
```

This comprehensive FAQ covers the most common questions and scenarios developers encounter when building FastMCP servers, providing practical solutions and best practices for each area.
