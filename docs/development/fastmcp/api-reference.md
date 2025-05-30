# API Reference

Complete reference for all FastMCP classes, methods, and utilities.

## Core Classes

### FastMCP

The main server class for creating MCP servers.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="My Server",
    instructions="Optional server instructions",
    debug=True,
    log_level="INFO"
)
```

#### Constructor Parameters

- **name** (`str | None`): Server name (defaults to "FastMCP")
- **instructions** (`str | None`): Optional instructions for clients
- **auth_server_provider** (`OAuthAuthorizationServerProvider | None`): OAuth provider for authentication
- **event_store** (`EventStore | None`): Event store for StreamableHTTP sessions
- **tools** (`list[Tool] | None`): Pre-defined tools to register
- **settings**: Additional settings passed as keyword arguments

#### Configuration Settings

All settings can be configured via environment variables with `FASTMCP_` prefix:

```python
# Python configuration
mcp = FastMCP(
    debug=True,
    log_level="DEBUG",
    host="0.0.0.0",
    port=8080,
    warn_on_duplicate_tools=False
)

# Environment variable configuration
# FASTMCP_DEBUG=true
# FASTMCP_LOG_LEVEL=DEBUG
# FASTMCP_HOST=0.0.0.0
# FASTMCP_PORT=8080
```

**Server Settings:**
- `debug` (`bool`): Enable debug mode (default: `False`)
- `log_level` (`str`): Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `"INFO"`)

**HTTP Settings:**
- `host` (`str`): Server host (default: `"127.0.0.1"`)
- `port` (`int`): Server port (default: `8000`)
- `mount_path` (`str`): Mount path for routes (default: `"/"`)
- `sse_path` (`str`): SSE endpoint path (default: `"/sse"`)
- `message_path` (`str`): Message endpoint path (default: `"/messages/"`)
- `streamable_http_path` (`str`): StreamableHTTP path (default: `"/mcp"`)

**StreamableHTTP Settings:**
- `json_response` (`bool`): Use JSON responses (default: `False`)
- `stateless_http` (`bool`): Use stateless mode (default: `False`)

**Warning Settings:**
- `warn_on_duplicate_resources` (`bool`): Warn on duplicate resources (default: `True`)
- `warn_on_duplicate_tools` (`bool`): Warn on duplicate tools (default: `True`)
- `warn_on_duplicate_prompts` (`bool`): Warn on duplicate prompts (default: `True`)

**Advanced Settings:**
- `dependencies` (`list[str]`): List of dependencies to install
- `lifespan` (`Callable`): Custom lifespan context manager
- `auth` (`AuthSettings | None`): Authentication configuration

#### Properties

**`name`** (`str`): Server name
```python
print(mcp.name)  # "My Server"
```

**`instructions`** (`str | None`): Server instructions
```python
print(mcp.instructions)  # "Optional server instructions"
```

**`session_manager`** (`StreamableHTTPSessionManager`): Session manager for StreamableHTTP
```python
# Only available after calling streamable_http_app()
manager = mcp.session_manager
```

#### Running the Server

**`run(transport, mount_path=None)`**: Run the server synchronously
```python
# Run with stdio (most common for MCP)
mcp.run("stdio")

# Run with SSE transport
mcp.run("sse")

# Run with StreamableHTTP transport
mcp.run("streamable-http")
```

**Async methods:**
- `run_stdio_async()`: Run with stdio transport
- `run_sse_async(mount_path=None)`: Run with SSE transport
- `run_streamable_http_async()`: Run with StreamableHTTP transport

#### Tool Management

**`@tool(name=None, description=None, annotations=None)`**: Decorator to register tools
```python
@mcp.tool()
def simple_tool(x: int) -> str:
    """Convert number to string."""
    return str(x)

@mcp.tool(name="custom_name", description="Custom description")
def named_tool(x: int) -> str:
    return str(x)
```

**`add_tool(fn, name=None, description=None, annotations=None)`**: Programmatically register tools
```python
def my_function(x: int) -> str:
    return str(x)

mcp.add_tool(my_function, name="convert", description="Convert to string")
```

#### Resource Management

**`@resource(uri, name=None, description=None, mime_type=None)`**: Decorator to register resources
```python
@mcp.resource("data://example")
def get_data() -> str:
    """Static resource."""
    return "Hello World"

@mcp.resource("data://{param}")
def get_dynamic_data(param: str) -> str:
    """Template resource with parameter."""
    return f"Data for {param}"
```

**`add_resource(resource)`**: Add a Resource instance
```python
from mcp.server.fastmcp.resources import FunctionResource

resource = FunctionResource.from_function(
    fn=get_data,
    uri="data://example",
    name="Example Data"
)
mcp.add_resource(resource)
```

#### Prompt Management

**`@prompt(name=None, description=None)`**: Decorator to register prompts
```python
@mcp.prompt()
def analyze_data(table_name: str) -> list[Message]:
    """Generate analysis prompt."""
    return [
        UserMessage(f"Analyze table: {table_name}")
    ]
```

**`add_prompt(prompt)`**: Add a Prompt instance
```python
from mcp.server.fastmcp.prompts import Prompt

prompt = Prompt.from_function(analyze_data, name="analyzer")
mcp.add_prompt(prompt)
```

#### Custom Routes

**`@custom_route(path, methods, name=None, include_in_schema=True)`**: Register custom HTTP endpoints
```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})

@mcp.custom_route("/oauth/callback", methods=["POST"])
async def oauth_callback(request: Request) -> JSONResponse:
    # Handle OAuth callback
    return JSONResponse({"success": True})
```

#### App Generation

**`sse_app(mount_path=None)`**: Get Starlette app for SSE transport
```python
app = mcp.sse_app()
# Can be used with ASGI servers like uvicorn directly
```

**`streamable_http_app()`**: Get Starlette app for StreamableHTTP transport
```python
app = mcp.streamable_http_app()
# Can be mounted in larger applications
```

#### Protocol Handlers

Internal methods (typically not called directly):

- `list_tools()`: List available tools
- `call_tool(name, arguments)`: Call a tool
- `list_resources()`: List available resources
- `read_resource(uri)`: Read a resource
- `list_prompts()`: List available prompts
- `get_prompt(name, arguments)`: Get a prompt
- `list_resource_templates()`: List resource templates

### Context

Context object providing access to MCP capabilities within tools and resources.

```python
from mcp.server.fastmcp import Context

@mcp.tool()
def my_tool(x: int, ctx: Context) -> str:
    # Context is automatically injected
    ctx.info(f"Processing {x}")
    return str(x)
```

#### Logging Methods

**`log(level, message, logger_name=None)`**: Send log message to client
```python
await ctx.log("info", "Processing data")
await ctx.log("error", "Something went wrong", logger_name="my_tool")
```

**Convenience methods:**
```python
await ctx.debug("Debug message")
await ctx.info("Info message")
await ctx.warning("Warning message")
await ctx.error("Error message")
```

#### Progress Reporting

**`report_progress(progress, total=None, message=None)`**: Report operation progress
```python
await ctx.report_progress(50, 100, "Halfway done")
await ctx.report_progress(75, 100)  # No message
await ctx.report_progress(25)  # No total
```

#### Resource Access

**`read_resource(uri)`**: Read a resource from within a tool
```python
content = await ctx.read_resource("file://data.txt")
for item in content:
    print(item.content, item.mime_type)
```

#### Properties

**`request_id`** (`str`): Unique request identifier
```python
request_id = ctx.request_id
```

**`client_id`** (`str | None`): Client identifier (if available)
```python
if ctx.client_id:
    print(f"Request from client: {ctx.client_id}")
```

**`session`**: Access to underlying session (advanced usage)
```python
session = ctx.session
```

**`fastmcp`** (`FastMCP`): Access to the FastMCP server instance
```python
server = ctx.fastmcp
```

## Tool Components

### Tool

Internal tool registration class (typically not used directly).

```python
from mcp.server.fastmcp.tools import Tool

tool = Tool.from_function(
    fn=my_function,
    name="custom_name",
    description="Tool description",
    annotations={"dangerous": True}
)
```

#### Properties

- `name` (`str`): Tool name
- `description` (`str`): Tool description
- `parameters` (`dict`): JSON schema for parameters
- `fn_metadata` (`FuncMetadata`): Function metadata
- `is_async` (`bool`): Whether tool is async
- `context_kwarg` (`str | None`): Context parameter name
- `annotations` (`ToolAnnotations | None`): Tool annotations

#### Methods

**`run(arguments, context=None)`**: Execute the tool
```python
result = await tool.run({"x": 5}, context=ctx)
```

## Resource Components

### Resource

Base class for all resources.

```python
from mcp.server.fastmcp.resources import Resource

class CustomResource(Resource):
    async def read(self) -> str | bytes:
        return "Custom content"

resource = CustomResource(
    uri="custom://example",
    name="Example",
    description="Custom resource",
    mime_type="text/plain"
)
```

#### Properties

- `uri` (`AnyUrl`): Resource URI
- `name` (`str`): Resource name
- `description` (`str | None`): Resource description
- `mime_type` (`str`): MIME type (default: "text/plain")

#### Methods

**`read()`**: Abstract method to read resource content
```python
content = await resource.read()  # Returns str or bytes
```

### FunctionResource

Resource implementation using a function.

```python
from mcp.server.fastmcp.resources import FunctionResource

def get_data() -> str:
    return "Hello World"

resource = FunctionResource.from_function(
    fn=get_data,
    uri="data://example",
    name="Example Data",
    description="Example resource",
    mime_type="text/plain"
)
```

## Prompt Components

### Prompt

Prompt template class.

```python
from mcp.server.fastmcp.prompts import Prompt

def create_prompt(topic: str) -> list[Message]:
    return [UserMessage(f"Tell me about {topic}")]

prompt = Prompt.from_function(
    fn=create_prompt,
    name="topic_prompt",
    description="Generate topic prompt"
)
```

#### Properties

- `name` (`str`): Prompt name
- `description` (`str | None`): Prompt description
- `arguments` (`list[PromptArgument] | None`): Available arguments

#### Methods

**`render(arguments=None)`**: Render prompt with arguments
```python
messages = await prompt.render({"topic": "Python"})
```

### Message Classes

Message types for prompt responses.

```python
from mcp.server.fastmcp.prompts import Message, UserMessage, AssistantMessage

# Create messages
user_msg = UserMessage("Hello")
assistant_msg = AssistantMessage("Hi there!")

# Generic message
msg = Message(role="user", content="Hello")
```

### PromptArgument

Represents a prompt argument.

```python
from mcp.server.fastmcp.prompts import PromptArgument

arg = PromptArgument(
    name="topic",
    description="Topic to discuss",
    required=True
)
```

## Utility Types

### Image

Utility class for handling images in tools.

```python
from mcp.server.fastmcp import Image

@mcp.tool()
def process_image(image_path: str) -> Image:
    """Return an image."""
    return Image.from_path(image_path)

@mcp.tool()
def create_image() -> Image:
    """Create image from bytes."""
    image_data = b"..."  # Your image bytes
    return Image.from_bytes(image_data, "image/png")
```

#### Class Methods

**`from_path(path)`**: Create image from file path
```python
image = Image.from_path("/path/to/image.png")
```

**`from_bytes(data, mime_type)`**: Create image from bytes
```python
image = Image.from_bytes(image_bytes, "image/jpeg")
```

#### Methods

**`to_image_content()`**: Convert to ImageContent for MCP
```python
content = image.to_image_content()
```

## Exception Classes

### ResourceError

Raised when resource operations fail.

```python
from mcp.server.fastmcp.exceptions import ResourceError

raise ResourceError("Could not read resource")
```

### ToolError

Raised when tool execution fails.

```python
from mcp.server.fastmcp.exceptions import ToolError

raise ToolError("Tool execution failed")
```

## Type Annotations

### ToolAnnotations

Optional annotations for tools providing additional metadata.

```python
from mcp.types import ToolAnnotations

@mcp.tool(annotations=ToolAnnotations(dangerous=True))
def dangerous_tool() -> str:
    """A dangerous operation."""
    return "Done"
```

## Advanced Usage

### Custom Lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def custom_lifespan(app: FastMCP):
    # Startup
    print("Server starting...")
    yield
    # Shutdown
    print("Server stopping...")

mcp = FastMCP("My Server", lifespan=custom_lifespan)
```

### Authentication Setup

```python
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings

# Set up OAuth provider
provider = OAuthAuthorizationServerProvider(...)

# Configure auth settings
auth_settings = AuthSettings(
    issuer_url="https://example.com",
    required_scopes=["read", "write"]
)

mcp = FastMCP(
    "Secure Server",
    auth_server_provider=provider,
    auth=auth_settings
)
```

### Session Management

```python
# For StreamableHTTP
mcp = FastMCP("My Server")
app = mcp.streamable_http_app()

# Access session manager after app creation
manager = mcp.session_manager
```

### Integration with FastAPI

```python
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Create FastMCP server
mcp = FastMCP("My Server")

@mcp.tool()
def example_tool() -> str:
    return "Hello"

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Mount FastMCP
fastmcp_app = mcp.streamable_http_app()
app.mount("/mcp", fastmcp_app)

# Add other FastAPI routes
@app.get("/health")
def health():
    return {"status": "ok"}
```

This reference covers all public APIs in FastMCP. For implementation details, see the [Examples](examples.md) and other topic-specific documentation.
