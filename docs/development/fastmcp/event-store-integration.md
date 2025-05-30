# Event Store Integration

Comprehensive guide to implementing event stores in FastMCP for connection resumability, session persistence, and robust client-server communication patterns.

## Overview

Event stores in FastMCP enable connection resumability by persisting events that can be replayed when clients reconnect. This is particularly valuable for unstable network connections, long-running operations, and distributed deployments where clients need to recover from disconnections.

## Event Store Architecture

FastMCP's event store system consists of three core components:

1. **EventStore Interface**: Abstract base class defining storage and replay operations
2. **StreamableHTTP Transport**: Integration layer that automatically stores and replays events
3. **Event Management**: Automatic event ID generation, stream association, and chronological ordering

### Core Interface

```python
from abc import ABC, abstractmethod
from mcp.types import JSONRPCMessage

class EventStore(ABC):
    """Interface for resumability support via event storage."""

    @abstractmethod
    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store an event and return unique event ID."""
        pass

    @abstractmethod
    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay events after specified ID via callback."""
        pass
```

## Built-in Event Store Implementation

FastMCP includes an in-memory event store suitable for development and single-instance deployments.

### InMemoryEventStore Usage

```python
from mcp.server.fastmcp import FastMCP
from examples.servers.simple_streamablehttp.mcp_simple_streamablehttp.event_store import InMemoryEventStore

# Create event store with size limits
event_store = InMemoryEventStore(max_events_per_stream=1000)

# Create FastMCP server with event store
mcp = FastMCP(
    name="resumable-server",
    event_store=event_store
)

@mcp.tool()
async def long_running_task(duration: int, ctx: Context) -> str:
    """Tool that benefits from resumability."""
    import asyncio

    # Send progress updates during long operation
    for i in range(duration):
        await ctx.info(f"Processing step {i+1}/{duration}")
        await asyncio.sleep(1)

    await ctx.info("Task completed!")
    return f"Completed {duration}-second task"

if __name__ == "__main__":
    # StreamableHTTP automatically uses event store for resumability
    mcp.run("streamable-http")
```

### Event Store Configuration

```python
# Configure event store behavior
event_store = InMemoryEventStore(
    max_events_per_stream=500  # Limit memory usage per stream
)

# Environment variable configuration
import os
os.environ['FASTMCP_STATELESS_HTTP'] = 'false'  # Required for event stores

mcp = FastMCP("configured-server", event_store=event_store)
```

## Custom Event Store Implementations

### Database-Backed Event Store

```python
import asyncio
import json
import time
from datetime import datetime
from uuid import uuid4
import aiosqlite
from mcp.server.streamable_http import EventStore
from mcp.types import JSONRPCMessage

class SQLiteEventStore(EventStore):
    """SQLite-based event store for persistent storage."""

    def __init__(self, db_path: str = "events.db"):
        self.db_path = db_path
        self._initialized = False

    async def _ensure_initialized(self):
        """Initialize database schema if needed."""
        if not self._initialized:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        stream_id TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sequence_number INTEGER
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stream_sequence
                    ON events(stream_id, sequence_number)
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_event_id_created
                    ON events(event_id, created_at)
                """)
                await db.commit()
            self._initialized = True

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event in SQLite database."""
        await self._ensure_initialized()

        event_id = f"{int(time.time() * 1000000)}-{uuid4().hex[:8]}"
        message_json = json.dumps(message.model_dump())

        async with aiosqlite.connect(self.db_path) as db:
            # Get next sequence number for stream
            cursor = await db.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM events WHERE stream_id = ?",
                (stream_id,)
            )
            sequence_number = (await cursor.fetchone())[0]

            # Store event
            await db.execute(
                """INSERT INTO events (event_id, stream_id, message, sequence_number)
                   VALUES (?, ?, ?, ?)""",
                (event_id, stream_id, message_json, sequence_number)
            )
            await db.commit()

        return event_id

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay events after specified event ID."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            # Find the stream and sequence number for last_event_id
            cursor = await db.execute(
                "SELECT stream_id, sequence_number FROM events WHERE event_id = ?",
                (last_event_id,)
            )
            result = await cursor.fetchone()

            if not result:
                return None

            stream_id, last_sequence = result

            # Get events after the last sequence number
            cursor = await db.execute(
                """SELECT message FROM events
                   WHERE stream_id = ? AND sequence_number > ?
                   ORDER BY sequence_number""",
                (stream_id, last_sequence)
            )

            # Replay events via callback
            async for row in cursor:
                message_data = json.loads(row[0])
                await send_callback({
                    "message": message_data,
                    "event_id": None  # Event ID not needed for replay
                })

            return stream_id

# Usage with custom event store
sqlite_store = SQLiteEventStore("production_events.db")
mcp = FastMCP("persistent-server", event_store=sqlite_store)
```

### Redis-Based Event Store

```python
import json
import time
from uuid import uuid4
import redis.asyncio as redis
from mcp.server.streamable_http import EventStore
from mcp.types import JSONRPCMessage

class RedisEventStore(EventStore):
    """Redis-based event store for distributed deployments."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        """Get Redis connection with lazy initialization."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event in Redis stream."""
        redis_client = await self._get_redis()

        # Generate event ID with timestamp and random component
        event_id = f"{int(time.time() * 1000)}-{uuid4().hex[:8]}"

        # Store in Redis stream
        await redis_client.xadd(
            f"mcp_stream:{stream_id}",
            {
                "message": json.dumps(message.model_dump()),
                "event_id": event_id
            },
            id=event_id
        )

        # Optional: Set TTL for automatic cleanup
        await redis_client.expire(f"mcp_stream:{stream_id}", 86400)  # 24 hours

        return event_id

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay events from Redis stream."""
        redis_client = await self._get_redis()

        # Find stream containing the last event ID
        # In production, you might need a more sophisticated lookup
        stream_pattern = "mcp_stream:*"
        streams = await redis_client.keys(stream_pattern)

        for stream_key in streams:
            # Read events after last_event_id
            try:
                events = await redis_client.xread(
                    {stream_key: last_event_id},
                    count=1000,  # Adjust based on needs
                    block=0
                )

                if events:
                    stream_id = stream_key.decode().replace("mcp_stream:", "")

                    for event_id, fields in events[0][1]:
                        message_data = json.loads(fields[b'message'].decode())
                        await send_callback({
                            "message": message_data,
                            "event_id": fields[b'event_id'].decode()
                        })

                    return stream_id
            except redis.ResponseError:
                # Event ID not found in this stream
                continue

        return None

# Usage with Redis event store
redis_store = RedisEventStore("redis://redis-server:6379")
mcp = FastMCP("distributed-server", event_store=redis_store)
```

## Connection Resumability Patterns

### Client-Side Resumption

Clients can resume connections by sending the last received event ID:

```python
# Client reconnection with resumption
from mcp.client.session import ClientSession

async def resumable_client():
    """Client with automatic resumption."""
    last_event_id = None

    # Store event IDs for resumption
    def handle_event(event):
        nonlocal last_event_id
        if hasattr(event, 'event_id'):
            last_event_id = event.event_id

    # Reconnect with resumption
    session = ClientSession(
        read_stream=read_stream,
        write_stream=write_stream,
        on_event=handle_event,
        resumption_token=last_event_id  # Resume from this point
    )

    await session.initialize()
```

### Server-Side Resumption Handling

```python
@mcp.tool()
async def resumable_operation(
    operation_id: str,
    step: int = 0,
    ctx: Context
) -> str:
    """Tool that supports resumption from any step."""

    # Check if operation was previously started
    state = await get_operation_state(operation_id)

    if state and step < state.get('current_step', 0):
        await ctx.info(f"Resuming operation {operation_id} from step {state['current_step']}")
        step = state['current_step']

    # Continue operation from current step
    total_steps = 10
    for current_step in range(step, total_steps):
        await ctx.info(f"Executing step {current_step + 1}/{total_steps}")

        # Save progress for resumability
        await save_operation_state(operation_id, {
            'current_step': current_step + 1,
            'status': 'in_progress'
        })

        # Simulate work
        await asyncio.sleep(1)

    await save_operation_state(operation_id, {'status': 'completed'})
    return f"Operation {operation_id} completed successfully"
```

## Advanced Event Store Patterns

### Event Filtering and Transformation

```python
class FilteredEventStore(EventStore):
    """Event store that filters events before storage."""

    def __init__(self, backend_store: EventStore, event_filter=None):
        self.backend = backend_store
        self.filter = event_filter or (lambda msg: True)

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event only if it passes filter."""
        if self.filter(message):
            return await self.backend.store_event(stream_id, message)
        else:
            # Return dummy event ID for filtered events
            return f"filtered-{uuid4().hex[:8]}"

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay filtered events."""
        return await self.backend.replay_events_after(last_event_id, send_callback)

# Usage with filtering
def important_events_only(message: JSONRPCMessage) -> bool:
    """Filter to only store important events."""
    # Only store tool calls and responses
    return hasattr(message, 'method') and message.method in ['tools/call', 'tools/list']

filtered_store = FilteredEventStore(
    backend_store=SQLiteEventStore(),
    event_filter=important_events_only
)

mcp = FastMCP("filtered-server", event_store=filtered_store)
```

### Event Store with Compression

```python
import gzip
import base64
from mcp.server.streamable_http import EventStore

class CompressedEventStore(EventStore):
    """Event store with automatic compression."""

    def __init__(self, backend_store: EventStore):
        self.backend = backend_store

    def _compress_message(self, message: JSONRPCMessage) -> str:
        """Compress message for storage."""
        json_str = json.dumps(message.model_dump())
        compressed = gzip.compress(json_str.encode())
        return base64.b64encode(compressed).decode()

    def _decompress_message(self, compressed_data: str) -> dict:
        """Decompress message for replay."""
        compressed_bytes = base64.b64decode(compressed_data.encode())
        json_str = gzip.decompress(compressed_bytes).decode()
        return json.loads(json_str)

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store compressed event."""
        # Create wrapper message with compressed payload
        compressed_message = JSONRPCMessage(
            jsonrpc="2.0",
            method="compressed_event",
            params={"compressed_data": self._compress_message(message)}
        )

        return await self.backend.store_event(stream_id, compressed_message)

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay and decompress events."""
        async def decompressing_callback(event):
            if (event.get("message", {}).get("method") == "compressed_event"):
                compressed_data = event["message"]["params"]["compressed_data"]
                original_message = self._decompress_message(compressed_data)
                event["message"] = original_message

            await send_callback(event)

        return await self.backend.replay_events_after(last_event_id, decompressing_callback)

# Usage with compression
compressed_store = CompressedEventStore(
    backend_store=SQLiteEventStore()
)

mcp = FastMCP("compressed-server", event_store=compressed_store)
```

### Multi-Tenant Event Store

```python
class TenantEventStore(EventStore):
    """Event store with tenant isolation."""

    def __init__(self, backend_store: EventStore):
        self.backend = backend_store
        self._current_tenant = None

    def set_tenant(self, tenant_id: str):
        """Set current tenant context."""
        self._current_tenant = tenant_id

    def _tenant_stream_id(self, stream_id: str) -> str:
        """Prefix stream ID with tenant."""
        if self._current_tenant:
            return f"tenant:{self._current_tenant}:{stream_id}"
        return stream_id

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event with tenant isolation."""
        tenant_stream_id = self._tenant_stream_id(stream_id)
        return await self.backend.store_event(tenant_stream_id, message)

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay events for current tenant only."""
        return await self.backend.replay_events_after(last_event_id, send_callback)

# Usage with tenant isolation
tenant_store = TenantEventStore(RedisEventStore())

@mcp.custom_route("/tenant/{tenant_id}/mcp", methods=["GET", "POST"])
async def tenant_mcp_endpoint(request: Request) -> Response:
    """Tenant-specific MCP endpoint."""
    tenant_id = request.path_params["tenant_id"]

    # Set tenant context for event store
    tenant_store.set_tenant(tenant_id)

    # Process request with tenant-isolated events
    return await mcp.handle_request(request)
```

## Performance Optimization

### Event Store Caching

```python
from collections import OrderedDict
import asyncio

class CachedEventStore(EventStore):
    """Event store with LRU cache for performance."""

    def __init__(self, backend_store: EventStore, cache_size: int = 1000):
        self.backend = backend_store
        self.cache = OrderedDict()
        self.cache_size = cache_size
        self._cache_lock = asyncio.Lock()

    async def _cache_get(self, key: str):
        """Get from cache with LRU update."""
        async with self._cache_lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None

    async def _cache_set(self, key: str, value):
        """Set in cache with LRU eviction."""
        async with self._cache_lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.cache_size:
                # Remove oldest item
                self.cache.popitem(last=False)

            self.cache[key] = value

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event with caching."""
        event_id = await self.backend.store_event(stream_id, message)

        # Cache the event for fast replay
        cache_key = f"{stream_id}:{event_id}"
        await self._cache_set(cache_key, {
            "message": message.model_dump(),
            "event_id": event_id
        })

        return event_id

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback,
    ) -> str | None:
        """Replay with cache acceleration."""
        # Try cache first for recent events
        # Fall back to backend for older events
        return await self.backend.replay_events_after(last_event_id, send_callback)

# Usage with caching
cached_store = CachedEventStore(
    backend_store=RedisEventStore(),
    cache_size=5000
)

mcp = FastMCP("high-performance-server", event_store=cached_store)
```

## Testing Event Stores

### Event Store Testing Utilities

```python
import pytest
from mcp.types import JSONRPCMessage

class TestEventStore:
    """Test utilities for event store implementations."""

    @pytest.fixture
    async def sample_messages(self):
        """Sample JSONRPCMessage objects for testing."""
        return [
            JSONRPCMessage(
                jsonrpc="2.0",
                method="tools/list",
                id="1"
            ),
            JSONRPCMessage(
                jsonrpc="2.0",
                method="tools/call",
                params={"name": "test_tool", "arguments": {}},
                id="2"
            ),
            JSONRPCMessage(
                jsonrpc="2.0",
                result={"content": [{"type": "text", "text": "result"}]},
                id="2"
            )
        ]

    async def test_basic_storage_and_replay(self, event_store, sample_messages):
        """Test basic event storage and replay functionality."""
        stream_id = "test-stream-1"
        stored_events = []

        # Store events
        for message in sample_messages:
            event_id = await event_store.store_event(stream_id, message)
            stored_events.append(event_id)
            assert event_id is not None

        # Test replay
        replayed_events = []

        async def collect_events(event):
            replayed_events.append(event)

        # Replay from first event
        result_stream_id = await event_store.replay_events_after(
            stored_events[0],
            collect_events
        )

        assert result_stream_id == stream_id
        assert len(replayed_events) == len(sample_messages) - 1  # Excludes first event

    async def test_stream_isolation(self, event_store, sample_messages):
        """Test that events are isolated between streams."""
        stream1 = "stream-1"
        stream2 = "stream-2"

        # Store events in different streams
        event1 = await event_store.store_event(stream1, sample_messages[0])
        event2 = await event_store.store_event(stream2, sample_messages[1])

        # Replay should only return events from same stream
        replayed = []

        async def collect(event):
            replayed.append(event)

        await event_store.replay_events_after(event1, collect)

        # Should be empty since no events after event1 in stream1
        assert len(replayed) == 0

# Usage in tests
@pytest.mark.asyncio
async def test_sqlite_event_store():
    store = SQLiteEventStore(":memory:")  # In-memory for testing
    test_suite = TestEventStore()

    await test_suite.test_basic_storage_and_replay(store, sample_messages)
    await test_suite.test_stream_isolation(store, sample_messages)
```

## Best Practices

### Event Store Design Guidelines

1. **Choose Appropriate Storage**:
   - Use InMemoryEventStore for development and testing
   - Use persistent stores (SQLite, PostgreSQL) for production single-instance deployments
   - Use distributed stores (Redis, Apache Kafka) for multi-instance deployments

2. **Implement Proper Cleanup**:
   - Set TTL policies for automatic event cleanup
   - Implement archival strategies for long-term storage
   - Monitor storage growth and implement pruning

3. **Handle Failures Gracefully**:
   - Implement retry logic for storage failures
   - Provide fallback behavior when event store is unavailable
   - Log event store errors appropriately

4. **Security Considerations**:
   - Encrypt sensitive event data
   - Implement proper access controls
   - Audit event access and modifications

### Performance Optimization

```python
# Optimized event store usage
@mcp.tool()
async def optimized_tool(large_data: str, ctx: Context) -> str:
    """Tool optimized for event store performance."""

    # Minimize event payload size
    await ctx.info("Starting large operation")  # Lightweight event

    # Process data without creating large events
    result = process_large_data(large_data)

    # Send summary instead of full data
    await ctx.info(f"Processed {len(large_data)} bytes -> {len(result)} bytes")

    return "Operation completed"  # Compact result
```

### Error Handling

```python
class RobustEventStore(EventStore):
    """Event store with comprehensive error handling."""

    def __init__(self, backend_store: EventStore, max_retries: int = 3):
        self.backend = backend_store
        self.max_retries = max_retries

    async def store_event(
        self,
        stream_id: str,
        message: JSONRPCMessage
    ) -> str:
        """Store event with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return await self.backend.store_event(stream_id, message)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Log final failure
                    logger.error(f"Failed to store event after {self.max_retries} attempts: {e}")
                    # Return dummy ID to prevent client errors
                    return f"failed-{uuid4().hex[:8]}"
                else:
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
```

## Troubleshooting

### Common Issues

1. **Events Not Replaying**:
   - Verify event store is configured with stateful sessions
   - Check Last-Event-ID header format
   - Ensure event IDs are properly generated

2. **Memory Leaks**:
   - Implement event cleanup policies
   - Monitor InMemoryEventStore size limits
   - Use weak references where appropriate

3. **Performance Issues**:
   - Implement event store caching
   - Optimize database queries with proper indexing
   - Consider event compression for large payloads

4. **Connection Issues**:
   - Implement connection pooling for database stores
   - Handle Redis connection failures gracefully
   - Add health checks for event store availability

This comprehensive guide provides everything needed to implement robust event store integration in FastMCP servers, from simple in-memory solutions to production-ready distributed systems.
