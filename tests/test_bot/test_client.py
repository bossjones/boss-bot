"""Tests for Discord bot client."""
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from boss_bot.bot.client import BossBot

@pytest.fixture
async def bot():
    """Create a bot instance for testing."""
    bot = BossBot()
    await bot._async_setup_hook()  # Initialize the bot
    dpytest.configure(bot)
    return bot

@pytest.mark.asyncio
async def test_bot_initialization(bot):
    """Test that bot initializes with correct configuration."""
    assert isinstance(bot, commands.Bot)
    assert bot.command_prefix == "$"
    assert bot.description == "Boss-Bot: A Discord Media Download Assistant"
    assert bot.intents.message_content is True

@pytest.mark.asyncio
async def test_bot_ready_event(bot):
    """Test that bot handles ready event."""
    # Trigger the ready event
    await dpytest.emit_ready()
    # Bot should be marked as ready
    assert bot.is_ready()

@pytest.mark.asyncio
async def test_bot_services_initialization(bot):
    """Test that bot initializes required services."""
    assert hasattr(bot, 'queue_manager'), "Bot should have queue_manager"
    assert hasattr(bot, 'download_manager'), "Bot should have download_manager"

@pytest.mark.asyncio
async def test_bot_extensions_loaded(bot):
    """Test that required extensions are loaded."""
    loaded_extensions = bot.extensions
    assert "boss_bot.cogs.downloads" in loaded_extensions
    assert "boss_bot.cogs.queue" in loaded_extensions
