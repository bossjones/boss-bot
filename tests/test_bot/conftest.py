"""Test fixtures for bot-related tests."""

from collections.abc import AsyncGenerator
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from pytest_mock import MockerFixture

from boss_bot.bot.client import BossBot
from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.env import BossSettings

@pytest.fixture(scope="function")
async def fixture_bot_test(fixture_settings_test: BossSettings) -> AsyncGenerator[BossBot, None]:
    """Create a bot instance for testing.

    Scope: function - ensures clean bot instance for each test
    Args:
        fixture_settings_test: Test settings fixture
    Returns: Configured BossBot instance
    Cleanup: Automatically closes bot after each test
    """
    bot = BossBot()
    await bot._async_setup_hook()
    dpytest.configure(bot)
    yield bot
    await bot.close()

@pytest.fixture(scope="function")
def fixture_mock_bot_test(mocker: MockerFixture) -> BossBot:
    """Create a mocked bot instance for testing.

    Scope: function - ensures clean mock for each test
    Args:
        mocker: PyTest mock fixture
    Returns: Mocked BossBot instance with configured managers
    """
    bot = mocker.Mock(spec=BossBot)
    bot.download_manager = mocker.Mock()
    bot.queue_manager = mocker.Mock()
    return bot

@pytest.fixture(scope="function")
def fixture_download_cog_test(fixture_mock_bot_test: BossBot) -> DownloadCog:
    """Create a downloads cog instance for testing.

    Scope: function - ensures clean cog for each test
    Args:
        fixture_mock_bot_test: Mocked bot fixture
    Returns: Configured DownloadCog instance
    """
    return DownloadCog(fixture_mock_bot_test)

@pytest.fixture(scope="function")
def fixture_help_command_test(mocker: MockerFixture) -> commands.HelpCommand:
    """Create a help command instance for testing.

    Scope: function - ensures clean help command for each test
    Args:
        mocker: PyTest mock fixture
    Returns: Configured help command instance
    """
    from boss_bot.bot.bot_help import BossHelpCommand
    help_cmd = BossHelpCommand()
    # Set up context
    ctx = mocker.Mock(spec=commands.Context)
    ctx.clean_prefix = "$"
    help_cmd.context = ctx
    return help_cmd
