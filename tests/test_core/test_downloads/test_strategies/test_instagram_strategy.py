"""Tests for Instagram download strategy."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.strategies.instagram_strategy import InstagramDownloadStrategy


class TestInstagramDownloadStrategy:
    """Test suite for Instagram download strategy."""

    @pytest.fixture
    def feature_flags_cli_mode(self, mocker: MockerFixture) -> DownloadFeatureFlags:
        """Create feature flags configured for CLI mode."""
        mock_settings = mocker.Mock()
        mock_settings.instagram_use_api_client = False
        mock_settings.download_api_fallback_to_cli = True
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def feature_flags_api_mode(self, mocker: MockerFixture) -> DownloadFeatureFlags:
        """Create feature flags configured for API mode."""
        mock_settings = mocker.Mock()
        mock_settings.instagram_use_api_client = True
        mock_settings.download_api_fallback_to_cli = True
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def feature_flags_api_no_fallback(self, mocker: MockerFixture) -> DownloadFeatureFlags:
        """Create feature flags configured for API mode without fallback."""
        mock_settings = mocker.Mock()
        mock_settings.instagram_use_api_client = True
        mock_settings.download_api_fallback_to_cli = False
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def sample_instagram_metadata(self) -> MediaMetadata:
        """Create sample Instagram metadata."""
        return MediaMetadata(
            url="https://instagram.com/p/ABC123",
            title="Test Instagram Post",
            author="test_user",
            platform="instagram",
            filename="instagram_test_ABC123.jpg",
            filesize=2048,
            description="This is a test Instagram post",
            download_method="cli",
            raw_metadata={
                "post_type": "post",
                "comment_count": 10,
                "is_video": False,
                "shortcode": "ABC123",
            },
        )

    @pytest.fixture
    def sample_api_response(self) -> dict:
        """Create sample API response from gallery-dl."""
        return {
            "description": "Test Instagram Post",
            "username": "test_user",
            "url": "https://instagram.com/p/ABC123/media.jpg",
            "filename": "instagram_test_ABC123.jpg",
            "filesize": 2048,
            "like_count": 100,
            "view_count": 500,
            "comment_count": 10,
            "shortcode": "ABC123",
            "is_video": False,
            "typename": "post",
            "date": "2024-01-01",
            "id": "123456789",
        }

    def test_initialization(self, feature_flags_cli_mode: DownloadFeatureFlags, tmp_path: Path):
        """Test strategy initialization."""
        strategy = InstagramDownloadStrategy(feature_flags_cli_mode, tmp_path)

        assert strategy.feature_flags is feature_flags_cli_mode
        assert strategy.download_dir == tmp_path
        assert strategy.platform_name == "instagram"
        assert strategy.cli_handler is not None
        assert strategy._api_client is None  # Lazy loaded

    def test_api_client_lazy_loading(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test API client lazy loading."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # API client should be None initially
        assert strategy._api_client is None

        # Mock the AsyncGalleryDL constructor
        mock_client = mocker.Mock()
        mock_async_gallery_dl = mocker.patch("boss_bot.core.downloads.clients.AsyncGalleryDL", return_value=mock_client)

        # Accessing api_client should trigger lazy loading
        client = strategy.api_client

        # Verify client was created with correct config
        mock_async_gallery_dl.assert_called_once()
        call_kwargs = mock_async_gallery_dl.call_args.kwargs

        assert "config" in call_kwargs
        assert "download_dir" in call_kwargs
        assert call_kwargs["download_dir"] == tmp_path

        # Verify Instagram-specific config
        config = call_kwargs["config"]
        assert "extractor" in config
        assert "instagram" in config["extractor"]
        instagram_config = config["extractor"]["instagram"]
        assert instagram_config["videos"] is True
        assert instagram_config["user-agent"] == "Wget/1.21.1"
        assert instagram_config["cookies-from-browser"] == "firefox"

        # Second access should return same client
        client2 = strategy.api_client
        assert client2 is client
        mock_async_gallery_dl.assert_called_once()  # Should not be called again

    def test_api_client_setter_getter(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test API client setter and getter for testing purposes."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Create a mock client
        mock_client = mocker.Mock()

        # Set the client
        strategy.api_client = mock_client
        assert strategy.api_client is mock_client

        # Delete the client
        del strategy.api_client
        assert strategy._api_client is None

    def test_supports_url(self, feature_flags_cli_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture):
        """Test URL support detection."""
        strategy = InstagramDownloadStrategy(feature_flags_cli_mode, tmp_path)

        # Mock the cli_handler's supports_url method
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        assert strategy.supports_url("https://instagram.com/p/ABC123") is True

        # Verify it delegates to cli_handler
        strategy.cli_handler.supports_url.assert_called_once_with("https://instagram.com/p/ABC123")

    @pytest.mark.asyncio
    async def test_download_cli_mode(
        self,
        feature_flags_cli_mode: DownloadFeatureFlags,
        tmp_path: Path,
        mocker: MockerFixture,
        sample_instagram_metadata: MediaMetadata,
    ):
        """Test download in CLI mode (existing behavior)."""
        strategy = InstagramDownloadStrategy(feature_flags_cli_mode, tmp_path)

        # Mock the CLI handler
        mock_download = mocker.patch.object(strategy.cli_handler, "download", return_value=sample_instagram_metadata)
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Mock asyncio.get_event_loop and run_in_executor
        mock_loop = mocker.Mock()
        mock_loop.run_in_executor = mocker.AsyncMock(return_value=sample_instagram_metadata)
        mocker.patch("asyncio.get_event_loop", return_value=mock_loop)

        # Execute download
        url = "https://instagram.com/p/ABC123"
        result = await strategy.download(url)

        # Verify CLI handler was called
        mock_loop.run_in_executor.assert_called_once_with(None, strategy.cli_handler.download, url)
        assert result is sample_instagram_metadata

    @pytest.mark.asyncio
    async def test_download_api_mode(
        self,
        feature_flags_api_mode: DownloadFeatureFlags,
        tmp_path: Path,
        mocker: MockerFixture,
        sample_api_response: dict,
    ):
        """Test download in API mode."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Mock supports_url
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Create mock API client
        mock_client = mocker.Mock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the download method to return an async generator
        async def mock_download_generator(*args, **kwargs):
            yield sample_api_response

        mock_client.download = mock_download_generator

        # Set the mocked client
        strategy.api_client = mock_client

        # Execute download
        url = "https://instagram.com/p/ABC123"
        result = await strategy.download(url)

        # Verify API client was used
        mock_client.__aenter__.assert_called_once()

        # Verify metadata conversion
        assert result.platform == "instagram"
        assert result.title == "Test Instagram Post"
        assert result.author == "test_user"
        assert result.download_method == "api"
        assert result.raw_metadata["shortcode"] == "ABC123"
        assert result.raw_metadata["comment_count"] == 10

    @pytest.mark.asyncio
    async def test_download_api_fallback_to_cli(
        self,
        feature_flags_api_mode: DownloadFeatureFlags,
        tmp_path: Path,
        mocker: MockerFixture,
        sample_instagram_metadata: MediaMetadata,
    ):
        """Test automatic fallback from API to CLI on failure."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Mock supports_url
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Mock API to fail
        mock_api_download = mocker.patch.object(
            strategy, "_download_via_api", side_effect=Exception("API error")
        )

        # Mock CLI to succeed
        mock_cli_download = mocker.patch.object(strategy, "_download_via_cli", return_value=sample_instagram_metadata)

        # Execute download
        url = "https://instagram.com/p/ABC123"
        result = await strategy.download(url)

        # Verify fallback behavior
        mock_api_download.assert_called_once_with(url)
        mock_cli_download.assert_called_once_with(url)
        assert result is sample_instagram_metadata

    @pytest.mark.asyncio
    async def test_download_api_no_fallback_failure(
        self, feature_flags_api_no_fallback: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test API failure without fallback enabled."""
        strategy = InstagramDownloadStrategy(feature_flags_api_no_fallback, tmp_path)

        # Mock supports_url
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Mock API to fail
        mock_api_download = mocker.patch.object(
            strategy, "_download_via_api", side_effect=Exception("API error")
        )

        # Execute download and expect exception
        url = "https://instagram.com/p/ABC123"
        with pytest.raises(Exception, match="API error"):
            await strategy.download(url)

        # Verify API was called but no fallback occurred
        mock_api_download.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_download_unsupported_url(
        self, feature_flags_cli_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test download with unsupported URL."""
        strategy = InstagramDownloadStrategy(feature_flags_cli_mode, tmp_path)

        # Mock supports_url to return False
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=False)

        # Execute download and expect ValueError
        url = "https://example.com/not-instagram"
        with pytest.raises(ValueError, match="URL not supported by Instagram strategy"):
            await strategy.download(url)

    @pytest.mark.asyncio
    async def test_get_metadata_cli_mode(
        self,
        feature_flags_cli_mode: DownloadFeatureFlags,
        tmp_path: Path,
        mocker: MockerFixture,
        sample_instagram_metadata: MediaMetadata,
    ):
        """Test metadata extraction in CLI mode."""
        strategy = InstagramDownloadStrategy(feature_flags_cli_mode, tmp_path)

        # Mock the CLI handler
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Mock asyncio.get_event_loop and run_in_executor
        mock_loop = mocker.Mock()
        mock_loop.run_in_executor = mocker.AsyncMock(return_value=sample_instagram_metadata)
        mocker.patch("asyncio.get_event_loop", return_value=mock_loop)

        # Execute metadata extraction
        url = "https://instagram.com/p/ABC123"
        result = await strategy.get_metadata(url)

        # Verify CLI handler was called
        mock_loop.run_in_executor.assert_called_once_with(None, strategy.cli_handler.get_metadata, url)
        assert result is sample_instagram_metadata

    @pytest.mark.asyncio
    async def test_get_metadata_api_mode(
        self,
        feature_flags_api_mode: DownloadFeatureFlags,
        tmp_path: Path,
        mocker: MockerFixture,
        sample_api_response: dict,
    ):
        """Test metadata extraction in API mode."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Mock supports_url
        mocker.patch.object(strategy.cli_handler, "supports_url", return_value=True)

        # Create mock API client
        mock_client = mocker.Mock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock the extract_metadata method to return an async generator
        async def mock_metadata_generator(*args, **kwargs):
            yield sample_api_response

        mock_client.extract_metadata = mock_metadata_generator

        # Set the mocked client
        strategy.api_client = mock_client

        # Execute metadata extraction
        url = "https://instagram.com/p/ABC123"
        result = await strategy.get_metadata(url)

        # Verify API client was used
        mock_client.__aenter__.assert_called_once()

        # Verify metadata conversion
        assert result.platform == "instagram"
        assert result.title == "Test Instagram Post"
        assert result.author == "test_user"
        assert result.download_method == "api"

    def test_convert_api_response_to_metadata(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path, sample_api_response: dict
    ):
        """Test API response to metadata conversion."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        url = "https://instagram.com/p/ABC123"
        result = strategy._convert_api_response_to_metadata(sample_api_response, url)

        # Verify basic fields
        assert result.url == url
        assert result.title == "Test Instagram Post"
        assert result.author == "test_user"
        assert result.platform == "instagram"
        assert result.filename == "instagram_test_ABC123.jpg"
        assert result.filesize == 2048
        assert result.description == "Test Instagram Post"
        assert result.download_method == "api"

        # Verify Instagram-specific metadata
        assert result.raw_metadata["post_type"] == "post"
        assert result.raw_metadata["comment_count"] == 10
        assert result.raw_metadata["is_video"] is False
        assert result.raw_metadata["shortcode"] == "ABC123"
        assert result.raw_metadata["post_id"] == "123456789"

        # Verify Instagram metrics
        assert result.like_count == 100
        assert result.view_count == 500

    def test_convert_api_response_with_dict_author(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path
    ):
        """Test API response conversion with author as dictionary."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        api_response = {
            "description": "Test Post",
            "uploader": {"username": "test_user", "full_name": "Test User"},
            "url": "https://instagram.com/p/ABC123/media.jpg",
            "filename": "test.jpg",
            "shortcode": "ABC123",
        }

        url = "https://instagram.com/p/ABC123"
        result = strategy._convert_api_response_to_metadata(api_response, url)

        assert result.author == "test_user"

    def test_convert_api_response_minimal_data(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path
    ):
        """Test API response conversion with minimal data."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        api_response = {
            "url": "https://instagram.com/p/ABC123/media.jpg",
        }

        url = "https://instagram.com/p/ABC123"
        result = strategy._convert_api_response_to_metadata(api_response, url)

        # Verify defaults are used
        assert result.title == "Instagram Content"
        assert result.author == "Unknown"
        assert result.platform == "instagram"
        assert result.filename == "media.jpg"  # Extracted from URL
        assert result.download_method == "api"

    def test_repr(self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path):
        """Test string representation."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        repr_str = repr(strategy)

        assert "InstagramDownloadStrategy" in repr_str
        assert "api_enabled=True" in repr_str
        assert "fallback_enabled=True" in repr_str
        assert f"download_dir={tmp_path}" in repr_str

    @pytest.mark.asyncio
    async def test_download_via_api_no_results(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test API download when no results are returned."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Create mock API client that returns empty results
        mock_client = mocker.Mock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock empty download results
        async def mock_empty_generator(*args, **kwargs):
            return
            yield  # This will never execute

        mock_client.download = mock_empty_generator

        # Set the mocked client
        strategy.api_client = mock_client

        # Execute download and expect RuntimeError
        url = "https://instagram.com/p/ABC123"
        with pytest.raises(RuntimeError, match="No content downloaded from"):
            await strategy._download_via_api(url)

    @pytest.mark.asyncio
    async def test_get_metadata_via_api_no_results(
        self, feature_flags_api_mode: DownloadFeatureFlags, tmp_path: Path, mocker: MockerFixture
    ):
        """Test API metadata extraction when no results are returned."""
        strategy = InstagramDownloadStrategy(feature_flags_api_mode, tmp_path)

        # Create mock API client that returns empty results
        mock_client = mocker.Mock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock empty metadata results
        async def mock_empty_generator(*args, **kwargs):
            return
            yield  # This will never execute

        mock_client.extract_metadata = mock_empty_generator

        # Set the mocked client
        strategy.api_client = mock_client

        # Execute metadata extraction and expect RuntimeError
        url = "https://instagram.com/p/ABC123"
        with pytest.raises(RuntimeError, match="No metadata extracted from"):
            await strategy._get_metadata_via_api(url)
