# Resources

Resources in FastMCP are data sources that MCP clients can read from. They provide a standardized way to expose files, databases, APIs, or any other data to LLM applications.

## Overview

Resources come in two types:

- **Static Resources**: Fixed URIs that return data (e.g., `data://config`, `file:///etc/hosts`)
- **Resource Templates**: URI patterns with parameters (e.g., `weather://{city}/current`, `user://{id}/profile`)

Both types are created using the `@mcp.resource()` decorator or by adding Resource objects directly.

## Static Resources

Static resources have fixed URIs and are ideal for configuration files, static data, or computed values.

### Basic Static Resource

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Data Server")

@mcp.resource("data://config")
def get_config() -> str:
    """Server configuration data."""
    return "debug=true\nport=8080\nhost=localhost"

@mcp.resource("data://status")
def get_status() -> dict:
    """Current server status."""
    return {
        "status": "running",
        "uptime": "2 hours",
        "memory_usage": "45MB"
    }
```

### File Resources

```python
from pathlib import Path

@mcp.resource("file://app.log")
def get_log_file() -> str:
    """Read the application log file."""
    log_path = Path("app.log")
    if log_path.exists():
        return log_path.read_text()
    return "Log file not found"

@mcp.resource("file://data.json")
def get_data_file() -> bytes:
    """Read binary data file."""
    return Path("data.json").read_bytes()
```

### Database Resources

```python
import sqlite3

@mcp.resource("db://users/count")
def get_user_count() -> dict:
    """Get total number of users."""
    conn = sqlite3.connect("app.db")
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()

    return {"total_users": count}

@mcp.resource("db://recent_orders")
def get_recent_orders() -> list[dict]:
    """Get recent orders from database."""
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT id, customer_name, total, created_at
        FROM orders
        ORDER BY created_at DESC
        LIMIT 10
    """)

    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return orders
```

### API Resources

```python
import httpx

@mcp.resource("api://github/status")
async def get_github_status() -> dict:
    """Get GitHub API status."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/status")
        return response.json()

@mcp.resource("api://weather/current")
async def get_current_weather() -> str:
    """Get current weather data."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://wttr.in/?format=j1")
        data = response.json()
        current = data["current_condition"][0]
        return f"Temperature: {current['temp_C']}°C, {current['weatherDesc'][0]['value']}"
```

## Resource Templates

Resource templates use URI patterns with parameters to create dynamic resources. They're perfect for user profiles, file browsers, or any parameterized data.

### Basic Templates

```python
@mcp.resource("user://{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """Get user profile by ID."""
    # This function will be called with user_id parameter
    # when client requests "user://123/profile"

    users = {
        "123": {"name": "Alice", "email": "alice@example.com"},
        "456": {"name": "Bob", "email": "bob@example.com"}
    }

    if user_id not in users:
        raise ValueError(f"User {user_id} not found")

    return users[user_id]

@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read any file by path."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except PermissionError:
        raise ValueError(f"Permission denied: {path}")
```

### Multiple Parameters

```python
@mcp.resource("weather://{city}/{type}")
def get_weather(city: str, type: str) -> dict:
    """Get weather data for a city and type.

    Examples:
    - weather://london/current
    - weather://paris/forecast
    - weather://tokyo/historical
    """

    if type not in ["current", "forecast", "historical"]:
        raise ValueError(f"Invalid weather type: {type}")

    # Mock weather data
    weather_data = {
        "current": {"temp": 20, "condition": "sunny"},
        "forecast": {"tomorrow": {"temp": 22, "condition": "cloudy"}},
        "historical": {"yesterday": {"temp": 18, "condition": "rainy"}}
    }

    return {
        "city": city,
        "type": type,
        "data": weather_data[type]
    }

@mcp.resource("repo://{owner}/{repo}/issues/{state}")
def get_repo_issues(owner: str, repo: str, state: str) -> list[dict]:
    """Get GitHub repository issues.

    Examples:
    - repo://microsoft/vscode/issues/open
    - repo://python/cpython/issues/closed
    """
    # Implementation would call GitHub API
    return [
        {"id": 1, "title": "Bug report", "state": state},
        {"id": 2, "title": "Feature request", "state": state}
    ]
```

### Typed Parameters

Use type hints and Pydantic Field for parameter validation:

```python
from pydantic import Field
from typing import Annotated

@mcp.resource("data://{category}/items/{page}")
def get_paginated_data(
    category: Annotated[str, Field(pattern=r"^[a-z]+$")],
    page: Annotated[int, Field(ge=1, le=100)]
) -> dict:
    """Get paginated data with validation.

    Category must be lowercase letters only.
    Page must be between 1 and 100.
    """

    items_per_page = 10
    start_idx = (page - 1) * items_per_page

    # Mock data
    all_items = [f"{category}_item_{i}" for i in range(1, 101)]
    page_items = all_items[start_idx:start_idx + items_per_page]

    return {
        "category": category,
        "page": page,
        "items": page_items,
        "total_pages": len(all_items) // items_per_page
    }
```

## Resource Metadata

### Custom Names and Descriptions

```python
@mcp.resource(
    "data://config",
    name="Server Configuration",
    description="Application configuration settings"
)
def get_config() -> str:
    return "config data here"

@mcp.resource(
    "user://{id}",
    name="User Profile",
    description="Get user profile information by ID"
)
def get_user(id: str) -> dict:
    return {"id": id, "name": "User"}
```

### MIME Types

Specify MIME types for non-text content:

```python
@mcp.resource(
    "image://logo",
    mime_type="image/png"
)
def get_logo() -> bytes:
    """Return PNG logo image."""
    return Path("logo.png").read_bytes()

@mcp.resource(
    "data://metrics",
    mime_type="application/json"
)
def get_metrics() -> dict:
    """Return JSON metrics data."""
    return {"cpu": 45, "memory": 67, "disk": 23}

@mcp.resource(
    "file://{path}",
    mime_type="text/plain"
)
def read_text_file(path: str) -> str:
    """Read text file."""
    return Path(path).read_text()
```

## Async Resources

Resources can be async for I/O operations:

```python
import asyncio
import aiofiles
import httpx

@mcp.resource("file://async/{filename}")
async def read_file_async(filename: str) -> str:
    """Read file asynchronously."""
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()

@mcp.resource("api://posts/{post_id}")
async def get_post(post_id: str) -> dict:
    """Fetch blog post from API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/posts/{post_id}")
        return response.json()

@mcp.resource("db://async/users")
async def get_users_async() -> list[dict]:
    """Get users from async database."""
    # Simulate async database call
    await asyncio.sleep(0.1)
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
```

## Programmatic Resource Creation

### Using Resource Classes

```python
from mcp.server.fastmcp.resources import TextResource, BinaryResource

# Text resource
text_resource = TextResource(
    uri="data://readme",
    text="# Welcome\nThis is the README",
    name="README File",
    description="Project README content"
)
mcp.add_resource(text_resource)

# Binary resource
binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
binary_resource = BinaryResource(
    uri="image://icon",
    data=binary_data,
    mime_type="image/png",
    name="Application Icon"
)
mcp.add_resource(binary_resource)
```

### Function Resources

```python
from mcp.server.fastmcp.resources import FunctionResource

def get_timestamp():
    from datetime import datetime
    return datetime.now().isoformat()

# Create function resource
timestamp_resource = FunctionResource.from_function(
    fn=get_timestamp,
    uri="time://current",
    name="Current Timestamp",
    description="Current server timestamp"
)
mcp.add_resource(timestamp_resource)
```

## Error Handling

### Graceful Error Handling

```python
@mcp.resource("file://{path}")
def safe_file_read(path: str) -> str:
    """Safely read a file with error handling."""
    try:
        file_path = Path(path)

        # Security check
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")

        # Size check (max 1MB)
        if file_path.stat().st_size > 1024 * 1024:
            raise ValueError(f"File too large: {path}")

        return file_path.read_text()

    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except PermissionError:
        raise ValueError(f"Permission denied: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not text: {path}")
```

### Resource Validation

```python
from pathlib import Path

@mcp.resource("directory://{path}/list")
def list_directory(path: str) -> list[str]:
    """List directory contents with validation."""

    # Validate path
    if not path or ".." in path:
        raise ValueError("Invalid path")

    dir_path = Path(path)

    if not dir_path.exists():
        raise ValueError(f"Directory does not exist: {path}")

    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    try:
        return [item.name for item in dir_path.iterdir()]
    except PermissionError:
        raise ValueError(f"Permission denied: {path}")
```

## Advanced Examples

### Database Resource with Connection Pooling

```python
import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

db_manager = DatabaseManager("app.db")

@mcp.resource("db://table/{table_name}")
def query_table(table_name: str) -> list[dict]:
    """Query any table in the database."""

    # Validate table name (prevent SQL injection)
    if not table_name.isalnum():
        raise ValueError("Invalid table name")

    with db_manager.get_connection() as conn:
        try:
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 100")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            raise ValueError(f"Database error: {e}")
```

### Cached Resource

```python
import time
from functools import lru_cache

@mcp.resource("api://cached/{endpoint}")
def cached_api_call(endpoint: str) -> dict:
    """API call with caching."""

    @lru_cache(maxsize=128)
    def _fetch_data(endpoint: str, cache_key: int) -> dict:
        # Cache key based on 5-minute intervals
        import httpx
        response = httpx.get(f"https://api.example.com/{endpoint}")
        return response.json()

    # Create cache key (refreshes every 5 minutes)
    cache_key = int(time.time() // 300)

    return _fetch_data(endpoint, cache_key)
```

### File Browser Resource

```python
import mimetypes
from pathlib import Path

@mcp.resource("browse://{path}")
def browse_filesystem(path: str) -> dict:
    """Browse filesystem with metadata."""

    # Security: restrict to specific directories
    allowed_roots = ["/home/user/documents", "/home/user/projects"]
    abs_path = Path(path).resolve()

    if not any(str(abs_path).startswith(root) for root in allowed_roots):
        raise ValueError("Access denied")

    if not abs_path.exists():
        raise ValueError(f"Path does not exist: {path}")

    if abs_path.is_file():
        stat = abs_path.stat()
        mime_type, _ = mimetypes.guess_type(str(abs_path))

        return {
            "type": "file",
            "name": abs_path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "mime_type": mime_type
        }

    elif abs_path.is_dir():
        items = []
        for item in abs_path.iterdir():
            stat = item.stat()
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
                "modified": stat.st_mtime
            })

        return {
            "type": "directory",
            "path": str(abs_path),
            "items": sorted(items, key=lambda x: (x["type"], x["name"]))
        }
```

## Best Practices

### 1. Use Meaningful URIs

```python
# Good: Clear, hierarchical URIs
@mcp.resource("user://{id}/profile")
@mcp.resource("project://{id}/files/{path}")
@mcp.resource("weather://{city}/current")

# Avoid: Unclear or flat URIs
@mcp.resource("data://{x}")
@mcp.resource("resource1")
```

### 2. Validate Parameters

```python
@mcp.resource("user://{user_id}/posts/{page}")
def get_user_posts(
    user_id: Annotated[str, Field(pattern=r"^\d+$")],
    page: Annotated[int, Field(ge=1, le=1000)]
) -> list[dict]:
    """Get user posts with validation."""
    # user_id must be numeric string
    # page must be 1-1000
    pass
```

### 3. Handle Errors Gracefully

```python
@mcp.resource("file://{path}")
def read_file_safe(path: str) -> str:
    """Read file with comprehensive error handling."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except PermissionError:
        raise ValueError(f"Access denied: {path}")
    except IsADirectoryError:
        raise ValueError(f"Path is a directory: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not text: {path}")
```

### 4. Use Appropriate MIME Types

```python
@mcp.resource("image://{name}", mime_type="image/png")
def get_image(name: str) -> bytes:
    return Path(f"{name}.png").read_bytes()

@mcp.resource("data://{name}", mime_type="application/json")
def get_json_data(name: str) -> dict:
    return {"data": name}

@mcp.resource("doc://{name}", mime_type="text/markdown")
def get_document(name: str) -> str:
    return f"# {name}\n\nDocument content..."
```

### 5. Implement Security

```python
from pathlib import Path

ALLOWED_PATHS = ["/safe/directory", "/another/safe/path"]

@mcp.resource("secure-file://{path}")
def secure_file_access(path: str) -> str:
    """Secure file access with path validation."""

    # Resolve path and check it's within allowed directories
    abs_path = Path(path).resolve()

    if not any(str(abs_path).startswith(allowed) for allowed in ALLOWED_PATHS):
        raise ValueError("Access denied: path outside allowed directories")

    if not abs_path.exists():
        raise ValueError(f"File not found: {path}")

    return abs_path.read_text()
```
