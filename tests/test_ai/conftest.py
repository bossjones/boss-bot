"""Test configuration and fixtures for AI components."""

import pytest
from unittest.mock import AsyncMock, Mock
from pathlib import Path
from typing import Dict, Any

from boss_bot.core.env import BossSettings
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags


@pytest.fixture(scope="function")
def fixture_test_settings() -> BossSettings:
    """Create test settings for AI components."""
    settings = Mock(spec=BossSettings)

    # AI feature flags
    settings.ai_strategy_selection_enabled = False
    settings.ai_content_analysis_enabled = False
    settings.ai_workflow_orchestration_enabled = False

    # Existing feature flags for compatibility
    settings.twitter_use_api_client = False
    settings.reddit_use_api_client = False
    settings.instagram_use_api_client = False
    settings.youtube_use_api_client = False
    settings.download_api_fallback_to_cli = True

    # Other settings
    settings.boss_bot_download_dir = str(Path.cwd() / ".downloads")

    return settings


@pytest.fixture(scope="function")
def fixture_ai_feature_flags(fixture_test_settings) -> DownloadFeatureFlags:
    """Create feature flags for AI testing."""
    return DownloadFeatureFlags(fixture_test_settings)


@pytest.fixture(scope="function")
def fixture_test_download_dir(tmp_path) -> Path:
    """Create temporary download directory for tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(exist_ok=True)
    return download_dir


@pytest.fixture(scope="function")
def fixture_mock_llm_model():
    """Create mock LLM model for testing."""
    mock_model = AsyncMock()
    mock_model.agenerate = AsyncMock()
    mock_model.ainvoke = AsyncMock()
    return mock_model


@pytest.fixture(scope="function")
def fixture_agent_context() -> dict[str, Any]:
    """Create test agent context."""
    return {
        "request_id": "test-request-123",
        "user_id": "test-user-456",
        "guild_id": "test-guild-789",
        "conversation_history": [],
        "metadata": {
            "platform": "discord",
            "command": "download",
            "timestamp": "2025-06-24T00:00:00Z"
        }
    }


@pytest.fixture(scope="function")
def fixture_test_urls() -> dict[str, str]:
    """Provide test URLs for different platforms."""
    return {
        "twitter": "https://twitter.com/user/status/123456789",
        "reddit": "https://reddit.com/r/pics/comments/abc123/title/",
        "instagram": "https://instagram.com/p/ABC123/",
        "youtube": "https://youtube.com/watch?v=VIDEO_ID",
        "unsupported": "https://example.com/not-supported"
    }


@pytest.fixture(scope="function")
def fixture_mock_agent_response():
    """Create mock agent response for testing."""
    mock_response = Mock()
    mock_response.success = True
    mock_response.result = "Mock agent result"
    mock_response.confidence = 0.95
    mock_response.reasoning = "Mock reasoning"
    mock_response.metadata = {}
    return mock_response
