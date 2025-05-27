"""Tests for YouTube download strategy."""

from __future__ import annotations

import pytest
from pathlib import Path
from pytest_mock import MockerFixture
from unittest.mock import Mock

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.strategies.youtube_strategy import YouTubeDownloadStrategy


class TestYouTubeDownloadStrategy:
    """Test suite for YouTube download strategy."""

    @pytest.fixture
    def fixture_feature_flags_test(self, mocker: MockerFixture) -> DownloadFeatureFlags:
        """Create DownloadFeatureFlags instance for testing.

        Returns a feature flags instance with configurable mock settings,
        allowing tests to control feature flag behavior.
        """
        mock_settings = mocker.Mock()
        mock_settings.youtube_use_api_client = False
        mock_settings.download_api_fallback_to_cli = True
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def fixture_youtube_strategy_test(
        self,
        fixture_feature_flags_test: DownloadFeatureFlags,
        tmp_path: Path
    ) -> YouTubeDownloadStrategy:
        """Create YouTubeDownloadStrategy instance for testing."""
        return YouTubeDownloadStrategy(fixture_feature_flags_test, tmp_path)

    def test_initialization(
        self,
        fixture_feature_flags_test: DownloadFeatureFlags,
        tmp_path: Path
    ):
        """Test strategy initialization."""
        strategy = YouTubeDownloadStrategy(fixture_feature_flags_test, tmp_path)

        assert strategy.feature_flags == fixture_feature_flags_test
        assert strategy.download_dir == tmp_path
        assert strategy.cli_handler is not None
        assert strategy.cli_handler.platform_name == "youtube"
        assert strategy._api_client is None  # Lazy loaded

    def test_api_client_lazy_loading(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test that API client is lazy loaded."""
        strategy = fixture_youtube_strategy_test

        # Initially None
        assert strategy._api_client is None

        # Access triggers loading
        client = strategy.api_client
        assert client is not None
        assert strategy._api_client is client

        # Subsequent access returns same instance
        client2 = strategy.api_client
        assert client2 is client

    def test_api_client_setter_getter(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy, mocker: MockerFixture):
        """Test API client setter and getter for testing."""
        strategy = fixture_youtube_strategy_test
        mock_client = mocker.Mock()

        # Test setter
        strategy.api_client = mock_client
        assert strategy._api_client is mock_client
        assert strategy.api_client is mock_client

        # Test deleter
        del strategy.api_client
        assert strategy._api_client is None

    def test_supports_url(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test URL support checking."""
        strategy = fixture_youtube_strategy_test

        # Valid YouTube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PLrUhA8hnVy"
        ]

        for url in valid_urls:
            assert strategy.supports_url(url), f"Should support: {url}"

        # Invalid URLs
        invalid_urls = [
            "https://twitter.com/user/status/123",
            "https://instagram.com/p/ABC123/",
            "https://reddit.com/r/test/comments/abc/",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert not strategy.supports_url(url), f"Should not support: {url}"

    @pytest.mark.asyncio
    async def test_download_cli_mode(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test download in CLI mode (feature flag disabled)."""
        strategy = fixture_youtube_strategy_test

        # Configure for CLI mode
        strategy.feature_flags.settings.youtube_use_api_client = False

        # Mock CLI handler download
        expected_metadata = MediaMetadata(platform="youtube", url="test-url", title="Test Video")
        mock_cli_download = mocker.patch.object(
            strategy, '_download_via_cli',
            return_value=expected_metadata
        )

        # Test download
        result = await strategy.download("https://www.youtube.com/watch?v=test")

        # Verify CLI method was called
        mock_cli_download.assert_called_once_with("https://www.youtube.com/watch?v=test")
        assert result == expected_metadata

    @pytest.mark.asyncio
    async def test_download_api_mode(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test download in API mode (feature flag enabled)."""
        strategy = fixture_youtube_strategy_test

        # Configure for API mode
        strategy.feature_flags.settings.youtube_use_api_client = True

        # Mock API download
        expected_metadata = MediaMetadata(platform="youtube", url="test-url", title="Test Video")
        mock_api_download = mocker.patch.object(
            strategy, '_download_via_api',
            return_value=expected_metadata
        )

        # Test download
        result = await strategy.download("https://www.youtube.com/watch?v=test")

        # Verify API method was called
        mock_api_download.assert_called_once_with("https://www.youtube.com/watch?v=test")
        assert result == expected_metadata

    @pytest.mark.asyncio
    async def test_download_api_fallback_to_cli(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test automatic fallback from API to CLI on failure."""
        strategy = fixture_youtube_strategy_test

        # Configure for API mode with fallback enabled
        strategy.feature_flags.settings.youtube_use_api_client = True
        strategy.feature_flags.settings.download_api_fallback_to_cli = True

        # Mock API to fail and CLI to succeed
        mock_api_download = mocker.patch.object(
            strategy, '_download_via_api',
            side_effect=Exception("API error")
        )
        expected_metadata = MediaMetadata(platform="youtube", url="test-url", title="Fallback Video")
        mock_cli_download = mocker.patch.object(
            strategy, '_download_via_cli',
            return_value=expected_metadata
        )

        # Test download
        result = await strategy.download("https://www.youtube.com/watch?v=test")

        # Verify both methods were called
        mock_api_download.assert_called_once()
        mock_cli_download.assert_called_once()
        assert result == expected_metadata

    @pytest.mark.asyncio
    async def test_download_api_no_fallback_failure(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test API failure without fallback enabled."""
        strategy = fixture_youtube_strategy_test

        # Configure for API mode with fallback disabled
        strategy.feature_flags.settings.youtube_use_api_client = True
        strategy.feature_flags.settings.download_api_fallback_to_cli = False

        # Mock API to fail
        mock_api_download = mocker.patch.object(
            strategy, '_download_via_api',
            side_effect=Exception("API error")
        )
        mock_cli_download = mocker.patch.object(strategy, '_download_via_cli')

        # Test download should raise exception
        with pytest.raises(Exception, match="API error"):
            await strategy.download("https://www.youtube.com/watch?v=test")

        # Verify only API method was called
        mock_api_download.assert_called_once()
        mock_cli_download.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_unsupported_url(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test download with unsupported URL."""
        strategy = fixture_youtube_strategy_test

        with pytest.raises(ValueError, match="URL not supported"):
            await strategy.download("https://twitter.com/user/status/123")

    @pytest.mark.asyncio
    async def test_get_metadata_cli_mode(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test metadata extraction in CLI mode."""
        strategy = fixture_youtube_strategy_test

        # Configure for CLI mode
        strategy.feature_flags.settings.youtube_use_api_client = False

        # Mock CLI metadata extraction
        expected_metadata = MediaMetadata(platform="youtube", url="test-url", title="Test Video")
        mock_cli_metadata = mocker.patch.object(
            strategy, '_get_metadata_via_cli',
            return_value=expected_metadata
        )

        # Test metadata extraction
        result = await strategy.get_metadata("https://www.youtube.com/watch?v=test")

        # Verify CLI method was called
        mock_cli_metadata.assert_called_once_with("https://www.youtube.com/watch?v=test")
        assert result == expected_metadata

    @pytest.mark.asyncio
    async def test_get_metadata_api_mode(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test metadata extraction in API mode."""
        strategy = fixture_youtube_strategy_test

        # Configure for API mode
        strategy.feature_flags.settings.youtube_use_api_client = True

        # Mock API metadata extraction
        expected_metadata = MediaMetadata(platform="youtube", url="test-url", title="Test Video")
        mock_api_metadata = mocker.patch.object(
            strategy, '_get_metadata_via_api',
            return_value=expected_metadata
        )

        # Test metadata extraction
        result = await strategy.get_metadata("https://www.youtube.com/watch?v=test")

        # Verify API method was called
        mock_api_metadata.assert_called_once_with("https://www.youtube.com/watch?v=test")
        assert result == expected_metadata

    def test_convert_api_response_to_metadata(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test API response conversion to metadata."""
        strategy = fixture_youtube_strategy_test

        # Test basic conversion
        api_response = {
            "url": "https://www.youtube.com/watch?v=test",
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 120,
            "view_count": 1000,
            "like_count": 50,
            "comment_count": 10,
            "upload_date": "20231215",
            "description": "Test description",
            "thumbnail": "https://img.youtube.com/vi/test/maxresdefault.jpg",
            "tags": ["test", "video"],
            "filename": "test_video.mp4",
        }

        metadata = strategy._convert_api_response_to_metadata(api_response)

        assert metadata.platform == "youtube"
        assert metadata.url == api_response["url"]
        assert metadata.title == api_response["title"]
        assert metadata.uploader == api_response["uploader"]
        assert metadata.duration == api_response["duration"]
        assert metadata.view_count == api_response["view_count"]
        assert metadata.like_count == api_response["like_count"]
        assert metadata.upload_date == api_response["upload_date"]
        assert metadata.description == api_response["description"]
        assert metadata.thumbnail_url == api_response["thumbnail"]
        assert metadata.filename == api_response["filename"]
        assert metadata.raw_metadata == api_response
        # comment_count and tags are stored in raw_metadata but not as direct fields
        assert metadata.raw_metadata["comment_count"] == api_response["comment_count"]
        assert metadata.raw_metadata["tags"] == api_response["tags"]

    def test_convert_api_response_with_dict_uploader(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test API response conversion with dict uploader."""
        strategy = fixture_youtube_strategy_test

        api_response = {
            "url": "https://www.youtube.com/watch?v=test",
            "title": "Test Video",
            "uploader": {"name": "Test Channel", "id": "UC123"},
        }

        metadata = strategy._convert_api_response_to_metadata(api_response)

        assert metadata.uploader == "Test Channel"

    def test_convert_api_response_minimal_data(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test API response conversion with minimal data."""
        strategy = fixture_youtube_strategy_test

        api_response = {"url": "https://www.youtube.com/watch?v=test"}

        metadata = strategy._convert_api_response_to_metadata(api_response)

        assert metadata.platform == "youtube"
        assert metadata.url == api_response["url"]
        assert metadata.title == ""
        assert metadata.uploader == "Unknown"

    def test_repr(self, fixture_youtube_strategy_test: YouTubeDownloadStrategy):
        """Test string representation."""
        strategy = fixture_youtube_strategy_test

        repr_str = repr(strategy)

        assert "YouTubeDownloadStrategy" in repr_str
        assert "api_enabled=False" in repr_str
        assert "fallback=True" in repr_str
        assert str(strategy.download_dir) in repr_str

    @pytest.mark.asyncio
    async def test_download_via_api_no_results(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test API download with no results."""
        strategy = fixture_youtube_strategy_test

        # Create async context manager mock that returns empty generator
        async def empty_generator():
            # Make it an async generator but yield nothing
            if False:
                yield

        # Create a mock context manager that will be returned by __aenter__
        mock_client_context = mocker.AsyncMock()
        mock_client_context.download = mocker.Mock(return_value=empty_generator())

        # Create the main mock that implements async context manager protocol
        mock_api_client = mocker.AsyncMock()
        mock_api_client.__aenter__ = mocker.AsyncMock(return_value=mock_client_context)
        mock_api_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the api_client property to return our mock
        mocker.patch.object(strategy, 'api_client', mock_api_client)

        # Test should raise exception for no results
        with pytest.raises(RuntimeError, match="No download results"):
            await strategy._download_via_api("https://www.youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_get_metadata_via_api_no_results(
        self,
        fixture_youtube_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test API metadata extraction with no results."""
        strategy = fixture_youtube_strategy_test

        # Create async context manager mock that returns empty generator
        async def empty_generator():
            # Make it an async generator but yield nothing
            if False:
                yield

        # Create a mock context manager that will be returned by __aenter__
        mock_client_context = mocker.AsyncMock()
        mock_client_context.extract_metadata = mocker.Mock(return_value=empty_generator())

        # Create the main mock that implements async context manager protocol
        mock_api_client = mocker.AsyncMock()
        mock_api_client.__aenter__ = mocker.AsyncMock(return_value=mock_client_context)
        mock_api_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the api_client property to return our mock
        mocker.patch.object(strategy, 'api_client', mock_api_client)

        # Test should raise exception for no results
        with pytest.raises(RuntimeError, match="No metadata results"):
            await strategy._get_metadata_via_api("https://www.youtube.com/watch?v=test")


class TestYouTubeDownloadStrategyQualitySelection:
    """Test suite for YouTube quality selection features."""

    @pytest.fixture
    def fixture_feature_flags_api_test(self, mocker: MockerFixture) -> DownloadFeatureFlags:
        """Create DownloadFeatureFlags with API mode enabled."""
        mock_settings = mocker.Mock()
        mock_settings.youtube_use_api_client = True
        mock_settings.download_api_fallback_to_cli = False
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def fixture_youtube_api_strategy_test(
        self,
        fixture_feature_flags_api_test: DownloadFeatureFlags,
        tmp_path: Path
    ) -> YouTubeDownloadStrategy:
        """Create YouTubeDownloadStrategy with API mode enabled."""
        return YouTubeDownloadStrategy(fixture_feature_flags_api_test, tmp_path)

    @pytest.mark.asyncio
    async def test_download_with_quality_720p(
        self,
        fixture_youtube_api_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test download with 720p quality selection."""
        strategy = fixture_youtube_api_strategy_test

        # Create mock download function that validates quality
        async def mock_download(url, **kwargs):
            # Verify quality option was passed correctly
            assert kwargs.get("format") == "best[height<=720]"
            yield {"url": "test", "title": "Test Video", "uploader": "Test Channel"}

        # Create a mock context manager that will be returned by __aenter__
        mock_client_context = mocker.AsyncMock()
        mock_client_context.download = mock_download

        # Create the main mock that implements async context manager protocol
        mock_api_client = mocker.AsyncMock()
        mock_api_client.__aenter__ = mocker.AsyncMock(return_value=mock_client_context)
        mock_api_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the api_client property to return our mock
        mocker.patch.object(strategy, 'api_client', mock_api_client)

        # Test download with 720p quality
        result = await strategy._download_via_api(
            "https://www.youtube.com/watch?v=test",
            quality="720p"
        )

        assert result.platform == "youtube"
        assert result.title == "Test Video"

    @pytest.mark.asyncio
    async def test_download_with_quality_1080p(
        self,
        fixture_youtube_api_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test download with 1080p quality selection."""
        strategy = fixture_youtube_api_strategy_test

        # Create mock download function that validates quality
        async def mock_download(url, **kwargs):
            # Verify quality option was passed correctly
            assert kwargs.get("format") == "best[height<=1080]"
            yield {"url": "test", "title": "Test Video", "uploader": "Test Channel"}

        # Create a mock context manager that will be returned by __aenter__
        mock_client_context = mocker.AsyncMock()
        mock_client_context.download = mock_download

        # Create the main mock that implements async context manager protocol
        mock_api_client = mocker.AsyncMock()
        mock_api_client.__aenter__ = mocker.AsyncMock(return_value=mock_client_context)
        mock_api_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the api_client property to return our mock
        mocker.patch.object(strategy, 'api_client', mock_api_client)

        # Test download with 1080p quality
        result = await strategy._download_via_api(
            "https://www.youtube.com/watch?v=test",
            quality="1080p"
        )

        assert result.platform == "youtube"
        assert result.title == "Test Video"

    @pytest.mark.asyncio
    async def test_download_audio_only(
        self,
        fixture_youtube_api_strategy_test: YouTubeDownloadStrategy,
        mocker: MockerFixture
    ):
        """Test audio-only download."""
        strategy = fixture_youtube_api_strategy_test

        # Create mock download function that validates audio options
        async def mock_download(url, **kwargs):
            # Verify audio-only options were passed correctly
            assert kwargs.get("format") == "bestaudio"
            assert "postprocessors" in kwargs
            yield {"url": "test", "title": "Test Audio", "uploader": "Test Channel"}

        # Create a mock context manager that will be returned by __aenter__
        mock_client_context = mocker.AsyncMock()
        mock_client_context.download = mock_download

        # Create the main mock that implements async context manager protocol
        mock_api_client = mocker.AsyncMock()
        mock_api_client.__aenter__ = mocker.AsyncMock(return_value=mock_client_context)
        mock_api_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the api_client property to return our mock
        mocker.patch.object(strategy, 'api_client', mock_api_client)

        # Test audio-only download
        result = await strategy._download_via_api(
            "https://www.youtube.com/watch?v=test",
            audio_only=True,
            audio_format="mp3"
        )

        assert result.platform == "youtube"
        assert result.title == "Test Audio"
