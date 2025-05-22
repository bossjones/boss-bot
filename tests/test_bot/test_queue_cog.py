"""Tests for queue command cog."""
import pytest
from discord.ext import commands
from pytest_mock import MockerFixture

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.task_queue import QueueCog


@pytest.mark.asyncio
async def test_clear_queue_command(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test clearing the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.clear_queue = mocker.AsyncMock()

    await cog.clear_queue.callback(cog, fixture_ctx_test)

    fixture_mock_bot_test.queue_manager.clear_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue cleared.")


@pytest.mark.asyncio
async def test_remove_from_queue_command(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test removing a download from the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=True)

    await cog.remove_from_queue.callback(cog, fixture_ctx_test, "test-download-id")

    fixture_mock_bot_test.queue_manager.remove_from_queue.assert_called_once_with("test-download-id")
    fixture_ctx_test.send.assert_called_once_with("Download test-download-id removed from queue.")


@pytest.mark.asyncio
async def test_remove_from_queue_not_found(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test removing a non-existent download from the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.remove_from_queue = mocker.AsyncMock(return_value=False)

    await cog.remove_from_queue.callback(cog, fixture_ctx_test, "invalid-id")

    fixture_mock_bot_test.queue_manager.remove_from_queue.assert_called_once_with("invalid-id")
    fixture_ctx_test.send.assert_called_once_with("Download invalid-id not found or you don't have permission to remove it.")


@pytest.mark.asyncio
async def test_pause_queue_command(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test pausing the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.pause_queue = mocker.AsyncMock()

    await cog.pause_queue.callback(cog, fixture_ctx_test)

    fixture_mock_bot_test.queue_manager.pause_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue paused. Current downloads will complete but no new downloads will start.")


@pytest.mark.asyncio
async def test_resume_queue_command(fixture_mock_bot_test: BossBot, fixture_ctx_test: commands.Context, mocker: MockerFixture) -> None:
    """Test resuming the queue."""
    cog = QueueCog(fixture_mock_bot_test)
    fixture_mock_bot_test.queue_manager.resume_queue = mocker.AsyncMock()

    await cog.resume_queue.callback(cog, fixture_ctx_test)

    fixture_mock_bot_test.queue_manager.resume_queue.assert_called_once()
    fixture_ctx_test.send.assert_called_once_with("Download queue resumed. New downloads will now start.")
