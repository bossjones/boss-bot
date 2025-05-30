# Lifespan Management

Comprehensive guide to managing server lifecycle, resource initialization, dependency injection, and graceful startup/shutdown patterns in FastMCP servers.

## Overview

Lifespan management in FastMCP enables proper resource lifecycle control, allowing you to initialize resources during server startup, make them available throughout the server's lifetime, and clean them up during shutdown. This is essential for database connections, HTTP clients, caches, and other long-lived resources.

## Basic Lifespan Patterns

### Simple Lifespan Context Manager

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context
import asyncio

@asynccontextmanager
async def basic_lifespan(server: FastMCP):
    """Basic lifespan with startup and shutdown hooks."""
    # Startup phase
    print("Server starting up...")

    # Initialize application state
    app_state = {
        "startup_time": time.time(),
        "request_count": 0,
        "status": "running"
    }

    try:
        # Yield control to the server
        yield app_state
    finally:
        # Shutdown phase
        print("Server shutting down...")
        app_state["status"] = "stopped"

# Create server with lifespan
mcp = FastMCP("basic-server", lifespan=basic_lifespan)

@mcp.tool()
async def get_server_stats(ctx: Context) -> dict:
    """Get server statistics from lifespan context."""
    # Access lifespan context
    app_state = ctx.request_context.lifespan_context

    # Update request count
    app_state["request_count"] += 1

    return {
        "startup_time": app_state["startup_time"],
        "request_count": app_state["request_count"],
        "status": app_state["status"],
        "uptime_seconds": time.time() - app_state["startup_time"]
    }

if __name__ == "__main__":
    mcp.run("stdio")
```

### Error Handling in Lifespan

```python
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def robust_lifespan(server: FastMCP):
    """Lifespan with comprehensive error handling."""
    context = {"initialized": False}

    try:
        # Startup with error handling
        logger.info("Starting server initialization...")

        # Initialize critical resources
        try:
            # Simulate resource initialization
            await asyncio.sleep(0.1)  # Database connection setup
            context["database"] = "connected"
            context["initialized"] = True
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        logger.info("Server initialization completed successfully")
        yield context

    except Exception as e:
        logger.error(f"Error during server lifecycle: {e}")
        context["initialized"] = False
        raise
    finally:
        # Cleanup with error handling
        logger.info("Starting server cleanup...")

        if context.get("database") == "connected":
            try:
                # Cleanup database connection
                await asyncio.sleep(0.1)  # Database cleanup
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error during database cleanup: {e}")

        logger.info("Server cleanup completed")

mcp = FastMCP("robust-server", lifespan=robust_lifespan)
```

## Database Integration Patterns

### Database Connection Pool Management

```python
import asyncpg
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_lifespan(server: FastMCP):
    """Lifespan managing PostgreSQL connection pool."""
    # Database configuration
    DATABASE_URL = "postgresql://user:password@localhost/dbname"

    # Initialize connection pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

    # Test connection
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")

    logger.info(f"Database pool created with {pool.get_size()} connections")

    context = {
        "db_pool": pool,
        "database_url": DATABASE_URL
    }

    try:
        yield context
    finally:
        # Close pool gracefully
        await pool.close()
        logger.info("Database pool closed")

mcp = FastMCP("database-server", lifespan=database_lifespan)

@mcp.tool()
async def create_user(name: str, email: str, ctx: Context) -> dict:
    """Create user using database pool from lifespan."""
    pool = ctx.request_context.lifespan_context["db_pool"]

    async with pool.acquire() as conn:
        # Insert user
        user_id = await conn.fetchval(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
            name, email
        )

        # Fetch created user
        user = await conn.fetchrow(
            "SELECT id, name, email, created_at FROM users WHERE id = $1",
            user_id
        )

        return dict(user)

@mcp.tool()
async def get_user(user_id: int, ctx: Context) -> dict | None:
    """Get user by ID using database pool."""
    pool = ctx.request_context.lifespan_context["db_pool"]

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name, email, created_at FROM users WHERE id = $1",
            user_id
        )

        return dict(user) if user else None
```

### SQLite with Connection Management

```python
import aiosqlite
from contextlib import asynccontextmanager

@asynccontextmanager
async def sqlite_lifespan(server: FastMCP):
    """Lifespan managing SQLite database."""
    db_path = "app_data.db"

    # Initialize database
    async with aiosqlite.connect(db_path) as db:
        # Create tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

    logger.info(f"SQLite database initialized: {db_path}")

    context = {"db_path": db_path}

    try:
        yield context
    finally:
        logger.info("SQLite database lifespan completed")

mcp = FastMCP("sqlite-server", lifespan=sqlite_lifespan)

@mcp.tool()
async def add_task(title: str, description: str = "", ctx: Context) -> dict:
    """Add task to SQLite database."""
    db_path = ctx.request_context.lifespan_context["db_path"]

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?) RETURNING id",
            (title, description)
        )
        task_id = (await cursor.fetchone())[0]
        await db.commit()

        # Fetch created task
        cursor = await db.execute(
            "SELECT id, title, description, completed, created_at FROM tasks WHERE id = ?",
            (task_id,)
        )
        task = await cursor.fetchone()

        return {
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "completed": bool(task[3]),
            "created_at": task[4]
        }
```

## HTTP Client and External Service Management

### HTTP Client Pool

```python
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def http_client_lifespan(server: FastMCP):
    """Lifespan managing HTTP client with connection pooling."""
    # Configure HTTP client with connection pooling
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    timeout = httpx.Timeout(10.0, read=30.0)

    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers={"User-Agent": "FastMCP Server/1.0"}
    ) as client:

        # Test external connectivity
        try:
            response = await client.get("https://httpbin.org/status/200")
            response.raise_for_status()
            logger.info("HTTP client connectivity verified")
        except Exception as e:
            logger.warning(f"HTTP client connectivity test failed: {e}")

        context = {
            "http_client": client,
            "external_apis": {
                "weather": "https://api.weather.com",
                "geocoding": "https://api.geocoding.com"
            }
        }

        yield context

mcp = FastMCP("http-client-server", lifespan=http_client_lifespan)

@mcp.tool()
async def fetch_weather(city: str, ctx: Context) -> dict:
    """Fetch weather data using managed HTTP client."""
    lifespan_ctx = ctx.request_context.lifespan_context
    client = lifespan_ctx["http_client"]
    weather_api = lifespan_ctx["external_apis"]["weather"]

    try:
        response = await client.get(f"{weather_api}/current", params={"city": city})
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        await ctx.error(f"Weather API request failed: {e}")
        raise
    except httpx.HTTPStatusError as e:
        await ctx.error(f"Weather API returned {e.response.status_code}")
        raise

@mcp.tool()
async def fetch_url(url: str, ctx: Context) -> dict:
    """Generic URL fetcher using managed HTTP client."""
    client = ctx.request_context.lifespan_context["http_client"]

    try:
        response = await client.get(url)
        response.raise_for_status()

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": response.headers.get("content-type"),
            "content": response.text[:1000]  # Limit content size
        }
    except Exception as e:
        await ctx.error(f"Failed to fetch URL {url}: {e}")
        raise
```

## Caching and State Management

### Redis Cache Integration

```python
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

@asynccontextmanager
async def redis_cache_lifespan(server: FastMCP):
    """Lifespan managing Redis cache."""
    redis_url = "redis://localhost:6379"

    # Initialize Redis connection
    redis_client = redis.from_url(redis_url)

    # Test Redis connectivity
    try:
        await redis_client.ping()
        logger.info("Redis cache connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    context = {
        "cache": redis_client,
        "cache_ttl": 3600  # 1 hour default TTL
    }

    try:
        yield context
    finally:
        await redis_client.close()
        logger.info("Redis cache connection closed")

mcp = FastMCP("redis-cache-server", lifespan=redis_cache_lifespan)

@mcp.tool()
async def cached_computation(input_data: str, ctx: Context) -> dict:
    """Perform computation with Redis caching."""
    lifespan_ctx = ctx.request_context.lifespan_context
    cache = lifespan_ctx["cache"]
    ttl = lifespan_ctx["cache_ttl"]

    # Generate cache key
    cache_key = f"computation:{hash(input_data)}"

    # Check cache
    cached_result = await cache.get(cache_key)
    if cached_result:
        await ctx.info("Cache hit")
        return json.loads(cached_result)

    # Perform computation
    await ctx.info("Cache miss - performing computation")
    result = {
        "input": input_data,
        "output": f"processed_{input_data}",
        "timestamp": time.time()
    }

    # Cache result
    await cache.setex(cache_key, ttl, json.dumps(result))

    return result

@mcp.tool()
async def clear_cache(pattern: str = "*", ctx: Context) -> dict:
    """Clear cache entries matching pattern."""
    cache = ctx.request_context.lifespan_context["cache"]

    keys = await cache.keys(f"computation:{pattern}")
    if keys:
        deleted_count = await cache.delete(*keys)
        await ctx.info(f"Cleared {deleted_count} cache entries")
        return {"cleared": deleted_count, "pattern": pattern}
    else:
        return {"cleared": 0, "pattern": pattern}
```

### In-Memory Cache

```python
from contextlib import asynccontextmanager
from collections import OrderedDict
import time

class LRUCache:
    """Simple LRU cache implementation."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()

    def get(self, key: str):
        """Get item from cache."""
        if key in self._cache:
            value, timestamp = self._cache.pop(key)
            if time.time() - timestamp < self.ttl:
                # Move to end (most recently used)
                self._cache[key] = (value, timestamp)
                return value
            # Expired
        return None

    def set(self, key: str, value):
        """Set item in cache."""
        if key in self._cache:
            self._cache.pop(key)
        elif len(self._cache) >= self.max_size:
            # Remove oldest item
            self._cache.popitem(last=False)

        self._cache[key] = (value, time.time())

    def clear(self, pattern: str = None):
        """Clear cache entries."""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        else:
            # Simple pattern matching
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)

@asynccontextmanager
async def memory_cache_lifespan(server: FastMCP):
    """Lifespan managing in-memory cache."""
    cache = LRUCache(max_size=5000, ttl=1800)  # 30 minutes TTL

    logger.info("In-memory cache initialized")

    context = {"cache": cache}

    try:
        yield context
    finally:
        cache.clear()
        logger.info("In-memory cache cleared")

mcp = FastMCP("memory-cache-server", lifespan=memory_cache_lifespan)

@mcp.tool()
async def cached_operation(key: str, value: str, ctx: Context) -> dict:
    """Operation with in-memory caching."""
    cache = ctx.request_context.lifespan_context["cache"]

    # Check cache
    cached_value = cache.get(key)
    if cached_value:
        await ctx.info(f"Cache hit for key: {key}")
        return {"key": key, "value": cached_value, "cached": True}

    # Process and cache
    processed_value = f"processed_{value}"
    cache.set(key, processed_value)

    await ctx.info(f"Cached new value for key: {key}")
    return {"key": key, "value": processed_value, "cached": False}
```

## Dependency Injection Patterns

### Service Container Pattern

```python
from dataclasses import dataclass
from contextlib import asynccontextmanager
import asyncpg
import httpx

@dataclass
class ServiceContainer:
    """Container for all application services."""
    db_pool: asyncpg.Pool
    http_client: httpx.AsyncClient
    cache: dict
    config: dict

    async def close(self):
        """Close all managed resources."""
        await self.db_pool.close()
        await self.http_client.aclose()

@asynccontextmanager
async def service_container_lifespan(server: FastMCP):
    """Lifespan providing dependency injection via service container."""
    # Initialize all services
    db_pool = await asyncpg.create_pool("postgresql://user:password@localhost/db")
    http_client = httpx.AsyncClient(timeout=30.0)
    cache = {}
    config = {
        "api_key": "secret-key",
        "debug": True,
        "max_requests_per_minute": 100
    }

    # Create service container
    services = ServiceContainer(
        db_pool=db_pool,
        http_client=http_client,
        cache=cache,
        config=config
    )

    logger.info("Service container initialized")

    context = {"services": services}

    try:
        yield context
    finally:
        await services.close()
        logger.info("Service container closed")

mcp = FastMCP("service-container-server", lifespan=service_container_lifespan)

@mcp.tool()
async def create_and_notify_user(name: str, email: str, ctx: Context) -> dict:
    """Tool using multiple injected services."""
    services = ctx.request_context.lifespan_context["services"]

    # Use database
    async with services.db_pool.acquire() as conn:
        user_id = await conn.fetchval(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
            name, email
        )

    # Cache user data
    services.cache[f"user:{user_id}"] = {"name": name, "email": email}

    # Send notification via HTTP API
    if services.config["debug"]:
        await ctx.info(f"Would send notification to {email}")
    else:
        response = await services.http_client.post(
            "https://api.notifications.com/send",
            json={"email": email, "message": f"Welcome {name}!"},
            headers={"Authorization": f"Bearer {services.config['api_key']}"}
        )
        response.raise_for_status()

    return {"user_id": user_id, "name": name, "email": email}
```

## Transport-Specific Lifespan Patterns

### StreamableHTTP with Session Manager

```python
from contextlib import asynccontextmanager
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

@asynccontextmanager
async def streamable_http_lifespan(server: FastMCP):
    """Lifespan for StreamableHTTP with session management."""
    # Initialize application state
    app_state = {
        "active_sessions": {},
        "session_count": 0,
        "startup_time": time.time()
    }

    logger.info("StreamableHTTP server starting")

    try:
        yield app_state
    finally:
        logger.info(f"StreamableHTTP server shutting down. "
                   f"Total sessions handled: {app_state['session_count']}")

mcp = FastMCP("streamable-http-server", lifespan=streamable_http_lifespan)

@mcp.tool()
async def get_session_stats(ctx: Context) -> dict:
    """Get StreamableHTTP session statistics."""
    app_state = ctx.request_context.lifespan_context

    return {
        "active_sessions": len(app_state["active_sessions"]),
        "total_sessions": app_state["session_count"],
        "uptime_seconds": time.time() - app_state["startup_time"]
    }

if __name__ == "__main__":
    mcp.run("streamable-http")
```

### Multi-Transport Configuration

```python
@asynccontextmanager
async def multi_transport_lifespan(server: FastMCP):
    """Lifespan supporting multiple transport types."""
    # Initialize common resources
    shared_resources = {
        "cache": {},
        "stats": {"requests": 0, "errors": 0}
    }

    # Transport-specific initialization could go here
    # (though FastMCP handles transport setup automatically)

    logger.info("Multi-transport server initialized")

    try:
        yield shared_resources
    finally:
        logger.info(f"Server shutdown. Final stats: {shared_resources['stats']}")

mcp = FastMCP("multi-transport-server", lifespan=multi_transport_lifespan)

@mcp.tool()
async def increment_stats(stat_name: str, ctx: Context) -> dict:
    """Increment a statistic counter."""
    stats = ctx.request_context.lifespan_context["stats"]
    stats[stat_name] = stats.get(stat_name, 0) + 1

    return {"stat": stat_name, "value": stats[stat_name]}
```

## Advanced Lifespan Patterns

### Health Check Integration

```python
from enum import Enum
from dataclasses import dataclass
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    last_check: float
    message: str = ""

class HealthMonitor:
    """Health monitoring service."""

    def __init__(self):
        self.checks = {}
        self._running = False
        self._task = None

    def add_check(self, name: str, check_func):
        """Add a health check."""
        self.checks[name] = check_func

    async def start(self):
        """Start health monitoring."""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop health monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Health monitoring loop."""
        while self._running:
            await asyncio.sleep(30)  # Check every 30 seconds
            for name, check_func in self.checks.items():
                try:
                    await check_func()
                except Exception as e:
                    logger.warning(f"Health check {name} failed: {e}")

@asynccontextmanager
async def health_monitored_lifespan(server: FastMCP):
    """Lifespan with integrated health monitoring."""
    # Initialize resources
    db_pool = await asyncpg.create_pool("postgresql://user:password@localhost/db")
    health_monitor = HealthMonitor()

    # Add health checks
    async def db_health_check():
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

    health_monitor.add_check("database", db_health_check)

    # Start health monitoring
    await health_monitor.start()

    context = {
        "db_pool": db_pool,
        "health_monitor": health_monitor
    }

    logger.info("Server with health monitoring started")

    try:
        yield context
    finally:
        await health_monitor.stop()
        await db_pool.close()
        logger.info("Health monitoring stopped")

mcp = FastMCP("health-monitored-server", lifespan=health_monitored_lifespan)

@mcp.tool()
async def health_status(ctx: Context) -> dict:
    """Get server health status."""
    # Implementation would access health monitor from context
    return {"status": "healthy", "timestamp": time.time()}
```

### Configuration Validation

```python
from pydantic import BaseSettings, validator
from contextlib import asynccontextmanager

class AppSettings(BaseSettings):
    """Application settings with validation."""
    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_key: str
    debug: bool = False
    max_connections: int = 100

    @validator('max_connections')
    def validate_max_connections(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('max_connections must be between 1 and 1000')
        return v

    class Config:
        env_prefix = "APP_"

@asynccontextmanager
async def validated_config_lifespan(server: FastMCP):
    """Lifespan with configuration validation."""
    try:
        # Load and validate configuration
        settings = AppSettings()
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize resources with validated config
    resources = {}

    try:
        # Database
        resources["db_pool"] = await asyncpg.create_pool(
            settings.database_url,
            max_size=settings.max_connections
        )

        # Redis
        resources["redis"] = redis.from_url(settings.redis_url)

        context = {
            "settings": settings,
            "resources": resources
        }

        yield context

    finally:
        # Cleanup resources
        for resource in resources.values():
            if hasattr(resource, 'close'):
                await resource.close()

mcp = FastMCP("validated-config-server", lifespan=validated_config_lifespan)
```

## Best Practices

### Lifespan Design Guidelines

1. **Keep It Simple**: Start with basic lifespan patterns and add complexity as needed
2. **Error Handling**: Always implement proper exception handling in startup and cleanup
3. **Resource Cleanup**: Ensure all resources are properly closed in the finally block
4. **Logging**: Add comprehensive logging for debugging lifecycle issues
5. **Testing**: Test both successful and failed initialization scenarios

### Performance Considerations

```python
@asynccontextmanager
async def optimized_lifespan(server: FastMCP):
    """Performance-optimized lifespan."""
    # Initialize resources concurrently
    async with asyncio.TaskGroup() as tg:
        db_task = tg.create_task(asyncpg.create_pool("postgresql://..."))
        redis_task = tg.create_task(redis.from_url("redis://..."))
        http_task = tg.create_task(httpx.AsyncClient().__aenter__())

    context = {
        "db_pool": db_task.result(),
        "redis": redis_task.result(),
        "http_client": http_task.result()
    }

    try:
        yield context
    finally:
        # Cleanup concurrently
        async with asyncio.TaskGroup() as tg:
            tg.create_task(context["db_pool"].close())
            tg.create_task(context["redis"].close())
            tg.create_task(context["http_client"].__aexit__(None, None, None))
```

### Security Considerations

```python
@asynccontextmanager
async def secure_lifespan(server: FastMCP):
    """Security-focused lifespan implementation."""
    # Load secrets securely
    import os
    database_url = os.environ.get("DATABASE_URL")
    api_key = os.environ.get("API_KEY")

    if not database_url or not api_key:
        raise ValueError("Required environment variables not set")

    # Initialize with security headers
    http_client = httpx.AsyncClient(
        headers={
            "User-Agent": "FastMCP-Server/1.0",
            "X-Request-ID": str(uuid.uuid4())
        },
        verify=True  # Verify SSL certificates
    )

    context = {
        "http_client": http_client,
        # Don't store secrets in context
        "api_key_set": bool(api_key)
    }

    try:
        yield context
    finally:
        await http_client.aclose()
        # Clear any sensitive data
        context.clear()
```

## Troubleshooting

### Common Issues

1. **Lifespan Errors**: Check exception handling in both startup and cleanup phases
2. **Resource Leaks**: Ensure all resources are properly closed in finally blocks
3. **Timeout Issues**: Set appropriate timeouts for resource initialization
4. **Context Access**: Verify lifespan context is accessed correctly in tools

### Debugging Lifespan Issues

```python
import traceback

@asynccontextmanager
async def debug_lifespan(server: FastMCP):
    """Lifespan with comprehensive debugging."""
    logger.info("=== LIFESPAN DEBUG: Starting initialization ===")

    context = {}
    initialization_steps = []

    try:
        # Step 1: Database
        logger.info("Step 1: Initializing database...")
        initialization_steps.append("database")
        context["db_pool"] = await asyncpg.create_pool("postgresql://...")
        logger.info("✓ Database initialized")

        # Step 2: Cache
        logger.info("Step 2: Initializing cache...")
        initialization_steps.append("cache")
        context["cache"] = {}
        logger.info("✓ Cache initialized")

        logger.info("=== LIFESPAN DEBUG: Initialization complete ===")
        yield context

    except Exception as e:
        logger.error(f"=== LIFESPAN DEBUG: Initialization failed at step: {initialization_steps[-1] if initialization_steps else 'unknown'} ===")
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        logger.info("=== LIFESPAN DEBUG: Starting cleanup ===")

        # Cleanup in reverse order
        for step in reversed(initialization_steps):
            try:
                if step == "database" and "db_pool" in context:
                    await context["db_pool"].close()
                    logger.info("✓ Database cleanup complete")
                elif step == "cache":
                    context.get("cache", {}).clear()
                    logger.info("✓ Cache cleanup complete")
            except Exception as e:
                logger.error(f"Cleanup error for {step}: {e}")

        logger.info("=== LIFESPAN DEBUG: Cleanup complete ===")
```

This comprehensive guide provides everything needed to implement robust lifespan management in FastMCP servers, from basic patterns to production-ready dependency injection and resource management systems.
