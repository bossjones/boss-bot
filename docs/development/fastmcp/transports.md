# Transport Protocols

FastMCP supports three transport protocols for client-server communication. Each protocol has different characteristics and is suitable for different deployment scenarios.

## Overview

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **stdio** | Local processes | Simple, efficient, reliable | Process-based only |
| **streamable-http** | Web deployment | HTTP compatible, resumable | More complex setup |
| **sse** | Legacy HTTP | Broad compatibility | Limited feature set |

## stdio Transport

**Recommended for: Local development, command-line tools, desktop applications**

The stdio transport uses standard input/output streams for communication. This is the most common and recommended transport for MCP servers.

### Characteristics

- **Process-based**: Client and server run as separate processes
- **Efficient**: Direct stdin/stdout communication with minimal overhead
- **Simple**: No network configuration required
- **Reliable**: Built-in process lifecycle management

### Usage

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

# Add your tools, resources, prompts...

if __name__ == "__main__":
    # Run with stdio (most common)
    mcp.run("stdio")
```

### Client Connection

Clients typically launch your server as a subprocess:

```bash
# Client runs your server directly
python my_server.py
```

### Configuration

Stdio transport uses minimal configuration:

```python
# No additional settings needed for stdio
mcp = FastMCP("My Server")
mcp.run("stdio")
```

## StreamableHTTP Transport

**Recommended for: Web deployment, cloud services, containerized environments**

StreamableHTTP is a modern HTTP-based protocol that supports resumable connections and stateful sessions.

### Characteristics

- **HTTP-based**: Works with standard web infrastructure
- **Resumable**: Clients can reconnect and resume sessions
- **Stateful**: Maintains session state between requests
- **Scalable**: Supports multiple concurrent clients

### Usage

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

# Add your tools, resources, prompts...

if __name__ == "__main__":
    # Run with StreamableHTTP
    mcp.run("streamable-http")
```

### Configuration

StreamableHTTP supports extensive configuration:

```python
mcp = FastMCP(
    "My Server",
    # HTTP settings
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/mcp",

    # StreamableHTTP specific
    json_response=True,  # Return JSON responses
    stateless_http=False,  # Enable session state
)

mcp.run("streamable-http")
```

### Environment Variables

```bash
# Configure via environment
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8000
FASTMCP_STREAMABLE_HTTP_PATH=/mcp
FASTMCP_JSON_RESPONSE=true
FASTMCP_STATELESS_HTTP=false
```

### Client Connection

Clients connect via HTTP:

```bash
# Server endpoint
http://localhost:8000/mcp
```

### Session Management

StreamableHTTP maintains sessions for each client:

- **Session ID**: Unique identifier per client connection
- **Event Store**: Optional storage for message history and resumability
- **Lifecycle**: Automatic cleanup when clients disconnect

```python
from mcp.server.streamable_http import EventStore

# Optional: Add event store for resumability
event_store = EventStore()

mcp = FastMCP(
    "My Server",
    event_store=event_store
)
```

## SSE Transport

**Recommended for: Legacy systems, HTTP-only environments**

Server-Sent Events (SSE) provides a simpler HTTP-based transport with broader compatibility.

### Characteristics

- **HTTP-compatible**: Works with standard HTTP infrastructure
- **One-way streaming**: Server-to-client via SSE, client-to-server via POST
- **Simple**: Easier to understand and debug than StreamableHTTP
- **Limited**: No built-in resumability or advanced features

### Usage

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

# Add your tools, resources, prompts...

if __name__ == "__main__":
    # Run with SSE
    mcp.run("sse")
```

### Configuration

```python
mcp = FastMCP(
    "My Server",
    # HTTP settings
    host="127.0.0.1",
    port=8000,
    mount_path="/",

    # SSE specific endpoints
    sse_path="/sse",
    message_path="/messages/",
)

mcp.run("sse")
```

### Endpoints

SSE creates two HTTP endpoints:

- **GET /sse**: Server-Sent Events stream for server-to-client messages
- **POST /messages/**: HTTP endpoint for client-to-server messages

## Choosing a Transport

### Use stdio when:

- Building command-line tools or desktop applications
- Developing locally or for single-user scenarios
- You want the simplest possible setup
- Your client can launch processes directly

### Use streamable-http when:

- Deploying to web servers or cloud platforms
- You need to support multiple concurrent clients
- You want resumable connections
- You're building web-based or distributed applications
- You need advanced features like authentication

### Use sse when:

- You need HTTP compatibility but StreamableHTTP is too complex
- Working with legacy systems or strict HTTP requirements
- You don't need advanced features like resumability
- Building simple web integrations

## Advanced Configuration

### Multiple Transports

You can run different transports in different environments:

```python
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

if __name__ == "__main__":
    # Choose transport based on environment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport)
```

### Custom HTTP Apps

For advanced use cases, you can access the underlying HTTP applications:

```python
# Get the Starlette app for StreamableHTTP
app = mcp.streamable_http_app()

# Get the Starlette app for SSE
app = mcp.sse_app()

# Then mount in your own FastAPI/Starlette application
```

### Authentication

HTTP transports support OAuth2 authentication:

```python
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings

# Configure authentication (HTTP transports only)
auth_provider = OAuthAuthorizationServerProvider(...)
auth_settings = AuthSettings(...)

mcp = FastMCP(
    "My Server",
    auth_server_provider=auth_provider,
    auth=auth_settings
)
```

## Performance Considerations

### stdio
- **Latency**: Lowest latency, direct process communication
- **Throughput**: High throughput for single client
- **Memory**: Minimal memory overhead
- **CPU**: Lowest CPU usage

### streamable-http
- **Latency**: Higher latency due to HTTP overhead
- **Throughput**: Good throughput, supports multiple clients
- **Memory**: Higher memory usage for session management
- **CPU**: Moderate CPU usage for HTTP processing

### sse
- **Latency**: Moderate latency, HTTP-based
- **Throughput**: Good for simple workloads
- **Memory**: Moderate memory usage
- **CPU**: Lower CPU usage than StreamableHTTP

## Debugging and Monitoring

### Logging

All transports support comprehensive logging:

```python
mcp = FastMCP(
    "My Server",
    log_level="DEBUG",  # Enable debug logging
    debug=True          # Enable debug mode
)
```

### Health Checks

HTTP transports can expose health check endpoints:

```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy"})
```
