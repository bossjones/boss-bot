# Discord.py Bot Testing with dpytest

This guide explains how to use `dpytest` for testing Discord bots built with `discord.py`. The examples are based on best practices from projects like [KoalaBot](https://github.com/KoalaBotUK/KoalaBot) and the official dpytest documentation.

## Overview

`dpytest` is a testing library specifically designed for Discord bots using `discord.py`. It allows you to:
- Simulate Discord messages and interactions
- Test bot commands without connecting to Discord
- Verify bot responses and behavior
- Create isolated test environments

## Prerequisites

- Python 3.8+
- discord.py (rewrite version)
- pytest and pytest-asyncio
- Basic understanding of async/await in Python

## Installation

```bash
# Install required packages
pip install dpytest pytest pytest-asyncio

# Or with uv (recommended for this project)
uv add --dev dpytest pytest pytest-asyncio
```

## Project Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── test_bot/
│   ├── __init__.py
│   ├── test_basic_commands.py
│   ├── test_cogs/
│   │   ├── __init__.py
│   │   ├── test_downloads.py
│   │   └── test_queue.py
│   └── test_error_handling.py
└── fixtures/            # Test data files
    └── sample_data.json
```

## Setting Up conftest.py

The `conftest.py` file contains shared fixtures that pytest automatically makes available to all test files:

```python
"""Test configuration and fixtures for Discord bot testing."""

import pytest
import pytest_asyncio
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from unittest.mock import Mock, AsyncMock

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings


@pytest_asyncio.fixture(scope="function")
async def bot_settings():
    """Create test settings for the bot."""
    return BossSettings(
        discord_token="test_token_123",
        openai_api_key="test_openai_key",
        langchain_api_key="test_langchain_key",
        langchain_hub_api_key="test_hub_key",
        debug=True,
        environment="testing"
    )


@pytest_asyncio.fixture(scope="function")
async def mock_bot(bot_settings):
    """Create a mocked BossBot instance for testing."""
    # Create bot with proper intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Mock external dependencies
    mock_download_manager = Mock()
    mock_download_manager.validate_url.return_value = True
    mock_download_manager.get_active_downloads.return_value = 0

    mock_queue_manager = Mock()
    mock_queue_manager.queue_size = 0
    mock_queue_manager.add_to_queue = AsyncMock()

    bot = BossBot(
        command_prefix="!",
        intents=intents,
        settings=bot_settings
    )

    # Inject mocked dependencies
    bot.download_manager = mock_download_manager
    bot.queue_manager = mock_queue_manager

    # Setup bot for testing
    await bot._async_setup_hook()

    # Load cogs if needed
    # await bot.load_extension("boss_bot.bot.cogs.downloads")

    # Configure dpytest
    dpytest.configure(bot)

    yield bot

    # Cleanup after test
    await dpytest.empty_queue()


@pytest_asyncio.fixture(scope="function")
async def ctx_mock():
    """Create a mocked Context for direct command testing."""
    ctx = Mock(spec=commands.Context)
    ctx.send = AsyncMock()
    ctx.author = Mock()
    ctx.author.id = 12345
    ctx.channel = Mock()
    ctx.channel.id = 67890
    return ctx


@pytest.fixture(scope="function")
def sample_urls():
    """Provide sample URLs for testing."""
    return {
        "twitter": "https://twitter.com/user/status/123456789",
        "reddit": "https://reddit.com/r/python/comments/abc123/test",
        "youtube": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "instagram": "https://instagram.com/p/ABC123/",
        "invalid": "not-a-url"
    }
```

## Basic Command Testing

Here's how to test basic bot commands using dpytest:

```python
"""Test basic bot commands."""

import pytest
import pytest_asyncio
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_ping_command(mock_bot):
    """Test basic ping command."""
    await dpytest.message("!ping")

    # Verify bot responded
    assert dpytest.verify().message().contains().content("Pong")


@pytest.mark.asyncio
async def test_help_command(mock_bot):
    """Test help command shows available commands."""
    await dpytest.message("!help")

    # Check that help message was sent
    assert dpytest.verify().message().content().contains("Commands")


@pytest.mark.asyncio
async def test_invalid_command(mock_bot):
    """Test bot handles invalid commands gracefully."""
    await dpytest.message("!invalid_command")

    # Should either ignore or send error message
    # Depends on your bot's error handling
    # This example assumes the bot sends an error message
    assert dpytest.verify().message().contains().content("not found")
```

## Testing Cogs and Complex Commands

For testing individual cogs or complex commands:

```python
"""Test download cog functionality."""

import pytest
import pytest_asyncio
import discord.ext.test as dpytest
from unittest.mock import Mock, AsyncMock, patch

from boss_bot.bot.cogs.downloads import DownloadCog


@pytest.mark.asyncio
async def test_download_command_twitter(mock_bot, sample_urls):
    """Test downloading from Twitter URL."""
    # Mock successful download
    with patch('boss_bot.core.downloads.strategies.TwitterDownloadStrategy.download') as mock_download:
        mock_metadata = Mock()
        mock_metadata.error = None
        mock_metadata.title = "Test Tweet"
        mock_metadata.download_method = "cli"
        mock_download.return_value = mock_metadata

        await dpytest.message(f"!download {sample_urls['twitter']}")

        # Verify success message
        assert dpytest.verify().message().contains().content("✅")
        assert dpytest.verify().message().contains().content("download completed")


@pytest.mark.asyncio
async def test_download_command_failure(mock_bot, sample_urls):
    """Test download command with failure."""
    with patch('boss_bot.core.downloads.strategies.TwitterDownloadStrategy.download') as mock_download:
        mock_metadata = Mock()
        mock_metadata.error = "Download failed: Network error"
        mock_download.return_value = mock_metadata

        await dpytest.message(f"!download {sample_urls['twitter']}")

        # Verify error message
        assert dpytest.verify().message().contains().content("❌")
        assert dpytest.verify().message().contains().content("failed")


@pytest.mark.asyncio
async def test_info_command(mock_bot, sample_urls):
    """Test metadata info command."""
    with patch('boss_bot.core.downloads.strategies.TwitterDownloadStrategy.get_metadata') as mock_metadata:
        mock_meta = Mock()
        mock_meta.title = "Sample Tweet Title"
        mock_meta.uploader = "@testuser"
        mock_meta.upload_date = "2024-01-01"
        mock_meta.like_count = 42
        mock_metadata.return_value = mock_meta

        await dpytest.message(f"!info {sample_urls['twitter']}")

        # Verify metadata is shown
        assert dpytest.verify().message().contains().content("Twitter Content Info")
        assert dpytest.verify().message().contains().content("Sample Tweet Title")


@pytest.mark.asyncio
async def test_strategies_command(mock_bot):
    """Test strategies configuration command."""
    await dpytest.message("!strategies")

    # Verify configuration is displayed
    assert dpytest.verify().message().contains().content("Download Strategy Configuration")
    assert dpytest.verify().message().contains().content("Twitter/X")
    assert dpytest.verify().message().contains().content("CLI Mode")
```

## Direct Command Testing (Without dpytest)

Sometimes you need to test command logic directly without the Discord simulation:

```python
"""Test command logic directly."""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock

from boss_bot.bot.cogs.downloads import DownloadCog


@pytest.mark.asyncio
async def test_download_callback_direct(ctx_mock, bot_settings):
    """Test download command callback directly."""
    # Create cog instance
    mock_bot = Mock()
    mock_bot.settings = bot_settings
    cog = DownloadCog(mock_bot)

    # Mock strategy
    mock_strategy = Mock()
    mock_metadata = Mock()
    mock_metadata.error = None
    mock_metadata.title = "Test Content"
    mock_strategy.download = AsyncMock(return_value=mock_metadata)

    # Patch strategy lookup
    with patch.object(cog, '_get_strategy_for_url', return_value=mock_strategy):
        # Call command callback directly
        await cog.download.callback(cog, ctx_mock, "https://twitter.com/test")

    # Verify context.send was called with success message
    assert ctx_mock.send.called
    sent_args = ctx_mock.send.call_args[0][0]
    assert "✅" in sent_args


@pytest.mark.asyncio
async def test_get_platform_info(bot_settings):
    """Test platform info helper method."""
    mock_bot = Mock()
    mock_bot.settings = bot_settings
    cog = DownloadCog(mock_bot)

    # Test different platforms
    twitter_info = cog._get_platform_info("https://twitter.com/test")
    assert twitter_info["emoji"] == "🐦"
    assert twitter_info["name"] == "Twitter/X"

    reddit_info = cog._get_platform_info("https://reddit.com/r/test")
    assert reddit_info["emoji"] == "🤖"
    assert reddit_info["name"] == "Reddit"
```

## Testing Error Handling

```python
"""Test error handling scenarios."""

import pytest
import pytest_asyncio
import discord.ext.test as dpytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_download_network_error(mock_bot, sample_urls):
    """Test handling of network errors during download."""
    with patch('boss_bot.core.downloads.strategies.TwitterDownloadStrategy.download') as mock_download:
        mock_download.side_effect = ConnectionError("Network unreachable")

        await dpytest.message(f"!download {sample_urls['twitter']}")

        # Verify error is handled gracefully
        assert dpytest.verify().message().contains().content("❌")
        assert dpytest.verify().message().contains().content("error")


@pytest.mark.asyncio
async def test_invalid_url_handling(mock_bot, sample_urls):
    """Test handling of invalid URLs."""
    await dpytest.message(f"!download {sample_urls['invalid']}")

    # Should fall back to queue system or show error
    # Verify appropriate response based on your bot's behavior
    assert dpytest.verify().message()  # Some response should be sent


@pytest.mark.asyncio
async def test_command_permission_error(mock_bot):
    """Test commands with insufficient permissions."""
    # Simulate permission error
    with patch('discord.ext.commands.Context.send', side_effect=discord.Forbidden(Mock(), "Insufficient permissions")):
        await dpytest.message("!download https://twitter.com/test")

        # dpytest should handle this gracefully
        # The exact assertion depends on your error handling
```

## Advanced Testing Patterns

### Testing with Different User Permissions

```python
@pytest.mark.asyncio
async def test_admin_only_command(mock_bot):
    """Test command that requires admin permissions."""
    # Get test guild and member
    config = dpytest.get_config()
    guild = config.guilds[0]

    # Create admin member
    admin_member = await dpytest.member_join(permissions=discord.Permissions.all())

    # Test with admin user
    await dpytest.message("!admin_command", member=admin_member)
    assert dpytest.verify().message().contains().content("Admin command executed")

    # Test with regular user (should fail)
    regular_member = await dpytest.member_join()
    await dpytest.message("!admin_command", member=regular_member)
    assert dpytest.verify().message().contains().content("permission")
```

### Testing Reactions and Interactions

```python
@pytest.mark.asyncio
async def test_reaction_handling(mock_bot):
    """Test bot responds to reactions."""
    # Send initial message
    await dpytest.message("!react_test")

    # Get the bot's response message
    message = dpytest.sent_queue[0]

    # Add reaction to the message
    await dpytest.add_reaction(message, "👍")

    # Verify bot handles the reaction
    # (Implementation depends on your bot's reaction handling)
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_bot/test_downloads.py

# Run with verbose output
pytest -v

# Run only async tests
pytest -m asyncio

# Run with coverage
pytest --cov=boss_bot --cov-report=html

# Run specific test
pytest tests/test_bot/test_downloads.py::test_download_command_twitter
```

## Best Practices

### 1. **Test Isolation**
- Always use `await dpytest.empty_queue()` in fixture teardown
- Use function-scoped fixtures to ensure clean state
- Mock external dependencies (APIs, file systems, databases)

### 2. **Realistic Testing**
```python
# Good: Test actual command flow
await dpytest.message("!download https://twitter.com/test")
assert dpytest.verify().message().contains().content("✅")

# Better: Also test edge cases
await dpytest.message("!download invalid-url")
assert dpytest.verify().message().contains().content("Invalid")
```

### 3. **Mock External Services**
```python
# Always mock external API calls
with patch('requests.get') as mock_get:
    mock_get.return_value.json.return_value = {"status": "success"}
    await dpytest.message("!download https://api.example.com/media/123")
```

### 4. **Test Command Variations**
```python
# Test different argument patterns
await dpytest.message("!download https://twitter.com/test")        # Basic
await dpytest.message("!download https://twitter.com/test --hd")   # With options
await dpytest.message("!download")                                 # Missing args
```

### 5. **Use Descriptive Test Names**
```python
def test_download_twitter_url_with_api_fallback_enabled():
    """Test Twitter download when API fails and fallback is enabled."""
    pass
```

## Common Pitfalls

1. **Forgetting to empty the queue**: Always use `await dpytest.empty_queue()` in teardown
2. **Not mocking external dependencies**: This leads to flaky tests and network dependencies
3. **Testing implementation details**: Focus on behavior, not internal method calls
4. **Inconsistent async/await**: Make sure all test functions are properly async
5. **Not testing error conditions**: Always test both success and failure scenarios

## Integration with CI/CD

Add to your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "asyncio: mark test as async",
    "integration: mark test as integration test",
    "slow: mark test as slow running",
]
```

And in GitHub Actions:

```yaml
- name: Run tests
  run: |
    uv run pytest tests/ -v --cov=boss_bot --cov-report=xml
```

## Conclusion

dpytest provides a powerful framework for testing Discord bots without requiring actual Discord API connections. By following these patterns and best practices, you can create comprehensive test suites that ensure your bot works correctly across different scenarios and edge cases.

For more advanced features and API reference, consult the [official dpytest documentation](https://dpytest.readthedocs.io/).
