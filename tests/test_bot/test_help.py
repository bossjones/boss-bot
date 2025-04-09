"""Tests for custom help command."""

import pytest
import discord
from discord.ext import commands

from boss_bot.bot.help import BossHelpCommand


@pytest.fixture
def help_command(mocker):
    """Create a help command instance for testing."""
    help_cmd = BossHelpCommand()
    # Set up context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_cmd.context = ctx
    return help_cmd

@pytest.mark.asyncio
async def test_get_command_signature(help_command, mocker):
    """Test command signature formatting."""
    # Create a mock command
    cmd = mocker.Mock(spec=commands.Command)
    cmd.parent = None
    cmd.name = "download"
    cmd.signature = "<url>"

    # Get signature
    sig = help_command.get_command_signature(cmd)

    # Verify format
    assert sig == "$download <url>"

@pytest.mark.asyncio
async def test_get_command_signature_with_parent(mocker):
    """Test getting command signature with parent command."""
    help_command = BossHelpCommand()

    # Set up command context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    # Create mock parent command
    parent = mocker.Mock(spec=commands.Command)
    parent.parent = None
    parent.name = "queue"

    # Create mock subcommand
    cmd = mocker.Mock(spec=commands.Command)
    cmd.parent = parent
    cmd.name = "list"
    cmd.signature = ""

    # Get signature and strip any trailing whitespace
    sig = help_command.get_command_signature(cmd).rstrip()
    assert sig == "$queue list"

@pytest.mark.asyncio
async def test_send_bot_help(mocker):
    """Test sending bot help message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    # Create destination with async send method
    destination = mocker.Mock()
    destination.send = mocker.AsyncMock()
    help_command.get_destination = mocker.Mock(return_value=destination)

    # Create mock cog and commands
    cog = mocker.Mock()
    cog.qualified_name = "Downloads"
    cmd = mocker.Mock(spec=commands.Command)
    cmd.name = "download"
    cmd.signature = "<url>"
    cmd.short_doc = "Download a file"
    cmd.parent = None  # Explicitly set parent to None

    # Create mapping
    mapping = {cog: [cmd]}

    # Mock filter_commands
    help_command.filter_commands = mocker.AsyncMock(return_value=[cmd])

    # Send help
    await help_command.send_bot_help(mapping)

    # Verify embed was sent
    destination.send.assert_awaited_once()  # Use assert_awaited_once instead of assert_called_once
    embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Boss-Bot Help"
    assert "Downloads" in [field.name for field in embed.fields]

@pytest.mark.asyncio
async def test_send_command_help(mocker):
    """Test sending command help message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    destination = mocker.Mock()
    destination.send = mocker.AsyncMock()  # Make send an async mock
    help_command.get_destination = mocker.Mock(return_value=destination)

    # Create mock command
    cmd = mocker.Mock(spec=commands.Command)
    cmd.name = "download"
    cmd.signature = "<url>"
    cmd.help = "Download a file from the given URL"
    cmd.aliases = ["dl"]
    cmd.parent = None

    # Mock cooldown
    cooldown = mocker.Mock()
    cooldown.rate = 1
    cooldown.per = 60
    cmd._buckets = mocker.Mock()
    cmd._buckets._cooldown = cooldown

    await help_command.send_command_help(cmd)

    # Verify embed was sent
    destination.send.assert_called_once()
    embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert "download" in embed.title
    assert "Aliases" in [field.name for field in embed.fields]
    assert "Cooldown" in [field.name for field in embed.fields]

@pytest.mark.asyncio
async def test_send_error_message(mocker):
    """Test sending error message."""
    help_command = BossHelpCommand()

    # Set up command context and destination
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_command.context = ctx

    destination = mocker.Mock()
    destination.send = mocker.AsyncMock()  # Make send an async mock
    help_command.get_destination = mocker.Mock(return_value=destination)

    error_msg = "Command not found"
    await help_command.send_error_message(error_msg)

    # Verify error embed was sent
    destination.send.assert_called_once()
    embed = destination.send.call_args[1]["embed"]
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Help Error"
    assert error_msg in embed.description
    assert embed.color == discord.Color.red()
