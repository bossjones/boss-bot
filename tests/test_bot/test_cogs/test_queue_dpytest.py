"""Test QueueCog functionality with direct command callback testing.

This module tests the QueueCog using direct command callback testing,
following TDD principles and the patterns from the existing codebase.

Tests cover:
- queue command with pagination and embed display
- clear command for emptying the queue
- remove command for selective item removal
- pause/resume commands for queue management
- Error handling and edge cases
- Permission and concurrent usage scenarios
"""

import asyncio
import pytest
import pytest_asyncio
import discord
from discord.ext import commands
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.queue import QueueCog
from boss_bot.core.queue.manager import QueueItem, QueueStatus


@pytest.fixture(scope="function")
def fixture_queue_test_data():
    """Provide test data for queue testing."""
    return {
        "sample_urls": [
            "https://twitter.com/user/status/123456789",
            "https://www.reddit.com/r/test/comments/abc123/test_post",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.instagram.com/p/ABC123/",
        ],
        "sample_filenames": [
            "twitter_post.mp4",
            "reddit_image.jpg",
            "youtube_video.mp4",
            "instagram_photo.jpg",
        ],
        "user_ids": [12345, 23456, 34567, 45678],
        "channel_id": 67890,
    }


@pytest.fixture(scope="function")
def fixture_mock_queue_items(fixture_queue_test_data):
    """Create mock queue items for testing."""
    items = []
    test_data = fixture_queue_test_data

    for i, (url, filename, user_id) in enumerate(zip(
        test_data["sample_urls"],
        test_data["sample_filenames"],
        test_data["user_ids"]
    )):
        item = QueueItem(
            download_id=uuid4(),
            url=url,
            user_id=user_id,
            channel_id=test_data["channel_id"],
            status=QueueStatus.QUEUED,
            created_at=datetime.now(),
            filename=filename,
        )
        items.append(item)

    return items


@pytest.fixture(scope="function")
def fixture_empty_queue_items():
    """Provide empty queue for testing."""
    return []


# RED PHASE: Write failing tests first

@pytest.mark.asyncio
async def test_show_queue_command_success_dpytest(
    fixture_bot_test,
    fixture_queue_test_data,
    fixture_mock_queue_items,
    mocker
):
    """Test queue command succeeds with items in queue using direct callback."""
    # Get the cog from the bot
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager to return test items
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_mock_queue_items)

    # Mock bot.get_user for username display
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call queue command directly
    await cog.show_queue.callback(cog, ctx, page=1)

    # Verify queue manager was called
    fixture_bot_test.queue_manager.get_queue_items.assert_called_once()

    # Verify embed was sent
    ctx.send.assert_called_once()
    call_args = ctx.send.call_args
    assert "embed" in call_args.kwargs

    embed = call_args.kwargs["embed"]
    assert embed.title == "📥 Download Queue"
    assert "twitter_post.mp4" in embed.description
    assert "User12345" in embed.description


@pytest.mark.asyncio
async def test_show_queue_command_empty_queue_dpytest(
    fixture_bot_test,
    fixture_empty_queue_items,
    mocker
):
    """Test queue command with empty queue using direct callback."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock empty queue
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_empty_queue_items)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call queue command directly
    await cog.show_queue.callback(cog, ctx, page=1)

    # Verify appropriate message for empty queue
    ctx.send.assert_called_once_with("The download queue is empty.")


@pytest.mark.asyncio
async def test_show_queue_command_pagination_dpytest(
    fixture_bot_test,
    fixture_mock_queue_items,
    mocker
):
    """Test queue command pagination functionality."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Create larger queue for testing pagination (10 items)
    large_queue = fixture_mock_queue_items * 3  # 12 items total
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=large_queue)

    # Mock bot.get_user
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Test page 2
    await cog.show_queue.callback(cog, ctx, page=2)

    # Verify embed pagination
    call_args = ctx.send.call_args
    embed = call_args.kwargs["embed"]
    assert "Page 2/3" in embed.footer.text


@pytest.mark.asyncio
async def test_clear_queue_command_success_dpytest(
    fixture_bot_test,
    mocker
):
    """Test clear command succeeds using direct callback."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager clear method
    fixture_bot_test.queue_manager.clear_queue = mocker.AsyncMock()

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call clear command directly
    await cog.clear_queue.callback(cog, ctx)

    # Verify queue manager was called
    fixture_bot_test.queue_manager.clear_queue.assert_called_once()

    # Verify success message
    ctx.send.assert_called_once_with("Download queue cleared.")


@pytest.mark.asyncio
async def test_remove_from_queue_command_success_dpytest(
    fixture_bot_test,
    mocker
):
    """Test remove command succeeds with valid download ID."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock successful removal
    test_download_id = "test-download-123"
    fixture_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=True)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call remove command directly
    await cog.remove_from_queue.callback(cog, ctx, test_download_id)

    # Verify queue manager was called with correct ID
    fixture_bot_test.queue_manager.remove_from_queue.assert_called_once_with(test_download_id)

    # Verify success message
    ctx.send.assert_called_once_with(f"Download {test_download_id} removed from queue.")


@pytest.mark.asyncio
async def test_remove_from_queue_command_not_found_dpytest(
    fixture_bot_test,
    mocker
):
    """Test remove command handles invalid download ID."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock failed removal
    invalid_download_id = "invalid-id-999"
    fixture_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=False)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call remove command directly
    await cog.remove_from_queue.callback(cog, ctx, invalid_download_id)

    # Verify appropriate error message
    expected_msg = f"Download {invalid_download_id} not found or you don't have permission to remove it."
    ctx.send.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_pause_queue_command_success_dpytest(
    fixture_bot_test,
    mocker
):
    """Test pause command succeeds using direct callback."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager pause method
    fixture_bot_test.queue_manager.pause_queue = mocker.AsyncMock()

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call pause command directly
    await cog.pause_queue.callback(cog, ctx)

    # Verify queue manager was called
    fixture_bot_test.queue_manager.pause_queue.assert_called_once()

    # Verify success message
    expected_msg = "Download queue paused. Current downloads will complete but no new downloads will start."
    ctx.send.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_resume_queue_command_success_dpytest(
    fixture_bot_test,
    mocker
):
    """Test resume command succeeds using direct callback."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager resume method
    fixture_bot_test.queue_manager.resume_queue = mocker.AsyncMock()

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call resume command directly
    await cog.resume_queue.callback(cog, ctx)

    # Verify queue manager was called
    fixture_bot_test.queue_manager.resume_queue.assert_called_once()

    # Verify success message
    expected_msg = "Download queue resumed. New downloads will now start."
    ctx.send.assert_called_once_with(expected_msg)


# ADVANCED TEST SCENARIOS

@pytest.mark.asyncio
async def test_queue_command_concurrent_usage_dpytest(
    fixture_bot_test,
    fixture_mock_queue_items,
    mocker
):
    """Test queue command handles concurrent usage correctly."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_mock_queue_items)

    # Mock bot.get_user
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create mock contexts for concurrent requests
    ctx1 = mocker.Mock(spec=commands.Context)
    ctx1.send = mocker.AsyncMock()
    ctx1.author = mocker.Mock()
    ctx1.author.id = 12345
    ctx1.channel = mocker.Mock()
    ctx1.channel.id = 67890

    ctx2 = mocker.Mock(spec=commands.Context)
    ctx2.send = mocker.AsyncMock()
    ctx2.author = mocker.Mock()
    ctx2.author.id = 54321
    ctx2.channel = mocker.Mock()
    ctx2.channel.id = 98765

    ctx3 = mocker.Mock(spec=commands.Context)
    ctx3.send = mocker.AsyncMock()
    ctx3.author = mocker.Mock()
    ctx3.author.id = 11111
    ctx3.channel = mocker.Mock()
    ctx3.channel.id = 22222

    # Simulate concurrent queue requests
    await asyncio.gather(
        cog.show_queue.callback(cog, ctx1, page=1),
        cog.show_queue.callback(cog, ctx2, page=1),
        cog.show_queue.callback(cog, ctx3, page=2)
    )

    # Verify all requests were processed
    ctx1.send.assert_called_once()
    ctx2.send.assert_called_once()
    ctx3.send.assert_called_once()

    # Verify queue manager was called multiple times
    assert fixture_bot_test.queue_manager.get_queue_items.call_count == 3


@pytest.mark.asyncio
async def test_queue_command_permission_handling_dpytest(
    fixture_bot_test,
    fixture_mock_queue_items,
    mocker
):
    """Test queue commands respect Discord permissions."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager methods
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_mock_queue_items)
    fixture_bot_test.queue_manager.clear_queue = mocker.AsyncMock()

    # Mock bot.get_user
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create contexts for different permission levels
    admin_ctx = mocker.Mock(spec=commands.Context)
    admin_ctx.send = mocker.AsyncMock()
    admin_ctx.author = mocker.Mock()
    admin_ctx.author.id = 12345
    admin_ctx.channel = mocker.Mock()
    admin_ctx.channel.id = 67890
    admin_ctx.author.guild_permissions = discord.Permissions.all()

    regular_ctx = mocker.Mock(spec=commands.Context)
    regular_ctx.send = mocker.AsyncMock()
    regular_ctx.author = mocker.Mock()
    regular_ctx.author.id = 54321
    regular_ctx.channel = mocker.Mock()
    regular_ctx.channel.id = 98765
    regular_ctx.author.guild_permissions = discord.Permissions.none()

    # Test admin access to queue viewing
    await cog.show_queue.callback(cog, admin_ctx, page=1)
    admin_ctx.send.assert_called_once()

    # Test regular user access to queue viewing (should work - queue viewing is public)
    await cog.show_queue.callback(cog, regular_ctx, page=1)
    regular_ctx.send.assert_called_once()

    # Test admin access to queue clearing
    await cog.clear_queue.callback(cog, admin_ctx)
    fixture_bot_test.queue_manager.clear_queue.assert_called_once()

    # Test regular user access to queue clearing (should also work - no permission checks implemented)
    await cog.clear_queue.callback(cog, regular_ctx)
    assert fixture_bot_test.queue_manager.clear_queue.call_count == 2


@pytest.mark.asyncio
async def test_command_isolation_dpytest(
    fixture_bot_test,
    fixture_mock_queue_items,
    mocker
):
    """Test that queue commands don't interfere with each other."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock all queue manager methods
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_mock_queue_items)
    fixture_bot_test.queue_manager.clear_queue = mocker.AsyncMock()
    fixture_bot_test.queue_manager.pause_queue = mocker.AsyncMock()
    fixture_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=True)

    # Mock bot.get_user
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create mock contexts for different commands
    queue_ctx = mocker.Mock(spec=commands.Context)
    queue_ctx.send = mocker.AsyncMock()
    queue_ctx.author = mocker.Mock()
    queue_ctx.author.id = 12345
    queue_ctx.channel = mocker.Mock()
    queue_ctx.channel.id = 67890

    clear_ctx = mocker.Mock(spec=commands.Context)
    clear_ctx.send = mocker.AsyncMock()
    clear_ctx.author = mocker.Mock()
    clear_ctx.author.id = 23456
    clear_ctx.channel = mocker.Mock()
    clear_ctx.channel.id = 78901

    pause_ctx = mocker.Mock(spec=commands.Context)
    pause_ctx.send = mocker.AsyncMock()
    pause_ctx.author = mocker.Mock()
    pause_ctx.author.id = 34567
    pause_ctx.channel = mocker.Mock()
    pause_ctx.channel.id = 89012

    remove_ctx = mocker.Mock(spec=commands.Context)
    remove_ctx.send = mocker.AsyncMock()
    remove_ctx.author = mocker.Mock()
    remove_ctx.author.id = 45678
    remove_ctx.channel = mocker.Mock()
    remove_ctx.channel.id = 90123

    # Run queue command
    await cog.show_queue.callback(cog, queue_ctx, page=1)
    queue_ctx.send.assert_called_once()

    # Run clear command - should be independent
    await cog.clear_queue.callback(cog, clear_ctx)
    clear_ctx.send.assert_called_once_with("Download queue cleared.")

    # Run pause command - should also be independent
    await cog.pause_queue.callback(cog, pause_ctx)
    pause_ctx.send.assert_called_once()

    # Run remove command - should also be independent
    await cog.remove_from_queue.callback(cog, remove_ctx, "test-id")
    remove_ctx.send.assert_called_once()

    # Verify each command was called independently
    fixture_bot_test.queue_manager.get_queue_items.assert_called_once()
    fixture_bot_test.queue_manager.clear_queue.assert_called_once()
    fixture_bot_test.queue_manager.pause_queue.assert_called_once()
    fixture_bot_test.queue_manager.remove_from_queue.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_queue_command_error_handling_dpytest(
    fixture_bot_test,
    mocker
):
    """Test queue command handles errors gracefully."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager to raise exception
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(side_effect=Exception("Database error"))

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Call queue command and expect it to handle the exception
    with pytest.raises(Exception, match="Database error"):
        await cog.show_queue.callback(cog, ctx, page=1)


@pytest.mark.asyncio
async def test_queue_pagination_edge_cases_dpytest(
    fixture_bot_test,
    fixture_mock_queue_items,
    mocker
):
    """Test queue pagination handles edge cases correctly."""
    cog = fixture_bot_test.get_cog("QueueCog")
    assert cog is not None, "QueueCog should be loaded"

    # Mock queue manager
    fixture_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=fixture_mock_queue_items)

    # Mock bot.get_user
    def mock_get_user(user_id):
        mock_user = mocker.Mock()
        mock_user.name = f"User{user_id}"
        return mock_user

    fixture_bot_test.get_user = mocker.Mock(side_effect=mock_get_user)

    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890

    # Test page 0 (should default to page 1)
    await cog.show_queue.callback(cog, ctx, page=0)
    call_args = ctx.send.call_args
    embed = call_args.kwargs["embed"]
    assert "Page 1/1" in embed.footer.text

    # Reset mock
    ctx.send.reset_mock()

    # Test page beyond maximum (should default to last page)
    await cog.show_queue.callback(cog, ctx, page=999)
    call_args = ctx.send.call_args
    embed = call_args.kwargs["embed"]
    assert "Page 1/1" in embed.footer.text  # Only 1 page for 4 items with 5 items per page
