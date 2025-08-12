"""Test downloads cog functionality with direct command testing.

This module tests the DownloadCog using direct command callback testing,
bypassing dpytest for more reliable testing of command logic.

Tests cover:
- download command with platform strategies
- metadata command for metadata extraction
- status command for system status
- strategies command for configuration display
- Error handling and edge cases
"""

import pytest
import pytest_asyncio
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


@pytest.fixture(scope="function")
def fixture_mock_ctx(mocker):
    """Create a mock context for testing."""
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.guild = mocker.Mock()
    ctx.guild.id = 13579
    ctx.message = mocker.Mock()
    ctx.message.id = 123456789
    return ctx


@pytest.fixture(scope="function")
def fixture_download_cog(fixture_mock_bot_test):
    """Create a DownloadCog instance for testing."""
    return DownloadCog(fixture_mock_bot_test)


# Direct command testing (bypassing dpytest)

@pytest.mark.asyncio
async def test_download_command_twitter_success_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command succeeds with Twitter URL using direct callback."""
    # Replace cog strategies with mocks
    fixture_download_cog.strategies = fixture_mock_strategies

    # Configure Twitter strategy to support URL and succeed
    twitter_strategy = fixture_mock_strategies["twitter"]

    # Configure Twitter strategy to support URL and succeed
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.download = mocker.AsyncMock(return_value=fixture_mock_metadata)

    # Ensure other strategies don't support this URL
    for name, strategy in fixture_mock_strategies.items():
        if name != "twitter":
            strategy.supports_url.return_value = False

    # Mock upload manager to avoid upload processing in tests
    fixture_download_cog.upload_manager = mocker.Mock()
    fixture_download_cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Call the download command's callback directly with upload=False for simpler testing
    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['twitter_url'],
        upload=False
    )

    # Verify strategy was called
    twitter_strategy.supports_url.assert_called_with(fixture_download_test_data['twitter_url'])
    twitter_strategy.download.assert_called_once_with(fixture_download_test_data['twitter_url'])

    # Verify bot responses
    assert fixture_mock_ctx.send.call_count >= 2  # At least downloading message and success message
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]

    # Check for expected messages
    assert any("🐦 Downloading Twitter/X content:" in arg for arg in call_args)
    assert any("✅ Twitter/X download completed!" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_reddit_success_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test download command succeeds with Reddit URL using direct callback."""
    fixture_download_cog.strategies = fixture_mock_strategies

    # Configure Reddit strategy to support URL and succeed
    reddit_strategy = fixture_mock_strategies["reddit"]
    reddit_strategy.supports_url.return_value = True
    reddit_strategy.download = mocker.AsyncMock(return_value=fixture_mock_metadata)

    # Ensure other strategies don't support this URL
    for name, strategy in fixture_mock_strategies.items():
        if name != "reddit":
            strategy.supports_url.return_value = False

    # Mock upload manager to avoid upload processing in tests
    fixture_download_cog.upload_manager = mocker.Mock()
    fixture_download_cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['reddit_url'],
        upload=False
    )

    # Verify strategy was called
    reddit_strategy.supports_url.assert_called_with(fixture_download_test_data['reddit_url'])
    reddit_strategy.download.assert_called_once_with(fixture_download_test_data['reddit_url'])

    # Verify bot responses
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("🤖 Downloading Reddit content:" in arg for arg in call_args)
    assert any("✅ Reddit download completed!" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_strategy_failure_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command handles strategy failure gracefully."""
    fixture_download_cog.strategies = fixture_mock_strategies

    # Configure Twitter strategy to support URL but fail download
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True

    # Mock failed download
    failed_metadata = mocker.Mock()
    failed_metadata.error = "Network timeout error"
    failed_metadata.title = None
    twitter_strategy.download = mocker.AsyncMock(return_value=failed_metadata)

    # Ensure other strategies don't support this URL
    for name, strategy in fixture_mock_strategies.items():
        if name != "twitter":
            strategy.supports_url.return_value = False

    # Mock upload manager to avoid upload processing in tests
    fixture_download_cog.upload_manager = mocker.Mock()
    fixture_download_cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Mock context message for download directory creation
    fixture_mock_ctx.message = mocker.Mock()
    fixture_mock_ctx.message.id = 123456789

    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['twitter_url'],
        upload=False
    )

    # Verify error handling
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("❌ Twitter/X download failed: Network timeout error" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_strategy_exception_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command handles strategy exceptions."""
    fixture_download_cog.strategies = fixture_mock_strategies

    # Configure Twitter strategy to support URL but throw exception
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.download = mocker.AsyncMock(side_effect=Exception("Strategy crashed unexpectedly"))

    # Ensure other strategies don't support this URL
    for name, strategy in fixture_mock_strategies.items():
        if name != "twitter":
            strategy.supports_url.return_value = False

    # Mock upload manager to avoid upload processing in tests
    fixture_download_cog.upload_manager = mocker.Mock()
    fixture_download_cog.upload_manager.process_downloaded_files = mocker.AsyncMock()

    # Mock context message for download directory creation
    fixture_mock_ctx.message = mocker.Mock()
    fixture_mock_ctx.message.id = 123456789

    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['twitter_url'],
        upload=False
    )

    # Verify exception handling
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("❌ Download error: Strategy crashed unexpectedly" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_fallback_to_queue_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command falls back to queue for unsupported URLs."""
    # Configure all strategies to not support the URL
    for strategy in fixture_mock_strategies.values():
        strategy.supports_url.return_value = False

    fixture_download_cog.strategies = fixture_mock_strategies

    # Mock the bot managers for fallback
    fixture_download_cog.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)
    fixture_download_cog.bot.queue_manager.add_to_queue = mocker.AsyncMock()

    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['unsupported_url']
    )

    # Verify fallback to queue system
    fixture_download_cog.bot.queue_manager.add_to_queue.assert_called_once()
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("Added" in arg and "to download queue" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_download_command_invalid_url_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    mocker
):
    """Test download command handles invalid URLs."""
    # Configure all strategies to not support the URL
    for strategy in fixture_mock_strategies.values():
        strategy.supports_url.return_value = False

    fixture_download_cog.strategies = fixture_mock_strategies

    # Mock the bot managers to reject invalid URL
    fixture_download_cog.bot.download_manager.validate_url = mocker.AsyncMock(return_value=False)

    await fixture_download_cog.download.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['invalid_url']
    )

    # Verify error message
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("Invalid URL provided" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_metadata_command_twitter_metadata_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test metadata command retrieves Twitter metadata."""
    # Configure Twitter strategy to support URL and return metadata
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True
    twitter_strategy.get_metadata.return_value = fixture_mock_metadata

    fixture_download_cog.strategies = fixture_mock_strategies

    await fixture_download_cog.metadata.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['twitter_url']
    )

    # Verify metadata extraction was called
    twitter_strategy.get_metadata.assert_called_once_with(fixture_download_test_data['twitter_url'])

    # Verify metadata display
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("🐦 **Twitter/X Content Info**" in arg for arg in call_args)
    assert any("Test Content Title" in arg for arg in call_args)
    assert any("testuser" in arg for arg in call_args)
    assert any("❤️ **Likes:** 100" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_metadata_command_reddit_metadata_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    fixture_download_test_data,
    fixture_mock_strategies,
    fixture_mock_metadata,
    mocker
):
    """Test metadata command retrieves Reddit metadata."""
    # Configure Reddit strategy to support URL and return metadata
    reddit_strategy = fixture_mock_strategies["reddit"]
    reddit_strategy.supports_url.return_value = True
    reddit_strategy.get_metadata.return_value = fixture_mock_metadata

    fixture_download_cog.strategies = fixture_mock_strategies

    await fixture_download_cog.metadata.callback(
        fixture_download_cog,
        fixture_mock_ctx,
        fixture_download_test_data['reddit_url']
    )

    # Verify metadata extraction was called
    reddit_strategy.get_metadata.assert_called_once_with(fixture_download_test_data['reddit_url'])

    # Verify Reddit-specific metadata display
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("🤖 **Reddit Content Info**" in arg for arg in call_args)
    assert any("📂 **Subreddit:** r/test" in arg for arg in call_args)
    assert any("⬆️ **Score:** 100" in arg for arg in call_args)
    assert any("💬 **Comments:** 42" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_status_command_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    mocker
):
    """Test status command displays current system status."""
    # Mock the bot managers
    fixture_download_cog.bot.download_manager.get_active_downloads = mocker.Mock(return_value=3)
    fixture_download_cog.bot.queue_manager.queue_size = 7

    await fixture_download_cog.status.callback(
        fixture_download_cog,
        fixture_mock_ctx
    )

    # Verify status display
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("Active downloads: 3" in arg for arg in call_args)
    assert any("Queue size: 7" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_strategies_command_direct(
    fixture_download_cog,
    fixture_mock_ctx,
    mocker
):
    """Test strategies command displays strategy configuration."""
    # Mock feature flags info
    mock_info = {
        "twitter_api": True,
        "reddit_api": False,
        "youtube_api": True,
        "instagram_api": False,
        "api_fallback": True,
        "ai_strategy_selection": True,
        "ai_content_analysis": False,
        "ai_workflow_orchestration": True
    }
    fixture_download_cog.feature_flags.get_strategy_info = mocker.Mock(return_value=mock_info)

    await fixture_download_cog.show_strategies.callback(
        fixture_download_cog,
        fixture_mock_ctx
    )

    # Verify strategy configuration display
    call_args = [call[0][0] for call in fixture_mock_ctx.send.call_args_list]
    assert any("🔧 **Download Strategy Configuration**" in arg for arg in call_args)
    assert any("🐦 Twitter/X: 🚀 **API-Direct**" in arg for arg in call_args)
    assert any("🤖 Reddit: 🖥️ **CLI Mode**" in arg for arg in call_args)


@pytest.mark.asyncio
async def test_get_platform_info_direct(
    fixture_download_cog,
    fixture_download_test_data
):
    """Test platform info helper method."""
    # Test different platforms
    twitter_info = fixture_download_cog._get_platform_info(fixture_download_test_data['twitter_url'])
    assert twitter_info["emoji"] == "🐦"
    assert twitter_info["name"] == "Twitter/X"

    reddit_info = fixture_download_cog._get_platform_info(fixture_download_test_data['reddit_url'])
    assert reddit_info["emoji"] == "🤖"
    assert reddit_info["name"] == "Reddit"

    youtube_info = fixture_download_cog._get_platform_info(fixture_download_test_data['youtube_url'])
    assert youtube_info["emoji"] == "📺"
    assert youtube_info["name"] == "YouTube"

    instagram_info = fixture_download_cog._get_platform_info(fixture_download_test_data['instagram_url'])
    assert instagram_info["emoji"] == "📷"
    assert instagram_info["name"] == "Instagram"

    unknown_info = fixture_download_cog._get_platform_info(fixture_download_test_data['unsupported_url'])
    assert unknown_info["emoji"] == "🔗"
    assert unknown_info["name"] == "Unknown"


@pytest.mark.asyncio
async def test_get_strategy_for_url_direct(
    fixture_download_cog,
    fixture_download_test_data,
    fixture_mock_strategies
):
    """Test strategy selection for URLs."""
    fixture_download_cog.strategies = fixture_mock_strategies

    # Configure Twitter strategy to support its URL
    twitter_strategy = fixture_mock_strategies["twitter"]
    twitter_strategy.supports_url.return_value = True

    # Test strategy selection
    selected_strategy = fixture_download_cog._get_strategy_for_url(fixture_download_test_data['twitter_url'])
    assert selected_strategy == twitter_strategy

    # Test no strategy found
    for strategy in fixture_mock_strategies.values():
        strategy.supports_url.return_value = False

    no_strategy = fixture_download_cog._get_strategy_for_url(fixture_download_test_data['unsupported_url'])
    assert no_strategy is None
