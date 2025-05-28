# pylint: disable=no-member
# pylint: disable=possibly-used-before-assignment
# pyright: reportImportCycles=false
# pyright: reportFunctionMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportInvalidTypeForm=false
# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=consider-using-with, consider-using-min-builtin
"""Tests for queue cog functionality."""

import pytest
import discord
from datetime import datetime, UTC
from uuid import UUID
from pytest_mock import MockerFixture
from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.queue import QueueCog
from boss_bot.core.core_queue import QueueItem, QueueStatus

# Note: Using standardized fixtures from conftest.py:
# - fixture_mock_bot_test: Mocked bot instance
# - fixture_settings_test: Test settings

@pytest.mark.asyncio
async def test_show_queue_empty(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test showing empty queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=[])

    await cog.show_queue.callback(cog, fixture_ctx_test)
    fixture_ctx_test.send.assert_called_once_with("The download queue is empty.")

@pytest.mark.asyncio
async def test_show_queue_with_items(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test showing queue with items."""
    cog = QueueCog(fixture_mock_bot_test)

    # Create test queue items
    items = [
        QueueItem(
            download_id=UUID("12345678-1234-5678-1234-567812345678"),
            url="https://example.com/test1",
            user_id=12345,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.now(UTC),
            filename="test1.mp4"
        ),
        QueueItem(
            download_id=UUID("87654321-4321-8765-4321-876543210987"),
            url="https://example.com/test2",
            user_id=54321,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.now(UTC)
        )
    ]
    fixture_mock_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=items)

    # Mock user lookup
    mock_user1 = mocker.Mock(spec=discord.User)
    mock_user2 = mocker.Mock(spec=discord.User)
    mock_user1.name = "User1"
    mock_user2.name = "User2"
    fixture_mock_bot_test.get_user = mocker.Mock(side_effect=[mock_user1, mock_user2])

    await cog.show_queue.callback(cog, fixture_ctx_test)

    # Verify embed was created and sent
    fixture_ctx_test.send.assert_called_once()
    call_args = fixture_ctx_test.send.call_args.kwargs['embed']
    assert isinstance(call_args, discord.Embed)
    assert call_args.title is not None and "Download Queue" in call_args.title
    assert call_args.description is not None and "test1.mp4" in call_args.description
    assert call_args.description is not None and "User1" in call_args.description
    assert call_args.description is not None and "User2" in call_args.description
    assert call_args.footer is not None and call_args.footer.text is not None and "Page 1/1" in call_args.footer.text

@pytest.mark.asyncio
async def test_show_queue_pagination(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test queue pagination."""
    cog = QueueCog(fixture_mock_bot_test)

    # Create 7 test items (more than one page)
    items = [
        QueueItem(
            download_id=UUID(f"12345678-1234-5678-1234-{i:012d}"),
            url=f"https://example.com/test{i}",
            user_id=12345,
            channel_id=67890,
            status=QueueStatus.QUEUED,
            created_at=datetime.now(UTC)
        ) for i in range(7)
    ]
    fixture_mock_bot_test.queue_manager.get_queue_items = mocker.AsyncMock(return_value=items)

    # Mock user lookup
    mock_user = mocker.Mock(spec=discord.User)
    mock_user.name = "User"
    fixture_mock_bot_test.get_user = mocker.Mock(return_value=mock_user)

    # Test first page
    await cog.show_queue.callback(cog, fixture_ctx_test, 1)
    call_args = fixture_ctx_test.send.call_args.kwargs['embed']
    assert isinstance(call_args, discord.Embed)
    assert call_args.footer is not None and call_args.footer.text is not None and "Page 1/2" in call_args.footer.text
    assert call_args.description is not None and len(call_args.description.strip().split("\n")) == 5  # 5 items per page

    # Reset mock and test second page
    fixture_ctx_test.send.reset_mock()
    await cog.show_queue.callback(cog, fixture_ctx_test, 2)
    call_args = fixture_ctx_test.send.call_args.kwargs['embed']
    assert call_args.footer is not None and call_args.footer.text is not None and "Page 2/2" in call_args.footer.text
    assert call_args.description is not None and len(call_args.description.strip().split("\n")) == 2  # 2 remaining items

@pytest.mark.asyncio
async def test_clear_queue(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test clearing the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.clear_queue = mocker.AsyncMock()

    await cog.clear_queue.callback(cog, fixture_ctx_test)
    fixture_mock_bot_test.queue_manager.clear_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue cleared.")

@pytest.mark.asyncio
async def test_remove_from_queue_success(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test successful queue item removal."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=True)

    await cog.remove_from_queue.callback(cog, fixture_ctx_test, "test-id")
    fixture_ctx_test.send.assert_called_once_with("Download test-id removed from queue.")

@pytest.mark.asyncio
async def test_remove_from_queue_not_found(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test removing non-existent queue item."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=False)

    await cog.remove_from_queue.callback(cog, fixture_ctx_test, "test-id")
    fixture_ctx_test.send.assert_called_once_with("Download test-id not found or you don't have permission to remove it.")

@pytest.mark.asyncio
async def test_pause_queue(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test pausing the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.pause_queue = mocker.AsyncMock()

    await cog.pause_queue.callback(cog, fixture_ctx_test)
    fixture_mock_bot_test.queue_manager.pause_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue paused. Current downloads will complete but no new downloads will start.")

@pytest.mark.asyncio
async def test_resume_queue(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test resuming the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.resume_queue = mocker.AsyncMock()

    await cog.resume_queue.callback(cog, fixture_ctx_test)
    fixture_mock_bot_test.queue_manager.resume_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue resumed. New downloads will now start.")
