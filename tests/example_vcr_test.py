"""Example VCR test demonstrating safe API interaction recording.

This test file shows how to use VCR with the experimental API-direct clients
while ensuring no sensitive data is recorded in cassettes.
"""

import pytest
from pathlib import Path
from typing import Dict, Any
from collections.abc import AsyncGenerator
from pytest_mock import MockerFixture

# Import VCR fixtures and utilities
from tests.conftest import (
    vcr_config,
    DictSubSet,
    RegexMatcher,
)

# Mock imports for experimental features (these don't exist yet)
# from boss_bot.core.downloads.clients.aio_gallery_dl import AsyncGalleryDL
# from boss_bot.core.downloads.strategies.twitter_strategy import TwitterDownloadStrategy
# from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags


class MockAsyncGalleryDL:
    """Mock AsyncGalleryDL for testing VCR integration."""

    def __init__(self, config: dict[str, Any] = None, **kwargs):
        self.config = config or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def download(self, url: str, **kwargs) -> AsyncGenerator[dict[str, Any], None]:
        """Mock download method that yields realistic response data."""
        # Simulate a Twitter download response
        mock_response = {
            "extractor": "twitter",
            "extractor_key": "TwitterTweetIE",
            "id": "1868256259251863704",
            "title": "Mock Tweet Content",
            "uploader": "mock_user",
            "upload_date": "20241214",
            "timestamp": 1734207123,
            "duration": None,
            "view_count": None,
            "like_count": 42,
            "repost_count": 7,
            "comment_count": 3,
            "url": url,
            "thumbnails": [],
            "description": "This is a mock tweet for testing",
            "webpage_url": url,
            "original_url": url,
            "filepath": "/tmp/downloads/twitter_mock_user_1868256259251863704_1.jpg",
            "filename": "twitter_mock_user_1868256259251863704_1.jpg",
            "filesize": 156789,
            "ext": "jpg",
            "format": "jpg",
            "format_id": "jpg",
            "http_headers": {},
        }
        yield mock_response


class MockDownloadFeatureFlags:
    """Mock feature flags for testing."""

    def __init__(self, settings):
        self.settings = settings

    @property
    def use_api_twitter(self) -> bool:
        return getattr(self.settings, 'twitter_use_api_client', False)

    @property
    def api_fallback_to_cli(self) -> bool:
        return getattr(self.settings, 'download_api_fallback_to_cli', True)


class MockTwitterStrategy:
    """Mock Twitter strategy for testing."""

    def __init__(self, feature_flags, download_dir: Path):
        self.feature_flags = feature_flags
        self.download_dir = download_dir
        self._api_client = None

    @property
    def api_client(self):
        if self._api_client is None:
            self._api_client = MockAsyncGalleryDL()
        return self._api_client

    def supports_url(self, url: str) -> bool:
        return "twitter.com" in url or "x.com" in url

    async def download(self, url: str, **kwargs):
        """Mock download using feature-flagged approach."""
        if self.feature_flags.use_api_twitter:
            try:
                return await self._download_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    return await self._download_via_cli(url, **kwargs)
                raise
        else:
            return await self._download_via_cli(url, **kwargs)

    async def _download_via_api(self, url: str, **kwargs):
        """Mock API download."""
        async with self.api_client as client:
            async for item in client.download(url, **kwargs):
                # Convert to MediaMetadata-like structure
                return {
                    "url": url,
                    "title": item["title"],
                    "platform": "twitter",
                    "uploader": item["uploader"],
                    "filename": item["filename"],
                    "filesize": item["filesize"],
                    "download_method": "api",
                }

    async def _download_via_cli(self, url: str, **kwargs):
        """Mock CLI download."""
        return {
            "url": url,
            "title": "Mock CLI Download",
            "platform": "twitter",
            "uploader": "cli_user",
            "filename": "cli_download.jpg",
            "filesize": 123456,
            "download_method": "cli",
        }


# --- VCR Tests --- #

@pytest.mark.asyncio
@pytest.mark.vcr  # This will create/use a cassette file
async def test_twitter_api_download_with_vcr():
    """Test Twitter API download with VCR recording."""
    # This test demonstrates how VCR captures API interactions safely

    async with MockAsyncGalleryDL() as client:
        items = []
        url = "https://x.com/example/status/1868256259251863704"

        async for item in client.download(url):
            items.append(item)

        # Verify the response structure
        assert len(items) == 1
        assert items[0]["extractor"] == "twitter"
        assert items[0]["id"] == "1868256259251863704"
        assert "mock_user" in items[0]["uploader"]

        # Use DictSubSet for flexible matching
        expected_fields = DictSubSet({
            "extractor": "twitter",
            "title": RegexMatcher(r"Mock.*"),
            "upload_date": "20241214",
        })
        assert items[0] == expected_fields


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_strategy_cli_mode(mocker: MockerFixture):
    """Test strategy in CLI mode (existing behavior)."""
    # Create mock settings to disable API client
    mock_settings = mocker.Mock()
    mock_settings.twitter_use_api_client = False

    feature_flags = MockDownloadFeatureFlags(mock_settings)
    strategy = MockTwitterStrategy(feature_flags, Path("/tmp"))

    url = "https://twitter.com/test/status/123"
    result = await strategy.download(url)

    # Should use CLI handler
    assert result["download_method"] == "cli"
    assert result["platform"] == "twitter"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_strategy_api_mode(mocker: MockerFixture):
    """Test strategy in API mode (new behavior)."""
    # Create mock settings to enable API client
    mock_settings = mocker.Mock()
    mock_settings.twitter_use_api_client = True

    feature_flags = MockDownloadFeatureFlags(mock_settings)
    strategy = MockTwitterStrategy(feature_flags, Path("/tmp"))

    url = "https://x.com/test/status/1868256259251863704"
    result = await strategy.download(url)

    # Should use API client
    assert result["download_method"] == "api"
    assert result["platform"] == "twitter"
    assert result["title"] == "Mock Tweet Content"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_api_fallback_to_cli(mocker: MockerFixture):
    """Test API failure fallback to CLI."""
    # Create mock settings
    mock_settings = mocker.Mock()
    mock_settings.twitter_use_api_client = True
    mock_settings.download_api_fallback_to_cli = True

    feature_flags = MockDownloadFeatureFlags(mock_settings)
    strategy = MockTwitterStrategy(feature_flags, Path("/tmp"))

    # Mock API failure using pytest-mock
    mocker.patch.object(strategy, '_download_via_api', side_effect=Exception("API Error"))

    url = "https://twitter.com/test/status/123"
    result = await strategy.download(url)

    # Should fallback to CLI
    assert result["download_method"] == "cli"
    assert result["platform"] == "twitter"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_multiple_platform_downloads():
    """Test downloading from multiple platforms with VCR."""
    urls = [
        "https://twitter.com/test1/status/123",
        "https://reddit.com/r/test/comments/abc123/test_post/",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]

    results = []
    for url in urls:
        # Mock different responses based on platform
        if "twitter" in url:
            async with MockAsyncGalleryDL() as client:
                async for item in client.download(url):
                    results.append({
                        "platform": "twitter",
                        "url": url,
                        "title": item["title"],
                    })
        # Add similar mocks for Reddit and YouTube

    assert len(results) >= 1  # At least Twitter should work
    assert any(r["platform"] == "twitter" for r in results)


# --- Configuration Tests --- #

def test_vcr_config_safety(vcr_config):
    """Test that VCR configuration properly sanitizes sensitive data."""
    config = vcr_config

    # Verify sensitive headers are filtered
    sensitive_headers = ["authorization", "x-api-key", "cookie"]
    for header in sensitive_headers:
        assert any(h[0] == header for h in config["filter_headers"])

    # Verify sensitive query parameters are filtered
    sensitive_params = ["api_key", "access_token", "client_secret"]
    for param in sensitive_params:
        assert param in config["filter_query_parameters"]

    # Verify we have request/response filters
    assert config["before_record_request"] is not None
    assert config["before_record_response"] is not None


def test_platform_url_detection():
    """Test URL platform detection functions."""
    from tests.conftest import is_twitter, is_reddit, is_youtube

    # Twitter URLs
    assert is_twitter("https://twitter.com/user/status/123")
    assert is_twitter("https://x.com/user/status/123")
    assert is_twitter("https://mobile.twitter.com/user/status/123")

    # Reddit URLs
    assert is_reddit("https://reddit.com/r/test/comments/abc123/")
    assert is_reddit("https://www.reddit.com/r/test/")
    assert is_reddit("https://old.reddit.com/r/test/")

    # YouTube URLs
    assert is_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_youtube("https://youtu.be/dQw4w9WgXcQ")
    assert is_youtube("https://youtube.com/shorts/abc123")


# --- Integration Tests --- #

@pytest.mark.integration
@pytest.mark.vcr
async def test_full_download_workflow(mocker: MockerFixture):
    """Integration test for full download workflow with VCR."""
    # This would be a comprehensive test using real API calls
    # but recorded safely in a cassette

    url = "https://x.com/example/status/1868256259251863704"

    # Create mock settings with API client enabled
    mock_settings = mocker.Mock()
    mock_settings.twitter_use_api_client = True

    feature_flags = MockDownloadFeatureFlags(mock_settings)
    strategy = MockTwitterStrategy(feature_flags, Path("/tmp"))

    result = await strategy.download(url)

    # Verify complete workflow
    assert result["url"] == url
    assert result["platform"] == "twitter"
    assert "filename" in result
    assert "filesize" in result
    assert result["download_method"] == "api"


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/example_vcr_test.py -v
    pytest.main([__file__, "-v"])
