# Performance Guide

Comprehensive guide for optimizing FastMCP servers, including benchmarking, scaling strategies, resource management, and performance monitoring.

## Quick Start

### Performance Basics

FastMCP is built on async Python and designed for high performance. Key principles:

- **Async by default**: Use `async/await` for I/O operations
- **Concurrent execution**: Multiple requests are handled concurrently
- **Resource pooling**: Share expensive resources like database connections
- **Caching**: Cache expensive computations and data

### Performance Checklist

```python
from mcp.server.fastmcp import FastMCP

# ✅ Good: Async operations
@mcp.tool()
async def fast_operation(data: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{data}")
        return response.text

# ❌ Bad: Blocking operations
@mcp.tool()
def slow_operation(data: str) -> str:
    import time
    time.sleep(1)  # Blocks entire server
    return "done"
```

## Async Programming

### 1. Async Tools and Resources

**Use async for I/O operations:**
```python
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("High Performance Server")

@mcp.tool()
async def fetch_multiple_apis(urls: list[str], ctx: Context) -> list[str]:
    """Fetch multiple APIs concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                ctx.warning(f"Failed to fetch {urls[i]}: {response}")
                results.append(f"Error: {response}")
            else:
                results.append(response.text)

        return results

@mcp.resource("data://batch/{batch_id}")
async def get_batch_data(batch_id: str) -> dict:
    """Process batch data asynchronously."""
    # Simulate async database query
    await asyncio.sleep(0.1)
    return {"batch_id": batch_id, "status": "processed"}

@mcp.tool()
async def parallel_processing(items: list[str], ctx: Context) -> dict:
    """Process multiple items in parallel."""
    async def process_item(item: str) -> str:
        # Simulate async processing
        await asyncio.sleep(0.01)
        return f"processed_{item}"

    await ctx.report_progress(0, len(items), "Starting batch processing")

    # Process in batches to avoid overwhelming the system
    batch_size = 10
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

        progress = min(i + batch_size, len(items))
        await ctx.report_progress(progress, len(items), f"Processed {progress} items")

    return {"total_processed": len(results), "results": results}
```

### 2. Async Context Managers

**Proper resource management:**
```python
from contextlib import asynccontextmanager
import asyncpg

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            "postgresql://user:pass@localhost/db",
            min_size=5,
            max_size=20,
            command_timeout=30
        )

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

# Global database manager
db = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastMCP):
    """Manage application lifespan with connection pooling."""
    await db.initialize()
    try:
        yield
    finally:
        await db.close()

mcp = FastMCP("Database Server", lifespan=lifespan)

@mcp.tool()
async def efficient_query(user_id: int) -> dict:
    """Efficient database query using connection pool."""
    async with db.pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return dict(result) if result else {}
```

## Caching Strategies

### 1. In-Memory Caching

**Simple LRU cache:**
```python
from functools import lru_cache
import asyncio
from typing import Dict, Any
import time

# Sync caching
@lru_cache(maxsize=1000)
def expensive_computation(data: str) -> str:
    """Cache expensive synchronous computations."""
    # Simulate expensive operation
    time.sleep(0.1)
    return f"processed_{data}"

@mcp.tool()
def cached_tool(data: str) -> str:
    """Tool using cached computation."""
    return expensive_computation(data)

# Async caching with manual cache
_async_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, float] = {}
CACHE_TTL = 300  # 5 minutes

async def cached_async_operation(key: str) -> str:
    """Async operation with TTL cache."""
    current_time = time.time()

    # Check cache
    if (key in _async_cache and
        key in _cache_timestamps and
        current_time - _cache_timestamps[key] < CACHE_TTL):
        return _async_cache[key]

    # Compute result
    await asyncio.sleep(0.1)  # Simulate async work
    result = f"computed_{key}_{current_time}"

    # Store in cache
    _async_cache[key] = result
    _cache_timestamps[key] = current_time

    return result

@mcp.tool()
async def cached_async_tool(key: str) -> str:
    """Tool using async cache."""
    return await cached_async_operation(key)
```

### 2. Advanced Caching

**Redis-based caching:**
```python
import json
import redis.asyncio as redis
from typing import Optional

class RedisCache:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(url)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL."""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass  # Fail silently for cache errors

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()

# Global cache instance
cache = RedisCache()

@asynccontextmanager
async def lifespan_with_cache(app: FastMCP):
    """Lifespan with Redis cache."""
    try:
        yield
    finally:
        await cache.close()

@mcp.tool()
async def cached_api_call(endpoint: str, ctx: Context) -> dict:
    """API call with Redis caching."""
    cache_key = f"api_call:{endpoint}"

    # Try cache first
    cached_result = await cache.get(cache_key)
    if cached_result:
        ctx.info("Cache hit")
        return cached_result

    # Make API call
    ctx.info("Cache miss, fetching from API")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{endpoint}")
        result = response.json()

    # Cache the result
    await cache.set(cache_key, result, ttl=600)  # 10 minutes

    return result
```

## Resource Management

### 1. Connection Pooling

**Database connection pooling:**
```python
import asyncpg
from contextlib import asynccontextmanager

class OptimizedDatabase:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        """Initialize optimized connection pool."""
        self.pool = await asyncpg.create_pool(
            "postgresql://user:pass@localhost/db",
            min_size=10,          # Minimum connections
            max_size=50,          # Maximum connections
            max_queries=50000,    # Max queries per connection
            max_inactive_connection_lifetime=300,  # 5 minutes
            command_timeout=60,   # Command timeout
            server_settings={
                "application_name": "fastmcp_server",
                "jit": "off",     # Disable JIT for predictable performance
            }
        )

    async def execute_query(self, query: str, *args) -> list:
        """Execute query with connection from pool."""
        async with self.pool.acquire() as conn:
            # Use prepared statements for better performance
            stmt = await conn.prepare(query)
            return await stmt.fetch(*args)

db = OptimizedDatabase()

@mcp.tool()
async def bulk_user_query(user_ids: list[int]) -> list[dict]:
    """Efficient bulk query using connection pooling."""
    if not user_ids:
        return []

    # Use ANY() for efficient bulk queries
    query = "SELECT * FROM users WHERE id = ANY($1)"
    results = await db.execute_query(query, user_ids)

    return [dict(row) for row in results]
```

### 2. HTTP Client Pooling

**Efficient HTTP client management:**
```python
import httpx
from contextlib import asynccontextmanager

class HTTPClientManager:
    def __init__(self):
        self.client = None

    async def initialize(self):
        """Initialize HTTP client with optimal settings."""
        timeout = httpx.Timeout(
            connect=5.0,    # Connection timeout
            read=30.0,      # Read timeout
            write=10.0,     # Write timeout
            pool=5.0        # Pool timeout
        )

        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )

        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            http2=True,  # Enable HTTP/2
            follow_redirects=True
        )

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

http_client = HTTPClientManager()

@asynccontextmanager
async def lifespan_with_http(app: FastMCP):
    """Lifespan with HTTP client management."""
    await http_client.initialize()
    try:
        yield
    finally:
        await http_client.close()

@mcp.tool()
async def efficient_api_calls(urls: list[str]) -> list[dict]:
    """Efficient API calls using shared client."""
    async def fetch_url(url: str) -> dict:
        try:
            response = await http_client.client.get(url)
            response.raise_for_status()
            return {"url": url, "status": "success", "data": response.json()}
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}

    # Use semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

    async def bounded_fetch(url: str) -> dict:
        async with semaphore:
            return await fetch_url(url)

    tasks = [bounded_fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## Performance Monitoring

### 1. Built-in Metrics

**Monitor server performance:**
```python
import time
import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any
import threading

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_in_progress": 0,
            "errors_total": 0,
            "start_time": time.time(),
        }
        self._lock = threading.Lock()

    def increment_request(self):
        with self._lock:
            self.metrics["requests_total"] += 1
            self.metrics["requests_in_progress"] += 1

    def decrement_request(self):
        with self._lock:
            self.metrics["requests_in_progress"] -= 1

    def increment_error(self):
        with self._lock:
            self.metrics["errors_total"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            process = psutil.Process()
            memory_info = process.memory_info()

            uptime = time.time() - self.metrics["start_time"]

            return {
                **self.metrics,
                "uptime_seconds": uptime,
                "memory_rss_mb": memory_info.rss / 1024 / 1024,
                "memory_vms_mb": memory_info.vms / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "thread_count": process.num_threads(),
                "fd_count": process.num_fds() if hasattr(process, 'num_fds') else 0,
                "timestamp": datetime.now().isoformat(),
            }

monitor = PerformanceMonitor()

@mcp.tool()
def get_server_metrics() -> Dict[str, Any]:
    """Get comprehensive server performance metrics."""
    return monitor.get_metrics()

# Decorator for monitoring tool performance
def monitored_tool(func):
    """Decorator to monitor tool performance."""
    async def wrapper(*args, **kwargs):
        monitor.increment_request()
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            monitor.increment_error()
            raise
        finally:
            monitor.decrement_request()
            duration = time.time() - start_time
            # Log slow operations
            if duration > 1.0:  # 1 second threshold
                print(f"Slow operation: {func.__name__} took {duration:.2f}s")

    return wrapper

@mcp.tool()
@monitored_tool
async def monitored_operation(data: str) -> str:
    """Tool with performance monitoring."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"Processed: {data}"
```

### 2. Health Checks

**Implement health check endpoints:**
```python
from starlette.responses import JSONResponse
from starlette.requests import Request

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Basic health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> JSONResponse:
    """Detailed metrics endpoint."""
    return JSONResponse(monitor.get_metrics())

@mcp.custom_route("/health/detailed", methods=["GET"])
async def detailed_health_check(request: Request) -> JSONResponse:
    """Detailed health check with dependency checks."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Check database connectivity
    try:
        if hasattr(db, 'pool') and db.pool:
            async with db.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["checks"]["database"] = "healthy"
        else:
            health_status["checks"]["database"] = "not_configured"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"

    # Check Redis cache
    try:
        if hasattr(cache, 'redis'):
            await cache.redis.ping()
            health_status["checks"]["cache"] = "healthy"
        else:
            health_status["checks"]["cache"] = "not_configured"
    except Exception as e:
        health_status["checks"]["cache"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"

    return JSONResponse(health_status)
```

## Optimization Techniques

### 1. Request Batching

**Batch multiple operations:**
```python
from collections import defaultdict
import asyncio

class RequestBatcher:
    def __init__(self, batch_size: int = 10, max_wait: float = 0.1):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.pending_requests = defaultdict(list)
        self._locks = defaultdict(asyncio.Lock)

    async def add_request(self, operation: str, request_data: Any) -> Any:
        """Add request to batch and wait for result."""
        async with self._locks[operation]:
            future = asyncio.get_event_loop().create_future()
            self.pending_requests[operation].append((request_data, future))

            # Process batch if full or start timer
            if len(self.pending_requests[operation]) >= self.batch_size:
                await self._process_batch(operation)
            else:
                asyncio.create_task(self._delayed_process(operation))

            return await future

    async def _delayed_process(self, operation: str):
        """Process batch after delay."""
        await asyncio.sleep(self.max_wait)
        async with self._locks[operation]:
            if self.pending_requests[operation]:
                await self._process_batch(operation)

    async def _process_batch(self, operation: str):
        """Process batch of requests."""
        requests = self.pending_requests[operation]
        self.pending_requests[operation] = []

        if not requests:
            return

        try:
            # Batch process all requests
            if operation == "database_query":
                results = await self._batch_database_query(
                    [req[0] for req in requests]
                )
            else:
                results = [f"processed_{req[0]}" for req in requests]

            # Resolve futures
            for (request_data, future), result in zip(requests, results):
                future.set_result(result)

        except Exception as e:
            # Reject all futures
            for request_data, future in requests:
                future.set_exception(e)

    async def _batch_database_query(self, user_ids: list[int]) -> list[dict]:
        """Batch database query."""
        async with db.pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT * FROM users WHERE id = ANY($1)", user_ids
            )
            # Map results back to original order
            result_map = {row['id']: dict(row) for row in results}
            return [result_map.get(uid, {}) for uid in user_ids]

batcher = RequestBatcher()

@mcp.tool()
async def batched_user_lookup(user_id: int) -> dict:
    """Look up user with automatic batching."""
    return await batcher.add_request("database_query", user_id)
```

### 2. Streaming and Pagination

**Handle large datasets efficiently:**
```python
from typing import AsyncGenerator

@mcp.tool()
async def stream_large_dataset(limit: int = 1000, ctx: Context) -> str:
    """Stream large dataset with progress reporting."""
    async def data_generator() -> AsyncGenerator[dict, None]:
        """Generate data in chunks."""
        for i in range(0, limit, 100):  # Process in chunks of 100
            chunk_size = min(100, limit - i)

            # Simulate database query
            await asyncio.sleep(0.01)

            for j in range(chunk_size):
                yield {"id": i + j, "data": f"item_{i + j}"}

            # Report progress
            await ctx.report_progress(i + chunk_size, limit, f"Processed {i + chunk_size} items")

    results = []
    async for item in data_generator():
        results.append(item)

    return f"Streamed {len(results)} items"

@mcp.resource("data://paginated/{page}")
async def paginated_data(page: int) -> dict:
    """Paginated resource for large datasets."""
    page_size = 50
    offset = (page - 1) * page_size

    # Simulate database query with pagination
    await asyncio.sleep(0.01)

    items = [
        {"id": i, "name": f"Item {i}"}
        for i in range(offset, offset + page_size)
    ]

    return {
        "page": page,
        "page_size": page_size,
        "items": items,
        "total_pages": 100,  # Example total
        "has_next": page < 100,
        "has_previous": page > 1
    }
```

## Benchmarking

### 1. Load Testing

**Test server performance under load:**
```python
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

async def benchmark_tool_performance():
    """Benchmark tool performance."""
    from mcp.shared.memory import create_connected_server_and_client_session

    # Create test server
    test_server = FastMCP("Benchmark Server")

    @test_server.tool()
    async def benchmark_tool(data: str) -> str:
        """Simple tool for benchmarking."""
        await asyncio.sleep(0.001)  # Simulate minimal work
        return f"processed_{data}"

    # Run benchmark
    async with create_connected_server_and_client_session(test_server._mcp_server) as (
        server_session,
        client_session,
    ):
        await client_session.initialize()

        # Warmup
        for _ in range(10):
            await client_session.call_tool("benchmark_tool", {"data": "warmup"})

        # Benchmark
        num_requests = 100
        start_time = time.time()

        tasks = [
            client_session.call_tool("benchmark_tool", {"data": f"test_{i}"})
            for i in range(num_requests)
        ]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        duration = end_time - start_time
        rps = num_requests / duration

        print(f"Benchmark Results:")
        print(f"  Requests: {num_requests}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Requests/sec: {rps:.2f}")
        print(f"  Avg latency: {duration/num_requests*1000:.2f}ms")

# Run benchmark
if __name__ == "__main__":
    asyncio.run(benchmark_tool_performance())
```

### 2. Performance Profiling

**Profile your FastMCP server:**
```python
import cProfile
import pstats
import io
from contextlib import contextmanager

@contextmanager
def profile_tool():
    """Context manager for profiling tool execution."""
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        print(s.getvalue())

@mcp.tool()
async def profiled_tool(data: str) -> str:
    """Tool with performance profiling."""
    with profile_tool():
        # Your tool logic here
        result = expensive_computation(data)
        return result

# Memory profiling with tracemalloc
import tracemalloc

@mcp.tool()
async def memory_profiled_tool(data: str) -> str:
    """Tool with memory profiling."""
    tracemalloc.start()

    # Your tool logic
    result = process_large_data(data)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Memory usage: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
    return result
```

## Scaling Strategies

### 1. Horizontal Scaling

**Deploy multiple server instances:**
```python
# Load balancer configuration (nginx example)
"""
upstream fastmcp_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    location / {
        proxy_pass http://fastmcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""

# Server configuration for horizontal scaling
import os

def create_scaled_server():
    """Create server instance for horizontal scaling."""
    # Use different ports for each instance
    port = int(os.environ.get("SERVER_PORT", "8000"))
    worker_id = os.environ.get("WORKER_ID", "0")

    mcp = FastMCP(
        f"FastMCP Worker {worker_id}",
        port=port,
        # Use shared cache for consistency
        # Configure database connection pooling
    )

    return mcp
```

### 2. Vertical Scaling

**Optimize single server performance:**
```python
import multiprocessing

def configure_for_vertical_scaling():
    """Configure server for maximum single-machine performance."""
    # Calculate optimal settings based on system resources
    cpu_count = multiprocessing.cpu_count()

    return FastMCP(
        "High Performance Server",
        # Configure based on available resources
        debug=False,  # Disable debug in production
        log_level="WARNING",  # Reduce logging overhead

        # HTTP settings optimized for performance
        host="0.0.0.0",
        port=8000,

        # Database connection pool sizing
        # Rule of thumb: (CPU cores * 2) + effective spindle count
        # For SSD: CPU cores * 2
        # For network storage: depends on network latency
    )
```

## Best Practices Summary

### 1. Do's

```python
# ✅ Use async/await for I/O operations
@mcp.tool()
async def good_api_call() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.text

# ✅ Use connection pooling
async with db.pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM table")

# ✅ Implement caching
@lru_cache(maxsize=1000)
def cached_operation(data: str) -> str:
    return expensive_computation(data)

# ✅ Batch similar operations
async def batch_process(items: list[str]) -> list[str]:
    return await asyncio.gather(*[process_item(item) for item in items])

# ✅ Use progress reporting for long operations
async def long_operation(ctx: Context) -> str:
    for i in range(100):
        await asyncio.sleep(0.01)
        await ctx.report_progress(i, 100, f"Step {i}")
    return "complete"
```

### 2. Don'ts

```python
# ❌ Don't block the event loop
def bad_blocking_operation() -> str:
    time.sleep(1)  # Blocks everything
    return "done"

# ❌ Don't create new connections for each request
def bad_database_query() -> dict:
    conn = psycopg2.connect("postgresql://...")  # New connection each time
    result = conn.execute("SELECT * FROM table")
    return result

# ❌ Don't ignore resource cleanup
def bad_resource_handling() -> str:
    file = open("large_file.txt")  # Never closed
    return file.read()

# ❌ Don't process large datasets without streaming
def bad_large_dataset() -> list:
    return [expensive_operation(i) for i in range(1000000)]  # Memory explosion
```

This performance guide provides comprehensive strategies for building high-performance FastMCP servers that can handle production workloads efficiently.
