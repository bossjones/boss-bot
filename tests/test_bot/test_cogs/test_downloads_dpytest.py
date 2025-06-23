"""Test downloads cog functionality with direct command callback testing.

This module tests the DownloadCog using direct command callback testing,
following TDD principles and the patterns from the existing codebase.

Tests cover:
- download command with platform strategies
- metadata command for metadata extraction
- status command for system status
- strategies command for configuration display
- Error handling and edge cases
- Permission and concurrent usage scenarios
"""

import asyncio
import pytest
import pytest_asyncio
import discord
from discord.ext import commands
from pathlib import Path

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.downloads.strategies import BaseDownloadStrategy
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata


@pytest.fixture(scope="function")
def fixture_download_test_data():
    """Provide test data for download testing."""
    return {
        "twitter_url": "https://twitter.com/user/status/123456789",
        "reddit_url": "https://www.reddit.com/r/test/comments/abc123/test_post",
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "instagram_url": "https://www.instagram.com/p/ABC123/",
        "unsupported_url": "https://unsupported-site.com/content/123",
        "invalid_url": "not_a_valid_url",
        "empty_url": "",
    }


@pytest.fixture(scope="function")
def fixture_mock_strategies(mocker):
    """Mock all download strategies for controlled testing."""
    mock_strategies = {}

    strategy_names = ["twitter", "reddit", "youtube", "instagram"]
    for name in strategy_names:
        mock_strategy = mocker.Mock(spec=BaseDownloadStrategy)
        mock_strategy.supports_url = mocker.Mock(return_value=False)  # Default to False
        mock_strategy.download = mocker.AsyncMock()
        mock_strategy.get_metadata = mocker.AsyncMock()
        mock_strategy.download_dir = Path("/tmp/downloads")  # Mock download directory
        mock_strategies[name] = mock_strategy

    return mock_strategies


@pytest.fixture(scope="function")
def fixture_mock_metadata(mocker):
    """Provide mock metadata for testing."""
    metadata = mocker.Mock()
    metadata.title = "Test Content Title"
    metadata.uploader = "testuser"
    metadata.upload_date = "2024-01-01"
    metadata.like_count = 100
    metadata.view_count = 50
    metadata.duration = "3:45"
    metadata.error = None
    metadata.download_method = "cli"
    metadata.raw_metadata = {"subreddit": "test", "num_comments": 42}
    return metadata


# RED PHASE: Write failing tests first

@pytest.mark.asyncio
async def test_download_command_twitter_success_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command succeeds with Twitter URL using direct callback."""
    # Get the cog from the bot
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Twitter strategy to support URL and succeed
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.download.return_value = fixture_mock_metadata

    # Replace cog strategies with mocks
    cog.strategies = fixture_mock_strategies

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.message = mocker.Mock()
    ctx.message.id = 123456789

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Call download command directly
    await cog.download.callback(cog, ctx, fixture_download_test_data['twitter_url'], upload=False)

    # Verify strategy was called
    twitter_strategy.supports_url.assert_called_with(fixture_download_test_data['twitter_url'])
    twitter_strategy.download.assert_called_once_with(fixture_download_test_data['twitter_url'])

    # Verify bot responses
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("🐦 Downloading Twitter/X content:" in arg for arg in call_args)
    assert any("✅ Twitter/X download completed!" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_reddit_success_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command succeeds with Reddit URL using direct callback."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Reddit strategy to support URL and succeed
    reddit_strategy = fixture_mock_strategies["reddit"]
    reddit_strategy.supports_url.return_value = True
    reddit_strategy.download.return_value = fixture_mock_metadata

    cog.strategies = fixture_mock_strategies

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.message = mocker.Mock()
    ctx.message.id = 123456789

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Call download command directly
    await cog.download.callback(cog, ctx, fixture_download_test_data['reddit_url'], upload=False)

    # Verify strategy was called
    reddit_strategy.supports_url.assert_called_with(fixture_download_test_data['reddit_url'])
    reddit_strategy.download.assert_called_once_with(fixture_download_test_data['reddit_url'])

    # Verify bot responses
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("🤖 Downloading Reddit content:" in arg for arg in call_args)
    assert any("✅ Reddit download completed!" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_strategy_failure_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command handles strategy failure gracefully."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Twitter strategy to support URL but fail download
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True

    # Mock failed download
    failed_metadata = mocker.Mock()
    failed_metadata.error = "Network timeout error"
    failed_metadata.title = None
    twitter_strategy.download.return_value = failed_metadata

    cog.strategies = fixture_mock_strategies

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.message = mocker.Mock()
    ctx.message.id = 123456789

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Call download command directly
    await cog.download.callback(cog, ctx, fixture_download_test_data['twitter_url'], upload=False)

    # Verify error handling
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("❌ Twitter/X download failed: Network timeout error" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_fallback_to_queue_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command falls back to queue for unsupported URLs."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure all strategies to not support the URL
    for strategy in fixture_mock_strategies.values():
        strategy.supports_url.return_value = False

    cog.strategies = fixture_mock_strategies

    # Mock the bot managers for fallback
    fixture_bot_test.download_manager.validate_url = mocker.AsyncMock(return_value=True)
    fixture_bot_test.queue_manager.add_to_queue = mocker.AsyncMock()

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call download command directly
    await cog.download.callback(cog, ctx, fixture_download_test_data['unsupported_url'])

    # Verify fallback to queue system
    fixture_bot_test.queue_manager.add_to_queue.assert_called_once()
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("Added" in arg for arg in call_args)
    assert any("to download queue" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_metadata_command_twitter_metadata_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test metadata command retrieves Twitter metadata using direct callback."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Twitter strategy to support URL and return metadata
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.get_metadata.return_value = fixture_mock_metadata

    cog.strategies = fixture_mock_strategies

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call metadata command directly
    await cog.metadata.callback(cog, ctx, fixture_download_test_data['twitter_url'])

    # Verify metadata extraction was called
    twitter_strategy.get_metadata.assert_called_once_with(fixture_download_test_data['twitter_url'])

    # Verify metadata display
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("🐦 **Twitter/X Content Info**" in arg for arg in call_args)
    assert any("Test Content Title" in arg for arg in call_args)
    assert any("testuser" in arg for arg in call_args)
    assert any("❤️ **Likes:** 100" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_status_command_dpytest(
    fixture_bot_test,
    mocker
):
    """Test status command displays current system status."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Mock the bot managers
    fixture_bot_test.download_manager.get_active_downloads = mocker.Mock(return_value=3)
    fixture_bot_test.queue_manager._queue = [mocker.Mock()] * 7  # Mock 7 items in queue

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call status command directly
    await cog.status.callback(cog, ctx)

    # Verify status display
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("Active downloads: 3" in arg for arg in call_args)
    assert any("Queue size: 7" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_strategies_command_dpytest(
    fixture_bot_test,
    mocker
):
    """Test strategies command displays strategy configuration."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Mock feature flags info
    mock_info = {
        "twitter_api": True,
        "reddit_api": False,
        "youtube_api": True,
        "instagram_api": False,
        "api_fallback": True
    }
    cog.feature_flags.get_strategy_info = mocker.Mock(return_value=mock_info)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call show_strategies command directly
    await cog.show_strategies.callback(cog, ctx)

    # Verify strategy configuration display
    call_args = [call[0][0] for call in ctx.send.call_args_list]
    assert any("🔧 **Download Strategy Configuration**" in arg for arg in call_args)
    assert any("🐦 Twitter/X: 🚀 **API-Direct**" in arg for arg in call_args)
    assert any("🤖 Reddit: 🖥️ **CLI Mode**" in arg for arg in call_args)


# ADVANCED TEST SCENARIOS

@pytest.mark.asyncio
async def test_download_command_concurrent_usage_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command handles concurrent usage correctly."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure multiple strategies to support different URLs
    twitter_strategy = fixture_mock_strategies["twitter"]
    reddit_strategy = fixture_mock_strategies["reddit"]

    # Make strategies selectively support URLs
    def twitter_supports_url(url):
        return "twitter.com" in url
    def reddit_supports_url(url):
        return "reddit.com" in url

    twitter_strategy.supports_url.side_effect = twitter_supports_url
    reddit_strategy.supports_url.side_effect = reddit_supports_url

    twitter_strategy.download.return_value = fixture_mock_metadata
    reddit_strategy.download.return_value = fixture_mock_metadata

    cog.strategies = fixture_mock_strategies

    # Create mock contexts for concurrent requests
    ctx1 = mocker.Mock(spec=commands.Context)
    ctx1.send = mocker.AsyncMock()
    ctx1.author = mocker.Mock()
    ctx1.author.id = 12345
    ctx1.channel = mocker.Mock()
    ctx1.channel.id = 67890
    ctx1.message = mocker.Mock()
    ctx1.message.id = 123456789

    ctx2 = mocker.Mock(spec=commands.Context)
    ctx2.send = mocker.AsyncMock()
    ctx2.author = mocker.Mock()
    ctx2.author.id = 54321
    ctx2.channel = mocker.Mock()
    ctx2.channel.id = 98765
    ctx2.message = mocker.Mock()
    ctx2.message.id = 987654321

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Simulate concurrent download requests
    await asyncio.gather(
        cog.download.callback(cog, ctx1, fixture_download_test_data['twitter_url'], upload=False),
        cog.download.callback(cog, ctx2, fixture_download_test_data['reddit_url'], upload=False)
    )

    # Verify downloads were processed
    twitter_strategy.download.assert_called()
    reddit_strategy.download.assert_called()

    # Verify responses for both contexts
    ctx1_args = [call[0][0] for call in ctx1.send.call_args_list]
    ctx2_args = [call[0][0] for call in ctx2.send.call_args_list]

    # Should have success messages in both contexts
    assert any("✅" in arg for arg in ctx1_args)
    assert any("✅" in arg for arg in ctx2_args)


@pytest.mark.asyncio
async def test_download_command_permission_handling_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command respects Discord permissions."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Twitter strategy
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.download.return_value = fixture_mock_metadata

    cog.strategies = fixture_mock_strategies

    # Create contexts for different permission levels
    admin_ctx = mocker.Mock(spec=commands.Context)
    admin_ctx.send = mocker.AsyncMock()
    admin_ctx.author = mocker.Mock()
    admin_ctx.author.id = 12345
    admin_ctx.channel = mocker.Mock()
    admin_ctx.channel.id = 67890
    admin_ctx.message = mocker.Mock()
    admin_ctx.message.id = 123456789
    admin_ctx.author.guild_permissions = discord.Permissions.all()

    regular_ctx = mocker.Mock(spec=commands.Context)
    regular_ctx.send = mocker.AsyncMock()
    regular_ctx.author = mocker.Mock()
    regular_ctx.author.id = 54321
    regular_ctx.channel = mocker.Mock()
    regular_ctx.channel.id = 98765
    regular_ctx.message = mocker.Mock()
    regular_ctx.message.id = 987654321
    regular_ctx.author.guild_permissions = discord.Permissions.none()

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Test admin access
    await cog.download.callback(cog, admin_ctx, fixture_download_test_data['twitter_url'], upload=False)

    # Verify admin can use command
    admin_args = [call[0][0] for call in admin_ctx.send.call_args_list]
    assert any("🐦 Downloading Twitter/X content:" in arg for arg in admin_args)

    # Test regular user access
    await cog.download.callback(cog, regular_ctx, fixture_download_test_data['twitter_url'], upload=False)

    # Regular users should also be able to use download command (no special permissions required)
    regular_args = [call[0][0] for call in regular_ctx.send.call_args_list]
    assert any("🐦 Downloading Twitter/X content:" in arg for arg in regular_args)


@pytest.mark.asyncio
async def test_command_isolation_dpytest(
    fixture_bot_test,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test that commands don't interfere with each other."""
    cog = fixture_bot_test.get_cog("DownloadCog")
    assert cog is not None, "DownloadCog should be loaded"

    # Configure Twitter strategy
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.download.return_value = fixture_mock_metadata
    twitter_strategy.get_metadata.return_value = fixture_mock_metadata

    cog.strategies = fixture_mock_strategies

    # Create mock contexts for different commands
    info_ctx = mocker.Mock(spec=commands.Context)
    info_ctx.send = mocker.AsyncMock()
    info_ctx.author = mocker.Mock()
    info_ctx.author.id = 12345
    info_ctx.channel = mocker.Mock()
    info_ctx.channel.id = 67890

    download_ctx = mocker.Mock(spec=commands.Context)
    download_ctx.send = mocker.AsyncMock()
    download_ctx.author = mocker.Mock()
    download_ctx.author.id = 23456
    download_ctx.channel = mocker.Mock()
    download_ctx.channel.id = 78901
    download_ctx.message = mocker.Mock()
    download_ctx.message.id = 123456789

    status_ctx = mocker.Mock(spec=commands.Context)
    status_ctx.send = mocker.AsyncMock()
    status_ctx.author = mocker.Mock()
    status_ctx.author.id = 34567
    status_ctx.channel = mocker.Mock()
    status_ctx.channel.id = 89012

    # Mock upload manager to avoid upload processing in tests
    cog.upload_manager = mocker.Mock()
    cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Run metadata command
    await cog.metadata.callback(cog, info_ctx, fixture_download_test_data['twitter_url'])
    info_args = [call[0][0] for call in info_ctx.send.call_args_list]
    assert any("🐦 **Twitter/X Content Info**" in arg for arg in info_args)

    # Run download command - should be independent
    await cog.download.callback(cog, download_ctx, fixture_download_test_data['twitter_url'], upload=False)
    download_args = [call[0][0] for call in download_ctx.send.call_args_list]
    assert any("✅ Twitter/X download completed!" in arg for arg in download_args)

    # Run status command - should also be independent
    fixture_bot_test.download_manager.get_active_downloads = mocker.Mock(return_value=1)
    fixture_bot_test.queue_manager._queue = [mocker.Mock()] * 2  # Mock 2 items in queue

    await cog.status.callback(cog, status_ctx)
    status_args = [call[0][0] for call in status_ctx.send.call_args_list]
    assert any("Active downloads: 1" in arg for arg in status_args)

    # Verify each command was called independently
    twitter_strategy.get_metadata.assert_called_once()
    twitter_strategy.download.assert_called_once()
