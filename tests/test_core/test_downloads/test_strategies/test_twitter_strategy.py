"""Tests for TwitterDownloadStrategy with CLI/API switching."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from pytest_mock import MockerFixture

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.strategies.twitter_strategy import TwitterDownloadStrategy


class TestTwitterDownloadStrategy:
    """Test TwitterDownloadStrategy functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for feature flags."""
        settings = MagicMock()
        settings.twitter_use_api_client = False
        settings.download_api_fallback_to_cli = True
        return settings

    @pytest.fixture
    def feature_flags(self, mock_settings):
        """Feature flags instance."""
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def temp_download_dir(self, tmp_path) -> Path:
        """Temporary download directory."""
        return tmp_path / "downloads"

    @pytest.fixture
    def strategy(self, feature_flags, temp_download_dir):
        """TwitterDownloadStrategy instance."""
        return TwitterDownloadStrategy(feature_flags, temp_download_dir)

    def test_strategy_initialization(self, strategy, feature_flags, temp_download_dir):
        """Test strategy initialization."""
        assert strategy.feature_flags is feature_flags
        assert strategy.download_dir == temp_download_dir
        assert strategy.cli_handler is not None
        assert strategy._api_client is None  # Lazy loaded
        assert strategy.platform_name == "twitter"

    def test_supports_url(self, strategy):
        """Test URL support checking."""
        # Test supported URLs
        assert strategy.supports_url("https://twitter.com/user/status/123") is True
        assert strategy.supports_url("https://x.com/user/status/123") is True
        assert strategy.supports_url("https://mobile.twitter.com/user/status/123") is True

        # Test unsupported URLs
        assert strategy.supports_url("https://youtube.com/watch?v=123") is False
        assert strategy.supports_url("https://reddit.com/r/test") is False
        assert strategy.supports_url("invalid-url") is False

    def test_api_client_lazy_loading(self, strategy):
        """Test API client is lazy loaded."""
        assert strategy._api_client is None

        # Access api_client property
        with patch('boss_bot.core.downloads.clients.AsyncGalleryDL') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = strategy.api_client

            assert client is mock_client
            assert strategy._api_client is mock_client
            mock_client_class.assert_called_once()

    def test_repr(self, strategy):
        """Test string representation."""
        repr_str = repr(strategy)
        assert "TwitterDownloadStrategy" in repr_str
        assert "api_enabled=False" in repr_str
        assert "fallback_enabled=True" in repr_str
        assert str(strategy.download_dir) in repr_str


class TestTwitterDownloadStrategyCLIMode:
    """Test TwitterDownloadStrategy in CLI mode."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with CLI mode enabled."""
        settings = MagicMock()
        settings.twitter_use_api_client = False  # CLI mode
        settings.download_api_fallback_to_cli = True
        return settings

    @pytest.fixture
    def feature_flags(self, mock_settings):
        """Feature flags instance."""
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def temp_download_dir(self, tmp_path) -> Path:
        """Temporary download directory."""
        return tmp_path / "downloads"

    @pytest.fixture
    def strategy(self, feature_flags, temp_download_dir):
        """TwitterDownloadStrategy instance."""
        return TwitterDownloadStrategy(feature_flags, temp_download_dir)

    @pytest.mark.asyncio
    async def test_download_cli_mode(self, strategy, mocker: MockerFixture):
        """Test download in CLI mode (existing behavior)."""
        url = "https://twitter.com/test/status/123"
        expected_metadata = MediaMetadata(
            title="Test Tweet",
            url=url,
            platform="twitter",
            download_method="cli"
        )

        # Mock the CLI handler download method
        mocker.patch.object(
            strategy.cli_handler,
            'download',
            return_value=expected_metadata
        )

        result = await strategy.download(url)

        # Should use CLI handler
        assert result is expected_metadata
        strategy.cli_handler.download.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_get_metadata_cli_mode(self, strategy, mocker: MockerFixture):
        """Test metadata extraction in CLI mode."""
        url = "https://twitter.com/test/status/123"
        expected_metadata = MediaMetadata(
            title="Test Tweet",
            url=url,
            platform="twitter"
        )

        # Mock the CLI handler get_metadata method
        mocker.patch.object(
            strategy.cli_handler,
            'get_metadata',
            return_value=expected_metadata
        )

        result = await strategy.get_metadata(url)

        # Should use CLI handler
        assert result is expected_metadata
        strategy.cli_handler.get_metadata.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_download_unsupported_url(self, strategy):
        """Test download with unsupported URL."""
        url = "https://youtube.com/watch?v=123"

        with pytest.raises(ValueError, match="URL not supported by Twitter strategy"):
            await strategy.download(url)

    @pytest.mark.asyncio
    async def test_get_metadata_unsupported_url(self, strategy):
        """Test metadata extraction with unsupported URL."""
        url = "https://youtube.com/watch?v=123"

        with pytest.raises(ValueError, match="URL not supported by Twitter strategy"):
            await strategy.get_metadata(url)


class TestTwitterDownloadStrategyAPIMode:
    """Test TwitterDownloadStrategy in API mode."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with API mode enabled."""
        settings = MagicMock()
        settings.twitter_use_api_client = True  # API mode
        settings.download_api_fallback_to_cli = False  # No fallback
        return settings

    @pytest.fixture
    def feature_flags(self, mock_settings):
        """Feature flags instance."""
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def temp_download_dir(self, tmp_path) -> Path:
        """Temporary download directory."""
        return tmp_path / "downloads"

    @pytest.fixture
    def strategy(self, feature_flags, temp_download_dir):
        """TwitterDownloadStrategy instance."""
        return TwitterDownloadStrategy(feature_flags, temp_download_dir)

    @pytest.mark.asyncio
    @pytest.mark.vcr
    async def test_download_api_mode(self, strategy, mocker: MockerFixture):
        """Test download in API mode (new behavior)."""
        url = "https://x.com/test/status/1868256259251863704"

        # Mock API client
        mock_client = AsyncMock()
        mock_download_result = {
            "title": "Mock Tweet Content",
            "uploader": "test_user",
            "url": "https://example.com/media.jpg",
            "filename": "media.jpg",
            "filesize": 123456,
            "upload_date": "20241214",
            "like_count": 42,
        }

        async def mock_download_generator(url, **kwargs):
            yield mock_download_result

        mock_client.download = mock_download_generator
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock the api_client property
        mocker.patch.object(strategy, 'api_client', mock_client)

        result = await strategy.download(url)

        # Should use API client and convert response
        assert result.title == "Mock Tweet Content"
        assert result.author == "test_user"
        assert result.filename == "media.jpg"
        assert result.filesize == 123456
        assert result.platform == "twitter"
        assert result.download_method == "api"

    @pytest.mark.asyncio
    @pytest.mark.vcr
    async def test_get_metadata_api_mode(self, strategy, mocker: MockerFixture):
        """Test metadata extraction in API mode."""
        url = "https://x.com/test/status/1868256259251863704"

        # Mock API client
        mock_client = AsyncMock()
        mock_metadata_result = {
            "title": "Mock Tweet Metadata",
            "uploader": "metadata_user",
            "description": "Test description",
            "upload_date": "20241214",
            "view_count": 1000,
        }

        async def mock_extract_metadata_generator(url, **kwargs):
            yield mock_metadata_result

        mock_client.extract_metadata = mock_extract_metadata_generator
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock the api_client property
        mocker.patch.object(strategy, 'api_client', mock_client)

        result = await strategy.get_metadata(url)

        # Should use API client and convert response
        assert result.title == "Mock Tweet Metadata"
        assert result.author == "metadata_user"
        assert result.description == "Test description"
        assert result.view_count == 1000
        assert result.platform == "twitter"
        assert result.download_method == "api"

    @pytest.mark.asyncio
    async def test_download_api_mode_no_results(self, strategy, mocker: MockerFixture):
        """Test download in API mode with no results."""
        url = "https://x.com/test/status/123"

        # Mock API client with no results
        mock_client = AsyncMock()

        async def mock_download_generator(url, **kwargs):
            return
            yield  # Never reached

        mock_client.download = mock_download_generator
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock the api_client property
        mocker.patch.object(strategy, 'api_client', mock_client)

        with pytest.raises(RuntimeError, match="No content downloaded from"):
            await strategy.download(url)

    @pytest.mark.asyncio
    async def test_get_metadata_api_mode_no_results(self, strategy, mocker: MockerFixture):
        """Test metadata extraction in API mode with no results."""
        url = "https://x.com/test/status/123"

        # Mock API client with no results
        mock_client = AsyncMock()

        async def mock_extract_metadata_generator(url, **kwargs):
            return
            yield  # Never reached

        mock_client.extract_metadata = mock_extract_metadata_generator
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock the api_client property
        mocker.patch.object(strategy, 'api_client', mock_client)

        with pytest.raises(RuntimeError, match="No metadata extracted from"):
            await strategy.get_metadata(url)


class TestTwitterDownloadStrategyFallback:
    """Test TwitterDownloadStrategy fallback from API to CLI."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with API mode and fallback enabled."""
        settings = MagicMock()
        settings.twitter_use_api_client = True  # API mode
        settings.download_api_fallback_to_cli = True  # Fallback enabled
        return settings

    @pytest.fixture
    def feature_flags(self, mock_settings):
        """Feature flags instance."""
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def temp_download_dir(self, tmp_path) -> Path:
        """Temporary download directory."""
        return tmp_path / "downloads"

    @pytest.fixture
    def strategy(self, feature_flags, temp_download_dir):
        """TwitterDownloadStrategy instance."""
        return TwitterDownloadStrategy(feature_flags, temp_download_dir)

    @pytest.mark.asyncio
    async def test_download_api_failure_fallback_to_cli(self, strategy, mocker: MockerFixture):
        """Test API failure fallback to CLI."""
        url = "https://twitter.com/test/status/123"
        expected_metadata = MediaMetadata(
            title="CLI Fallback Tweet",
            url=url,
            platform="twitter",
            download_method="cli"
        )

        # Mock API client to raise exception
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mocker.patch.object(strategy, 'api_client', mock_client)

        # Mock CLI handler to succeed
        mocker.patch.object(
            strategy.cli_handler,
            'download',
            return_value=expected_metadata
        )

        result = await strategy.download(url)

        # Should fallback to CLI handler
        assert result is expected_metadata
        strategy.cli_handler.download.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_get_metadata_api_failure_fallback_to_cli(self, strategy, mocker: MockerFixture):
        """Test API metadata failure fallback to CLI."""
        url = "https://twitter.com/test/status/123"
        expected_metadata = MediaMetadata(
            title="CLI Fallback Metadata",
            url=url,
            platform="twitter"
        )

        # Mock API client to raise exception
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mocker.patch.object(strategy, 'api_client', mock_client)

        # Mock CLI handler to succeed
        mocker.patch.object(
            strategy.cli_handler,
            'get_metadata',
            return_value=expected_metadata
        )

        result = await strategy.get_metadata(url)

        # Should fallback to CLI handler
        assert result is expected_metadata
        strategy.cli_handler.get_metadata.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_download_api_failure_no_fallback(self, strategy, mocker: MockerFixture):
        """Test API failure with no fallback (should raise)."""
        # Disable fallback
        strategy.feature_flags.settings.download_api_fallback_to_cli = False

        url = "https://twitter.com/test/status/123"

        # Mock API client to raise exception
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mocker.patch.object(strategy, 'api_client', mock_client)

        # Should raise the original exception
        with pytest.raises(Exception, match="API Error"):
            await strategy.download(url)


class TestTwitterDownloadStrategyConversion:
    """Test API response to MediaMetadata conversion."""

    @pytest.fixture
    def strategy(self):
        """TwitterDownloadStrategy instance."""
        settings = MagicMock()
        feature_flags = DownloadFeatureFlags(settings)
        return TwitterDownloadStrategy(feature_flags, Path("/tmp"))

    def test_convert_api_response_basic(self, strategy):
        """Test basic API response conversion."""
        api_response = {
            "title": "Test Tweet",
            "uploader": "test_user",
            "url": "https://example.com/media.jpg",
            "filename": "media.jpg",
            "filesize": 123456,
        }
        url = "https://twitter.com/test/status/123"

        result = strategy._convert_api_response_to_metadata(api_response, url)

        assert result.title == "Test Tweet"
        assert result.author == "test_user"
        assert result.uploader == "test_user"  # Should be synced
        assert result.filename == "media.jpg"
        assert result.filesize == 123456
        assert result.file_size == 123456  # Should be synced
        assert result.platform == "twitter"
        assert result.download_method == "api"

    def test_convert_api_response_with_dict_author(self, strategy):
        """Test API response conversion with dict author."""
        api_response = {
            "title": "Test Tweet",
            "user": {"screen_name": "test_user", "name": "Test User"},
            "filename": "media.jpg",
        }
        url = "https://twitter.com/test/status/123"

        result = strategy._convert_api_response_to_metadata(api_response, url)

        assert result.author == "test_user"
        assert result.uploader == "test_user"

    def test_convert_api_response_missing_filename(self, strategy):
        """Test API response conversion with missing filename."""
        api_response = {
            "title": "Test Tweet",
            "uploader": "test_user",
            "url": "https://example.com/path/media.jpg",
        }
        url = "https://twitter.com/test/status/123"

        result = strategy._convert_api_response_to_metadata(api_response, url)

        assert result.filename == "media.jpg"  # Extracted from URL

    def test_convert_api_response_all_fields(self, strategy):
        """Test API response conversion with all fields."""
        api_response = {
            "title": "Complete Tweet",
            "description": "Tweet description",
            "uploader": "complete_user",
            "upload_date": "20241214",
            "duration": 30.5,
            "view_count": 1000,
            "like_count": 50,
            "filename": "complete.mp4",
            "filesize": 5000000,
            "thumbnail": "https://example.com/thumb.jpg",
        }
        url = "https://twitter.com/test/status/123"

        result = strategy._convert_api_response_to_metadata(api_response, url)

        assert result.title == "Complete Tweet"
        assert result.description == "Tweet description"
        assert result.author == "complete_user"
        assert result.upload_date == "20241214"
        assert result.duration == 30.5
        assert result.view_count == 1000
        assert result.like_count == 50
        assert result.filename == "complete.mp4"
        assert result.filesize == 5000000
        assert result.thumbnail_url == "https://example.com/thumb.jpg"
        assert result.platform == "twitter"
        assert result.download_method == "api"
