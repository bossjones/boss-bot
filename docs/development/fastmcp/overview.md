# FastMCP Overview

FastMCP is a high-level, ergonomic Python framework for building MCP (Model Context Protocol) servers. It provides a simple decorator-based API that abstracts away the complexity of the underlying MCP protocol while giving you full access to its capabilities.

## What is MCP?

The Model Context Protocol (MCP) enables seamless integration between LLM applications and external data sources and tools. MCP servers expose three main types of capabilities to clients:

- **Tools**: Functions that clients can call to perform actions
- **Resources**: Data sources that clients can read from
- **Prompts**: Templates that help clients interact with your server

## Why FastMCP?

FastMCP simplifies MCP server development by providing:

- **Decorator-based API**: Simple `@tool`, `@resource`, and `@prompt` decorators
- **Automatic type validation**: Built on Pydantic for robust input validation
- **Multiple transport protocols**: Support for stdio, HTTP+SSE, and StreamableHTTP
- **Context injection**: Easy access to MCP capabilities like logging and progress reporting
- **Authentication**: Built-in OAuth2 support for secure servers
- **Development-friendly**: Hot reload, detailed error messages, and comprehensive logging

## Quick Start

Here's a minimal FastMCP server:

```python
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("My Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.resource("data://example")
def get_data() -> str:
    """Provide example data."""
    return "Hello from FastMCP!"

# Run with stdio transport (most common)
if __name__ == "__main__":
    mcp.run("stdio")
```

## Core Concepts

### Server Creation

Every FastMCP server starts with creating a `FastMCP` instance:

```python
from mcp.server.fastmcp import FastMCP

# Basic server
mcp = FastMCP("Server Name")

# Server with instructions for the client
mcp = FastMCP(
    name="Calculator Server",
    instructions="A server that provides mathematical operations"
)
```

### Decorators

FastMCP uses decorators to register capabilities:

- `@mcp.tool()` - Register a function as a callable tool
- `@mcp.resource()` - Register a function as a readable resource
- `@mcp.prompt()` - Register a function as a prompt template

### Transport Protocols

FastMCP supports three transport protocols:

1. **stdio** (recommended): Uses standard input/output, ideal for local processes
2. **streamable-http**: HTTP-based protocol for web deployments
3. **sse**: Server-Sent Events, compatible with HTTP infrastructure

```python
# Run with different transports
mcp.run("stdio")              # Most common
mcp.run("streamable-http")    # For web deployment
mcp.run("sse")               # For HTTP compatibility
```

### Context and Capabilities

Tools and resources can access MCP capabilities through context injection:

```python
from mcp.server.fastmcp import FastMCP, Context

@mcp.tool()
async def advanced_tool(data: str, ctx: Context) -> str:
    # Log messages to the client
    await ctx.info(f"Processing: {data}")

    # Report progress
    await ctx.report_progress(50, 100, "Half done")

    # Read other resources
    resource_content = await ctx.read_resource("data://other")

    return f"Processed: {data}"
```

## Next Steps

- **[Transport Protocols](transports.md)** - Learn about stdio vs HTTP transports
- **[Tools](tools.md)** - Build interactive tools for clients to call
- **[Resources](resources.md)** - Expose data sources and templates
- **[Context](context.md)** - Use logging, progress, and other MCP capabilities
- **[Configuration](configuration.md)** - Environment variables and settings
- **[Examples](examples.md)** - Common patterns and best practices

## Installation

FastMCP is included with the MCP Python SDK:

```bash
uv add mcp
```

Or with pip:

```bash
pip install mcp
```
