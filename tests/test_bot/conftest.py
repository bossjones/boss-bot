"""Test fixtures for bot-related tests."""

import glob
import os
from collections.abc import AsyncGenerator
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from pytest_mock import MockerFixture
from _pytest.main import Session
from _pytest.config import ExitCode

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
    bot = BossBot(settings=fixture_settings_test)
    await bot._async_setup_hook()
    dpytest.configure(bot)
    yield bot
    # Teardown
    await dpytest.empty_queue() # empty the global message queue as test teardown


@pytest.fixture(scope="function")
def fixture_mock_bot_test(mocker: MockerFixture, fixture_settings_test: BossSettings) -> BossBot:
    """Create a mocked bot instance for testing.

    Scope: function - ensures clean mock for each test
    Args:
        mocker: PyTest mock fixture
        fixture_settings_test: Test settings fixture
    Returns: Mocked BossBot instance with configured managers
    """
    bot = mocker.Mock(spec=BossBot)
    bot.download_manager = mocker.Mock()
    bot.queue_manager = mocker.Mock()
    bot.settings = fixture_settings_test
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

@pytest.fixture(scope="function")
def fixture_ctx_test(mocker: MockerFixture) -> commands.Context:
    """Create a mock context for testing.

    Scope: function - ensures clean context for each test
    Args:
        mocker: PyTest mock fixture
    Returns: Mocked Context instance
    """
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    ctx.guild = mocker.Mock()
    ctx.guild.id = 13579
    return ctx

def pytest_sessionfinish(session: Session, exitstatus: ExitCode | int) -> None:
    """Code to execute after all tests.

    Cleans up dpytest attachment files that may have been created during testing.

    Args:
        session: The pytest session object
        exitstatus: The status code from the test run
    """
    print("\n-------------------------\nClean dpytest_*.dat files")
    fileList = glob.glob('./dpytest_*.dat')
    for filePath in fileList:
        try:
            os.remove(filePath)
        except Exception:
            print("Error while deleting file : ", filePath)
