# Configuration

FastMCP provides extensive configuration options through constructor parameters and environment variables. This guide covers all available settings and how to use them effectively.

## Basic Configuration

### Server Creation

```python
from mcp.server.fastmcp import FastMCP

# Minimal configuration
mcp = FastMCP("My Server")

# With basic settings
mcp = FastMCP(
    name="My Server",
    instructions="A helpful server that provides data analysis tools"
)

# With transport settings
mcp = FastMCP(
    name="My Server",
    host="0.0.0.0",        # Listen on all interfaces
    port=8080,             # Custom port
    debug=True             # Enable debug mode
)
```

### Environment Variables

All settings can be configured via environment variables with the `FASTMCP_` prefix:

```bash
# Server settings
FASTMCP_DEBUG=true
FASTMCP_LOG_LEVEL=DEBUG

# HTTP settings
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8080
FASTMCP_MOUNT_PATH=/api/mcp

# StreamableHTTP settings
FASTMCP_JSON_RESPONSE=true
FASTMCP_STATELESS_HTTP=false
```

### Configuration File

FastMCP automatically loads settings from a `.env` file:

```env
# .env file
FASTMCP_DEBUG=true
FASTMCP_LOG_LEVEL=INFO
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000
FASTMCP_WARN_ON_DUPLICATE_TOOLS=false
```

## Complete Settings Reference

### Server Settings

```python
mcp = FastMCP(
    # Core server settings
    name="My Server",                    # Server name (required)
    instructions="Server description",   # Instructions for clients
    debug=False,                        # Enable debug mode
    log_level="INFO",                   # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
)
```

**Environment Variables:**
- `FASTMCP_DEBUG`: Enable debug mode (`true`/`false`)
- `FASTMCP_LOG_LEVEL`: Set log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

### HTTP Settings

```python
mcp = FastMCP(
    # HTTP transport settings
    host="127.0.0.1",                  # Host to bind to
    port=8000,                         # Port to listen on
    mount_path="/",                    # Mount path for SSE endpoints
    sse_path="/sse",                   # SSE endpoint path
    message_path="/messages/",         # SSE message endpoint path
    streamable_http_path="/mcp",       # StreamableHTTP endpoint path
)
```

**Environment Variables:**
- `FASTMCP_HOST`: Host address (`127.0.0.1`, `0.0.0.0`, etc.)
- `FASTMCP_PORT`: Port number (`8000`, `8080`, etc.)
- `FASTMCP_MOUNT_PATH`: Mount path (`/`, `/api`, etc.)
- `FASTMCP_SSE_PATH`: SSE endpoint (`/sse`, `/events`, etc.)
- `FASTMCP_MESSAGE_PATH`: Message endpoint (`/messages/`, `/msg/`, etc.)
- `FASTMCP_STREAMABLE_HTTP_PATH`: StreamableHTTP endpoint (`/mcp`, `/stream`, etc.)

### StreamableHTTP Settings

```python
mcp = FastMCP(
    # StreamableHTTP specific settings
    json_response=False,               # Return JSON responses instead of raw
    stateless_http=False,              # Use stateless mode (new transport per request)
)
```

**Environment Variables:**
- `FASTMCP_JSON_RESPONSE`: Enable JSON responses (`true`/`false`)
- `FASTMCP_STATELESS_HTTP`: Enable stateless mode (`true`/`false`)

### Warning Settings

```python
mcp = FastMCP(
    # Warning control
    warn_on_duplicate_tools=True,      # Warn when registering duplicate tools
    warn_on_duplicate_resources=True,  # Warn when registering duplicate resources
    warn_on_duplicate_prompts=True,    # Warn when registering duplicate prompts
)
```

**Environment Variables:**
- `FASTMCP_WARN_ON_DUPLICATE_TOOLS`: Warn on duplicate tools (`true`/`false`)
- `FASTMCP_WARN_ON_DUPLICATE_RESOURCES`: Warn on duplicate resources (`true`/`false`)
- `FASTMCP_WARN_ON_DUPLICATE_PROMPTS`: Warn on duplicate prompts (`true`/`false`)

### Dependencies

```python
mcp = FastMCP(
    # Runtime dependencies
    dependencies=[
        "requests>=2.25.0",
        "pandas>=1.3.0",
        "numpy"
    ]
)
```

**Environment Variable:**
- `FASTMCP_DEPENDENCIES`: Comma-separated list of dependencies

## Configuration Patterns

### Development Configuration

```python
# development.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Dev Server",
    debug=True,                        # Enable debug mode
    log_level="DEBUG",                 # Verbose logging
    host="127.0.0.1",                 # Local only
    port=8000,                         # Standard port
    warn_on_duplicate_tools=True,      # Catch registration issues
)
```

### Production Configuration

```python
# production.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Production Server",
    debug=False,                       # Disable debug mode
    log_level="INFO",                  # Standard logging
    host="0.0.0.0",                   # Accept external connections
    port=8080,                         # Production port
    warn_on_duplicate_tools=False,     # Reduce noise in logs
)
```

### Environment-Based Configuration

```python
import os
from mcp.server.fastmcp import FastMCP

# Determine environment
is_production = os.getenv("ENVIRONMENT") == "production"
is_development = os.getenv("ENVIRONMENT") == "development"

mcp = FastMCP(
    name=os.getenv("SERVER_NAME", "FastMCP Server"),
    debug=not is_production,
    log_level="INFO" if is_production else "DEBUG",
    host="0.0.0.0" if is_production else "127.0.0.1",
    port=int(os.getenv("PORT", "8000")),
)
```

### Configuration Class

```python
from pydantic_settings import BaseSettings
from mcp.server.fastmcp import FastMCP

class ServerConfig(BaseSettings):
    """Custom configuration with validation."""

    server_name: str = "FastMCP Server"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    # Custom settings
    max_connections: int = 100
    timeout: int = 30

    class Config:
        env_prefix = "SERVER_"

config = ServerConfig()

mcp = FastMCP(
    name=config.server_name,
    debug=config.debug,
    log_level=config.log_level,
    host=config.host,
    port=config.port,
)
```

## Transport-Specific Configuration

### stdio Configuration

```python
# stdio requires minimal configuration
mcp = FastMCP("stdio Server")

if __name__ == "__main__":
    mcp.run("stdio")  # No additional config needed
```

### SSE Configuration

```python
mcp = FastMCP(
    "SSE Server",
    host="0.0.0.0",                   # Host for HTTP server
    port=8000,                        # HTTP port
    mount_path="/github",             # Custom mount path
    sse_path="/events",               # Custom SSE endpoint
    message_path="/api/messages/",    # Custom message endpoint
    debug=True                        # Enable debug mode
)

if __name__ == "__main__":
    mcp.run("sse")
```

### StreamableHTTP Configuration

```python
mcp = FastMCP(
    "StreamableHTTP Server",
    host="0.0.0.0",                   # Host for HTTP server
    port=8080,                        # HTTP port
    streamable_http_path="/stream",   # Custom endpoint
    json_response=True,               # JSON responses
    stateless_http=False,             # Stateful sessions
    debug=False                       # Production mode
)

if __name__ == "__main__":
    mcp.run("streamable-http")
```

## Advanced Configuration

### Nested Environment Variables

FastMCP supports nested configuration via double underscores:

```bash
# Authentication settings (when using auth)
FASTMCP_AUTH__ISSUER_URL=https://auth.example.com
FASTMCP_AUTH__REQUIRED_SCOPES=read,write
FASTMCP_AUTH__SERVICE_DOCUMENTATION_URL=https://docs.example.com
```

### Custom Lifespan

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def custom_lifespan(app: FastMCP):
    """Custom lifespan for setup/teardown."""
    print("Server starting up...")

    # Setup code here
    database = await setup_database()

    try:
        yield {"database": database}
    finally:
        # Cleanup code here
        await database.close()
        print("Server shutting down...")

async def setup_database():
    """Mock database setup."""
    return {"connection": "mock_db"}

mcp = FastMCP(
    "Lifespan Server",
    lifespan=custom_lifespan
)
```

### Event Store Configuration

```python
from mcp.server.streamable_http import EventStore
from mcp.server.fastmcp import FastMCP

# Custom event store for resumability
event_store = EventStore()

mcp = FastMCP(
    "Resumable Server",
    event_store=event_store,
    stateless_http=False  # Required for resumability
)
```

## Configuration Validation

### Type Validation

```python
from typing import Literal
from pydantic import BaseModel, validator

class ValidatedConfig(BaseModel):
    """Configuration with validation."""

    name: str
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("host")
    def validate_host(cls, v):
        if v not in ["127.0.0.1", "0.0.0.0", "localhost"]:
            # In real scenario, you might want more sophisticated validation
            pass
        return v

# Use validated config
config = ValidatedConfig(
    name="Validated Server",
    port=8080,
    debug=True
)

mcp = FastMCP(
    name=config.name,
    debug=config.debug,
    log_level=config.log_level,
    host=config.host,
    port=config.port
)
```

### Environment Validation

```python
import os
from mcp.server.fastmcp import FastMCP

def get_validated_config():
    """Get configuration with environment validation."""

    # Required environment variables
    required_vars = ["SERVER_NAME"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    # Validate log level
    log_level = os.getenv("LOG_LEVEL", "INFO")
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"Invalid log level: {log_level}")

    # Validate port
    port = int(os.getenv("PORT", "8000"))
    if not 1 <= port <= 65535:
        raise ValueError(f"Invalid port: {port}")

    return {
        "name": os.getenv("SERVER_NAME"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": log_level,
        "port": port,
        "host": os.getenv("HOST", "127.0.0.1")
    }

# Use validated environment config
config = get_validated_config()
mcp = FastMCP(**config)
```

## Configuration Best Practices

### 1. Use Environment Variables for Deployment

```python
# Good: Environment-based configuration
mcp = FastMCP(
    name=os.getenv("SERVER_NAME", "Default Server"),
    debug=os.getenv("DEBUG", "false").lower() == "true",
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000"))
)

# Avoid: Hard-coded values
mcp = FastMCP(
    name="My Server",
    debug=True,
    host="192.168.1.100",  # Don't hard-code IPs
    port=8000
)
```

### 2. Separate Configuration by Environment

```python
# config/development.py
development_config = {
    "debug": True,
    "log_level": "DEBUG",
    "host": "127.0.0.1",
    "warn_on_duplicate_tools": True
}

# config/production.py
production_config = {
    "debug": False,
    "log_level": "INFO",
    "host": "0.0.0.0",
    "warn_on_duplicate_tools": False
}

# main.py
import os
from config import development, production

env = os.getenv("ENVIRONMENT", "development")
config = development_config if env == "development" else production_config

mcp = FastMCP("My Server", **config)
```

### 3. Validate Critical Settings

```python
import os
from mcp.server.fastmcp import FastMCP

# Validate critical settings
port = int(os.getenv("PORT", "8000"))
if port < 1024 and os.getuid() != 0:  # Unix-specific check
    raise ValueError("Ports below 1024 require root privileges")

host = os.getenv("HOST", "127.0.0.1")
if host == "0.0.0.0":
    print("WARNING: Server will accept connections from any IP address")

mcp = FastMCP(
    name="Validated Server",
    host=host,
    port=port
)
```

### 4. Document Configuration Options

```python
class ServerConfig:
    """
    FastMCP Server Configuration

    Environment Variables:
        SERVER_NAME: Name of the server (default: "FastMCP Server")
        DEBUG: Enable debug mode (default: false)
        LOG_LEVEL: Logging level (default: "INFO")
        HOST: Host to bind to (default: "127.0.0.1")
        PORT: Port to listen on (default: 8000)

    Example:
        export SERVER_NAME="My API Server"
        export DEBUG=true
        export LOG_LEVEL=DEBUG
        export HOST=0.0.0.0
        export PORT=8080
    """

    def __init__(self):
        self.name = os.getenv("SERVER_NAME", "FastMCP Server")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))

config = ServerConfig()
mcp = FastMCP(
    name=config.name,
    debug=config.debug,
    log_level=config.log_level,
    host=config.host,
    port=config.port
)
```

### 5. Use Configuration Files for Complex Settings

```yaml
# config.yaml
server:
  name: "Production Server"
  debug: false
  log_level: "INFO"

http:
  host: "0.0.0.0"
  port: 8080
  mount_path: "/api"

streamable_http:
  json_response: true
  stateless: false

warnings:
  duplicate_tools: false
  duplicate_resources: false
  duplicate_prompts: false
```

```python
import yaml
from mcp.server.fastmcp import FastMCP

def load_config(config_file: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # Flatten nested config
    return {
        "name": config["server"]["name"],
        "debug": config["server"]["debug"],
        "log_level": config["server"]["log_level"],
        "host": config["http"]["host"],
        "port": config["http"]["port"],
        "mount_path": config["http"]["mount_path"],
        "json_response": config["streamable_http"]["json_response"],
        "stateless_http": config["streamable_http"]["stateless"],
        "warn_on_duplicate_tools": config["warnings"]["duplicate_tools"],
        "warn_on_duplicate_resources": config["warnings"]["duplicate_resources"],
        "warn_on_duplicate_prompts": config["warnings"]["duplicate_prompts"],
    }

config = load_config("config.yaml")
mcp = FastMCP(**config)
```
