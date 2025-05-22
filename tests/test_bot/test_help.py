"""Tests for custom help command."""

import pytest
from pytest_mock import MockerFixture
import discord
from discord.ext import commands

from boss_bot.bot.bot_help import BossHelpCommand

# Fixture migrated to test_bot/conftest.py as fixture_help_command_test
# Original fixture: help_command
# New fixture: fixture_help_command_test
# Migration date: 2024-03-19

@pytest.mark.asyncio
async def test_get_command_signature(fixture_help_command_test: commands.HelpCommand, mocker: MockerFixture) -> None:
    """Test command signature formatting."""
    # Create a mock command
    cmd: commands.Command = mocker.Mock(spec=commands.Command)
    cmd.parent = None
    cmd.name = "download"
    cmd.signature = "<url>"

    # Get signature
    sig = fixture_help_command_test.get_command_signature(cmd)

    # Verify format
    assert sig == "$download <url>"

@pytest.mark.asyncio
async def test_get_command_signature_with_parent(mocker: MockerFixture) -> None:
    """Test getting command signature with parent command."""
    help_command = BossHelpCommand()

    # Set up command context
    ctx: commands.Context = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    # Create mock parent command
    parent: commands.Command = mocker.Mock(spec=commands.Command)
    parent.parent = None
    parent.name = "queue"

    # Create mock subcommand
    cmd: commands.Command = mocker.Mock(spec=commands.Command)
    cmd.parent = parent
    cmd.name = "list"
    cmd.signature = ""

    # Get signature and strip any trailing whitespace
    sig = help_command.get_command_signature(cmd).rstrip()
    assert sig == "$queue list"

@pytest.mark.asyncio
async def test_send_bot_help(mocker: MockerFixture) -> None:
    """Test sending bot help message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx: commands.Context = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    # Create destination with async send method
    destination: discord.abc.Messageable = mocker.Mock(spec=discord.abc.Messageable)
    destination.send = mocker.AsyncMock()
    help_command.get_destination = mocker.Mock(return_value=destination)

    # Create mock cog and commands
    cog: commands.Cog = mocker.Mock(spec=commands.Cog)
    cog.qualified_name = "Downloads"
    cmd: commands.Command = mocker.Mock(spec=commands.Command)
    cmd.name = "download"
    cmd.signature = "<url>"
    cmd.short_doc = "Download a file"
    cmd.parent = None  # Explicitly set parent to None

    # Create mapping
    mapping: dict[commands.Cog, list[commands.Command]] = {cog: [cmd]}

    # Mock filter_commands
    help_command.filter_commands = mocker.AsyncMock(return_value=[cmd])

    # Send help
    await help_command.send_bot_help(mapping)

    # Verify embed was sent
    destination.send.assert_awaited_once()  # Use assert_awaited_once instead of assert_called_once
    embed: discord.Embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Boss-Bot Help"
    assert "Downloads" in [field.name for field in embed.fields]

@pytest.mark.asyncio
async def test_send_command_help(mocker: MockerFixture) -> None:
    """Test sending command help message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx: commands.Context = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    destination: discord.abc.Messageable = mocker.Mock(spec=discord.abc.Messageable)
    destination.send = mocker.AsyncMock()  # Make send an async mock
    help_command.get_destination = mocker.Mock(return_value=destination)

    # Create mock command
    cmd: commands.Command = mocker.Mock(spec=commands.Command)
    cmd.name = "download"
    cmd.signature = "<url>"
    cmd.help = "Download a file from the given URL"
    cmd.aliases = ["dl"]
    cmd.parent = None

    # Mock cooldown
    cooldown: commands.Cooldown = mocker.Mock(spec=commands.Cooldown)
    cooldown.rate = 1
    cooldown.per = 60
    cmd._buckets = mocker.Mock()
    cmd._buckets._cooldown = cooldown

    await help_command.send_command_help(cmd)

    # Verify embed was sent
    destination.send.assert_called_once()
    embed: discord.Embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert embed.title is not None and "download" in embed.title
    assert "Aliases" in [field.name for field in embed.fields]
    assert "Cooldown" in [field.name for field in embed.fields]

@pytest.mark.asyncio
async def test_send_error_message(mocker: MockerFixture) -> None:
    """Test sending error message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx: commands.Context = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    destination: discord.abc.Messageable = mocker.Mock(spec=discord.abc.Messageable)
    destination.send = mocker.AsyncMock()  # Make send an async mock
    help_command.get_destination = mocker.Mock(return_value=destination)

    error_msg = "Command not found"
    await help_command.send_error_message(error_msg)

    # Verify error embed was sent
    destination.send.assert_called_once()
    embed: discord.Embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Help Error"
    assert embed.description is not None and error_msg in embed.description
    assert embed.color == discord.Color.red()
