# Session Management

Advanced guide to session handling in FastMCP servers, covering stateful vs stateless patterns, event store integration, session lifecycle management, and custom session patterns.

## Overview

FastMCP provides sophisticated session management capabilities that vary by transport type. This guide covers advanced session patterns, particularly for StreamableHTTP transport which supports both stateful and stateless session modes.

## Session Architecture

FastMCP's session system has three key components:

1. **ServerSession**: Core session implementation with initialization state management
2. **Transport Layer**: Protocol-specific session handling (stdio, SSE, StreamableHTTP)
3. **Session Manager**: High-level session lifecycle and coordination

### Session States

```python
from enum import Enum

class InitializationState(Enum):
    NotInitialized = "not_initialized"
    Initializing = "initializing"
    Initialized = "initialized"

# Session progresses through these states during handshake
```

## Transport-Specific Session Behavior

### Stdio Transport

```python
from mcp.server.fastmcp import FastMCP

# Stdio: Single persistent session
mcp = FastMCP("stdio-server")

# Session lifecycle tied to process lifetime
if __name__ == "__main__":
    mcp.run("stdio")  # One session until process terminates
```

**Characteristics**:
- Single session per process
- Direct stdin/stdout communication
- Session ends when process terminates
- No session resumability

### SSE Transport

```python
# SSE: Session per browser connection
mcp = FastMCP("sse-server")

# Each browser connection creates new session
if __name__ == "__main__":
    mcp.run("sse")  # Session per HTTP connection
```

**Characteristics**:
- Session per HTTP connection
- Automatic cleanup on disconnect
- No built-in resumability
- Browser-friendly with automatic reconnection

### StreamableHTTP Transport

StreamableHTTP offers the most advanced session management with configurable behavior.

## Stateful vs Stateless Sessions

### Stateful Sessions (Default)

```python
from mcp.server.fastmcp import FastMCP

# Stateful mode - sessions persist between requests
mcp = FastMCP("stateful-server")

# Configure for persistent sessions
mcp.settings.stateless_http = False  # Default

@mcp.tool()
async def stateful_tool(message: str, ctx: Context) -> str:
    """Tool with session-aware behavior."""
    session_id = ctx.session_id if hasattr(ctx, 'session_id') else 'unknown'

    # Session state persists across requests
    await ctx.info(f"Processing in session {session_id}")

    return f"Processed '{message}' in persistent session"

if __name__ == "__main__":
    mcp.run("streamable-http")
```

**Characteristics**:
- Sessions persist between HTTP requests
- Client maintains session ID via headers
- Better for long-running conversations
- Supports event store integration for resumability

### Stateless Sessions

```python
from mcp.server.fastmcp import FastMCP

# Stateless mode - new session per request
mcp = FastMCP("stateless-server")
mcp.settings.stateless_http = True

@mcp.tool()
async def stateless_tool(data: str, ctx: Context) -> str:
    """Tool optimized for stateless operation."""
    # Each request creates fresh session
    # No persistent state between requests
    return f"Processed '{data}' in fresh session"

if __name__ == "__main__":
    mcp.run("streamable-http")
```

**Characteristics**:
- Fresh session created per request
- No session ID tracking required
- Lower memory footprint
- Simpler deployment and scaling

## Event Store Integration

Event stores enable session resumability by persisting session events that can be replayed after disconnection.

### Built-in In-Memory Event Store

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http import InMemoryEventStore

# Create event store for resumability
event_store = InMemoryEventStore(max_events_per_stream=1000)

# Configure server with event store
mcp = FastMCP("resumable-server")

# Event store enables automatic resumability
@mcp.tool()
async def logged_operation(action: str, ctx: Context) -> str:
    """Tool with automatic event logging."""
    # All interactions automatically logged to event store
    await ctx.info(f"Executing action: {action}")

    # Simulate work
    import asyncio
    await asyncio.sleep(1)

    await ctx.info(f"Completed action: {action}")
    return f"Action '{action}' completed successfully"

if __name__ == "__main__":
    # Events automatically stored and available for replay
    mcp.run("streamable-http")
```

### Custom Event Store Implementation

```python
from mcp.server.streamable_http import EventStore, EventId, StreamId
from mcp.types import JSONRPCMessage
import asyncio
import json

class DatabaseEventStore(EventStore):
    """Custom event store using database backend."""

    def __init__(self, db_connection):
        self.db = db_connection
        self._next_event_id = 1

    async def store_event(
        self,
        stream_id: StreamId,
        message: JSONRPCMessage
    ) -> EventId:
        """Store event in database."""
        event_id = EventId(self._next_event_id)
        self._next_event_id += 1

        # Store in database
        await self.db.execute(
            "INSERT INTO events (event_id, stream_id, message, timestamp) VALUES (?, ?, ?, ?)",
            (event_id, stream_id, json.dumps(message.model_dump()), time.time())
        )

        return event_id

    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback
    ) -> StreamId | None:
        """Replay events from database."""
        cursor = await self.db.execute(
            "SELECT stream_id, message FROM events WHERE event_id > ? ORDER BY event_id",
            (last_event_id,)
        )

        stream_id = None
        async for row in cursor:
            stream_id = StreamId(row[0])
            message_data = json.loads(row[1])

            # Reconstruct message and send
            await send_callback(message_data)

        return stream_id

# Usage with custom event store
async def create_db_event_store():
    # Initialize database connection
    db = await aiosqlite.connect("events.db")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            stream_id TEXT,
            message TEXT,
            timestamp REAL
        )
    """)
    return DatabaseEventStore(db)

# Configure FastMCP with custom event store
event_store = await create_db_event_store()
mcp = FastMCP("db-resumable-server")
```

## Advanced Session Patterns

### Session-Aware Tools

```python
from mcp.server.fastmcp import FastMCP, Context
from collections import defaultdict
import time

# Session state storage
session_state = defaultdict(dict)

mcp = FastMCP("session-aware-server")

@mcp.tool()
async def set_session_data(key: str, value: str, ctx: Context) -> str:
    """Store data in session scope."""
    session_id = getattr(ctx, 'session_id', 'default')
    session_state[session_id][key] = {
        'value': value,
        'timestamp': time.time()
    }

    await ctx.info(f"Stored {key} in session {session_id}")
    return f"Stored {key} = {value}"

@mcp.tool()
async def get_session_data(key: str, ctx: Context) -> str:
    """Retrieve data from session scope."""
    session_id = getattr(ctx, 'session_id', 'default')

    if session_id in session_state and key in session_state[session_id]:
        data = session_state[session_id][key]
        await ctx.info(f"Retrieved {key} from session {session_id}")
        return f"{key} = {data['value']} (stored at {data['timestamp']})"
    else:
        return f"No data found for key '{key}' in current session"

@mcp.tool()
async def list_session_keys(ctx: Context) -> str:
    """List all keys in current session."""
    session_id = getattr(ctx, 'session_id', 'default')

    if session_id in session_state:
        keys = list(session_state[session_id].keys())
        return f"Session {session_id} keys: {keys}"
    else:
        return f"No data in session {session_id}"
```

### Session Lifecycle Management

```python
from contextlib import asynccontextmanager
from typing import Dict, Any
import asyncio

class SessionManager:
    """Custom session lifecycle manager."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cleanup_tasks: Dict[str, asyncio.Task] = {}

    async def create_session(self, session_id: str) -> Dict[str, Any]:
        """Initialize new session with cleanup timer."""
        session_data = {
            'created_at': time.time(),
            'last_activity': time.time(),
            'request_count': 0,
            'data': {}
        }

        self.sessions[session_id] = session_data

        # Schedule cleanup after inactivity
        self.cleanup_tasks[session_id] = asyncio.create_task(
            self._cleanup_after_timeout(session_id, timeout=3600)  # 1 hour
        )

        return session_data

    async def _cleanup_after_timeout(self, session_id: str, timeout: int):
        """Clean up session after timeout."""
        await asyncio.sleep(timeout)

        if session_id in self.sessions:
            last_activity = self.sessions[session_id]['last_activity']
            if time.time() - last_activity >= timeout:
                await self.cleanup_session(session_id)

    async def cleanup_session(self, session_id: str):
        """Remove session and cancel cleanup task."""
        if session_id in self.sessions:
            del self.sessions[session_id]

        if session_id in self.cleanup_tasks:
            self.cleanup_tasks[session_id].cancel()
            del self.cleanup_tasks[session_id]

    def update_activity(self, session_id: str):
        """Update last activity timestamp."""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = time.time()
            self.sessions[session_id]['request_count'] += 1

# Global session manager
session_manager = SessionManager()

@mcp.tool()
async def managed_tool(data: str, ctx: Context) -> str:
    """Tool with managed session lifecycle."""
    session_id = getattr(ctx, 'session_id', 'default')

    # Ensure session exists
    if session_id not in session_manager.sessions:
        await session_manager.create_session(session_id)

    # Update activity
    session_manager.update_activity(session_id)

    # Access session data
    session_data = session_manager.sessions[session_id]

    return f"Processed '{data}' (request #{session_data['request_count']})"
```

### Multi-Session Coordination

```python
from typing import Set
import asyncio

class MultiSessionCoordinator:
    """Coordinate actions across multiple sessions."""

    def __init__(self):
        self.active_sessions: Set[str] = set()
        self.broadcast_queue = asyncio.Queue()
        self.session_contexts: Dict[str, Context] = {}

    async def register_session(self, session_id: str, ctx: Context):
        """Register session for coordination."""
        self.active_sessions.add(session_id)
        self.session_contexts[session_id] = ctx

    async def unregister_session(self, session_id: str):
        """Unregister session."""
        self.active_sessions.discard(session_id)
        self.session_contexts.pop(session_id, None)

    async def broadcast_message(self, message: str, exclude_session: str = None):
        """Broadcast message to all active sessions."""
        for session_id in self.active_sessions:
            if session_id != exclude_session:
                ctx = self.session_contexts.get(session_id)
                if ctx:
                    try:
                        await ctx.info(f"Broadcast: {message}")
                    except Exception as e:
                        # Handle failed delivery
                        await self.unregister_session(session_id)

coordinator = MultiSessionCoordinator()

@mcp.tool()
async def join_coordination(ctx: Context) -> str:
    """Join multi-session coordination."""
    session_id = getattr(ctx, 'session_id', 'default')
    await coordinator.register_session(session_id, ctx)

    await coordinator.broadcast_message(
        f"Session {session_id} joined",
        exclude_session=session_id
    )

    return f"Joined coordination as session {session_id}"

@mcp.tool()
async def broadcast_to_sessions(message: str, ctx: Context) -> str:
    """Broadcast message to all other sessions."""
    session_id = getattr(ctx, 'session_id', 'default')

    await coordinator.broadcast_message(message, exclude_session=session_id)

    return f"Broadcasted '{message}' to {len(coordinator.active_sessions) - 1} other sessions"
```

## Session Security Patterns

### Session-Based Authentication

```python
from mcp.server.auth.middleware import get_access_token
from mcp.server.fastmcp import Context

# Session authentication state
authenticated_sessions: Set[str] = set()

@mcp.tool()
async def secure_login(username: str, password: str, ctx: Context) -> str:
    """Authenticate current session."""
    session_id = getattr(ctx, 'session_id', 'default')

    # Validate credentials (implement your auth logic)
    if await validate_credentials(username, password):
        authenticated_sessions.add(session_id)
        await ctx.info(f"Session {session_id} authenticated as {username}")
        return f"Authenticated as {username}"
    else:
        await ctx.error("Authentication failed")
        raise ValueError("Invalid credentials")

@mcp.tool()
async def secure_operation(action: str, ctx: Context) -> str:
    """Operation requiring session authentication."""
    session_id = getattr(ctx, 'session_id', 'default')

    # Check session authentication
    if session_id not in authenticated_sessions:
        raise ValueError("Session not authenticated. Call secure_login first.")

    # Also check OAuth token if available
    access_token = get_access_token()
    if access_token and "admin" not in access_token.scopes:
        raise ValueError("Insufficient permissions")

    await ctx.info(f"Executing secure action: {action}")
    return f"Executed secure action: {action}"

@mcp.tool()
async def logout(ctx: Context) -> str:
    """Logout current session."""
    session_id = getattr(ctx, 'session_id', 'default')
    authenticated_sessions.discard(session_id)

    await ctx.info(f"Session {session_id} logged out")
    return "Logged out successfully"
```

### Session Data Isolation

```python
import hashlib
from typing import Dict, Any

class SecureSessionStorage:
    """Secure session data storage with encryption."""

    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key.encode()
        self._storage: Dict[str, Dict[str, str]] = {}

    def _encrypt_data(self, data: str) -> str:
        """Simple encryption (use proper crypto in production)."""
        import base64
        return base64.b64encode(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Simple decryption (use proper crypto in production)."""
        import base64
        return base64.b64decode(encrypted_data.encode()).decode()

    async def store_secure_data(
        self,
        session_id: str,
        key: str,
        value: str
    ) -> None:
        """Store encrypted data for session."""
        if session_id not in self._storage:
            self._storage[session_id] = {}

        encrypted_value = self._encrypt_data(value)
        self._storage[session_id][key] = encrypted_value

    async def get_secure_data(
        self,
        session_id: str,
        key: str
    ) -> str | None:
        """Retrieve and decrypt data for session."""
        if session_id in self._storage and key in self._storage[session_id]:
            encrypted_value = self._storage[session_id][key]
            return self._decrypt_data(encrypted_value)
        return None

secure_storage = SecureSessionStorage("your-encryption-key")

@mcp.tool()
async def store_sensitive_data(
    key: str,
    value: str,
    ctx: Context
) -> str:
    """Store sensitive data securely in session."""
    session_id = getattr(ctx, 'session_id', 'default')

    await secure_storage.store_secure_data(session_id, key, value)
    await ctx.info(f"Stored sensitive data for key: {key}")

    return f"Securely stored data for key: {key}"

@mcp.tool()
async def retrieve_sensitive_data(key: str, ctx: Context) -> str:
    """Retrieve sensitive data from session."""
    session_id = getattr(ctx, 'session_id', 'default')

    value = await secure_storage.get_secure_data(session_id, key)

    if value:
        await ctx.info(f"Retrieved sensitive data for key: {key}")
        return f"Retrieved: {value}"
    else:
        return f"No data found for key: {key}"
```

## Configuration and Environment Variables

### Session Configuration

```python
from mcp.server.fastmcp import FastMCP
import os

# Configure via environment variables
os.environ.update({
    'FASTMCP_STATELESS_HTTP': 'false',  # Enable stateful sessions
    'FASTMCP_JSON_RESPONSE': 'true',    # JSON responses
    'FASTMCP_HOST': '0.0.0.0',
    'FASTMCP_PORT': '8080'
})

mcp = FastMCP("configured-server")

# Or configure programmatically
mcp.settings.stateless_http = False
mcp.settings.json_response = True
mcp.settings.host = "0.0.0.0"
mcp.settings.port = 8080

@mcp.tool()
async def get_server_config(ctx: Context) -> dict:
    """Return current server configuration."""
    return {
        "stateless_http": mcp.settings.stateless_http,
        "json_response": mcp.settings.json_response,
        "host": mcp.settings.host,
        "port": mcp.settings.port,
        "mount_path": mcp.settings.mount_path,
        "streamable_http_path": mcp.settings.streamable_http_path
    }
```

## Performance Considerations

### Session Memory Management

```python
import asyncio
import weakref
from typing import WeakSet

class SessionResourceManager:
    """Manage session resources and prevent memory leaks."""

    def __init__(self):
        self._session_resources: Dict[str, WeakSet] = defaultdict(weakref.WeakSet)
        self._cleanup_interval = 300  # 5 minutes
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def register_resource(self, session_id: str, resource):
        """Register resource for cleanup when session ends."""
        self._session_resources[session_id].add(resource)

    async def cleanup_session_resources(self, session_id: str):
        """Clean up all resources for a session."""
        if session_id in self._session_resources:
            resources = list(self._session_resources[session_id])
            for resource in resources:
                try:
                    if hasattr(resource, 'close'):
                        await resource.close()
                    elif hasattr(resource, '__aexit__'):
                        await resource.__aexit__(None, None, None)
                except Exception as e:
                    # Log cleanup errors
                    print(f"Error cleaning up resource: {e}")

            del self._session_resources[session_id]

    async def _periodic_cleanup(self):
        """Periodically clean up dead references."""
        while True:
            await asyncio.sleep(self._cleanup_interval)

            # Clean up empty weak sets
            empty_sessions = [
                session_id for session_id, resources in self._session_resources.items()
                if len(resources) == 0
            ]

            for session_id in empty_sessions:
                del self._session_resources[session_id]

resource_manager = SessionResourceManager()

@mcp.tool()
async def create_managed_resource(resource_type: str, ctx: Context) -> str:
    """Create resource with automatic cleanup."""
    session_id = getattr(ctx, 'session_id', 'default')

    # Create resource (example: file handle)
    if resource_type == "file":
        resource = open(f"/tmp/session_{session_id}.txt", "w")
        await resource_manager.register_resource(session_id, resource)
        return f"Created file resource for session {session_id}"

    return f"Unknown resource type: {resource_type}"
```

## Best Practices

### Session Design Guidelines

1. **Choose Appropriate Session Mode**:
   - Use **stateless** for simple, independent requests
   - Use **stateful** for conversational or multi-step workflows

2. **Implement Proper Cleanup**:
   - Always clean up session resources
   - Use weak references to prevent memory leaks
   - Implement session timeouts for inactive sessions

3. **Security Considerations**:
   - Validate session IDs and implement proper authentication
   - Encrypt sensitive session data
   - Implement session isolation between users

4. **Performance Optimization**:
   - Monitor session memory usage
   - Implement efficient session storage
   - Use connection pooling for external resources

### Error Handling

```python
@mcp.tool()
async def robust_session_tool(data: str, ctx: Context) -> str:
    """Tool with comprehensive session error handling."""
    try:
        session_id = getattr(ctx, 'session_id', 'unknown')

        # Validate session state
        if not session_id or session_id == 'unknown':
            await ctx.error("Invalid session state")
            raise ValueError("Session ID not available")

        # Process with proper error handling
        result = await process_session_data(session_id, data)

        await ctx.info(f"Successfully processed data in session {session_id}")
        return result

    except Exception as e:
        await ctx.error(f"Error in session tool: {e}")

        # Attempt session recovery
        try:
            await recover_session_state(session_id)
            await ctx.info("Session state recovered")
        except Exception as recovery_error:
            await ctx.error(f"Session recovery failed: {recovery_error}")

        raise  # Re-raise original exception
```

## Troubleshooting

### Common Session Issues

1. **Session ID Not Available**:
   - Check transport type (stdio doesn't have session IDs)
   - Verify client is sending proper session headers
   - Ensure stateful mode is enabled for StreamableHTTP

2. **Session State Loss**:
   - Implement event store for resumability
   - Check session timeout settings
   - Verify session storage implementation

3. **Memory Leaks**:
   - Implement proper session cleanup
   - Use weak references for session data
   - Monitor session count and memory usage

4. **Authentication Issues**:
   - Verify auth middleware configuration
   - Check token validation logic
   - Ensure proper scope checking

This guide provides comprehensive patterns for implementing advanced session management in FastMCP servers. Choose the appropriate patterns based on your application's requirements for state persistence, security, and performance.
