"""Tests for core bot functionality."""

from typing import Any, cast

import pytest
from discord.ext import commands
import discord
from pytest_mock import MockerFixture

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings

# Note: Using standardized fixtures from conftest.py:
# - fixture_bot_test: Clean bot instance for each test
# - fixture_mock_bot_test: Mocked bot instance for testing

@pytest.mark.asyncio
async def test_bot_error_handling(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that bot handles command errors appropriately."""
    # Create mock context
    mock_ctx = mocker.Mock(spec=commands.Context)
    mock_ctx.send = mocker.AsyncMock()  # Make send a coroutine
    ctx = cast(commands.Context[commands.Bot], mock_ctx)

    # Create test error
    error = commands.MissingPermissions(["manage_messages"])

    # Call error handler
    await fixture_bot_test.on_command_error(ctx, error)

    # Verify error was handled
    mock_ctx.send.assert_called_once()
    assert "You don't have permission" in mock_ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_missing_arguments_error(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that bot handles missing arguments appropriately."""
    mock_ctx = mocker.Mock(spec=commands.Context)
    mock_ctx.send = mocker.AsyncMock()
    ctx = cast(commands.Context[commands.Bot], mock_ctx)

    # Create mock parameter with proper attributes
    param = mocker.Mock()
    param.name = "url"
    error = commands.MissingRequiredArgument(param)

    await fixture_bot_test.on_command_error(ctx, error)

    mock_ctx.send.assert_called_once()
    assert "Missing required argument" in mock_ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_cooldown_error(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that bot handles cooldown errors appropriately."""
    mock_ctx = mocker.Mock(spec=commands.Context)
    mock_ctx.send = mocker.AsyncMock()
    ctx = cast(commands.Context[commands.Bot], mock_ctx)

    # Create cooldown with proper type
    cooldown = commands.Cooldown(1, 60.0)
    error = commands.CommandOnCooldown(cooldown=cooldown, retry_after=5.0, type=commands.BucketType.default)

    await fixture_bot_test.on_command_error(ctx, error)

    mock_ctx.send.assert_called_once()
    assert "You're on cooldown" in mock_ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_status_setup(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that bot sets up status correctly."""
    # Mock the change_presence method
    mock_change_presence = mocker.AsyncMock()
    mocker.patch.object(fixture_bot_test, 'change_presence', mock_change_presence)

    # Call ready event
    await fixture_bot_test.on_ready()

    # Verify status was set
    mock_change_presence.assert_called_once()
    call_kwargs = cast(dict[str, Any], mock_change_presence.call_args[1])
    assert isinstance(call_kwargs['activity'], discord.Activity)
    assert call_kwargs['activity'].type == discord.ActivityType.watching
    assert "downloads" in call_kwargs['activity'].name.lower()

@pytest.mark.asyncio
async def test_help_command_customization(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that help command is customized correctly."""
    # Verify help command attributes
    assert fixture_bot_test.help_command is not None
    help_command = fixture_bot_test.help_command

    # Create a mock help command with the expected attributes
    mock_help = mocker.Mock(spec=commands.DefaultHelpCommand)
    mock_help.dm_help = False
    mock_help.case_insensitive = True

    # Verify the attributes match
    assert help_command.dm_help == mock_help.dm_help
    assert help_command.case_insensitive == mock_help.case_insensitive

@pytest.mark.asyncio
async def test_bot_reconnect_handling(
    mocker: MockerFixture,
    fixture_bot_test: BossBot
) -> None:
    """Test that bot handles reconnection appropriately."""
    # Mock the setup hook method
    mock_setup_hook = mocker.AsyncMock()
    mocker.patch.object(fixture_bot_test, '_async_setup_hook', mock_setup_hook)

    # Simulate disconnect and reconnect
    await fixture_bot_test.on_disconnect()
    await fixture_bot_test.on_connect()

    # Verify reconnect behavior
    mock_setup_hook.assert_called_once()
