# Context

The Context object provides tools and resources with access to MCP capabilities like logging, progress reporting, and resource access. It's automatically injected into functions that request it through type annotations.

## Overview

The Context object enables:

- **Logging**: Send messages to the client at different log levels
- **Progress reporting**: Update clients on long-running operations
- **Resource access**: Read other resources from within tools/resources
- **Request metadata**: Access request IDs, client information, and session data

Context is only available during request processing and provides a clean interface to MCP's underlying capabilities.

## Context Injection

### Automatic Injection

FastMCP automatically injects Context into functions that request it via type hints:

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Server")

@mcp.tool()
async def tool_with_context(x: int, ctx: Context) -> str:
    """Tool that uses context capabilities."""
    await ctx.info(f"Processing value: {x}")
    return f"Processed: {x}"

@mcp.resource("data://{id}")
async def resource_with_context(id: str, context: Context) -> str:
    """Resource that uses context capabilities."""
    await context.debug(f"Fetching data for ID: {id}")
    return f"Data for {id}"
```

### Parameter Naming

The context parameter can have any name as long as it's typed as `Context`:

```python
@mcp.tool()
async def tool_ctx(x: int, ctx: Context) -> str:
    await ctx.info("Using 'ctx' parameter name")
    return str(x)

@mcp.tool()
async def tool_context(x: int, context: Context) -> str:
    await context.info("Using 'context' parameter name")
    return str(x)

@mcp.tool()
async def tool_mcp_context(x: int, mcp_context: Context) -> str:
    await mcp_context.info("Using 'mcp_context' parameter name")
    return str(x)
```

### Mixed Parameters

Context can be mixed with other parameters in any order:

```python
@mcp.tool()
async def mixed_params(
    required_param: str,
    ctx: Context,
    optional_param: int = 42
) -> str:
    """Context mixed with other parameters."""
    await ctx.info(f"Required: {required_param}, Optional: {optional_param}")
    return f"Result: {required_param}_{optional_param}"
```

## Logging

### Log Levels

Send messages to the client at different severity levels:

```python
@mcp.tool()
async def logging_example(data: str, ctx: Context) -> str:
    """Demonstrate different log levels."""

    # Debug information (detailed diagnostic info)
    await ctx.debug(f"Starting processing with data: {data}")

    # General information
    await ctx.info("Processing data...")

    # Warning about potential issues
    if len(data) > 1000:
        await ctx.warning("Large data detected, processing may take longer")

    # Error conditions
    if not data.strip():
        await ctx.error("Empty data provided")
        raise ValueError("Data cannot be empty")

    return f"Processed: {data}"
```

### Structured Logging

```python
@mcp.tool()
async def structured_logging(file_path: str, ctx: Context) -> dict:
    """Example of structured logging with context."""

    await ctx.info(f"Processing file: {file_path}")

    try:
        # Simulate file processing
        file_size = len(file_path) * 100  # Mock calculation

        await ctx.debug(f"File size calculated: {file_size} bytes")

        if file_size > 10000:
            await ctx.warning(f"Large file detected: {file_size} bytes")

        result = {
            "file_path": file_path,
            "size": file_size,
            "status": "processed"
        }

        await ctx.info("File processing completed successfully")
        return result

    except Exception as e:
        await ctx.error(f"Failed to process file {file_path}: {e}")
        raise
```

### Custom Logger Names

```python
@mcp.tool()
async def custom_logger(data: str, ctx: Context) -> str:
    """Use custom logger names for organization."""

    # Use the low-level log method with custom logger name
    await ctx.log("info", "Starting data validation", logger_name="validator")

    if not data:
        await ctx.log("error", "Validation failed: empty data", logger_name="validator")
        raise ValueError("Data is required")

    await ctx.log("info", "Validation passed", logger_name="validator")
    await ctx.log("info", "Processing data", logger_name="processor")

    result = data.upper()

    await ctx.log("info", "Processing completed", logger_name="processor")
    return result
```

## Progress Reporting

### Basic Progress

Report progress for long-running operations:

```python
import asyncio

@mcp.tool()
async def long_operation(items: list[str], ctx: Context) -> list[str]:
    """Demonstrate progress reporting."""

    total = len(items)
    results = []

    await ctx.info(f"Processing {total} items...")

    for i, item in enumerate(items):
        # Report progress with current/total and optional message
        await ctx.report_progress(i, total, f"Processing {item}")

        # Simulate work
        await asyncio.sleep(0.1)
        results.append(f"processed_{item}")

        await ctx.debug(f"Completed item {i + 1}/{total}")

    # Report completion
    await ctx.report_progress(total, total, "Complete")
    await ctx.info("All items processed successfully")

    return results
```

### Percentage Progress

```python
@mcp.tool()
async def percentage_progress(iterations: int, ctx: Context) -> str:
    """Show progress as percentages."""

    await ctx.info(f"Starting {iterations} iterations")

    for i in range(iterations):
        # Calculate percentage
        progress_pct = (i / iterations) * 100

        # Report with percentage in message
        await ctx.report_progress(
            progress=i,
            total=iterations,
            message=f"Progress: {progress_pct:.1f}%"
        )

        # Simulate work
        await asyncio.sleep(0.05)

    await ctx.report_progress(iterations, iterations, "100% Complete")
    return f"Completed {iterations} iterations"
```

### Multi-Stage Progress

```python
@mcp.tool()
async def multi_stage_operation(data: list[str], ctx: Context) -> dict:
    """Progress reporting across multiple stages."""

    total_items = len(data)
    stages = ["validation", "processing", "optimization", "finalization"]

    results = {"processed": [], "errors": []}

    for stage_idx, stage in enumerate(stages):
        await ctx.info(f"Stage {stage_idx + 1}/{len(stages)}: {stage}")

        for item_idx, item in enumerate(data):
            # Calculate overall progress across all stages
            overall_progress = (stage_idx * total_items + item_idx)
            overall_total = len(stages) * total_items

            await ctx.report_progress(
                progress=overall_progress,
                total=overall_total,
                message=f"{stage.title()}: {item} ({item_idx + 1}/{total_items})"
            )

            # Simulate stage-specific work
            if stage == "validation" and not item:
                results["errors"].append(f"Empty item at index {item_idx}")
                continue

            await asyncio.sleep(0.02)  # Simulate work

            if stage == "processing":
                results["processed"].append(f"{stage}_{item}")

    await ctx.report_progress(
        progress=len(stages) * total_items,
        total=len(stages) * total_items,
        message="All stages complete"
    )

    return results
```

## Resource Access

### Reading Resources

Access other resources from within tools and resources:

```python
@mcp.tool()
async def config_aware_tool(setting_name: str, ctx: Context) -> str:
    """Tool that reads configuration from resources."""

    try:
        # Read configuration resource
        config_data = await ctx.read_resource("config://app")
        await ctx.info("Successfully loaded configuration")

        # Parse configuration (assuming it's JSON)
        import json
        config = json.loads(config_data[0].content)  # type: ignore

        if setting_name in config:
            value = config[setting_name]
            await ctx.info(f"Found setting {setting_name}: {value}")
            return f"{setting_name} = {value}"
        else:
            await ctx.warning(f"Setting {setting_name} not found in configuration")
            return f"Setting {setting_name} not found"

    except Exception as e:
        await ctx.error(f"Failed to read configuration: {e}")
        raise

@mcp.tool()
async def data_processor(source: str, ctx: Context) -> dict:
    """Process data from various sources."""

    await ctx.info(f"Reading data from {source}")

    try:
        # Read data resource
        resource_data = await ctx.read_resource(f"data://{source}")

        content = resource_data[0].content
        mime_type = resource_data[0].mime_type

        await ctx.debug(f"Received {len(content)} chars of {mime_type} data")

        # Process based on MIME type
        if mime_type == "application/json":
            import json
            data = json.loads(content)  # type: ignore
            await ctx.info("Parsed JSON data successfully")
        else:
            data = {"raw_content": content}
            await ctx.info("Treating as raw text data")

        return {
            "source": source,
            "mime_type": mime_type,
            "processed_data": data
        }

    except Exception as e:
        await ctx.error(f"Failed to process data from {source}: {e}")
        raise
```

### Cross-Resource Dependencies

```python
@mcp.resource("report://{report_id}")
async def generate_report(report_id: str, ctx: Context) -> str:
    """Generate a report that depends on other resources."""

    await ctx.info(f"Generating report {report_id}")

    try:
        # Read report template
        template_data = await ctx.read_resource(f"template://report_{report_id}")
        template = template_data[0].content

        await ctx.debug("Loaded report template")

        # Read data for the report
        data_resource = await ctx.read_resource(f"data://report_data_{report_id}")
        data = data_resource[0].content

        await ctx.debug("Loaded report data")

        # Simple template substitution (in real case, use proper templating)
        report = template.replace("{{data}}", str(data))  # type: ignore
        report = report.replace("{{report_id}}", report_id)  # type: ignore

        await ctx.info("Report generated successfully")
        return report

    except Exception as e:
        await ctx.error(f"Failed to generate report {report_id}: {e}")
        raise ValueError(f"Report generation failed: {e}")
```

## Request Metadata

### Request Information

Access information about the current request:

```python
@mcp.tool()
async def request_info_tool(ctx: Context) -> dict:
    """Tool that provides information about the current request."""

    # Get request ID
    request_id = ctx.request_id
    await ctx.info(f"Processing request {request_id}")

    # Get client ID (if available)
    client_id = ctx.client_id
    if client_id:
        await ctx.info(f"Request from client: {client_id}")
    else:
        await ctx.debug("No client ID available")

    return {
        "request_id": request_id,
        "client_id": client_id,
        "timestamp": "2024-01-01T12:00:00Z"  # You could add actual timestamp
    }
```

### Session Access

Access the underlying session for advanced use cases:

```python
@mcp.tool()
async def advanced_session_tool(ctx: Context) -> dict:
    """Tool that accesses session information."""

    # Access session (for advanced use cases)
    session = ctx.session

    await ctx.info("Accessing session information")

    # You can use session for advanced MCP operations
    # This is for advanced users who need direct access

    return {
        "request_id": ctx.request_id,
        "has_session": session is not None,
        "session_type": type(session).__name__
    }
```

## Error Handling with Context

### Graceful Error Reporting

```python
@mcp.tool()
async def robust_tool(data: dict, ctx: Context) -> dict:
    """Tool with comprehensive error handling and context logging."""

    try:
        await ctx.info("Starting data processing")

        # Validate input
        if not isinstance(data, dict):
            await ctx.error("Invalid input: expected dictionary")
            raise TypeError("Input must be a dictionary")

        if "required_field" not in data:
            await ctx.error("Missing required field in input data")
            raise ValueError("required_field is mandatory")

        await ctx.debug(f"Processing data with keys: {list(data.keys())}")

        # Process data
        result = {"processed": True, "original": data}

        await ctx.info("Data processing completed successfully")
        return result

    except TypeError as e:
        await ctx.error(f"Type error: {e}")
        raise
    except ValueError as e:
        await ctx.error(f"Value error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during processing: {e}")
        raise
```

### Resource Error Handling

```python
@mcp.tool()
async def safe_resource_reader(resource_uri: str, ctx: Context) -> dict:
    """Safely read resources with error handling."""

    await ctx.info(f"Attempting to read resource: {resource_uri}")

    try:
        resource_data = await ctx.read_resource(resource_uri)

        if not resource_data:
            await ctx.warning(f"No data returned for resource: {resource_uri}")
            return {"status": "empty", "uri": resource_uri}

        content = resource_data[0].content
        mime_type = resource_data[0].mime_type

        await ctx.info(f"Successfully read {len(content)} chars of {mime_type} data")

        return {
            "status": "success",
            "uri": resource_uri,
            "mime_type": mime_type,
            "content_length": len(content)
        }

    except Exception as e:
        await ctx.error(f"Failed to read resource {resource_uri}: {e}")

        return {
            "status": "error",
            "uri": resource_uri,
            "error": str(e)
        }
```

## Advanced Context Usage

### Performance Monitoring

```python
import time

@mcp.tool()
async def performance_monitored_tool(data: list[str], ctx: Context) -> dict:
    """Tool that monitors and reports performance metrics."""

    start_time = time.time()
    await ctx.info(f"Starting processing of {len(data)} items")

    results = []

    for i, item in enumerate(data):
        item_start = time.time()

        # Simulate processing
        await asyncio.sleep(0.01)
        processed_item = f"processed_{item}"
        results.append(processed_item)

        item_time = time.time() - item_start

        # Report progress with timing
        await ctx.report_progress(
            progress=i + 1,
            total=len(data),
            message=f"Item {i + 1}: {item_time:.3f}s"
        )

        # Log slow items
        if item_time > 0.05:
            await ctx.warning(f"Slow processing detected for item {i}: {item_time:.3f}s")

    total_time = time.time() - start_time
    avg_time = total_time / len(data) if data else 0

    await ctx.info(f"Processing completed in {total_time:.3f}s (avg: {avg_time:.3f}s per item)")

    return {
        "results": results,
        "performance": {
            "total_time": total_time,
            "average_time": avg_time,
            "items_processed": len(data)
        }
    }
```

### Conditional Logging

```python
@mcp.tool()
async def conditional_logging_tool(
    data: list[str],
    verbose: bool = False,
    ctx: Context
) -> list[str]:
    """Tool with conditional logging based on parameters."""

    log_level = "debug" if verbose else "info"

    await ctx.log(log_level, f"Starting processing with verbose={verbose}")

    results = []

    for i, item in enumerate(data):
        if verbose:
            await ctx.debug(f"Processing item {i}: {item}")

        # Simulate processing
        result = item.upper()
        results.append(result)

        if verbose:
            await ctx.debug(f"Item {i} result: {result}")
        elif i % 10 == 0:  # Log every 10th item when not verbose
            await ctx.info(f"Processed {i + 1}/{len(data)} items")

    await ctx.info(f"Completed processing {len(data)} items")
    return results
```

## Best Practices

### 1. Always Handle Context Gracefully

```python
@mcp.tool()
async def graceful_context_tool(data: str, ctx: Context) -> str:
    """Tool that handles context operations gracefully."""

    try:
        await ctx.info("Starting processing")

        # Main processing logic
        result = data.upper()

        await ctx.info("Processing completed successfully")
        return result

    except Exception as e:
        # Always log errors before re-raising
        await ctx.error(f"Processing failed: {e}")
        raise
```

### 2. Use Appropriate Log Levels

```python
@mcp.tool()
async def well_logged_tool(config: dict, ctx: Context) -> dict:
    """Tool demonstrating appropriate log level usage."""

    # Debug: Detailed diagnostic information
    await ctx.debug(f"Tool called with config keys: {list(config.keys())}")

    # Info: General information about progress
    await ctx.info("Validating configuration")

    # Warning: Something unexpected but not fatal
    if "deprecated_field" in config:
        await ctx.warning("Configuration uses deprecated field 'deprecated_field'")

    # Error: Something went wrong
    if not config.get("required_setting"):
        await ctx.error("Missing required_setting in configuration")
        raise ValueError("required_setting is mandatory")

    await ctx.info("Configuration validation complete")
    return {"status": "valid", "config": config}
```

### 3. Provide Meaningful Progress Updates

```python
@mcp.tool()
async def meaningful_progress_tool(files: list[str], ctx: Context) -> list[dict]:
    """Tool with meaningful progress reporting."""

    total_files = len(files)
    results = []

    await ctx.info(f"Processing {total_files} files")

    for i, file_path in enumerate(files):
        # Descriptive progress messages
        await ctx.report_progress(
            progress=i,
            total=total_files,
            message=f"Processing {file_path} ({i + 1}/{total_files})"
        )

        # Simulate file processing with sub-steps
        await ctx.debug(f"Reading file: {file_path}")

        # Simulate work
        await asyncio.sleep(0.1)

        result = {
            "file": file_path,
            "size": len(file_path) * 10,  # Mock size
            "status": "processed"
        }
        results.append(result)

        await ctx.debug(f"Completed processing: {file_path}")

    await ctx.report_progress(total_files, total_files, "All files processed")
    await ctx.info(f"Successfully processed {total_files} files")

    return results
```

### 4. Handle Resource Dependencies

```python
@mcp.tool()
async def resource_dependent_tool(config_name: str, ctx: Context) -> dict:
    """Tool that properly handles resource dependencies."""

    await ctx.info(f"Loading configuration: {config_name}")

    try:
        # Try to read primary config
        config_data = await ctx.read_resource(f"config://{config_name}")
        await ctx.info("Primary configuration loaded")

    except Exception as e:
        await ctx.warning(f"Primary config failed: {e}")

        try:
            # Fallback to default config
            await ctx.info("Attempting to load default configuration")
            config_data = await ctx.read_resource("config://default")
            await ctx.info("Default configuration loaded as fallback")

        except Exception as fallback_error:
            await ctx.error(f"Both primary and default configs failed: {fallback_error}")
            raise ValueError("No configuration available")

    # Process configuration
    config_content = config_data[0].content
    await ctx.debug(f"Configuration content length: {len(config_content)}")

    return {
        "config_name": config_name,
        "loaded": True,
        "content_length": len(config_content)
    }
```
