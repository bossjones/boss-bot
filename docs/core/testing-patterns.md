# Testing Patterns

This document covers critical testing knowledge for Boss-Bot development, focusing on pytest-mock patterns, Discord command testing, and async testing best practices.

## Core Testing Principles

### 1. pytest-mock Exclusive Usage

**✅ ALWAYS use `mocker` fixture**
```python
# ✅ CORRECT: Use mocker fixture
@pytest.mark.asyncio
async def test_download_command(mocker: MockerFixture):
    mock_handler = mocker.Mock(spec=TwitterHandler)
    mock_handler.download.return_value = MediaMetadata(platform="twitter")
```

**❌ NEVER import unittest.mock directly**
```python
# ❌ WRONG: Don't import unittest.mock
from unittest.mock import Mock, AsyncMock  # DON'T DO THIS
```

### 2. Fixture Naming Conventions

All custom fixtures use standardized naming:

```python
# ✅ CORRECT: Standardized fixture names
@pytest.fixture(scope="function")
def fixture_settings_test() -> BossSettings:
    """Mock BossSettings for testing."""

@pytest.fixture(scope="function")
def fixture_mock_bot_test(mocker: MockerFixture) -> Mock:
    """Mock BossBot instance for testing."""

@pytest.fixture(scope="function")
def fixture_queue_manager_test() -> QueueManager:
    """Real QueueManager instance for testing."""
```

**Naming Pattern:**
- **Prefix**: `fixture_` (always)
- **Component**: `settings`, `bot`, `queue_manager`, etc.
- **Suffix**: `_test`, `_mock`, `_data` (descriptive)

### 3. Function-Scoped Fixtures for Isolation

```python
@pytest.fixture(scope="function")  # Ensures test isolation
def fixture_mock_discord_context(mocker: MockerFixture) -> Mock:
    """Create mocked Discord context for command testing."""
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    return ctx
```

## Discord Command Testing Patterns

### The `.callback()` Pattern

**✅ CORRECT: Use `.callback()` for command testing**
```python
@pytest.mark.asyncio
async def test_download_command(
    mocker: MockerFixture,
    fixture_mock_discord_context: Mock
):
    """Test download command using callback pattern."""
    # Create cog
    cog = DownloadCog(bot=None)

    # Mock the download handler
    mock_download = mocker.patch.object(
        cog, 'download_handler',
        return_value=MediaMetadata(platform="twitter", title="Test")
    )

    # Test command via callback (not direct call)
    await cog.download.callback(cog, fixture_mock_discord_context, "https://twitter.com/test")

    # Verify behavior
    mock_download.assert_called_once_with("https://twitter.com/test")
    fixture_mock_discord_context.send.assert_called_once()
```

**❌ WRONG: Direct command method calls**
```python
# ❌ DON'T DO THIS: Direct call won't work with @commands.command decorator
await cog.download(ctx, url)  # This will fail
```

### Discord Context Mocking

Always create fully mocked Discord contexts:

```python
@pytest.fixture(scope="function")
def fixture_discord_context_test(mocker: MockerFixture) -> Mock:
    """Create comprehensive Discord context mock."""
    ctx = mocker.Mock(spec=commands.Context)

    # Essential async methods
    ctx.send = mocker.AsyncMock()
    ctx.reply = mocker.AsyncMock()

    # Author information
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.author.name = "testuser"
    ctx.author.display_name = "Test User"

    # Channel information
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.channel.name = "test-channel"

    # Guild information (optional)
    ctx.guild = mocker.Mock()
    ctx.guild.id = 98765
    ctx.guild.name = "Test Guild"

    return ctx
```

### Error Handling in Commands

Test error scenarios with proper exception handling:

```python
@pytest.mark.asyncio
async def test_download_command_quota_exceeded(
    mocker: MockerFixture,
    fixture_discord_context_test: Mock
):
    """Test download command when quota is exceeded."""
    cog = DownloadCog(bot=None)

    # Mock quota exceeded exception
    mocker.patch.object(
        cog, 'download_handler',
        side_effect=QuotaExceededError("Storage quota exceeded")
    )

    # Execute command
    await cog.download.callback(cog, fixture_discord_context_test, "test_url")

    # Verify error message sent to user
    sent_message = fixture_discord_context_test.send.call_args[0][0]
    assert "quota exceeded" in sent_message.lower()
```

## Async Testing Best Practices

### 1. Proper AsyncMock Usage

```python
@pytest.mark.asyncio
async def test_async_operation(mocker: MockerFixture):
    """Test async operations with AsyncMock."""

    # ✅ CORRECT: AsyncMock for async methods
    mock_client = mocker.Mock()
    mock_client.download = mocker.AsyncMock(
        return_value={"status": "success"}
    )

    # ✅ CORRECT: AsyncMock for context managers
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

    # Test async context manager
    async with mock_client as client:
        result = await client.download("test_url")
        assert result["status"] == "success"
```

### 2. Async Generator Mocking

```python
async def async_generator_mock():
    """Helper to create async generator mock responses."""
    yield {"extractor": "twitter", "url": "test1.jpg"}
    yield {"extractor": "twitter", "url": "test2.jpg"}

@pytest.mark.asyncio
async def test_async_generator(mocker: MockerFixture):
    """Test code that uses async generators."""
    mock_client = mocker.Mock()
    mock_client.download = mocker.AsyncMock(
        return_value=async_generator_mock()
    )

    items = []
    async for item in await mock_client.download("test_url"):
        items.append(item)

    assert len(items) == 2
    assert items[0]["extractor"] == "twitter"
```

### 3. Executor Pattern Testing

For sync operations in async contexts:

```python
@pytest.mark.asyncio
async def test_sync_in_async_context(mocker: MockerFixture):
    """Test sync operations executed in thread pool."""

    # Mock the sync operation
    mock_sync_operation = mocker.Mock(return_value="sync_result")

    # Mock executor
    mock_executor = mocker.patch('asyncio.get_event_loop')
    mock_loop = mocker.Mock()
    mock_executor.return_value = mock_loop
    mock_loop.run_in_executor = mocker.AsyncMock(return_value="sync_result")

    # Test async wrapper
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, mock_sync_operation, "arg")

    assert result == "sync_result"
    mock_loop.run_in_executor.assert_called_once_with(None, mock_sync_operation, "arg")
```

## VCR Testing for API Interactions

### Basic VCR Configuration

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def vcr_config():
    """Configure VCR for safe API testing."""
    return {
        "record_mode": "once",  # Record once, then replay
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "filter_headers": [
            "authorization", "cookie", "x-api-key", "user-agent"
        ],
        "filter_query_parameters": [
            "api_key", "access_token", "client_secret"
        ],
    }
```

### VCR Test Patterns

```python
@pytest.mark.asyncio
@pytest.mark.vcr(cassette_library_dir="tests/cassettes")
async def test_api_download_with_vcr():
    """Test API download with VCR recording."""
    config = {
        "extractor": {
            "twitter": {"videos": True, "quoted": True}
        }
    }

    async with AsyncGalleryDL(config=config) as client:
        items = []
        async for item in client.download("https://twitter.com/example/status/123"):
            items.append(item)

        assert len(items) > 0
        assert items[0]["extractor"] == "twitter"
```

### Security Filtering for VCR

```python
def filter_request(request):
    """Remove sensitive data from VCR recordings."""
    # Remove authorization headers
    if 'authorization' in request.headers:
        request.headers['authorization'] = '<REDACTED>'

    # Filter API keys from query parameters
    if hasattr(request, 'query') and request.query:
        filtered_query = []
        for param in request.query:
            if 'api_key' in param[0].lower():
                filtered_query.append((param[0], '<REDACTED>'))
            else:
                filtered_query.append(param)
        request.query = filtered_query

    return request
```

## Fixture Organization and Documentation

### Fixture Documentation Standards

```python
@pytest.fixture(scope="function")
def fixture_download_strategy_test(
    fixture_settings_test: BossSettings,
    tmp_path: Path
) -> TwitterDownloadStrategy:
    """Create TwitterDownloadStrategy instance for testing.

    Provides a strategy instance with mocked settings and temporary
    download directory for isolated testing.

    Args:
        fixture_settings_test: Mocked BossSettings instance
        tmp_path: Pytest temporary directory fixture

    Returns:
        TwitterDownloadStrategy: Configured strategy instance

    Dependencies:
        - fixture_settings_test: For configuration
        - tmp_path: For isolated file operations
    """
    return TwitterDownloadStrategy(
        settings=fixture_settings_test,
        download_dir=tmp_path
    )
```

### Conftest.py Organization

```python
# tests/conftest.py - Organized by sections

"""Test configuration and fixtures for boss-bot."""

import pytest
from unittest.mock import Mock, AsyncMock
from pytest_mock import MockerFixture

# ============================================================================
# Environment and Settings Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_env_vars_test() -> dict[str, str]:
    """Provide test environment variables."""
    return {
        "DISCORD_TOKEN": "test_token",
        "COMMAND_PREFIX": "$",
        "DOWNLOAD_DIR": "/tmp/downloads"
    }

@pytest.fixture(scope="function")
def fixture_settings_test(fixture_env_vars_test: dict) -> BossSettings:
    """Create BossSettings instance for testing."""
    return BossSettings(**fixture_env_vars_test)

# ============================================================================
# Bot and Discord Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_mock_bot_test(mocker: MockerFixture) -> Mock:
    """Create a mocked BossBot instance for testing."""
    bot = mocker.Mock(spec=BossBot)
    bot.queue_manager = mocker.Mock()
    bot.download_manager = mocker.Mock()
    return bot

# ============================================================================
# Download System Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_twitter_handler_test(tmp_path: Path) -> TwitterHandler:
    """Create TwitterHandler instance for testing."""
    return TwitterHandler(download_dir=tmp_path)
```

## Test Structure and File Organization

### Test Directory Structure

```
tests/
├── conftest.py                    # Global fixtures
├── test_bot/
│   ├── conftest.py               # Bot-specific fixtures
│   ├── test_client.py            # BossBot client tests
│   └── test_cogs/
│       ├── test_downloads.py     # Download cog tests
│       └── test_queue.py         # Queue cog tests
├── test_core/
│   ├── conftest.py               # Core-specific fixtures
│   ├── test_downloads/
│   │   ├── test_handlers/        # Handler tests (CLI)
│   │   ├── test_strategies/      # Strategy tests (API)
│   │   └── test_clients/         # API client tests with VCR
│   └── test_queue/
│       └── test_manager.py       # Queue manager tests
└── fixtures/                     # Test data files
    ├── sample_responses.json
    └── test_media_files/
```

### Test Naming Conventions

```python
# Test class organization
class TestDownloadCog:
    """Test suite for DownloadCog."""

    @pytest.mark.asyncio
    async def test_download_command_success(self):
        """Test successful download command execution."""

    @pytest.mark.asyncio
    async def test_download_command_invalid_url(self):
        """Test download command with invalid URL."""

    @pytest.mark.asyncio
    async def test_download_command_quota_exceeded(self):
        """Test download command when quota is exceeded."""

# Test function naming patterns
def test_twitter_handler_supports_url():
    """Test URL support detection for Twitter handler."""

def test_twitter_handler_download_success():
    """Test successful Twitter content download."""

def test_twitter_handler_download_failure():
    """Test Twitter download error handling."""
```

## Common Testing Pitfalls to Avoid

### 1. Direct Discord Command Calls
```python
# ❌ WRONG: This won't work with @commands.command
await cog.download(ctx, url)

# ✅ CORRECT: Use callback pattern
await cog.download.callback(cog, ctx, url)
```

### 2. Missing AsyncMock for Async Methods
```python
# ❌ WRONG: Regular Mock for async method
ctx.send = mocker.Mock()

# ✅ CORRECT: AsyncMock for async method
ctx.send = mocker.AsyncMock()
```

### 3. Insufficient Context Mocking
```python
# ❌ WRONG: Incomplete context mock
ctx = mocker.Mock()
ctx.send = mocker.AsyncMock()

# ✅ CORRECT: Complete context mock with all required attributes
ctx = mocker.Mock(spec=commands.Context)
ctx.send = mocker.AsyncMock()
ctx.author = mocker.Mock()
ctx.author.id = 12345
ctx.channel = mocker.Mock()
ctx.channel.id = 67890
```

### 4. Sync/Async Mixing
```python
# ❌ WRONG: Missing @pytest.mark.asyncio
def test_async_function():
    result = await some_async_function()

# ✅ CORRECT: Proper async test decoration
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
```

Following these testing patterns ensures reliable, maintainable tests that accurately verify Discord bot functionality and async operations.
