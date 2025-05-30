# Tools

Tools are functions that MCP clients can call to perform actions. FastMCP makes it easy to register Python functions as tools using simple decorators.

## Quick Start

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

## Basic Tool Registration

### Using the Decorator

The `@mcp.tool()` decorator is the recommended way to register tools:

```python
@mcp.tool()
def simple_tool(x: int) -> str:
    """Convert a number to string."""
    return str(x)
```

### Using add_tool Method

You can also register tools programmatically:

```python
def my_function(x: int) -> str:
    return str(x)

mcp.add_tool(my_function, name="convert", description="Convert number to string")
```

### Custom Names and Descriptions

```python
@mcp.tool(
    name="custom_name",
    description="This overrides the docstring description"
)
def my_tool(x: int) -> str:
    """This docstring will be ignored."""
    return str(x)
```

## Type Validation

FastMCP automatically validates tool inputs and outputs using Python type hints and Pydantic.

### Basic Types

```python
@mcp.tool()
def basic_types(
    text: str,
    number: int,
    decimal: float,
    flag: bool,
    items: list[str]
) -> dict[str, any]:
    """Tool with various basic types."""
    return {
        "text": text,
        "number": number,
        "decimal": decimal,
        "flag": flag,
        "items": items
    }
```

### Optional Parameters

```python
@mcp.tool()
def optional_params(
    required: str,
    optional: str = "default value",
    maybe_none: str | None = None
) -> str:
    """Tool with optional parameters."""
    result = f"Required: {required}"
    if optional != "default value":
        result += f", Optional: {optional}"
    if maybe_none:
        result += f", Maybe: {maybe_none}"
    return result
```

### Parameter Descriptions

Use Pydantic `Field` for detailed parameter documentation:

```python
from pydantic import Field

@mcp.tool()
def documented_tool(
    name: str = Field(description="The person's name to greet"),
    title: str = Field(description="Optional title like Mr/Ms/Dr", default=""),
    times: int = Field(description="Number of times to repeat", default=1, ge=1, le=10)
) -> str:
    """Greet someone with optional title and repetition."""
    greeting = f"Hello {title + ' ' if title else ''}{name}!"
    return "\n".join([greeting] * times)
```

### Complex Types with Pydantic Models

```python
from pydantic import BaseModel
from typing import Annotated

class User(BaseModel):
    name: Annotated[str, Field(max_length=50)]
    age: Annotated[int, Field(ge=0, le=150)]
    email: str

@mcp.tool()
def create_user(user: User) -> str:
    """Create a new user account."""
    return f"Created user {user.name} ({user.age}) with email {user.email}"
```

### Validation with Constraints

```python
from typing import Annotated
from pydantic import Field

@mcp.tool()
def constrained_inputs(
    # String constraints
    username: Annotated[str, Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")],

    # Numeric constraints
    age: Annotated[int, Field(ge=0, le=150)],

    # List constraints
    tags: Annotated[list[str], Field(max_length=5)],

    # Custom validation
    email: Annotated[str, Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")]
) -> dict:
    """Tool with various input constraints."""
    return {
        "username": username,
        "age": age,
        "tags": tags,
        "email": email
    }
```

## Async Tools

FastMCP supports both synchronous and asynchronous tools:

```python
import asyncio
import httpx

@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data from a URL asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

@mcp.tool()
async def slow_operation(duration: int) -> str:
    """Simulate a slow operation."""
    await asyncio.sleep(duration)
    return f"Completed after {duration} seconds"
```

## Context Injection

Tools can access MCP capabilities through context injection:

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def tool_with_context(text: str, ctx: Context) -> str:
    """Tool that uses MCP context capabilities."""

    # Log messages to the client
    await ctx.info(f"Processing: {text}")
    await ctx.debug("Debug information")
    await ctx.warning("Warning message")

    # Report progress
    await ctx.report_progress(25, 100, "Started processing")

    # Simulate work
    import asyncio
    await asyncio.sleep(1)

    await ctx.report_progress(75, 100, "Almost done")

    # Read resources
    try:
        resource_data = await ctx.read_resource("data://config")
        await ctx.info("Found configuration data")
    except Exception as e:
        await ctx.error(f"Could not read config: {e}")

    await ctx.report_progress(100, 100, "Complete")

    return f"Processed: {text}"
```

### Context Parameter Names

The context parameter can have any name as long as it's typed as `Context`:

```python
@mcp.tool()
async def my_tool(x: int, context: Context) -> str:
    await context.info("Using 'context' parameter name")
    return str(x)

@mcp.tool()
async def another_tool(x: int, ctx: Context) -> str:
    await ctx.info("Using 'ctx' parameter name")
    return str(x)

@mcp.tool()
async def third_tool(x: int, mcp_context: Context) -> str:
    await mcp_context.info("Using 'mcp_context' parameter name")
    return str(x)
```

## Return Types

Tools can return various types of data:

### Simple Returns

```python
@mcp.tool()
def return_string() -> str:
    return "Hello, world!"

@mcp.tool()
def return_number() -> int:
    return 42

@mcp.tool()
def return_dict() -> dict:
    return {"status": "success", "data": [1, 2, 3]}
```

### Rich Content

```python
from mcp.types import TextContent, ImageContent
from mcp.server.fastmcp import Image

@mcp.tool()
def return_rich_content() -> list[TextContent]:
    """Return rich text content."""
    return [
        TextContent(type="text", text="Here's the result:"),
        TextContent(type="text", text="Some formatted data")
    ]

@mcp.tool()
def return_image() -> Image:
    """Return an image."""
    # Read image data
    with open("chart.png", "rb") as f:
        image_data = f.read()

    return Image(data=image_data, mime_type="image/png")
```

### Multiple Return Types

```python
from typing import Union

@mcp.tool()
def flexible_return(format: str) -> Union[str, dict, list]:
    """Return different types based on format parameter."""
    data = {"name": "John", "age": 30}

    if format == "json":
        return data
    elif format == "list":
        return [data["name"], data["age"]]
    else:
        return f"Name: {data['name']}, Age: {data['age']}"
```

## Error Handling

### Automatic Error Handling

FastMCP automatically catches and reports tool errors:

```python
@mcp.tool()
def might_fail(x: int) -> str:
    """Tool that might raise an exception."""
    if x < 0:
        raise ValueError("x must be positive")
    return f"Result: {x * 2}"
```

### Custom Error Types

```python
from mcp.server.fastmcp.exceptions import ToolError

@mcp.tool()
def custom_error(x: int) -> str:
    """Tool with custom error handling."""
    if x < 0:
        raise ToolError("Custom error: x must be positive")
    return str(x)
```

### Error Context

```python
@mcp.tool()
async def error_with_context(x: int, ctx: Context) -> str:
    """Tool that reports errors through context."""
    try:
        if x < 0:
            raise ValueError("Negative values not allowed")
        return str(x)
    except ValueError as e:
        await ctx.error(f"Validation error: {e}")
        raise  # Re-raise so client knows it failed
```

## Tool Annotations

Add metadata to tools using annotations:

```python
from mcp.types import ToolAnnotations

@mcp.tool(annotations=ToolAnnotations(
    audience=["human", "ai"],
    priority="high"
))
def important_tool(x: int) -> str:
    """A high-priority tool."""
    return str(x)
```

## Advanced Examples

### File Processing Tool

```python
import json
from pathlib import Path

@mcp.tool()
async def process_file(
    file_path: str,
    operation: str = Field(description="Operation: 'read', 'size', or 'type'"),
    ctx: Context
) -> str:
    """Process a file and return information about it."""

    await ctx.info(f"Processing file: {file_path}")

    try:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if operation == "read":
            await ctx.info("Reading file contents")
            return path.read_text()

        elif operation == "size":
            size = path.stat().st_size
            await ctx.info(f"File size: {size} bytes")
            return f"{size} bytes"

        elif operation == "type":
            suffix = path.suffix
            await ctx.info(f"File type: {suffix}")
            return suffix or "no extension"

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        await ctx.error(f"Error processing file: {e}")
        raise ToolError(str(e))
```

### Database Query Tool

```python
import sqlite3
from typing import List, Dict, Any

@mcp.tool()
async def query_database(
    query: str = Field(description="SQL query to execute"),
    params: List[Any] = Field(description="Query parameters", default=[]),
    ctx: Context
) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results."""

    await ctx.info(f"Executing query: {query}")

    try:
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        results = [dict(row) for row in rows]

        await ctx.info(f"Query returned {len(results)} rows")
        return results

    except sqlite3.Error as e:
        await ctx.error(f"Database error: {e}")
        raise ToolError(f"Database error: {e}")
    finally:
        conn.close()
```

### HTTP API Tool

```python
import httpx
from typing import Optional, Dict, Any

@mcp.tool()
async def api_request(
    url: str,
    method: str = Field(description="HTTP method", default="GET"),
    headers: Optional[Dict[str, str]] = Field(description="Request headers", default=None),
    data: Optional[Dict[str, Any]] = Field(description="Request body", default=None),
    ctx: Context
) -> Dict[str, Any]:
    """Make an HTTP API request."""

    await ctx.info(f"Making {method} request to {url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers or {},
                json=data
            )

            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

            await ctx.info(f"Request completed with status {response.status_code}")
            return result

    except httpx.RequestError as e:
        await ctx.error(f"Request failed: {e}")
        raise ToolError(f"Request failed: {e}")
```

## Best Practices

### 1. Use Descriptive Names and Docstrings

```python
@mcp.tool()
def calculate_compound_interest(
    principal: float = Field(description="Initial investment amount"),
    rate: float = Field(description="Annual interest rate (as decimal, e.g., 0.05 for 5%)"),
    time: int = Field(description="Number of years"),
    compound_freq: int = Field(description="Compounding frequency per year", default=1)
) -> float:
    """
    Calculate compound interest on an investment.

    Uses the formula: A = P(1 + r/n)^(nt)
    Where A is final amount, P is principal, r is rate, n is compound frequency, t is time.
    """
    return principal * (1 + rate / compound_freq) ** (compound_freq * time)
```

### 2. Validate Inputs Early

```python
@mcp.tool()
def divide_numbers(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### 3. Use Context for User Feedback

```python
@mcp.tool()
async def long_running_task(items: list[str], ctx: Context) -> str:
    """Process a list of items with progress reporting."""
    total = len(items)
    results = []

    for i, item in enumerate(items):
        await ctx.report_progress(i, total, f"Processing {item}")

        # Process item...
        result = f"processed_{item}"
        results.append(result)

        await ctx.info(f"Completed {item}")

    await ctx.report_progress(total, total, "Complete")
    return ", ".join(results)
```

### 4. Handle Errors Gracefully

```python
@mcp.tool()
async def robust_tool(data: dict, ctx: Context) -> str:
    """A robust tool with comprehensive error handling."""
    try:
        # Validate required fields
        if "name" not in data:
            raise ValueError("Missing required field: name")

        # Process data
        result = process_data(data)

        await ctx.info("Processing completed successfully")
        return result

    except ValueError as e:
        await ctx.error(f"Validation error: {e}")
        raise ToolError(f"Invalid input: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise ToolError(f"Processing failed: {e}")
```

### 5. Return Structured Data

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    score: float
    recommendations: list[str]
    metadata: dict[str, Any]

@mcp.tool()
def analyze_data(data: list[float]) -> AnalysisResult:
    """Analyze numerical data and return structured results."""
    avg = sum(data) / len(data)
    score = min(avg / 100, 1.0)

    return AnalysisResult(
        summary=f"Analyzed {len(data)} data points",
        score=score,
        recommendations=["Consider more data points"] if len(data) < 10 else [],
        metadata={"count": len(data), "average": avg}
    )
```
