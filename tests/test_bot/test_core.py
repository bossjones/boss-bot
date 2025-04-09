"""Tests for core bot functionality."""

import pytest
from discord.ext import commands
import discord

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings

@pytest.mark.asyncio
async def test_bot_error_handling(mocker, bot):
    """Test that bot handles command errors appropriately."""
    # Create mock context
    ctx = mocker.Mock(spec=commands.Context)

    # Create test error
    error = commands.MissingPermissions(["manage_messages"])

    # Call error handler
    await bot.on_command_error(ctx, error)

    # Verify error was handled
    ctx.send.assert_called_once()
    assert "You don't have permission" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_missing_arguments_error(mocker, bot):
    """Test that bot handles missing arguments appropriately."""
    ctx = mocker.Mock(spec=commands.Context)
    error = commands.MissingRequiredArgument(param=mocker.Mock(name="url"))

    await bot.on_command_error(ctx, error)

    ctx.send.assert_called_once()
    assert "Missing required argument" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_cooldown_error(mocker, bot):
    """Test that bot handles cooldown errors appropriately."""
    ctx = mocker.Mock(spec=commands.Context)
    error = commands.CommandOnCooldown(cooldown=mocker.Mock(), retry_after=5.0)

    await bot.on_command_error(ctx, error)

    ctx.send.assert_called_once()
    assert "You're on cooldown" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_bot_status_setup(mocker, bot):
    """Test that bot sets up status correctly."""
    # Mock the change_presence method
    mocker.patch.object(bot, 'change_presence', side_effect=mocker.AsyncMock())

    # Call ready event
    await bot.on_ready()

    # Verify status was set
    bot.change_presence.assert_called_once()
    args = bot.change_presence.call_args[1]
    assert isinstance(args['activity'], discord.Activity)
    assert args['activity'].type == discord.ActivityType.watching
    assert "downloads" in args['activity'].name.lower()

@pytest.mark.asyncio
async def test_help_command_customization(mocker, bot):
    """Test that help command is customized correctly."""
    # Verify help command attributes
    assert bot.help_command is not None
    assert bot.help_command.dm_help is False  # Help should be sent in channel
    assert bot.help_command.case_insensitive is True

@pytest.mark.asyncio
async def test_bot_reconnect_handling(mocker, bot):
    """Test that bot handles reconnection appropriately."""
    # Mock the reconnect method
    mocker.patch.object(bot, '_async_setup_hook', side_effect=mocker.AsyncMock())

    # Simulate disconnect and reconnect
    await bot.on_disconnect()
    await bot.on_connect()

    # Verify reconnect behavior
    bot._async_setup_hook.assert_called_once()
