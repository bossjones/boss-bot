"""Test configuration and fixtures for Boss-Bot."""

import asyncio
import copy
import functools
import os
import re
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from discord.ext import commands
from pydantic import AnyHttpUrl
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from vcr import filters

from boss_bot.bot.client import BossBot
from boss_bot.core.env import BossSettings, Environment
from boss_bot.core.core_queue import QueueManager
from boss_bot.downloaders.base import DownloadManager

# --- Test Environment Configuration --- #

@pytest.fixture(scope="function")
def fixture_env_vars_test(monkeypatch: MonkeyPatch) -> Generator[MonkeyPatch, None, None]:
    """Mock environment variables for unit tests.

    Scope: function - ensures clean environment for each test
    Yields: MonkeyPatch instance for test modifications
    Cleanup: Automatically resets environment after each test
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("BETTER_EXCEPTIONS", "true")
    monkeypatch.setenv("COHERE_API_KEY", "test-cohere-key")
    monkeypatch.setenv("DEBUG_AIDER", "true")
    monkeypatch.setenv("DISCORD_ADMIN_USER_ID", "12345")
    monkeypatch.setenv("DISCORD_ADMIN_USER_INVITED", "false")
    monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789")
    monkeypatch.setenv("DISCORD_SERVER_ID", "987654321")
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("ENABLE_AI", "true")
    monkeypatch.setenv("ENABLE_REDIS", "false")
    monkeypatch.setenv("ENABLE_SENTRY", "false")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-firecrawl-key")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "test-langchain-key")
    monkeypatch.setenv("LANGCHAIN_DEBUG_LOGS", "true")
    monkeypatch.setenv("LANGCHAIN_ENDPOINT", "http://localhost:8000")
    monkeypatch.setenv("LANGCHAIN_HUB_API_KEY", "test-hub-key")
    monkeypatch.setenv("LANGCHAIN_HUB_API_URL", "http://localhost:8001")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "test-project")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LOCAL_TEST_DEBUG", "true")
    monkeypatch.setenv("LOCAL_TEST_ENABLE_EVALS", "true")
    monkeypatch.setenv("OCO_LANGUAGE", "en")
    monkeypatch.setenv("OCO_MODEL", "gpt-4o")
    monkeypatch.setenv("OCO_OPENAI_API_KEY", "sk-test-oco-key")
    monkeypatch.setenv("OCO_PROMPT_MODULE", "conventional-commit")
    monkeypatch.setenv("OCO_TOKENS_MAX_INPUT", "4096")
    monkeypatch.setenv("OCO_TOKENS_MAX_OUTPUT", "500")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123456789abcdef")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("PINECONE_ENV", "test-env")
    monkeypatch.setenv("PINECONE_INDEX", "test-index")
    monkeypatch.setenv("PYTHON_DEBUG", "true")
    monkeypatch.setenv("PYTHONASYNCIODEBUG", "1")
    monkeypatch.setenv("SENTRY_DSN", "https://test-sentry-dsn")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("UNSTRUCTURED_API_KEY", "test-unstructured-key")
    monkeypatch.setenv("UNSTRUCTURED_API_URL", "http://localhost:8002")

    # Return the monkeypatch instance so tests can modify environment variables if needed
    yield monkeypatch

    # No explicit teardown needed - pytest's monkeypatch fixture handles cleanup automatically

@pytest.fixture
def set_langsmith_env_vars_evals(monkeypatch: MonkeyPatch) -> None:
    """Set environment variables for LangSmith evals."""
    monkeypatch.setenv("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY"))
    monkeypatch.setenv("LANGCHAIN_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT"))
    monkeypatch.setenv("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT"))

@pytest.fixture
def mock_env_vars_unit(monkeypatch: MonkeyPatch) -> None:
    """Mock environment variables for unit tests."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token_123")
    monkeypatch.setenv("DISCORD_CLIENT_ID", "123456789012345678")
    monkeypatch.setenv("DISCORD_SERVER_ID", "876543210987654321")
    monkeypatch.setenv("DISCORD_ADMIN_USER_ID", "111222333444555666")
    monkeypatch.setenv("STORAGE_ROOT", "/tmp/boss-bot")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("ENVIRONMENT", "development")

@pytest.fixture
def mock_env(monkeypatch: MonkeyPatch) -> None:
    """Mock environment variables for environment tests."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("ENVIRONMENT", "development")

@pytest.fixture
def ctx(mocker: MockerFixture) -> commands.Context:
    """Create a mock Discord context."""
    context = mocker.Mock(spec=commands.Context)
    context.send = mocker.AsyncMock()
    context.author = mocker.Mock()
    context.author.id = 12345
    context.channel = mocker.Mock()
    context.channel.id = 67890
    return context

# --- Core Test Fixtures --- #

@pytest.fixture(scope="function")
def fixture_event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create and provide a new event loop for each test.

    Scope: function - ensures each test gets a fresh event loop
    Yields: asyncio.AbstractEventLoop
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def fixture_settings_test(fixture_env_vars_test: MonkeyPatch) -> BossSettings:
    """Provide standardized test settings.

    Scope: function - ensures clean settings for each test
    Args:
        fixture_env_vars_test: Environment variables fixture
    Returns: BossSettings instance with test configuration
    """
    return BossSettings(
        # Discord settings
        discord_token="test_token",
        discord_client_id=123456789,
        discord_server_id=987654321,
        discord_admin_user_id=12345,
        discord_admin_user_invited=False,

        # Feature flags
        enable_ai=True,
        enable_redis=False,
        enable_sentry=False,

        # Service settings
        sentry_dsn=None,
        openai_api_key="sk-test123456789",

        # Storage Configuration
        storage_root=Path("/tmp/boss-bot-test"),
        max_file_size_mb=50,
        max_concurrent_downloads=2,
        max_queue_size=50,

        # Monitoring Configuration
        log_level="DEBUG",
        enable_metrics=True,
        metrics_port=9090,
        enable_health_check=True,
        health_check_port=8080,

        # Security Configuration
        rate_limit_requests=100,
        rate_limit_window_seconds=60,
        enable_file_validation=True,

        # Development Settings
        debug=True,
        environment=Environment.DEVELOPMENT,

        # Upload Settings
        upload_batch_size_mb=20,
        upload_max_files_per_batch=10,
        upload_cleanup_after_success=True,
        upload_enable_progress_updates=True,

        # Additional API Keys and Settings
        cohere_api_key="test-cohere-key",
        debug_aider=True,
        firecrawl_api_key="test-firecrawl-key",
        langchain_api_key="test-langchain-key",
        langchain_debug_logs=True,
        langchain_endpoint=AnyHttpUrl("http://localhost:8000"),
        langchain_hub_api_key="test-langchain-hub-key",
        langchain_hub_api_url=AnyHttpUrl("http://localhost:8001"),
        langchain_project="test-project",
        langchain_tracing_v2=True,
        pinecone_api_key="test-pinecone-key",
        pinecone_env="test-env",
        pinecone_index="test-index",
        tavily_api_key="test-tavily-key",
        unstructured_api_key="test-unstructured-key",
        unstructured_api_url=AnyHttpUrl("http://localhost:8002")
    )

# --- Discord Bot Fixtures --- #

@pytest.fixture(scope="function")
async def fixture_discord_bot(
    fixture_settings_test: BossSettings,
    mocker: MockerFixture
) -> AsyncGenerator[BossBot, None]:
    """Provide a mock Discord bot for testing.

    Scope: function - ensures clean bot for each test
    Args:
        fixture_settings_test: Test settings fixture
        mocker: PyTest mocker fixture
    Returns: Configured BossBot instance
    Cleanup: Automatically closes bot after each test
    """
    bot = mocker.AsyncMock(spec=BossBot)
    # bot.configure_mock = configure_mock
    bot.configure_mock()  # Default to full mocking

    yield bot

    # Cleanup
    if not bot.is_closed():
        await bot.close()

@pytest.fixture(scope="function")
def fixture_discord_context(
    fixture_discord_bot: BossBot,
    mocker: MockerFixture
) -> commands.Context:
    """Provide a mock Discord context for command testing.

    Scope: function - ensures clean context for each test
    Args:
        fixture_discord_bot: Bot fixture
        mocker: PyTest mocker fixture
    Returns: Mocked Discord Context
    """
    ctx = mocker.Mock(spec=commands.Context)
    ctx.bot = fixture_discord_bot
    ctx.send = mocker.AsyncMock()
    ctx.author = mocker.Mock()
    ctx.author.id = 12345
    ctx.channel = mocker.Mock()
    ctx.channel.id = 67890
    return ctx

# --- Service Fixtures --- #

@pytest.fixture(scope="function")
def fixture_queue_manager_test(fixture_settings_test: BossSettings) -> QueueManager:
    """Provide a test queue manager instance.

    Scope: function - ensures clean manager for each test
    Args:
        fixture_settings_test: Test settings fixture
    Returns: Configured QueueManager instance
    """
    manager = QueueManager(max_queue_size=fixture_settings_test.max_queue_size)

    def reset_state():
        """Reset queue state between tests."""
        manager._queue.clear()

    manager.reset_state = reset_state
    manager.reset_state()  # Start clean

    return manager

@pytest.fixture(scope="function")
def fixture_download_manager(fixture_settings_test: BossSettings) -> DownloadManager:
    """Provide a test download manager instance.

    Scope: function - ensures clean manager for each test
    Args:
        fixture_settings_test: Test settings fixture
    Returns: Configured DownloadManager instance
    """
    manager = DownloadManager(
        settings=fixture_settings_test,
        max_concurrent_downloads=fixture_settings_test.max_concurrent_downloads
    )

    def reset_state():
        """Reset download state between tests."""
        manager.active_downloads.clear()

    manager.reset_state = reset_state
    manager.reset_state()  # Start clean

    return manager


# --- VCR Configuration for API Testing --- #

# Environment detection
IS_RUNNING_ON_GITHUB_ACTIONS = bool(os.environ.get("GITHUB_ACTOR"))

# Hosts to ignore during VCR recording
IGNORE_HOSTS: list[str] = [
    "api.smith.langchain.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]


def is_twitter(uri: str) -> bool:
    """Check if a URI is a Twitter/X URI."""
    pattern = (
        r"(?:https?://)?(?:www\.|mobile\.|api\.)?"
        r"(?:(?:[fv]x)?twitter|(?:fix(?:up|v))?x)\.com"
    )
    return bool(re.search(pattern, uri))


def is_reddit(uri: str) -> bool:
    """Check if a URI is a Reddit URI."""
    patterns = [
        r"(?:https?://)?(?:\w+\.)?reddit\.com(/r/[^/?#]+(?:/([a-z]+))?)/?(?:\?([^#]*))?(?:$|#)",
        r"(?:https?://)?(?:\w+\.)?reddit\.com((?:/([a-z]+))?)/?(?:\?([^#]*))?(?:$|#)",
        r"(?:https?://)?(?:\w+\.)?reddit\.com/u(?:ser)?/([^/?#]+(?:/([a-z]+))?)/?(?:\?([^#]*))?$",
        r"(?:https?://)?(?:(?:\w+\.)?reddit\.com/(?:(?:r|u|user)/[^/?#]+/comments|gallery)|redd\.it)/([a-z0-9]+)",
        r"(?:https?://)?((?:i|preview)\.redd\.it|i\.reddituploads\.com)/([^/?#]+)(\?[^#]*)?",
        r"(?:https?://)?(?:(?:\w+\.)?reddit\.com/(?:(?:r)/([^/?#]+)))/s/([a-zA-Z0-9]{10})",
    ]
    return any(bool(re.search(pattern, uri)) for pattern in patterns)


def is_youtube(uri: str) -> bool:
    """Check if a URI is a YouTube URI."""
    patterns = [
        r"""(?x)^
            (?:https?://|//)
            (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\.com|
               (?:www\.)?deturl\.com/www\.youtube\.com|
               (?:www\.)?pwnyoutube\.com|
               (?:www\.)?hooktube\.com|
               (?:www\.)?yourepeat\.com|
               tube\.majestyc\.net|
               youtube\.googleapis\.com)/
            (?:.*?\#/)?
            (?:
                (?:(?:v|embed|e|shorts|live)/(?!videoseries|live_stream))
                |(?:
                    (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?
                    (?:\?|\#!?)
                    (?:.*?[&;])??
                    v=
                )
            ))
            |(?:
               youtu\.be|
               vid\.plus|
               zwearz\.com/watch
            )/
            |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
            )?
            [0-9A-Za-z_-]{11}
            (?:\#|$)""",
        r"^(?:https?://(?:www\.)?youtube\.com)?/(@[a-zA-Z0-9_-]+)",
        r"^(?:https?://(?:www\.)?youtube\.com)?/(UC[a-zA-Z0-9_-]{22})",
        r"(?:https?:)?//(?:www\.)?youtube(?:-nocookie)?\.com/(?:embed|v|p)/[0-9A-Za-z_-]{11}",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[0-9A-Za-z_-]+",
    ]
    return any(bool(re.search(pattern, uri, re.VERBOSE)) for pattern in patterns)


def is_gallery_dl_platform(uri: str) -> bool:
    """Check if URI is for a platform supported by gallery-dl."""
    return any([is_twitter(uri), is_reddit(uri)])


def is_yt_dlp_platform(uri: str) -> bool:
    """Check if URI is for a platform supported by yt-dlp."""
    return is_youtube(uri)


def filter_response(response: dict[str, Any]) -> dict[str, Any]:
    """Filter the response before recording to remove sensitive data."""
    if "retry-after" in response.get("headers", {}):
        response["headers"]["retry-after"] = "0"

    # Standardize rate limiting headers
    rate_limit_headers = {
        "x-ratelimit-remaining-requests": "144",
        "x-ratelimit-remaining-tokens": "143324",
        "x-request-id": "fake-request-id",
        "x-rate-limit-remaining": "49",
        "x-rate-limit-reset": "1735960916",
    }

    for header, fake_value in rate_limit_headers.items():
        if header in response.get("headers", {}):
            response["headers"][header] = fake_value

    # Sanitize cookies
    if "Set-Cookie" in response.get("headers", {}):
        response["headers"]["Set-Cookie"] = [
            "guest_id_marketing=v1%3FAKEBROTHER; Max-Age=63072000; Path=/; Domain=.x.com; Secure",
            "guest_id_ads=v1%3FAKEBROTHER; Max-Age=63072000; Path=/; Domain=.x.com; Secure",
            "personalization_id=v1_SUPERFAKE; Max-Age=63072000; Path=/; Domain=.x.com; Secure",
            "guest_id=v1%3FAKEBROTHER; Max-Age=63072000; Path=/; Domain=.x.com; Secure",
        ]

    return response


def request_matcher(r1: dict[str, Any], r2: dict[str, Any]) -> bool:
    """Custom matcher to determine if requests are equivalent."""
    # Direct URI match
    if r1.uri == r2.uri:
        return r1.body == r2.body

    # Platform-specific matching
    if (
        # Gallery-dl platforms
        (is_gallery_dl_platform(r1.uri) and is_gallery_dl_platform(r2.uri))
        # YT-dlp platforms
        or (is_yt_dlp_platform(r1.uri) and is_yt_dlp_platform(r2.uri))
    ):
        return r1.body == r2.body

    return False


def filter_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Filter the request before recording to remove sensitive data."""
    # Skip requests to ignored hosts
    if IGNORE_HOSTS and any(host in request.uri for host in IGNORE_HOSTS):
        return None

    # Skip login requests
    if request.path == "/login":
        return None

    # Handle multipart requests specially
    if ctype := request.headers.get("Content-Type"):
        ctype = ctype.decode("utf-8") if isinstance(ctype, bytes) else ctype
        if "multipart/form-data" in ctype:
            request.headers = {}
            return request

    request = copy.deepcopy(request)

    # Clear sensitive headers
    request.headers = {}

    # Filter sensitive POST data
    filter_post_data_parameters = [
        "api-version", "client_id", "client_secret", "code",
        "username", "password", "api_key", "authorization"
    ]
    replacements = [(p, "DUMMY_VALUE") for p in filter_post_data_parameters]
    filter_function = functools.partial(filters.replace_post_data_parameters, replacements=replacements)
    request = filter_function(request)

    return request


def pytest_recording_configure(config, vcr) -> None:
    """Configure VCR for pytest-recording."""
    vcr.register_matcher("request_matcher", request_matcher)
    vcr.match_on = ["request_matcher"]


@pytest.fixture(scope="function")
def vcr_config() -> dict[str, Any]:
    """VCR configuration fixture for safe API interaction recording."""
    return {
        "filter_headers": [
            ("authorization", "DUMMY_AUTHORIZATION"),
            ("x-api-key", "DUMMY_API_KEY"),
            ("api-key", "DUMMY_API_KEY"),
            ("cookie", "DUMMY_COOKIE"),
            ("x-guest-token", "DUMMY_GUEST_TOKEN"),
            ("x-csrf-token", "DUMMY_CSRF_TOKEN"),
            ("user-agent", "DUMMY_USER_AGENT"),
        ],
        "ignore_localhost": False,
        "filter_query_parameters": [
            "api-version",
            "client_id",
            "client_secret",
            "code",
            "api_key",
            "access_token",
            "refresh_token",
        ],
        "before_record_request": filter_request,
        "before_record_response": filter_response,
        "match_on": ["method", "scheme", "port", "path", "query", "body"],
        "record_mode": "once",  # Only record if cassette doesn't exist
        "decode_compressed_response": True,
    }


# VCR utility classes for testing
class IgnoreOrder:
    """pytest helper to test equality of lists/tuples ignoring item order."""

    def __init__(self, items: list | tuple, key: Any = None) -> None:
        self.items = items
        self.key = key

    def __eq__(self, other: Any) -> bool:
        return type(other) == type(self.items) and sorted(other, key=self.key) == sorted(self.items, key=self.key)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.items!r})"


class RegexMatcher:
    """pytest helper to check a string against a regex."""

    def __init__(self, pattern: str, flags: int = 0) -> None:
        self.regex = re.compile(pattern=pattern, flags=flags)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, str) and bool(self.regex.match(other))

    def __repr__(self) -> str:
        return self.regex.pattern


class DictSubSet:
    """pytest helper to check if a dictionary contains a subset of items."""

    __slots__ = ["items", "_missing", "_differing"]

    def __init__(self, items: dict[Any | str, Any] | None = None, **kwargs: Any) -> None:
        self.items = {**(items or {}), **kwargs}
        self._missing: dict[Any, Any] | None = None
        self._differing: dict[Any, tuple[Any, Any]] | None = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self.items)):
            return False
        self._missing = {k: v for k, v in self.items.items() if k not in other}
        self._differing = {k: (v, other[k]) for k, v in self.items.items() if k in other and other[k] != v}
        return not (self._missing or self._differing)

    def __repr__(self) -> str:
        msg = repr(self.items)
        if self._missing:
            msg += f"\n    # Missing: {self._missing}"
        if self._differing:
            msg += f"\n    # Differing: {self._differing}"
        return msg
