# Development Workflow

Complete guide for developing FastMCP servers locally, including setup, testing, debugging, and deployment.

## Quick Start

### 1. Environment Setup

**Python Version:** FastMCP requires Python 3.10 or later.

**Package Manager:** Use `uv` exclusively (never pip):
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init my-mcp-server
cd my-mcp-server

# Add FastMCP dependency
uv add mcp
```

### 2. Project Structure

Create a well-organized project structure:
```
my-mcp-server/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── tools/           # Tool implementations
│       ├── resources/       # Resource handlers
│       └── prompts/         # Prompt templates
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   ├── test_resources.py
│   └── test_integration.py
└── examples/
    └── client_examples.py
```

### 3. Basic Server Template

Create `src/my_mcp_server/main.py`:
```python
"""My MCP Server - A FastMCP server implementation."""

from mcp.server.fastmcp import FastMCP, Context

# Create server with descriptive name and instructions
mcp = FastMCP(
    name="My MCP Server",
    instructions="A helpful server that provides X, Y, and Z capabilities"
)

@mcp.tool()
def example_tool(input_text: str, ctx: Context) -> str:
    """Example tool with logging and error handling."""
    ctx.info(f"Processing: {input_text}")

    try:
        result = input_text.upper()
        ctx.info(f"Result: {result}")
        return result
    except Exception as e:
        ctx.error(f"Tool failed: {e}")
        raise

@mcp.resource("data://example")
def example_resource() -> str:
    """Example static resource."""
    return "Hello from my MCP server!"

@mcp.prompt()
def example_prompt(topic: str) -> str:
    """Generate a prompt about a topic."""
    return f"Please explain {topic} in simple terms."

if __name__ == "__main__":
    # Run with stdio transport for MCP clients
    mcp.run("stdio")
```

## Development Workflow

### 1. Local Development Setup

**Install development dependencies:**
```bash
# Add development tools
uv add --dev pytest pytest-anyio pytest-examples
uv add --dev ruff pyright
uv add --dev uvicorn  # For HTTP transport testing
```

**Configure your `pyproject.toml`:**
```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "My FastMCP server"
requires-python = ">=3.10"
dependencies = ["mcp"]

[project.scripts]
my-mcp-server = "my_mcp_server.main:main"

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pyright]
venvPath = "."
venv = ".venv"
include = ["src", "tests"]
```

### 2. Code Quality Setup

**Install pre-commit hooks:**
```bash
uv add --dev pre-commit
uv run pre-commit install
```

**Create `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: Ruff Format
        entry: uv run ruff format
        language: system
        types: [python]
        pass_filenames: false
      - id: ruff-check
        name: Ruff Check
        entry: uv run ruff check --fix
        language: system
        types: [python]
        pass_filenames: false
      - id: pyright
        name: Type Check
        entry: uv run pyright
        language: system
        types: [python]
        pass_filenames: false
```

### 3. Development Loop

**Daily development workflow:**
```bash
# 1. Code formatting (run frequently)
uv run ruff format .

# 2. Linting and auto-fixes
uv run ruff check . --fix

# 3. Type checking
uv run pyright

# 4. Run tests
uv run pytest

# 5. Test your server manually
uv run python -m my_mcp_server.main
```

## Testing

### 1. Unit Testing Setup

**Basic test structure** (`tests/test_tools.py`):
```python
import pytest
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.memory import create_connected_server_and_client_session

@pytest.mark.anyio
async def test_example_tool():
    """Test tool functionality."""
    mcp = FastMCP("Test Server")

    @mcp.tool()
    def test_tool(x: int) -> int:
        return x * 2

    # Test with connected session
    async with create_connected_server_and_client_session(mcp._mcp_server) as (
        server_session,
        client_session,
    ):
        # Call tool through client
        result = await client_session.call_tool("test_tool", {"x": 5})
        assert result.content[0].text == "10"
```

**Testing with context** (`tests/test_context.py`):
```python
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP, Context

@pytest.mark.anyio
async def test_tool_with_context():
    """Test tool that uses context."""
    mcp = FastMCP("Test Server")

    @mcp.tool()
    async def context_tool(message: str, ctx: Context) -> str:
        await ctx.info(f"Processing: {message}")
        return f"Processed: {message}"

    # Create mock context
    mock_context = AsyncMock(spec=Context)

    # Test tool directly
    tool = mcp._tool_manager._tools["context_tool"]
    result = await tool.run({"message": "test"}, context=mock_context)

    assert result == "Processed: test"
    mock_context.info.assert_called_once_with("Processing: test")
```

**Resource testing** (`tests/test_resources.py`):
```python
import pytest
from mcp.server.fastmcp import FastMCP

@pytest.mark.anyio
async def test_static_resource():
    """Test static resource."""
    mcp = FastMCP("Test Server")

    @mcp.resource("data://test")
    def test_resource() -> str:
        return "test data"

    # Test resource reading
    content = await mcp.read_resource("data://test")
    assert content[0].content == "test data"

@pytest.mark.anyio
async def test_template_resource():
    """Test template resource."""
    mcp = FastMCP("Test Server")

    @mcp.resource("data://{param}")
    def template_resource(param: str) -> str:
        return f"data for {param}"

    # Test with parameter
    content = await mcp.read_resource("data://example")
    assert content[0].content == "data for example"
```

### 2. Integration Testing

**HTTP transport testing:**
```python
import pytest
import httpx
from mcp.server.fastmcp import FastMCP

@pytest.mark.anyio
async def test_sse_server():
    """Test SSE transport integration."""
    mcp = FastMCP("Test Server", port=8001)

    @mcp.tool()
    def test_tool() -> str:
        return "success"

    # Start server in background
    import asyncio
    server_task = asyncio.create_task(mcp.run_sse_async())

    try:
        # Wait for server to start
        await asyncio.sleep(0.1)

        # Test health endpoint (if you add one)
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200
    finally:
        server_task.cancel()
```

### 3. Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools.py

# Run with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto

# Debug failing tests
uv run pytest -s --tb=long
```

## Debugging

### 1. Local Debugging

**Enable debug mode:**
```python
mcp = FastMCP(
    "My Server",
    debug=True,           # Enable debug mode
    log_level="DEBUG"     # Verbose logging
)
```

**Environment variables:**
```bash
# Set via environment
export FASTMCP_DEBUG=true
export FASTMCP_LOG_LEVEL=DEBUG

# Run your server
uv run python -m my_mcp_server.main
```

**Rich logging (recommended):**
```bash
# Install rich for better logging
uv add rich

# Rich logging is automatically used when available
uv run python -m my_mcp_server.main
```

### 2. Tool Debugging

**Add logging to tools:**
```python
@mcp.tool()
async def debug_tool(data: dict, ctx: Context) -> str:
    """Tool with comprehensive logging."""
    ctx.debug(f"Input data: {data}")
    ctx.info("Processing started")

    try:
        # Your tool logic
        result = process_data(data)
        ctx.info(f"Processing completed: {result}")
        return result
    except ValueError as e:
        ctx.warning(f"Invalid input: {e}")
        return f"Error: {e}"
    except Exception as e:
        ctx.error(f"Unexpected error: {e}")
        raise
```

**Progress reporting for long operations:**
```python
@mcp.tool()
async def long_operation(items: list[str], ctx: Context) -> str:
    """Tool with progress reporting."""
    total = len(items)
    results = []

    for i, item in enumerate(items):
        # Report progress
        await ctx.report_progress(i, total, f"Processing {item}")

        # Process item
        result = await process_item(item)
        results.append(result)

    await ctx.report_progress(total, total, "Complete")
    return f"Processed {total} items"
```

### 3. HTTP Transport Debugging

**Debug HTTP endpoints:**
```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/debug", methods=["GET"])
async def debug_endpoint(request: Request) -> JSONResponse:
    """Debug endpoint to inspect server state."""
    return JSONResponse({
        "tools": len(mcp._tool_manager._tools),
        "resources": len(mcp._resource_manager._resources),
        "prompts": len(mcp._prompt_manager._prompts),
    })

# Test the endpoint
# curl http://localhost:8000/debug
```

**Request logging:**
```python
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("request")
        logger.info(f"{request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response

# Add to your server (advanced usage)
```

### 4. Client Testing

**Manual client testing:**
```python
"""Test client for manual debugging."""
import asyncio
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async def test_client():
    """Connect to your server and test it."""
    # Start your server with stdio: python -m my_mcp_server.main

    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool
            result = await session.call_tool("example_tool", {"input_text": "hello"})
            print(f"Tool result: {result.content}")

            # Read a resource
            resource = await session.read_resource("data://example")
            print(f"Resource: {resource.contents}")

if __name__ == "__main__":
    asyncio.run(test_client())
```

## Best Practices

### 1. Code Organization

**Separate concerns:**
```python
# tools/calculator.py
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# resources/data.py
@mcp.resource("data://users/{user_id}")
def get_user_data(user_id: str) -> dict:
    """Get user data by ID."""
    return load_user_data(user_id)

# main.py
from .tools import calculator
from .resources import data
```

**Use type hints everywhere:**
```python
from typing import List, Dict, Optional

@mcp.tool()
def process_items(
    items: List[str],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """Process items with type safety."""
    return {item: len(item) for item in items}
```

### 2. Error Handling

**Graceful error handling:**
```python
@mcp.tool()
async def robust_tool(data: str, ctx: Context) -> str:
    """Tool with comprehensive error handling."""
    try:
        # Validate input
        if not data.strip():
            raise ValueError("Data cannot be empty")

        # Process
        result = await process_data(data)

        # Validate output
        if not result:
            ctx.warning("Processing returned empty result")
            return "No data processed"

        return result

    except ValueError as e:
        ctx.error(f"Validation error: {e}")
        return f"Error: {e}"
    except Exception as e:
        ctx.error(f"Unexpected error: {e}")
        # Log full traceback for debugging
        import traceback
        ctx.debug(traceback.format_exc())
        raise
```

### 3. Performance Considerations

**Async best practices:**
```python
import asyncio

@mcp.tool()
async def batch_process(items: List[str], ctx: Context) -> List[str]:
    """Process items concurrently."""
    ctx.info(f"Processing {len(items)} items concurrently")

    # Use asyncio.gather for concurrent processing
    tasks = [process_single_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            ctx.warning(f"Item {i} failed: {result}")
            processed.append(f"Error: {result}")
        else:
            processed.append(result)

    return processed
```

**Resource caching:**
```python
import functools
from typing import Dict, Any

# Simple in-memory cache
_cache: Dict[str, Any] = {}

@mcp.resource("data://cached/{key}")
@functools.lru_cache(maxsize=100)
def cached_resource(key: str) -> str:
    """Resource with caching."""
    # This will be cached automatically
    return expensive_computation(key)
```

### 4. Testing Strategies

**Mock external dependencies:**
```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.anyio
async def test_tool_with_external_api():
    """Test tool that calls external API."""
    mcp = FastMCP("Test Server")

    @mcp.tool()
    async def api_tool(query: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com?q={query}")
            return response.json()["result"]

    # Mock the external API
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": "mocked data"}
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        # Test the tool
        tool = mcp._tool_manager._tools["api_tool"]
        result = await tool.run({"query": "test"})
        assert "mocked data" in result
```

### 5. Environment Configuration

**Configuration management:**
```python
from pydantic_settings import BaseSettings

class ServerSettings(BaseSettings):
    """Server configuration."""
    debug: bool = False
    log_level: str = "INFO"
    api_key: str = ""
    database_url: str = "sqlite:///data.db"

    class Config:
        env_prefix = "MCP_"

settings = ServerSettings()

mcp = FastMCP(
    "My Server",
    debug=settings.debug,
    log_level=settings.log_level
)
```

**Environment files:**
```bash
# .env
MCP_DEBUG=true
MCP_LOG_LEVEL=DEBUG
MCP_API_KEY=your-secret-key
MCP_DATABASE_URL=postgresql://user:pass@localhost/db
```

## Deployment

### 1. Building for Distribution

**Create distributable package:**
```bash
# Build wheel
uv build

# Install locally for testing
uv pip install dist/my_mcp_server-0.1.0-py3-none-any.whl
```

### 2. Container Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Install dependencies
RUN uv sync --frozen

# Run server
CMD ["uv", "run", "python", "-m", "my_mcp_server.main"]
```

### 3. Production Considerations

**Graceful shutdown:**
```python
import signal
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastMCP):
    """Handle startup and shutdown."""
    print("Server starting...")

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        print("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        yield
    finally:
        print("Server shutting down...")

mcp = FastMCP("Production Server", lifespan=lifespan)
```

This workflow guide provides everything needed for professional FastMCP development, from initial setup through production deployment.
