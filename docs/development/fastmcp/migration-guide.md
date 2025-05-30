# Migration Guide

Complete guide for migrating from the raw MCP SDK to FastMCP, including step-by-step migration examples, feature comparisons, and best practices.

## Overview

FastMCP provides a high-level, decorator-based API that significantly simplifies MCP server development compared to the raw MCP SDK. This guide helps you migrate existing servers to take advantage of FastMCP's ergonomic features.

### Key Benefits of Migration

- **Simpler API**: Decorator-based tool, resource, and prompt registration
- **Automatic Type Validation**: Built-in Pydantic validation
- **Context Injection**: Easy access to MCP capabilities via Context object
- **Better Error Handling**: Automatic error wrapping and reporting
- **Reduced Boilerplate**: Less code required for common patterns
- **Enhanced Development Experience**: Better debugging, testing, and monitoring

## Migration Process

### 1. Dependency Updates

**Update your `pyproject.toml`:**
```toml
# Before (raw MCP SDK)
dependencies = ["mcp"]

# After (FastMCP)
dependencies = ["mcp"]  # Same package, FastMCP is included
```

**Import changes:**
```python
# Before (raw MCP SDK)
from mcp.server.lowlevel import Server
import mcp.types as types
from mcp.server.stdio import stdio_server

# After (FastMCP)
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts.base import UserMessage, AssistantMessage
# Note: mcp.types still available for compatibility
```

### 2. Server Initialization

**Before (Raw MCP SDK):**
```python
import anyio
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

def main():
    app = Server("my-mcp-server")

    # Register handlers (shown below)

    async def arun():
        async with stdio_server() as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options()
            )

    anyio.run(arun)

if __name__ == "__main__":
    main()
```

**After (FastMCP):**
```python
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("my-mcp-server")

# Register handlers with decorators (shown below)

if __name__ == "__main__":
    mcp.run("stdio")  # Much simpler!
```

## Tool Migration

### Simple Tools

**Before (Raw MCP SDK):**
```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="add_numbers",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "required": ["a", "b"],
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "add_numbers":
        if "a" not in arguments or "b" not in arguments:
            raise ValueError("Missing required arguments")

        try:
            a = float(arguments["a"])
            b = float(arguments["b"])
            result = a + b
            return [types.TextContent(type="text", text=str(result))]
        except (ValueError, TypeError):
            raise ValueError("Arguments must be numbers")

    raise ValueError(f"Unknown tool: {name}")
```

**After (FastMCP):**
```python
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

# That's it! FastMCP handles:
# - Schema generation from type hints
# - Input validation
# - Error handling
# - Return value conversion
```

### Tools with Context

**Before (Raw MCP SDK):**
```python
from mcp.shared.context import RequestContext

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "logged_operation":
        # Manual context access (complex)
        request_ctx = app.request_context

        # Manual logging to client
        await request_ctx.session.send_log_message(
            level="info",
            data="Processing operation",
            related_request_id=request_ctx.request_id
        )

        result = process_data(arguments.get("data", ""))
        return [types.TextContent(type="text", text=result)]
```

**After (FastMCP):**
```python
@mcp.tool()
async def logged_operation(data: str, ctx: Context) -> str:
    """Operation with logging."""
    await ctx.info("Processing operation")
    result = process_data(data)
    return result

# FastMCP automatically:
# - Injects Context object
# - Handles logging to client
# - Manages request context
```

### Complex Tools with Validation

**Before (Raw MCP SDK):**
```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_user",
            description="Create a new user",
            inputSchema={
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "age": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 150
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "create_user":
        # Manual validation
        if not arguments.get("name") or len(arguments["name"]) > 100:
            raise ValueError("Invalid name")

        # Manual email validation
        email = arguments.get("email", "")
        if "@" not in email:
            raise ValueError("Invalid email")

        # Create user logic
        user = create_user(arguments["name"], email, arguments.get("age"))
        return [types.TextContent(type="text", text=f"Created user: {user.id}")]
```

**After (FastMCP):**
```python
from pydantic import BaseModel, Field, EmailStr

class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int | None = Field(None, ge=0, le=150)

@mcp.tool()
def create_user(user_data: UserInput) -> str:
    """Create a new user with validation."""
    user = create_user(user_data.name, user_data.email, user_data.age)
    return f"Created user: {user.id}"

# FastMCP automatically:
# - Generates JSON schema from Pydantic model
# - Validates all inputs
# - Provides helpful error messages
```

## Resource Migration

### Static Resources

**Before (Raw MCP SDK):**
```python
from pydantic import AnyUrl

SAMPLE_RESOURCES = {
    "greeting": "Hello! This is a sample resource.",
    "help": "Help documentation here.",
}

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=AnyUrl(f"file:///{name}.txt"),
            name=name,
            description=f"A sample text resource named {name}",
            mimeType="text/plain",
        )
        for name in SAMPLE_RESOURCES.keys()
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str | bytes:
    if uri.path is None:
        raise ValueError(f"Invalid resource path: {uri}")
    name = uri.path.replace(".txt", "").lstrip("/")

    if name not in SAMPLE_RESOURCES:
        raise ValueError(f"Unknown resource: {uri}")

    return SAMPLE_RESOURCES[name]
```

**After (FastMCP):**
```python
SAMPLE_RESOURCES = {
    "greeting": "Hello! This is a sample resource.",
    "help": "Help documentation here.",
}

@mcp.resource("file:///greeting.txt")
def greeting_resource() -> str:
    """Sample greeting resource."""
    return SAMPLE_RESOURCES["greeting"]

@mcp.resource("file:///help.txt")
def help_resource() -> str:
    """Help documentation resource."""
    return SAMPLE_RESOURCES["help"]

# FastMCP handles:
# - Resource registration and listing
# - URI matching
# - Error handling
```

### Template Resources

**Before (Raw MCP SDK):**
```python
@app.list_resource_templates()
async def list_resource_templates() -> list[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            uriTemplate="file:///{name}.txt",
            name="Dynamic file resource",
            description="Access files by name"
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str | bytes:
    # Manual template parameter extraction
    if uri.path is None:
        raise ValueError("Invalid URI path")

    name = uri.path.replace(".txt", "").lstrip("/")

    # Manual parameter validation
    if not name or ".." in name or "/" in name:
        raise ValueError("Invalid file name")

    return load_file_content(name)
```

**After (FastMCP):**
```python
@mcp.resource("file:///{name}.txt")
def dynamic_file_resource(name: str) -> str:
    """Access files by name."""
    # FastMCP validates parameters automatically
    return load_file_content(name)

# FastMCP automatically:
# - Extracts template parameters
# - Validates parameter types
# - Handles template registration
```

## Prompt Migration

**Before (Raw MCP SDK):**
```python
@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="analyze_data",
            description="Generate data analysis prompt",
            arguments=[
                types.PromptArgument(
                    name="dataset",
                    description="Dataset to analyze",
                    required=True
                ),
                types.PromptArgument(
                    name="focus",
                    description="Analysis focus area",
                    required=False
                )
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name != "analyze_data":
        raise ValueError(f"Unknown prompt: {name}")

    if not arguments or "dataset" not in arguments:
        raise ValueError("Missing required argument: dataset")

    dataset = arguments["dataset"]
    focus = arguments.get("focus", "general trends")

    messages = [
        types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=f"Analyze the {dataset} dataset, focusing on {focus}"
            )
        )
    ]

    return types.GetPromptResult(
        messages=messages,
        description="Data analysis prompt"
    )
```

**After (FastMCP):**
```python
from mcp.server.fastmcp.prompts.base import UserMessage

@mcp.prompt()
def analyze_data(dataset: str, focus: str = "general trends") -> list[UserMessage]:
    """Generate data analysis prompt."""
    return [
        UserMessage(f"Analyze the {dataset} dataset, focusing on {focus}")
    ]

# FastMCP automatically:
# - Generates argument schema from function signature
# - Validates required/optional parameters
# - Handles prompt registration and rendering
```

## Transport Migration

### Stdio Transport

**Before (Raw MCP SDK):**
```python
import anyio
from mcp.server.stdio import stdio_server

async def arun():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

anyio.run(arun)
```

**After (FastMCP):**
```python
mcp.run("stdio")  # That's it!
```

### HTTP Transports

**Before (Raw MCP SDK):**
```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
import uvicorn

sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )
    return Response()

starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

uvicorn.run(starlette_app, host="127.0.0.1", port=8000)
```

**After (FastMCP):**
```python
mcp.run("sse")  # Or "streamable-http"
```

## Advanced Migration Patterns

### Error Handling

**Before (Raw MCP SDK):**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "risky_operation":
            result = perform_risky_operation(arguments.get("data"))
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        # Manual error handling and logging
        logger.error(f"Tool {name} failed: {e}")
        raise  # Re-raise for client
```

**After (FastMCP):**
```python
@mcp.tool()
async def risky_operation(data: str, ctx: Context) -> str:
    """Operation with automatic error handling."""
    try:
        result = perform_risky_operation(data)
        await ctx.info("Operation completed successfully")
        return result
    except Exception as e:
        await ctx.error(f"Operation failed: {e}")
        raise  # FastMCP handles error formatting for client

# FastMCP automatically:
# - Wraps exceptions appropriately
# - Provides context for logging
# - Formats errors for client
```

### Custom HTTP Routes

**Before (Raw MCP SDK):**
```python
from starlette.routing import Route
from starlette.responses import JSONResponse

async def health_check(request):
    return JSONResponse({"status": "healthy"})

# Manual route setup in Starlette app
additional_routes = [Route("/health", endpoint=health_check)]
```

**After (FastMCP):**
```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy"})

# FastMCP automatically integrates custom routes
```

### Lifespan Management

**Before (Raw MCP SDK):**
```python
# Complex manual setup required
import asyncio
from contextlib import asynccontextmanager

database_pool = None

async def initialize():
    global database_pool
    database_pool = await create_database_pool()

async def cleanup():
    global database_pool
    if database_pool:
        await database_pool.close()

# Manual lifecycle management in main()
```

**After (FastMCP):**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastMCP):
    """Manage application lifecycle."""
    # Startup
    database_pool = await create_database_pool()
    app.database_pool = database_pool

    try:
        yield
    finally:
        # Cleanup
        await database_pool.close()

mcp = FastMCP("My Server", lifespan=lifespan)

@mcp.tool()
async def database_tool(query: str, ctx: Context) -> str:
    """Tool that uses managed database connection."""
    pool = ctx.fastmcp.database_pool
    async with pool.acquire() as conn:
        result = await conn.fetchval(query)
        return str(result)
```

## Complete Migration Example

Here's a complete before/after example showing a full server migration:

### Before (Raw MCP SDK)

```python
import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared._httpx_utils import create_mcp_http_client

# Data storage
USERS = {}
user_counter = 0

async def fetch_weather(city: str) -> str:
    """Fetch weather data for a city."""
    async with create_mcp_http_client() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        response.raise_for_status()
        return response.json()["temperature"]

@click.command()
def main():
    app = Server("user-weather-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="create_user",
                description="Create a new user",
                inputSchema={
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            ),
            types.Tool(
                name="get_weather",
                description="Get weather for a city",
                inputSchema={
                    "type": "object",
                    "required": ["city"],
                    "properties": {
                        "city": {"type": "string"}
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        global user_counter

        if name == "create_user":
            if "name" not in arguments or "email" not in arguments:
                raise ValueError("Missing required arguments")

            user_counter += 1
            user_id = user_counter
            USERS[user_id] = {
                "name": arguments["name"],
                "email": arguments["email"]
            }

            return [types.TextContent(
                type="text",
                text=f"Created user {user_id}: {arguments['name']}"
            )]

        elif name == "get_weather":
            if "city" not in arguments:
                raise ValueError("Missing city argument")

            try:
                temp = await fetch_weather(arguments["city"])
                return [types.TextContent(
                    type="text",
                    text=f"Temperature in {arguments['city']}: {temp}°C"
                )]
            except Exception as e:
                raise ValueError(f"Failed to fetch weather: {e}")

        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=f"users://user/{user_id}",
                name=f"User {user_id}",
                description=f"User data for {data['name']}",
                mimeType="application/json"
            )
            for user_id, data in USERS.items()
        ]

    @app.read_resource()
    async def read_resource(uri: str) -> str:
        if not uri.startswith("users://user/"):
            raise ValueError("Invalid URI")

        user_id = int(uri.split("/")[-1])
        if user_id not in USERS:
            raise ValueError("User not found")

        import json
        return json.dumps(USERS[user_id])

    async def arun():
        async with stdio_server() as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options()
            )

    anyio.run(arun)

if __name__ == "__main__":
    main()
```

### After (FastMCP)

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared._httpx_utils import create_mcp_http_client
from pydantic import BaseModel, EmailStr

# Create server
mcp = FastMCP("user-weather-server")

# Data storage
USERS = {}
user_counter = 0

# Pydantic models for validation
class UserInput(BaseModel):
    name: str
    email: EmailStr

@mcp.tool()
async def create_user(user_data: UserInput, ctx: Context) -> str:
    """Create a new user with validation."""
    global user_counter

    user_counter += 1
    user_id = user_counter

    USERS[user_id] = {
        "name": user_data.name,
        "email": user_data.email
    }

    await ctx.info(f"Created user {user_id}")
    return f"Created user {user_id}: {user_data.name}"

@mcp.tool()
async def get_weather(city: str, ctx: Context) -> str:
    """Get weather for a city."""
    await ctx.info(f"Fetching weather for {city}")

    try:
        async with create_mcp_http_client() as client:
            response = await client.get(f"https://api.weather.com/{city}")
            response.raise_for_status()
            temp = response.json()["temperature"]

        await ctx.info("Weather data retrieved successfully")
        return f"Temperature in {city}: {temp}°C"

    except Exception as e:
        await ctx.error(f"Failed to fetch weather: {e}")
        raise

@mcp.resource("users://user/{user_id}")
def get_user(user_id: int) -> dict:
    """Get user data by ID."""
    if user_id not in USERS:
        raise ValueError("User not found")

    return USERS[user_id]

if __name__ == "__main__":
    mcp.run("stdio")
```

## Migration Checklist

### Pre-Migration

- [ ] **Audit current server**: List all tools, resources, and prompts
- [ ] **Review error handling**: Note custom error handling patterns
- [ ] **Check dependencies**: Identify external libraries and integrations
- [ ] **Document custom features**: Note any custom transport or middleware

### During Migration

- [ ] **Update imports**: Switch to FastMCP imports
- [ ] **Convert server creation**: Replace Server with FastMCP
- [ ] **Migrate tools**: Convert to decorator-based registration
- [ ] **Migrate resources**: Use @resource decorator
- [ ] **Migrate prompts**: Use @prompt decorator
- [ ] **Add type hints**: Enable automatic validation
- [ ] **Update transport**: Simplify transport setup
- [ ] **Add context usage**: Leverage Context for logging and progress

### Post-Migration Testing

- [ ] **Test all tools**: Verify functionality and validation
- [ ] **Test all resources**: Check URI resolution and content
- [ ] **Test all prompts**: Verify argument handling
- [ ] **Test error cases**: Ensure proper error handling
- [ ] **Test transports**: Verify stdio and HTTP transports work
- [ ] **Performance testing**: Compare performance (should be similar or better)

### Validation

- [ ] **Code reduction**: Confirm significant reduction in boilerplate
- [ ] **Type safety**: Verify automatic validation works
- [ ] **Error handling**: Check improved error messages
- [ ] **Development experience**: Confirm easier debugging and testing

## Common Migration Issues

### 1. Type Annotation Requirements

**Issue**: FastMCP requires type annotations for automatic validation.

```python
# ❌ Won't work - no type annotations
@mcp.tool()
def bad_tool(x, y):
    return x + y

# ✅ Works - proper type annotations
@mcp.tool()
def good_tool(x: int, y: int) -> int:
    return x + y
```

### 2. Context Parameter Detection

**Issue**: Context must be properly typed to be detected.

```python
# ❌ Won't be detected as context
@mcp.tool()
def bad_context_tool(x: int, ctx) -> str:
    return str(x)

# ✅ Properly detected
@mcp.tool()
def good_context_tool(x: int, ctx: Context) -> str:
    return str(x)
```

### 3. Resource URI Template Matching

**Issue**: Template parameters must match function parameters exactly.

```python
# ❌ Parameter name mismatch
@mcp.resource("data://{user_id}")
def bad_resource(id: str) -> str:  # 'id' != 'user_id'
    return f"User {id}"

# ✅ Parameter names match
@mcp.resource("data://{user_id}")
def good_resource(user_id: str) -> str:
    return f"User {user_id}"
```

This migration guide provides everything needed to successfully transition from the raw MCP SDK to FastMCP's more ergonomic approach.
