# Debugging

Comprehensive guide to debugging FastMCP servers effectively during development and production, including logging, tracing, error handling, and troubleshooting techniques.

## Overview

FastMCP provides extensive debugging capabilities built on top of Python's logging system with Rich console integration, structured error handling, and context-aware debugging tools. This guide covers all aspects of debugging FastMCP servers from development to production deployment.

## Debug Configuration

### Environment Variables

FastMCP supports comprehensive debugging configuration through environment variables:

```bash
# Enable debug mode
export FASTMCP_DEBUG=true

# Set detailed logging level
export FASTMCP_LOG_LEVEL=DEBUG

# Disable warnings for development
export FASTMCP_WARN_ON_DUPLICATE_TOOLS=false
export FASTMCP_WARN_ON_DUPLICATE_RESOURCES=false
export FASTMCP_WARN_ON_DUPLICATE_PROMPTS=false

# Development server configuration
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=8080
```

### Programmatic Configuration

```python
from mcp.server.fastmcp import FastMCP

# Configure debug settings
mcp = FastMCP("debug-server")
mcp.settings.debug = True
mcp.settings.log_level = "DEBUG"
mcp.settings.warn_on_duplicate_tools = False

# Or pass settings during initialization
mcp = FastMCP(
    "debug-server",
    debug=True,
    log_level="DEBUG",
    warn_on_duplicate_tools=False
)

if __name__ == "__main__":
    mcp.run("streamable-http")
```

## Logging and Tracing

### Rich Console Integration

FastMCP uses Rich console for enhanced debugging output with syntax highlighting and formatted tracebacks:

```python
from mcp.server.fastmcp.utilities.logging import configure_logging

# Configure Rich logging with enhanced tracebacks
configure_logging(level="DEBUG")

# Example output will include:
# - Syntax-highlighted code in tracebacks
# - Formatted exception display
# - Structured log messages with timestamps
```

### Context-Based Logging in Tools

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("logging-server")

@mcp.tool()
async def debug_tool(operation: str, data: dict, ctx: Context) -> dict:
    """Tool demonstrating comprehensive logging."""

    # Debug level logging
    await ctx.debug(f"Starting operation: {operation}")
    await ctx.debug(f"Input data keys: {list(data.keys())}")

    # Info level logging
    await ctx.info(f"Processing {operation} with {len(data)} items")

    # Progress reporting for long operations
    total_steps = len(data)
    for i, (key, value) in enumerate(data.items()):
        await ctx.report_progress(
            progress=(i + 1) / total_steps,
            total=1.0,
            message=f"Processing {key}"
        )

        # Process each item
        await ctx.debug(f"Processing item {key}: {value}")

        # Simulate work
        import asyncio
        await asyncio.sleep(0.1)

    # Warning for edge cases
    if not data:
        await ctx.warning("No data provided for processing")

    # Error logging (without raising)
    if operation == "test_error":
        await ctx.error("Test error condition detected")

    result = {
        "operation": operation,
        "processed_items": len(data),
        "status": "completed"
    }

    await ctx.info(f"Operation {operation} completed successfully")
    return result

@mcp.tool()
async def request_info_tool(ctx: Context) -> dict:
    """Tool for inspecting request context."""
    return {
        "request_id": ctx.request_id,
        "client_id": ctx.client_id,
        "session_available": hasattr(ctx, 'session'),
        "lifespan_context_available": hasattr(ctx.request_context, 'lifespan_context')
    }
```

### Structured Logging

```python
import logging
import json

# Get FastMCP logger
logger = logging.getLogger("mcp.server.fastmcp")

@mcp.tool()
async def structured_logging_tool(data: dict, ctx: Context) -> str:
    """Tool demonstrating structured logging patterns."""

    # Structured logging with extra fields
    logger.debug(
        "Tool execution started",
        extra={
            "tool_name": "structured_logging_tool",
            "request_id": ctx.request_id,
            "data_size": len(data),
            "data_keys": list(data.keys())
        }
    )

    # Log with JSON context
    context = {
        "operation": "data_processing",
        "input_size": len(data),
        "timestamp": time.time()
    }

    await ctx.info(f"Processing context: {json.dumps(context)}")

    # Process data with detailed logging
    for key, value in data.items():
        logger.debug(
            "Processing data item",
            extra={
                "key": key,
                "value_type": type(value).__name__,
                "request_id": ctx.request_id
            }
        )

    return f"Processed {len(data)} items with structured logging"
```

## Error Handling and Stack Traces

### Exception Hierarchy

FastMCP provides a structured exception hierarchy for better debugging:

```python
from mcp.server.fastmcp.exceptions import (
    FastMCPError,
    ValidationError,
    ResourceError,
    ToolError
)

@mcp.tool()
async def error_demonstration_tool(
    error_type: str,
    message: str,
    ctx: Context
) -> str:
    """Tool demonstrating different error types."""

    await ctx.debug(f"Simulating error type: {error_type}")

    try:
        if error_type == "validation":
            raise ValidationError(f"Validation failed: {message}")
        elif error_type == "resource":
            raise ResourceError(f"Resource error: {message}")
        elif error_type == "tool":
            raise ToolError(f"Tool error: {message}")
        elif error_type == "generic":
            raise FastMCPError(f"Generic FastMCP error: {message}")
        elif error_type == "python":
            raise ValueError(f"Standard Python error: {message}")
        else:
            await ctx.warning(f"Unknown error type: {error_type}")
            return f"No error simulated for type: {error_type}"

    except Exception as e:
        # Log the error with context
        await ctx.error(f"Error occurred: {type(e).__name__}: {e}")

        # Log stack trace in debug mode
        import traceback
        await ctx.debug(f"Stack trace: {traceback.format_exc()}")

        # Re-raise to let FastMCP handle it
        raise
```

### Custom Error Handling

```python
import traceback
import sys

@mcp.tool()
async def robust_error_handling_tool(
    operation: str,
    fail_probability: float,
    ctx: Context
) -> dict:
    """Tool with comprehensive error handling."""

    await ctx.debug(f"Starting {operation} with fail rate {fail_probability}")

    try:
        # Simulate operation that might fail
        import random
        if random.random() < fail_probability:
            raise RuntimeError(f"Simulated failure in {operation}")

        # Successful operation
        result = {"operation": operation, "status": "success"}
        await ctx.info(f"Operation {operation} completed successfully")
        return result

    except Exception as e:
        # Comprehensive error logging
        error_info = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "operation": operation,
            "fail_probability": fail_probability
        }

        # Log error details
        await ctx.error(f"Operation failed: {error_info}")

        # In debug mode, log full traceback
        if mcp.settings.debug:
            tb = traceback.format_exc()
            await ctx.debug(f"Full traceback:\n{tb}")

        # Log system information for debugging
        await ctx.debug(f"Python version: {sys.version}")
        await ctx.debug(f"Platform: {sys.platform}")

        # Return error information instead of raising
        # (or raise depending on your error handling strategy)
        return {
            "operation": operation,
            "status": "error",
            "error": error_info
        }
```

## Request and Response Debugging

### Request Tracing

```python
import time
import uuid

@mcp.tool()
async def request_tracing_tool(
    data: str,
    trace_id: str = None,
    ctx: Context
) -> dict:
    """Tool demonstrating request tracing patterns."""

    # Generate trace ID if not provided
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    await ctx.debug(f"[{trace_id}] Request started")
    await ctx.debug(f"[{trace_id}] Input data length: {len(data)}")
    await ctx.debug(f"[{trace_id}] Request ID: {ctx.request_id}")
    await ctx.debug(f"[{trace_id}] Client ID: {ctx.client_id}")

    # Simulate processing stages
    stages = ["validation", "processing", "formatting", "completion"]

    for i, stage in enumerate(stages):
        stage_start = time.time()
        await ctx.debug(f"[{trace_id}] Stage {i+1}: {stage} started")

        # Simulate stage work
        import asyncio
        await asyncio.sleep(0.1)

        stage_duration = time.time() - stage_start
        await ctx.debug(f"[{trace_id}] Stage {i+1}: {stage} completed in {stage_duration:.3f}s")

        # Report progress
        await ctx.report_progress(
            progress=(i + 1) / len(stages),
            total=1.0,
            message=f"[{trace_id}] Completed {stage}"
        )

    total_duration = time.time() - start_time

    result = {
        "trace_id": trace_id,
        "request_id": ctx.request_id,
        "client_id": ctx.client_id,
        "processing_time": total_duration,
        "stages_completed": len(stages),
        "data_length": len(data)
    }

    await ctx.info(f"[{trace_id}] Request completed in {total_duration:.3f}s")

    return result
```

### Response Validation

```python
from pydantic import BaseModel, ValidationError
from typing import Any

class ToolResponse(BaseModel):
    """Response model for validation."""
    status: str
    data: Any
    timestamp: float
    metadata: dict = {}

@mcp.tool()
async def validated_response_tool(
    operation: str,
    ctx: Context
) -> dict:
    """Tool demonstrating response validation."""

    await ctx.debug("Preparing response with validation")

    # Prepare response data
    response_data = {
        "status": "success",
        "data": f"Processed {operation}",
        "timestamp": time.time(),
        "metadata": {
            "operation": operation,
            "request_id": ctx.request_id
        }
    }

    # Validate response before returning
    try:
        validated_response = ToolResponse(**response_data)
        await ctx.debug("Response validation successful")
        return validated_response.dict()

    except ValidationError as e:
        await ctx.error(f"Response validation failed: {e}")
        # Return error response
        return {
            "status": "error",
            "data": "Response validation failed",
            "timestamp": time.time(),
            "metadata": {"error": str(e)}
        }
```

## Transport-Specific Debugging

### Stdio Transport Debugging

```python
# stdio_debug_server.py
import sys
import logging

# Configure logging to stderr for stdio transport
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: use stderr to avoid interfering with MCP protocol
)

mcp = FastMCP("stdio-debug-server")
mcp.settings.debug = True
mcp.settings.log_level = "DEBUG"

@mcp.tool()
async def stdio_debug_tool(message: str, ctx: Context) -> str:
    """Tool for debugging stdio transport."""

    # Log to stderr (won't interfere with protocol)
    logging.debug(f"Stdio tool called with message: {message}")

    # Use context logging (goes to MCP client)
    await ctx.debug(f"Processing message: {message}")

    return f"Processed: {message}"

if __name__ == "__main__":
    print("Starting stdio debug server...", file=sys.stderr)
    mcp.run("stdio")
```

### HTTP Transport Debugging

```python
import uvicorn

mcp = FastMCP("http-debug-server")
mcp.settings.debug = True
mcp.settings.log_level = "DEBUG"
mcp.settings.host = "127.0.0.1"
mcp.settings.port = 8080

@mcp.custom_route("/debug/health", methods=["GET"])
async def debug_health(request):
    """Debug health endpoint."""
    return JSONResponse({
        "status": "healthy",
        "debug_mode": mcp.settings.debug,
        "log_level": mcp.settings.log_level,
        "tools_count": len(mcp._tool_manager.tools),
        "timestamp": time.time()
    })

@mcp.custom_route("/debug/logs", methods=["GET"])
async def debug_logs(request):
    """Endpoint to retrieve recent logs."""
    # In a real implementation, you'd collect logs from a handler
    return JSONResponse({
        "message": "Log retrieval endpoint",
        "note": "Implement log collection for production use"
    })

@mcp.tool()
async def http_debug_tool(data: dict, ctx: Context) -> dict:
    """Tool for debugging HTTP transport."""

    # HTTP-specific debugging
    await ctx.debug(f"HTTP tool called with data: {data}")
    await ctx.debug(f"Request ID: {ctx.request_id}")

    # Simulate HTTP-specific operations
    await ctx.info("Performing HTTP-specific processing")

    return {
        "processed_data": data,
        "transport": "http",
        "debug_mode": mcp.settings.debug
    }

if __name__ == "__main__":
    print(f"Starting HTTP debug server on {mcp.settings.host}:{mcp.settings.port}")
    mcp.run("streamable-http")
```

## Resource and Tool Debugging

### Resource Debugging

```python
from mcp.server.fastmcp.resources.base import Resource
from pydantic import AnyUrl

@mcp.resource("debug://static/{name}")
def debug_static_resource(name: str) -> str:
    """Debug static resource with logging."""

    # Log resource access
    logger = logging.getLogger(__name__)
    logger.debug(f"Accessing static resource: {name}")

    resources = {
        "config": "Debug configuration data",
        "status": "Debug status information",
        "logs": "Debug log entries"
    }

    if name in resources:
        logger.debug(f"Resource {name} found")
        return resources[name]
    else:
        logger.warning(f"Resource {name} not found")
        raise ValueError(f"Resource not found: {name}")

class DebugDynamicResource(Resource):
    """Custom resource class with debugging."""

    def __init__(self, uri: str, debug_info: dict):
        super().__init__(uri=uri)
        self.debug_info = debug_info

        # Log resource creation
        logger.debug(f"Created debug resource: {uri} with info: {debug_info}")

    async def read(self) -> str:
        """Read resource with debug logging."""
        logger.debug(f"Reading debug resource: {self.uri}")

        return json.dumps({
            "uri": self.uri,
            "debug_info": self.debug_info,
            "read_timestamp": time.time()
        })

@mcp.resource("debug://dynamic/{resource_id}")
async def debug_dynamic_resource(resource_id: str) -> DebugDynamicResource:
    """Dynamic resource with debugging."""

    debug_info = {
        "resource_id": resource_id,
        "creation_time": time.time(),
        "debug_mode": mcp.settings.debug
    }

    return DebugDynamicResource(
        uri=f"debug://dynamic/{resource_id}",
        debug_info=debug_info
    )
```

### Tool Manager Debugging

```python
@mcp.tool()
async def debug_tool_manager(ctx: Context) -> dict:
    """Tool to inspect tool manager state."""

    tool_manager = mcp._tool_manager

    # Get tool information
    tools_info = {}
    for name, tool in tool_manager.tools.items():
        tools_info[name] = {
            "name": tool.name,
            "description": tool.description,
            "is_async": tool.is_async,
            "context_kwarg": tool.context_kwarg,
            "parameter_count": len(tool.fn_metadata.parameters)
        }

    await ctx.debug(f"Tool manager has {len(tools_info)} tools")

    return {
        "tools_count": len(tools_info),
        "tools": tools_info,
        "warn_on_duplicates": tool_manager.warn_on_duplicate_tools
    }

@mcp.tool()
async def debug_resource_manager(ctx: Context) -> dict:
    """Tool to inspect resource manager state."""

    resource_manager = mcp._resource_manager

    # Get resource information
    resources_info = {}
    for uri, resource in resource_manager.resources.items():
        resources_info[uri] = {
            "uri": uri,
            "type": type(resource).__name__,
            "name": getattr(resource, 'name', None)
        }

    templates_info = {}
    for pattern, template in resource_manager._templates.items():
        templates_info[pattern] = {
            "pattern": pattern,
            "type": type(template).__name__
        }

    await ctx.debug(f"Resource manager has {len(resources_info)} resources and {len(templates_info)} templates")

    return {
        "resources_count": len(resources_info),
        "templates_count": len(templates_info),
        "resources": resources_info,
        "templates": templates_info
    }
```

## Performance Debugging

### Timing and Profiling

```python
import time
import functools
import asyncio
from typing import Callable

def debug_timing(func: Callable) -> Callable:
    """Decorator to add timing information to tools."""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        ctx = kwargs.get('ctx')

        if ctx:
            await ctx.debug(f"Starting {func.__name__}")

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            if ctx:
                await ctx.debug(f"Completed {func.__name__} in {duration:.3f}s")

            return result
        except Exception as e:
            duration = time.time() - start_time
            if ctx:
                await ctx.error(f"Failed {func.__name__} after {duration:.3f}s: {e}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        ctx = kwargs.get('ctx')

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            if ctx and hasattr(ctx, 'debug'):
                # Can't await in sync function, but we can log
                logging.debug(f"Completed {func.__name__} in {duration:.3f}s")

            return result
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"Failed {func.__name__} after {duration:.3f}s: {e}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

@mcp.tool()
@debug_timing
async def performance_debug_tool(
    operation_count: int,
    delay_seconds: float,
    ctx: Context
) -> dict:
    """Tool for performance debugging."""

    await ctx.info(f"Starting performance test: {operation_count} operations with {delay_seconds}s delay")

    operation_times = []

    for i in range(operation_count):
        op_start = time.time()

        # Simulate work
        await asyncio.sleep(delay_seconds)

        op_duration = time.time() - op_start
        operation_times.append(op_duration)

        await ctx.report_progress(
            progress=(i + 1) / operation_count,
            total=1.0,
            message=f"Operation {i + 1} completed in {op_duration:.3f}s"
        )

    # Calculate statistics
    avg_time = sum(operation_times) / len(operation_times)
    min_time = min(operation_times)
    max_time = max(operation_times)

    result = {
        "operation_count": operation_count,
        "total_time": sum(operation_times),
        "average_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "operation_times": operation_times
    }

    await ctx.info(f"Performance test completed: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")

    return result
```

### Memory Debugging

```python
import psutil
import gc
import sys

@mcp.tool()
async def memory_debug_tool(ctx: Context) -> dict:
    """Tool for memory debugging and inspection."""

    # Get process memory info
    process = psutil.Process()
    memory_info = process.memory_info()

    # Get Python garbage collection stats
    gc_stats = {}
    for i, stats in enumerate(gc.get_stats()):
        gc_stats[f"generation_{i}"] = stats

    # Get object counts
    object_counts = {}
    for obj_type in [dict, list, str, int, float]:
        count = len([obj for obj in gc.get_objects() if type(obj) is obj_type])
        object_counts[obj_type.__name__] = count

    await ctx.debug(f"Memory usage: RSS={memory_info.rss / 1024 / 1024:.2f}MB")
    await ctx.debug(f"GC collections: {gc.get_count()}")

    result = {
        "memory": {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        },
        "garbage_collection": {
            "counts": gc.get_count(),
            "stats": gc_stats,
            "total_objects": len(gc.get_objects())
        },
        "object_counts": object_counts,
        "python_info": {
            "version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
    }

    return result
```

## Integration with Python Debugging Tools

### PyDebugger Integration

```python
import pdb
import sys

@mcp.tool()
async def debugger_tool(
    message: str,
    enable_pdb: bool = False,
    ctx: Context
) -> str:
    """Tool that can trigger Python debugger."""

    await ctx.debug(f"Debugger tool called with message: {message}")

    if enable_pdb:
        await ctx.warning("Triggering Python debugger (pdb)")
        # Set breakpoint for debugging
        pdb.set_trace()

    # Process message
    result = f"Processed: {message}"

    await ctx.debug(f"Returning result: {result}")

    return result

# For development with debugpy (VS Code debugging)
def enable_remote_debugging(port: int = 5678):
    """Enable remote debugging with debugpy."""
    try:
        import debugpy
        debugpy.listen(port)
        print(f"Waiting for debugger on port {port}...")
        debugpy.wait_for_client()
        print("Debugger attached!")
    except ImportError:
        print("debugpy not available. Install with: pip install debugpy")

# Usage in development
if __name__ == "__main__":
    if "--debug-remote" in sys.argv:
        enable_remote_debugging()

    mcp.run("stdio")
```

## Production Debugging

### Health Check and Diagnostics

```python
@mcp.custom_route("/debug/health", methods=["GET"])
async def debug_health_check(request) -> JSONResponse:
    """Comprehensive health check for debugging."""

    start_time = time.time()

    health_data = {
        "status": "healthy",
        "timestamp": start_time,
        "server": {
            "name": mcp.name,
            "debug_mode": mcp.settings.debug,
            "log_level": mcp.settings.log_level
        },
        "components": {},
        "metrics": {}
    }

    # Check tool manager
    try:
        tools_count = len(mcp._tool_manager.tools)
        health_data["components"]["tools"] = {
            "status": "healthy",
            "count": tools_count
        }
    except Exception as e:
        health_data["components"]["tools"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check resource manager
    try:
        resources_count = len(mcp._resource_manager.resources)
        templates_count = len(mcp._resource_manager._templates)
        health_data["components"]["resources"] = {
            "status": "healthy",
            "resources_count": resources_count,
            "templates_count": templates_count
        }
    except Exception as e:
        health_data["components"]["resources"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # System metrics
    try:
        process = psutil.Process()
        health_data["metrics"] = {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "uptime_seconds": time.time() - process.create_time()
        }
    except Exception as e:
        health_data["metrics"] = {"error": str(e)}

    # Calculate response time
    health_data["response_time_ms"] = (time.time() - start_time) * 1000

    return JSONResponse(health_data)

@mcp.custom_route("/debug/config", methods=["GET"])
async def debug_config(request) -> JSONResponse:
    """Debug endpoint to show current configuration."""

    config_data = {
        "settings": {
            "debug": mcp.settings.debug,
            "log_level": mcp.settings.log_level,
            "host": mcp.settings.host,
            "port": mcp.settings.port,
            "warn_on_duplicate_tools": mcp.settings.warn_on_duplicate_tools,
            "warn_on_duplicate_resources": mcp.settings.warn_on_duplicate_resources,
            "warn_on_duplicate_prompts": mcp.settings.warn_on_duplicate_prompts
        },
        "environment": {
            key: value for key, value in os.environ.items()
            if key.startswith("FASTMCP_")
        },
        "python": {
            "version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
    }

    return JSONResponse(config_data)
```

## Best Practices

### Debug Guidelines

1. **Use Environment Variables**: Configure debugging through `FASTMCP_*` environment variables for easy deployment
2. **Structured Logging**: Include context information in all log messages
3. **Progress Reporting**: Use `ctx.report_progress()` for long-running operations
4. **Error Context**: Preserve error context when wrapping exceptions
5. **Transport Considerations**: Remember stdio uses stderr for logging to avoid protocol interference

### Performance Debugging

1. **Timing Decorators**: Use timing decorators for performance-critical tools
2. **Memory Monitoring**: Monitor memory usage in long-running servers
3. **Request Tracing**: Implement request tracing for complex workflows
4. **Health Checks**: Implement comprehensive health check endpoints

### Security Considerations

1. **Log Sanitization**: Don't log sensitive information in production
2. **Debug Mode**: Disable debug mode in production unless necessary
3. **Error Messages**: Don't expose internal details in error messages
4. **Access Control**: Secure debug endpoints with proper authentication

This comprehensive debugging guide provides all the tools and techniques needed to effectively debug FastMCP servers throughout the development lifecycle, from local development to production troubleshooting.
