# Testing Guide

Comprehensive guide for testing FastMCP servers, including unit tests, integration tests, mocking strategies, and testing best practices.

## Quick Start

### Basic Test Setup

**Install testing dependencies:**
```bash
uv add --dev pytest pytest-anyio pytest-examples
uv add --dev pytest-mock pytest-cov  # Optional: mocking and coverage
```

**Configure pytest in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--anyio-backends=asyncio",
    "--strict-markers",
    "--strict-config",
    "-ra"
]
markers = [
    "anyio: mark test as async",
    "integration: mark test as integration test"
]
```

**Basic test structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_tools.py           # Tool tests
├── test_resources.py       # Resource tests
├── test_prompts.py         # Prompt tests
├── test_integration.py     # Integration tests
└── test_performance.py     # Performance tests
```

### Essential conftest.py

Create `tests/conftest.py` with shared fixtures:

```python
import pytest
from mcp.server.fastmcp import FastMCP

@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"

@pytest.fixture
def test_server():
    """Create a test FastMCP server."""
    return FastMCP("Test Server", debug=True)

@pytest.fixture
def sample_data():
    """Sample test data."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
    }
```

## Unit Testing

### 1. Testing Tools

**Basic tool testing:**
```python
import pytest
from mcp.server.fastmcp import FastMCP, Context

class TestTools:
    @pytest.mark.anyio
    async def test_simple_tool(self, test_server):
        """Test a simple synchronous tool."""

        @test_server.tool()
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Test tool registration
        tools = await test_server.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "add_numbers"
        assert tools[0].description == "Add two numbers."

        # Test tool execution
        result = await test_server.call_tool("add_numbers", {"a": 5, "b": 3})
        assert result[0].text == "8"

    @pytest.mark.anyio
    async def test_async_tool(self, test_server):
        """Test an async tool."""

        @test_server.tool()
        async def fetch_data(url: str) -> str:
            """Fetch data from URL."""
            # Simulate async operation
            import asyncio
            await asyncio.sleep(0.01)
            return f"Data from {url}"

        result = await test_server.call_tool("fetch_data", {"url": "https://api.example.com"})
        assert result[0].text == "Data from https://api.example.com"

    @pytest.mark.anyio
    async def test_tool_with_context(self, test_server):
        """Test tool that uses context."""

        context_messages = []

        @test_server.tool()
        async def logging_tool(message: str, ctx: Context) -> str:
            """Tool that uses context for logging."""
            await ctx.info(f"Processing: {message}")
            context_messages.append(f"Processing: {message}")
            return f"Processed: {message}"

        # Create a mock context to capture logging
        from unittest.mock import AsyncMock
        mock_context = AsyncMock(spec=Context)

        # Get the tool and run it directly with mock context
        tool = test_server._tool_manager.get_tool("logging_tool")
        result = await tool.run({"message": "test"}, context=mock_context)

        assert result == "Processed: test"
        mock_context.info.assert_called_once_with("Processing: test")

    @pytest.mark.anyio
    async def test_tool_error_handling(self, test_server):
        """Test tool error handling."""

        @test_server.tool()
        def error_tool(should_fail: bool) -> str:
            """Tool that can fail."""
            if should_fail:
                raise ValueError("Tool failed!")
            return "success"

        # Test successful execution
        result = await test_server.call_tool("error_tool", {"should_fail": False})
        assert result[0].text == "success"

        # Test error handling
        with pytest.raises(Exception):  # FastMCP wraps errors
            await test_server.call_tool("error_tool", {"should_fail": True})

    def test_tool_validation(self, test_server):
        """Test tool parameter validation."""
        from pydantic import Field

        @test_server.tool()
        def validated_tool(
            name: str = Field(min_length=2, max_length=50),
            age: int = Field(ge=0, le=150)
        ) -> str:
            """Tool with validation."""
            return f"{name} is {age} years old"

        # Test schema generation
        tools = test_server._tool_manager.list_tools()
        tool_info = tools[0]

        assert "name" in tool_info.parameters["properties"]
        assert "age" in tool_info.parameters["properties"]
        assert tool_info.parameters["properties"]["name"]["minLength"] == 2
        assert tool_info.parameters["properties"]["age"]["minimum"] == 0
```

### 2. Testing Resources

**Resource testing patterns:**
```python
import pytest
from mcp.server.fastmcp import FastMCP

class TestResources:
    @pytest.mark.anyio
    async def test_static_resource(self, test_server):
        """Test static resource."""

        @test_server.resource("data://config")
        def get_config() -> str:
            """Server configuration."""
            return "debug=true\nport=8000"

        # Test resource listing
        resources = await test_server.list_resources()
        assert len(resources) == 1
        assert str(resources[0].uri) == "data://config"
        assert resources[0].mime_type == "text/plain"

        # Test resource reading
        content = await test_server.read_resource("data://config")
        assert content[0].content == "debug=true\nport=8000"

    @pytest.mark.anyio
    async def test_template_resource(self, test_server, sample_data):
        """Test template resource with parameters."""

        @test_server.resource("data://users/{user_id}")
        def get_user(user_id: int) -> dict:
            """Get user by ID."""
            users = sample_data["users"]
            user = next((u for u in users if u["id"] == user_id), None)
            if not user:
                raise ValueError(f"User {user_id} not found")
            return user

        # Test template listing
        templates = await test_server.list_resource_templates()
        assert len(templates) == 1
        assert templates[0].uriTemplate == "data://users/{user_id}"

        # Test resource access
        content = await test_server.read_resource("data://users/1")
        import json
        data = json.loads(content[0].content)
        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"

    @pytest.mark.anyio
    async def test_binary_resource(self, test_server):
        """Test binary resource."""

        @test_server.resource("data://image", mime_type="image/png")
        def get_image() -> bytes:
            """Get a test image."""
            # Create a minimal PNG header (simplified)
            return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        content = await test_server.read_resource("data://image")
        assert isinstance(content[0].content, bytes)
        assert content[0].mime_type == "image/png"

    @pytest.mark.anyio
    async def test_async_resource(self, test_server):
        """Test async resource."""

        @test_server.resource("data://async")
        async def get_async_data() -> str:
            """Get data asynchronously."""
            import asyncio
            await asyncio.sleep(0.01)  # Simulate async operation
            return "async data"

        content = await test_server.read_resource("data://async")
        assert content[0].content == "async data"

    @pytest.mark.anyio
    async def test_resource_error_handling(self, test_server):
        """Test resource error handling."""

        @test_server.resource("data://error")
        def error_resource() -> str:
            """Resource that fails."""
            raise RuntimeError("Resource error!")

        with pytest.raises(Exception):  # FastMCP wraps resource errors
            await test_server.read_resource("data://error")
```

### 3. Testing Prompts

**Prompt testing patterns:**
```python
import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import UserMessage, AssistantMessage

class TestPrompts:
    @pytest.mark.anyio
    async def test_simple_prompt(self, test_server):
        """Test simple prompt."""

        @test_server.prompt()
        def greeting_prompt(name: str) -> str:
            """Generate a greeting prompt."""
            return f"Hello, {name}! How are you doing today?"

        # Test prompt listing
        prompts = await test_server.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "greeting_prompt"

        # Test prompt rendering
        result = await test_server.get_prompt("greeting_prompt", {"name": "Alice"})
        messages = result.messages
        assert len(messages) == 1
        assert messages[0]["content"]["text"] == "Hello, Alice! How are you doing today?"

    @pytest.mark.anyio
    async def test_prompt_with_messages(self, test_server):
        """Test prompt returning Message objects."""

        @test_server.prompt()
        def conversation_prompt(topic: str) -> list:
            """Generate a conversation prompt."""
            return [
                UserMessage(f"Let's discuss {topic}"),
                AssistantMessage("I'd be happy to discuss that with you!")
            ]

        result = await test_server.get_prompt("conversation_prompt", {"topic": "Python"})
        messages = result.messages
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.anyio
    async def test_async_prompt(self, test_server):
        """Test async prompt."""

        @test_server.prompt()
        async def async_prompt(query: str) -> str:
            """Generate prompt asynchronously."""
            import asyncio
            await asyncio.sleep(0.01)  # Simulate async operation
            return f"Please analyze: {query}"

        result = await test_server.get_prompt("async_prompt", {"query": "data trends"})
        assert "Please analyze: data trends" in result.messages[0]["content"]["text"]

    @pytest.mark.anyio
    async def test_prompt_validation(self, test_server):
        """Test prompt parameter validation."""

        @test_server.prompt()
        def validated_prompt(required_param: str, optional_param: str = "default") -> str:
            """Prompt with required and optional parameters."""
            return f"{required_param} - {optional_param}"

        # Test with required parameter
        result = await test_server.get_prompt("validated_prompt", {"required_param": "test"})
        assert "test - default" in result.messages[0]["content"]["text"]

        # Test missing required parameter
        with pytest.raises(Exception):
            await test_server.get_prompt("validated_prompt", {})
```

## Integration Testing

### 1. End-to-End Testing

**Test complete client-server interaction:**
```python
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

class TestIntegration:
    @pytest.mark.anyio
    async def test_full_server_interaction(self, test_server, sample_data):
        """Test complete server interaction."""

        # Set up server
        @test_server.tool()
        def get_user_count() -> int:
            """Get total user count."""
            return len(sample_data["users"])

        @test_server.resource("data://summary")
        def get_summary() -> str:
            """Get data summary."""
            return f"Total users: {len(sample_data['users'])}"

        @test_server.prompt()
        def analysis_prompt() -> str:
            """Generate analysis prompt."""
            return "Please analyze the user data."

        # Test with connected session
        async with create_connected_server_and_client_session(test_server._mcp_server) as (
            server_session,
            client_session,
        ):
            # Test initialization
            await client_session.initialize()

            # Test tool listing and execution
            tools_result = await client_session.list_tools()
            assert len(tools_result.tools) == 1

            tool_result = await client_session.call_tool("get_user_count")
            assert tool_result.content[0].text == "2"

            # Test resource listing and reading
            resources_result = await client_session.list_resources()
            assert len(resources_result.resources) == 1

            resource_result = await client_session.read_resource("data://summary")
            assert resource_result.contents[0].text == "Total users: 2"

            # Test prompt listing and rendering
            prompts_result = await client_session.list_prompts()
            assert len(prompts_result.prompts) == 1

            prompt_result = await client_session.get_prompt("analysis_prompt")
            assert "analyze the user data" in prompt_result.messages[0]["content"]["text"]

    @pytest.mark.anyio
    async def test_error_propagation(self, test_server):
        """Test that errors propagate correctly through the protocol."""

        @test_server.tool()
        def failing_tool() -> str:
            """Tool that always fails."""
            raise ValueError("This tool always fails")

        async with create_connected_server_and_client_session(test_server._mcp_server) as (
            server_session,
            client_session,
        ):
            await client_session.initialize()

            with pytest.raises(Exception):
                await client_session.call_tool("failing_tool")
```

### 2. HTTP Transport Testing

**Test HTTP transports:**
```python
import pytest
import asyncio
import socket
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

class TestHTTPTransport:
    @pytest.fixture
    def server_port(self):
        """Get a free port for testing."""
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    @pytest.mark.anyio
    async def test_sse_transport(self, test_server, server_port):
        """Test SSE transport."""

        @test_server.tool()
        def ping() -> str:
            """Simple ping tool."""
            return "pong"

        # Configure server for testing
        test_server.settings.port = server_port

        # Start server in background
        server_task = asyncio.create_task(test_server.run_sse_async())

        try:
            # Wait for server to start
            await asyncio.sleep(0.1)

            # Test client connection
            async with sse_client(f"http://127.0.0.1:{server_port}") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await session.call_tool("ping")
                    assert result.content[0].text == "pong"
        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
```

## Mocking and Fixtures

### 1. Mocking External Dependencies

**Mock external API calls:**
```python
import pytest
from unittest.mock import AsyncMock, patch
import httpx

class TestExternalAPIs:
    @pytest.mark.anyio
    async def test_tool_with_api_call(self, test_server):
        """Test tool that makes external API calls."""

        @test_server.tool()
        async def fetch_weather(city: str) -> str:
            """Fetch weather for a city."""
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.weather.com/{city}")
                data = response.json()
                return f"Weather in {city}: {data['temperature']}°C"

        # Mock the HTTP client
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"temperature": 22}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await test_server.call_tool("fetch_weather", {"city": "London"})
            assert result[0].text == "Weather in London: 22°C"

    @pytest.mark.anyio
    async def test_tool_with_database(self, test_server):
        """Test tool that uses database."""

        @test_server.tool()
        async def get_user_from_db(user_id: int) -> str:
            """Get user from database."""
            # This would normally connect to a real database
            import asyncpg
            conn = await asyncpg.connect("postgresql://...")
            user = await conn.fetchrow("SELECT name FROM users WHERE id = $1", user_id)
            return user["name"]

        # Mock the database connection
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {"name": "Alice"}
            mock_connect.return_value = mock_conn

            result = await test_server.call_tool("get_user_from_db", {"user_id": 1})
            assert result[0].text == "Alice"
```

### 2. Test Fixtures

**Create reusable test fixtures:**
```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    (temp_dir / "data.txt").write_text("sample data")
    (temp_dir / "config.json").write_text('{"setting": "value"}')
    return temp_dir

@pytest.fixture
def mock_database():
    """Mock database with sample data."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
        ]
    }

class TestWithFixtures:
    @pytest.mark.anyio
    async def test_file_operations(self, test_server, sample_files):
        """Test file operations with fixtures."""

        @test_server.tool()
        def read_file(filename: str) -> str:
            """Read a file."""
            return (sample_files / filename).read_text()

        result = await test_server.call_tool("read_file", {"filename": "data.txt"})
        assert result[0].text == "sample data"
```

### 3. Context Mocking

**Mock FastMCP Context:**
```python
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.server.fastmcp import Context

@pytest.fixture
def mock_context():
    """Create a mock Context for testing."""
    ctx = AsyncMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.request_id = "test-request-123"
    ctx.client_id = "test-client"
    return ctx

class TestContextUsage:
    @pytest.mark.anyio
    async def test_tool_logging(self, test_server, mock_context):
        """Test tool that uses context for logging."""

        @test_server.tool()
        async def logged_operation(data: str, ctx: Context) -> str:
            """Operation with comprehensive logging."""
            await ctx.info(f"Starting operation with: {data}")
            await ctx.report_progress(0, 100, "Starting")

            # Simulate work
            result = data.upper()

            await ctx.report_progress(100, 100, "Complete")
            await ctx.info(f"Operation completed: {result}")
            return result

        # Test the tool directly with mock context
        tool = test_server._tool_manager.get_tool("logged_operation")
        result = await tool.run({"data": "test"}, context=mock_context)

        assert result == "TEST"

        # Verify logging calls
        mock_context.info.assert_any_call("Starting operation with: test")
        mock_context.info.assert_any_call("Operation completed: TEST")
        mock_context.report_progress.assert_any_call(0, 100, "Starting")
        mock_context.report_progress.assert_any_call(100, 100, "Complete")
```

## Performance Testing

### 1. Load Testing

**Test server under load:**
```python
import pytest
import asyncio
import time

class TestPerformance:
    @pytest.mark.anyio
    async def test_concurrent_tool_calls(self, test_server):
        """Test handling multiple concurrent tool calls."""

        @test_server.tool()
        async def slow_operation(duration: float) -> str:
            """Simulate a slow operation."""
            await asyncio.sleep(duration)
            return f"Completed after {duration}s"

        async with create_connected_server_and_client_session(test_server._mcp_server) as (
            server_session,
            client_session,
        ):
            await client_session.initialize()

            # Run multiple operations concurrently
            start_time = time.time()
            tasks = [
                client_session.call_tool("slow_operation", {"duration": 0.1})
                for _ in range(10)
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Should complete in roughly 0.1s (concurrent), not 1.0s (sequential)
            assert end_time - start_time < 0.5
            assert len(results) == 10

    @pytest.mark.anyio
    async def test_memory_usage(self, test_server):
        """Test memory usage doesn't grow excessively."""
        import psutil
        import os

        @test_server.tool()
        def memory_test(size: int) -> str:
            """Tool that creates temporary data."""
            # Create temporary data
            data = "x" * size
            return f"Created {len(data)} characters"

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run tool multiple times
        async with create_connected_server_and_client_session(test_server._mcp_server) as (
            server_session,
            client_session,
        ):
            await client_session.initialize()

            for _ in range(100):
                await client_session.call_tool("memory_test", {"size": 1000})

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (less than 10MB for this test)
        assert memory_growth < 10 * 1024 * 1024
```

### 2. Benchmarking

**Benchmark critical operations:**
```python
import pytest
import time

class TestBenchmarks:
    @pytest.mark.anyio
    async def test_tool_registration_performance(self):
        """Benchmark tool registration performance."""

        start_time = time.time()
        test_server = FastMCP("Benchmark Server")

        # Register many tools
        for i in range(1000):
            def make_tool(index):
                def tool_func(x: int) -> int:
                    return x + index
                tool_func.__name__ = f"tool_{index}"
                return tool_func

            test_server.add_tool(make_tool(i))

        end_time = time.time()
        registration_time = end_time - start_time

        # Should register 1000 tools in reasonable time
        assert registration_time < 5.0  # 5 seconds max
        assert len(test_server._tool_manager._tools) == 1000

    @pytest.mark.anyio
    async def test_large_payload_handling(self, test_server):
        """Test handling large payloads."""

        @test_server.tool()
        def process_large_data(data: str) -> str:
            """Process large data payload."""
            return f"Processed {len(data)} characters"

        # Test with large payload (1MB)
        large_data = "x" * (1024 * 1024)

        start_time = time.time()
        result = await test_server.call_tool("process_large_data", {"data": large_data})
        end_time = time.time()

        assert "Processed 1048576 characters" in result[0].text
        assert end_time - start_time < 1.0  # Should process quickly
```

## Testing Best Practices

### 1. Test Organization

**Organize tests logically:**
```python
# tests/test_user_management.py
class TestUserManagement:
    """Tests for user-related functionality."""

    class TestUserCreation:
        """Tests for creating users."""
        pass

    class TestUserRetrieval:
        """Tests for retrieving users."""
        pass

    class TestUserValidation:
        """Tests for user data validation."""
        pass

# tests/test_data_processing.py
class TestDataProcessing:
    """Tests for data processing tools."""
    pass
```

### 2. Test Data Management

**Use factories for test data:**
```python
import pytest
from typing import Dict, Any

class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        user = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "active": True,
            "created_at": "2024-01-01T00:00:00Z",
        }
        if overrides:
            user.update(overrides)
        return user

@pytest.fixture
def users():
    """Create test users."""
    return [
        UserFactory.create({"id": 1, "name": "Alice"}),
        UserFactory.create({"id": 2, "name": "Bob", "active": False}),
    ]
```

### 3. Error Testing

**Test error conditions systematically:**
```python
class TestErrorHandling:
    @pytest.mark.anyio
    async def test_tool_validation_errors(self, test_server):
        """Test various validation errors."""

        @test_server.tool()
        def validated_tool(
            positive_int: int,
            non_empty_string: str,
            email: str
        ) -> str:
            if positive_int <= 0:
                raise ValueError("Must be positive")
            if not non_empty_string.strip():
                raise ValueError("Cannot be empty")
            if "@" not in email:
                raise ValueError("Invalid email")
            return "valid"

        # Test each validation error
        with pytest.raises(Exception):
            await test_server.call_tool("validated_tool", {
                "positive_int": -1,
                "non_empty_string": "test",
                "email": "test@example.com"
            })

        with pytest.raises(Exception):
            await test_server.call_tool("validated_tool", {
                "positive_int": 1,
                "non_empty_string": "",
                "email": "test@example.com"
            })

        with pytest.raises(Exception):
            await test_server.call_tool("validated_tool", {
                "positive_int": 1,
                "non_empty_string": "test",
                "email": "invalid-email"
            })
```

### 4. Test Coverage

**Run tests with coverage:**
```bash
# Install coverage
uv add --dev pytest-cov

# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

**Configuration in `pyproject.toml`:**
```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/conftest.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Running Tests

### 1. Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_tools.py

# Run specific test class
uv run pytest tests/test_tools.py::TestTools

# Run specific test method
uv run pytest tests/test_tools.py::TestTools::test_simple_tool

# Run with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### 2. Test Filtering

```bash
# Run only integration tests
uv run pytest -m integration

# Run everything except integration tests
uv run pytest -m "not integration"

# Run tests matching pattern
uv run pytest -k "test_tool"

# Run failed tests from last run
uv run pytest --lf
```

### 3. Debugging Tests

```bash
# Drop into debugger on failure
uv run pytest --pdb

# Stop on first failure
uv run pytest -x

# Show local variables in tracebacks
uv run pytest -l

# Capture print statements
uv run pytest -s
```

This comprehensive testing guide provides everything needed to thoroughly test FastMCP servers, from simple unit tests to complex integration scenarios and performance benchmarks.
