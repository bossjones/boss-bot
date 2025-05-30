# Examples and Best Practices

This guide provides practical examples and best practices for building production-ready FastMCP servers.

## Complete Server Examples

### 1. File Management Server

A comprehensive server for file operations with proper error handling and security:

```python
import os
import mimetypes
from pathlib import Path
from typing import Literal, Annotated
from pydantic import Field

from mcp.server.fastmcp import FastMCP, Context

# Configuration
ALLOWED_DIRECTORIES = [
    Path.home() / "Documents",
    Path.home() / "Projects"
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

mcp = FastMCP(
    name="File Manager",
    instructions="Secure file management with read/write operations"
)

def validate_path(path_str: str) -> Path:
    """Validate and normalize file paths for security."""
    path = Path(path_str).resolve()

    # Check if path is within allowed directories
    if not any(str(path).startswith(str(allowed)) for allowed in ALLOWED_DIRECTORIES):
        raise ValueError(f"Access denied: {path} is outside allowed directories")

    return path

@mcp.tool()
async def list_files(
    directory: str,
    pattern: str = "*",
    include_hidden: bool = False,
    ctx: Context
) -> list[dict]:
    """List files in a directory with optional filtering."""

    await ctx.info(f"Listing files in {directory}")

    try:
        dir_path = validate_path(directory)

        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        files = []
        for item in dir_path.glob(pattern):
            # Skip hidden files unless requested
            if item.name.startswith('.') and not include_hidden:
                continue

            stat = item.stat()
            mime_type, _ = mimetypes.guess_type(str(item))

            files.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
                "modified": stat.st_mtime,
                "mime_type": mime_type if item.is_file() else None
            })

        await ctx.info(f"Found {len(files)} items")
        return sorted(files, key=lambda x: (x["type"], x["name"]))

    except Exception as e:
        await ctx.error(f"Failed to list files: {e}")
        raise

@mcp.tool()
async def read_file(file_path: str, ctx: Context) -> str:
    """Read file contents with safety checks."""

    await ctx.info(f"Reading file: {file_path}")

    try:
        path = validate_path(file_path)

        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file size
        if path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes (max: {MAX_FILE_SIZE})")

        await ctx.debug(f"File size: {path.stat().st_size} bytes")

        try:
            content = path.read_text(encoding='utf-8')
            await ctx.info(f"Successfully read {len(content)} characters")
            return content
        except UnicodeDecodeError:
            # Try binary read for non-text files
            await ctx.warning("File is not UTF-8 text, reading as binary")
            binary_content = path.read_bytes()
            return f"Binary file ({len(binary_content)} bytes): {path.name}"

    except Exception as e:
        await ctx.error(f"Failed to read file: {e}")
        raise

@mcp.tool()
async def write_file(
    file_path: str,
    content: str,
    overwrite: bool = False,
    ctx: Context
) -> dict:
    """Write content to a file with safety checks."""

    await ctx.info(f"Writing to file: {file_path}")

    try:
        path = validate_path(file_path)

        # Check if file exists and overwrite policy
        if path.exists() and not overwrite:
            raise ValueError(f"File exists and overwrite=False: {file_path}")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        await ctx.debug(f"Ensured directory exists: {path.parent}")

        # Write content
        path.write_text(content, encoding='utf-8')

        # Get file info
        stat = path.stat()

        await ctx.info(f"Successfully wrote {len(content)} characters to {file_path}")

        return {
            "path": str(path),
            "size": stat.st_size,
            "created": not overwrite or not path.existed_before_write,  # Simplified
            "modified": stat.st_mtime
        }

    except Exception as e:
        await ctx.error(f"Failed to write file: {e}")
        raise

@mcp.resource("file://{path}")
async def file_resource(path: str, ctx: Context) -> str:
    """Expose files as resources."""
    await ctx.debug(f"Accessing file resource: {path}")
    return await read_file(path, ctx)

@mcp.resource("directory://{path}")
async def directory_resource(path: str, ctx: Context) -> list[dict]:
    """Expose directory listings as resources."""
    await ctx.debug(f"Accessing directory resource: {path}")
    return await list_files(path, ctx=ctx)

if __name__ == "__main__":
    mcp.run()
```

### 2. Database Integration Server

A server that integrates with databases using proper connection management:

```python
import sqlite3
import json
from contextlib import asynccontextmanager
from typing import Any, Optional
from pydantic import Field

from mcp.server.fastmcp import FastMCP, Context

# Database configuration
DATABASE_PATH = "app.db"

mcp = FastMCP(
    name="Database Server",
    instructions="SQL database operations with query building and data analysis"
)

class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database with sample tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    product TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    total_amount DECIMAL(10,2),
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Insert sample data if tables are empty
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                sample_users = [
                    ("Alice Johnson", "alice@example.com"),
                    ("Bob Smith", "bob@example.com"),
                    ("Carol Davis", "carol@example.com")
                ]
                conn.executemany(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    sample_users
                )

                sample_orders = [
                    (1, "Laptop", 1, 999.99),
                    (1, "Mouse", 2, 49.98),
                    (2, "Keyboard", 1, 79.99),
                    (3, "Monitor", 1, 299.99)
                ]
                conn.executemany(
                    "INSERT INTO orders (user_id, product, quantity, total_amount) VALUES (?, ?, ?, ?)",
                    sample_orders
                )

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

# Initialize database manager
db_manager = DatabaseManager(DATABASE_PATH)

@mcp.tool()
async def execute_query(
    query: str,
    params: list[Any] = Field(default=[], description="Query parameters for safety"),
    limit: int = Field(default=100, description="Maximum rows to return"),
    ctx: Context
) -> dict:
    """Execute a SQL query with safety restrictions."""

    await ctx.info(f"Executing query: {query[:100]}...")

    # Safety checks
    query_lower = query.lower().strip()

    # Only allow SELECT statements
    if not query_lower.startswith('select'):
        await ctx.error("Only SELECT queries are allowed")
        raise ValueError("Only SELECT queries are allowed for safety")

    # Prevent dangerous operations
    dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter', 'create']
    if any(keyword in query_lower for keyword in dangerous_keywords):
        await ctx.error("Query contains dangerous keywords")
        raise ValueError("Query contains dangerous keywords")

    try:
        async with db_manager.get_connection() as conn:
            await ctx.debug(f"Executing with params: {params}")

            cursor = conn.execute(f"{query} LIMIT {limit}", params)
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = [dict(row) for row in rows]

            await ctx.info(f"Query returned {len(results)} rows")

            return {
                "query": query,
                "row_count": len(results),
                "results": results,
                "columns": list(rows[0].keys()) if rows else []
            }

    except sqlite3.Error as e:
        await ctx.error(f"Database error: {e}")
        raise ValueError(f"Database error: {e}")

@mcp.tool()
async def get_table_info(table_name: str, ctx: Context) -> dict:
    """Get information about a database table."""

    await ctx.info(f"Getting info for table: {table_name}")

    # Validate table name (prevent SQL injection)
    if not table_name.isalnum():
        raise ValueError("Table name must be alphanumeric")

    try:
        async with db_manager.get_connection() as conn:
            # Get table schema
            schema_cursor = conn.execute(f"PRAGMA table_info({table_name})")
            schema = schema_cursor.fetchall()

            if not schema:
                raise ValueError(f"Table {table_name} does not exist")

            # Get row count
            count_cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = count_cursor.fetchone()["count"]

            columns = [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "nullable": not row["notnull"],
                    "primary_key": bool(row["pk"])
                }
                for row in schema
            ]

            await ctx.info(f"Table {table_name} has {len(columns)} columns and {row_count} rows")

            return {
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count
            }

    except sqlite3.Error as e:
        await ctx.error(f"Database error: {e}")
        raise ValueError(f"Database error: {e}")

@mcp.tool()
async def analyze_data(
    table_name: str,
    column: str,
    analysis_type: Literal["summary", "distribution", "nulls"] = "summary",
    ctx: Context
) -> dict:
    """Analyze data in a specific table column."""

    await ctx.info(f"Analyzing {column} in {table_name}")

    # Validate inputs
    if not table_name.isalnum() or not column.replace('_', '').isalnum():
        raise ValueError("Invalid table or column name")

    try:
        async with db_manager.get_connection() as conn:
            if analysis_type == "summary":
                # Get basic statistics
                query = f"""
                    SELECT
                        COUNT(*) as total_count,
                        COUNT({column}) as non_null_count,
                        MIN({column}) as min_value,
                        MAX({column}) as max_value,
                        AVG(CASE WHEN typeof({column}) = 'real' OR typeof({column}) = 'integer'
                            THEN {column} END) as avg_value
                    FROM {table_name}
                """

            elif analysis_type == "distribution":
                # Get value distribution
                query = f"""
                    SELECT {column} as value, COUNT(*) as count
                    FROM {table_name}
                    GROUP BY {column}
                    ORDER BY count DESC
                    LIMIT 20
                """

            elif analysis_type == "nulls":
                # Get null analysis
                query = f"""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT({column}) as non_null_count,
                        (COUNT(*) - COUNT({column})) as null_count,
                        ROUND((COUNT(*) - COUNT({column})) * 100.0 / COUNT(*), 2) as null_percentage
                    FROM {table_name}
                """

            cursor = conn.execute(query)
            results = [dict(row) for row in cursor.fetchall()]

            await ctx.info(f"Analysis complete for {column}")

            return {
                "table": table_name,
                "column": column,
                "analysis_type": analysis_type,
                "results": results
            }

    except sqlite3.Error as e:
        await ctx.error(f"Database error: {e}")
        raise ValueError(f"Database error: {e}")

@mcp.resource("db://tables")
async def list_tables(ctx: Context) -> list[str]:
    """List all database tables."""
    await ctx.debug("Listing database tables")

    async with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        return [row["name"] for row in cursor.fetchall()]

@mcp.resource("db://table/{table_name}/schema")
async def table_schema_resource(table_name: str, ctx: Context) -> dict:
    """Get table schema as a resource."""
    await ctx.debug(f"Getting schema for table: {table_name}")
    return await get_table_info(table_name, ctx)

if __name__ == "__main__":
    mcp.run()
```

### 3. Web API Integration Server

A server that integrates with external APIs and provides caching:

```python
import httpx
import json
import time
from typing import Optional, Dict, Any
from functools import lru_cache
from pydantic import Field, HttpUrl

from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP(
    name="API Integration Server",
    instructions="Integrate with external APIs with caching and rate limiting"
)

# Configuration
API_TIMEOUT = 30.0
CACHE_TTL = 300  # 5 minutes
MAX_RETRIES = 3

class APIClient:
    """HTTP client with caching and error handling."""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        return f"{url}?{json.dumps(params, sort_keys=True)}"

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry["timestamp"] < CACHE_TTL

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Make HTTP GET request with caching."""

        params = params or {}
        cache_key = self._get_cache_key(url, params)

        # Check cache first
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                if ctx:
                    await ctx.debug("Returning cached response")
                return cache_entry["data"]

        # Make HTTP request with retries
        for attempt in range(MAX_RETRIES):
            try:
                if ctx:
                    await ctx.debug(f"Making HTTP request to {url} (attempt {attempt + 1})")

                async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()

                    data = response.json()

                    # Cache successful response
                    if use_cache:
                        self.cache[cache_key] = {
                            "data": data,
                            "timestamp": time.time()
                        }

                    if ctx:
                        await ctx.info(f"Successfully fetched data from {url}")

                    return data

            except httpx.RequestError as e:
                if ctx:
                    await ctx.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.HTTPStatusError as e:
                if ctx:
                    await ctx.error(f"HTTP error {e.response.status_code}: {e}")
                raise

# Global API client
api_client = APIClient()

@mcp.tool()
async def fetch_weather(
    city: str,
    units: Literal["metric", "imperial"] = "metric",
    ctx: Context
) -> dict:
    """Fetch weather data for a city."""

    await ctx.info(f"Fetching weather for {city}")

    # This is a mock API call - replace with real weather API
    mock_weather_data = {
        "london": {"temp": 15, "condition": "cloudy", "humidity": 80},
        "paris": {"temp": 18, "condition": "sunny", "humidity": 60},
        "tokyo": {"temp": 22, "condition": "rainy", "humidity": 85},
        "new york": {"temp": 12, "condition": "snow", "humidity": 70}
    }

    city_lower = city.lower()
    if city_lower not in mock_weather_data:
        await ctx.error(f"Weather data not available for {city}")
        raise ValueError(f"Weather data not available for {city}")

    base_data = mock_weather_data[city_lower]

    # Convert units if needed
    if units == "imperial":
        temp_f = (base_data["temp"] * 9/5) + 32
        data = {**base_data, "temp": round(temp_f, 1), "units": "°F"}
    else:
        data = {**base_data, "temp": base_data["temp"], "units": "°C"}

    await ctx.info(f"Weather for {city}: {data['temp']}{data['units']}, {data['condition']}")
    return {
        "city": city,
        "weather": data,
        "timestamp": time.time()
    }

@mcp.tool()
async def search_news(
    query: str,
    limit: int = Field(default=5, ge=1, le=20),
    language: str = "en",
    ctx: Context
) -> list[dict]:
    """Search for news articles."""

    await ctx.info(f"Searching news for: {query}")

    # Mock news data - replace with real news API
    mock_articles = [
        {
            "title": f"Breaking: {query} updates",
            "summary": f"Latest developments in {query} situation...",
            "url": f"https://example.com/news/{query.replace(' ', '-')}-1",
            "published": time.time() - 3600,  # 1 hour ago
            "source": "Example News"
        },
        {
            "title": f"Analysis: Impact of {query}",
            "summary": f"Expert analysis on {query} and its implications...",
            "url": f"https://example.com/news/{query.replace(' ', '-')}-2",
            "published": time.time() - 7200,  # 2 hours ago
            "source": "Tech Today"
        },
        {
            "title": f"{query}: What you need to know",
            "summary": f"Comprehensive guide to understanding {query}...",
            "url": f"https://example.com/news/{query.replace(' ', '-')}-3",
            "published": time.time() - 10800,  # 3 hours ago
            "source": "Daily Reporter"
        }
    ]

    # Simulate API delay
    import asyncio
    await asyncio.sleep(0.5)

    results = mock_articles[:limit]
    await ctx.info(f"Found {len(results)} articles")

    return results

@mcp.tool()
async def translate_text(
    text: str,
    target_language: str = "es",
    source_language: str = "auto",
    ctx: Context
) -> dict:
    """Translate text between languages."""

    await ctx.info(f"Translating text to {target_language}")

    # Mock translation - replace with real translation API
    translations = {
        "es": {
            "hello": "hola",
            "world": "mundo",
            "how are you": "¿cómo estás?",
            "thank you": "gracias"
        },
        "fr": {
            "hello": "bonjour",
            "world": "monde",
            "how are you": "comment allez-vous?",
            "thank you": "merci"
        }
    }

    text_lower = text.lower()
    translated = translations.get(target_language, {}).get(text_lower, f"[{text}]")

    await ctx.info(f"Translated '{text}' to '{translated}'")

    return {
        "original_text": text,
        "translated_text": translated,
        "source_language": source_language,
        "target_language": target_language,
        "confidence": 0.95
    }

@mcp.resource("api://weather/{city}")
async def weather_resource(city: str, ctx: Context) -> dict:
    """Weather data as a resource."""
    return await fetch_weather(city, ctx=ctx)

@mcp.resource("api://news/{query}")
async def news_resource(query: str, ctx: Context) -> list[dict]:
    """News search as a resource."""
    return await search_news(query, ctx=ctx)

if __name__ == "__main__":
    mcp.run()
```

## Architecture Patterns

### 1. Modular Server Design

```python
# server_modules/auth.py
from mcp.server.fastmcp import FastMCP, Context

def add_auth_tools(mcp: FastMCP):
    """Add authentication-related tools."""

    @mcp.tool()
    async def login(username: str, password: str, ctx: Context) -> dict:
        # Authentication logic
        pass

    @mcp.tool()
    async def logout(ctx: Context) -> bool:
        # Logout logic
        pass

# server_modules/data.py
def add_data_tools(mcp: FastMCP):
    """Add data management tools."""

    @mcp.tool()
    async def export_data(format: str, ctx: Context) -> str:
        # Export logic
        pass

# main.py
from mcp.server.fastmcp import FastMCP
from server_modules import auth, data

mcp = FastMCP("Modular Server")

# Add modules
auth.add_auth_tools(mcp)
data.add_data_tools(mcp)

if __name__ == "__main__":
    mcp.run()
```

### 2. Plugin System

```python
from abc import ABC, abstractmethod
from typing import Protocol

class MCPPlugin(Protocol):
    """Protocol for MCP plugins."""

    name: str
    version: str

    def install(self, mcp: FastMCP) -> None:
        """Install plugin into MCP server."""
        ...

class DatabasePlugin:
    """Database operations plugin."""

    name = "database"
    version = "1.0.0"

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def install(self, mcp: FastMCP) -> None:
        """Install database tools and resources."""

        @mcp.tool()
        async def query_db(sql: str, ctx: Context) -> list[dict]:
            # Database query implementation
            pass

        @mcp.resource("db://tables")
        async def list_tables(ctx: Context) -> list[str]:
            # List tables implementation
            pass

# Usage
mcp = FastMCP("Plugin Server")

# Install plugins
db_plugin = DatabasePlugin("sqlite:///app.db")
db_plugin.install(mcp)

if __name__ == "__main__":
    mcp.run()
```

### 3. Configuration-Driven Server

```python
import yaml
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

class ConfigurableServer:
    """Server that configures itself from YAML."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.mcp = FastMCP(
            name=self.config["server"]["name"],
            **self.config["server"].get("settings", {})
        )

        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self):
        """Dynamically create tools from configuration."""
        for tool_config in self.config.get("tools", []):
            self._create_tool(tool_config)

    def _create_tool(self, config: Dict[str, Any]):
        """Create a tool from configuration."""

        async def dynamic_tool(*args, ctx: Context, **kwargs):
            await ctx.info(f"Executing {config['name']}")
            # Implement tool logic based on config
            return {"message": f"Executed {config['name']}"}

        # Set function metadata
        dynamic_tool.__name__ = config["name"]
        dynamic_tool.__doc__ = config.get("description", "")

        self.mcp.add_tool(dynamic_tool)

    def run(self):
        """Run the configured server."""
        transport = self.config["server"].get("transport", "stdio")
        self.mcp.run(transport)

# config.yaml
"""
server:
  name: "Configurable Server"
  transport: "stdio"
  settings:
    debug: true
    log_level: "DEBUG"

tools:
  - name: "hello"
    description: "Say hello"
    type: "simple"
  - name: "analyze"
    description: "Analyze data"
    type: "complex"

resources:
  - uri: "data://config"
    type: "static"
    content: "Configuration data"
"""

if __name__ == "__main__":
    server = ConfigurableServer("config.yaml")
    server.run()
```

## Best Practices

### 1. Error Handling and Logging

```python
from enum import Enum
from typing import Optional

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

async def handle_error(
    ctx: Context,
    error: Exception,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None
) -> None:
    """Standardized error handling."""

    # Log technical details
    await ctx.error(f"Operation '{operation}' failed: {error}")

    # Log user-friendly message if provided
    if user_message:
        log_method = {
            ErrorSeverity.LOW: ctx.info,
            ErrorSeverity.MEDIUM: ctx.warning,
            ErrorSeverity.HIGH: ctx.error,
            ErrorSeverity.CRITICAL: ctx.error
        }[severity]

        await log_method(user_message)

@mcp.tool()
async def robust_operation(data: str, ctx: Context) -> dict:
    """Tool with comprehensive error handling."""

    try:
        await ctx.info("Starting operation")

        # Validate input
        if not data or not data.strip():
            await handle_error(
                ctx,
                ValueError("Empty data"),
                "input_validation",
                ErrorSeverity.LOW,
                "Please provide non-empty data"
            )
            raise ValueError("Data is required")

        # Process data
        result = process_data(data)

        await ctx.info("Operation completed successfully")
        return {"result": result, "status": "success"}

    except ValueError as e:
        await handle_error(ctx, e, "data_processing", ErrorSeverity.MEDIUM)
        raise
    except Exception as e:
        await handle_error(ctx, e, "data_processing", ErrorSeverity.HIGH)
        raise

def process_data(data: str) -> str:
    """Mock data processing."""
    return data.upper()
```

### 2. Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import List, Optional
import re

class UserInput(BaseModel):
    """Validated user input model."""

    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(..., ge=13, le=120)
    tags: List[str] = Field(default=[], max_items=10)

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric with underscores')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tags must be 50 characters or less')
        return v

@mcp.tool()
async def create_user(user_data: UserInput, ctx: Context) -> dict:
    """Create user with validated input."""

    await ctx.info(f"Creating user: {user_data.username}")

    # Pydantic automatically validates the input
    # Additional business logic validation can go here

    return {
        "user_id": hash(user_data.username) % 10000,
        "username": user_data.username,
        "email": user_data.email,
        "created": True
    }
```

### 3. Performance Optimization

```python
import asyncio
from functools import lru_cache
from typing import List, Dict, Any

# Caching expensive operations
@lru_cache(maxsize=128)
def expensive_computation(data: str) -> str:
    """Cached expensive computation."""
    # Simulate expensive operation
    import time
    time.sleep(0.1)
    return data.upper()

@mcp.tool()
async def batch_process(
    items: List[str],
    batch_size: int = 10,
    ctx: Context
) -> List[dict]:
    """Process items in batches for better performance."""

    await ctx.info(f"Processing {len(items)} items in batches of {batch_size}")

    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1

        await ctx.report_progress(
            progress=batch_num - 1,
            total=total_batches,
            message=f"Processing batch {batch_num}/{total_batches}"
        )

        # Process batch concurrently
        batch_results = await asyncio.gather(*[
            process_item_async(item) for item in batch
        ])

        results.extend(batch_results)

        await ctx.debug(f"Completed batch {batch_num}")

    await ctx.report_progress(total_batches, total_batches, "Complete")
    return results

async def process_item_async(item: str) -> dict:
    """Process single item asynchronously."""
    # Simulate async processing
    await asyncio.sleep(0.01)
    return {"item": item, "processed": True}
```

### 4. Testing

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

# Mock context for testing
class MockContext:
    def __init__(self):
        self.logs = []
        self.progress_reports = []

    async def info(self, message: str):
        self.logs.append(("info", message))

    async def error(self, message: str):
        self.logs.append(("error", message))

    async def report_progress(self, progress: int, total: int, message: str = ""):
        self.progress_reports.append((progress, total, message))

@pytest.mark.asyncio
async def test_file_operations():
    """Test file operations tool."""
    from pathlib import Path
    import tempfile

    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        ctx = MockContext()

        # Test reading file
        content = await read_file(temp_path, ctx)
        assert content == "test content"
        assert any("Successfully read" in msg for level, msg in ctx.logs if level == "info")

    finally:
        # Clean up
        Path(temp_path).unlink()

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in tools."""
    ctx = MockContext()

    # Test with invalid input
    with pytest.raises(ValueError):
        await read_file("/nonexistent/file", ctx)

    # Check error was logged
    assert any("Failed to read file" in msg for level, msg in ctx.logs if level == "error")

def test_input_validation():
    """Test input validation."""
    # Valid input
    valid_input = UserInput(
        username="testuser",
        email="test@example.com",
        age=25,
        tags=["python", "programming"]
    )
    assert valid_input.username == "testuser"

    # Invalid input
    with pytest.raises(ValueError):
        UserInput(
            username="test user",  # Spaces not allowed
            email="invalid-email",
            age=25
        )
```

### 5. Documentation and Type Hints

```python
from typing import TypeVar, Generic, Union, Optional, Literal
from pydantic import BaseModel, Field

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

@mcp.tool()
async def comprehensive_tool(
    input_data: str = Field(
        ...,
        description="Input data to process",
        example="sample text"
    ),
    processing_mode: Literal["fast", "thorough", "custom"] = Field(
        default="fast",
        description="Processing mode: 'fast' for quick results, 'thorough' for detailed analysis"
    ),
    options: Optional[dict] = Field(
        default=None,
        description="Additional processing options (mode-specific)"
    ),
    ctx: Context
) -> APIResponse[dict]:
    """
    Comprehensive data processing tool with multiple modes.

    This tool processes input data using different algorithms based on the selected mode:

    - 'fast': Quick processing with basic analysis
    - 'thorough': Detailed processing with comprehensive analysis
    - 'custom': User-defined processing with custom options

    Args:
        input_data: The data to process (required)
        processing_mode: Algorithm to use for processing
        options: Additional configuration (varies by mode)
        ctx: MCP context for logging and progress reporting

    Returns:
        APIResponse containing processed data and metadata

    Raises:
        ValueError: If input data is invalid or processing fails
        RuntimeError: If processing mode is not supported

    Example:
        >>> await comprehensive_tool("hello world", "fast")
        APIResponse(success=True, data={"result": "HELLO WORLD", "mode": "fast"})
    """

    await ctx.info(f"Processing data in {processing_mode} mode")

    try:
        # Process based on mode
        if processing_mode == "fast":
            result = {"result": input_data.upper(), "mode": processing_mode}
        elif processing_mode == "thorough":
            result = {
                "result": input_data.upper(),
                "length": len(input_data),
                "word_count": len(input_data.split()),
                "mode": processing_mode
            }
        elif processing_mode == "custom":
            # Use custom options
            custom_options = options or {}
            result = {
                "result": input_data.upper(),
                "mode": processing_mode,
                "options_used": custom_options
            }
        else:
            raise RuntimeError(f"Unsupported processing mode: {processing_mode}")

        await ctx.info("Processing completed successfully")

        return APIResponse(success=True, data=result)

    except Exception as e:
        await ctx.error(f"Processing failed: {e}")
        return APIResponse(success=False, error=str(e))
```

## Deployment Patterns

### 1. Container Deployment

```dockerfile
# Dockerfile
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

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "server.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTMCP_DEBUG=false
      - FASTMCP_LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@db:5432/mcpdb
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcpdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 2. Production Configuration

```python
# production.py
import os
import logging
from mcp.server.fastmcp import FastMCP

# Production configuration
mcp = FastMCP(
    name="Production Server",
    debug=False,
    log_level="INFO",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    warn_on_duplicate_tools=False,
    warn_on_duplicate_resources=False,
    warn_on_duplicate_prompts=False
)

# Production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/mcp-server.log')
    ]
)

if __name__ == "__main__":
    mcp.run("streamable-http")
```

This comprehensive documentation provides a solid foundation for building production-ready FastMCP servers with proper error handling, validation, testing, and deployment strategies.
