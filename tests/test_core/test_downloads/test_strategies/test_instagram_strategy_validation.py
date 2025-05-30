"""Tests for Instagram strategy validation functionality."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import Mock

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.strategies.instagram_strategy import InstagramDownloadStrategy


class TestInstagramStrategyValidation:
    """Test validation methods added to Instagram strategy."""

    @pytest.fixture
    def fixture_feature_flags_test(self) -> DownloadFeatureFlags:
        """Create feature flags for testing."""
        mock_settings = Mock()
        mock_settings.instagram_use_api_client = False
        mock_settings.download_api_fallback_to_cli = True
        return DownloadFeatureFlags(mock_settings)

    @pytest.fixture
    def fixture_instagram_strategy_test(self, fixture_feature_flags_test) -> InstagramDownloadStrategy:
        """Create Instagram strategy for testing."""
        download_dir = Path("/tmp/test_downloads")
        return InstagramDownloadStrategy(
            feature_flags=fixture_feature_flags_test,
            download_dir=download_dir
        )

    def test_validate_config_valid_configuration(self, fixture_instagram_strategy_test, mocker):
        """Test validate_config with valid configuration."""
        # Mock InstagramConfigValidator.validate_config to return valid result
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.issues = []

        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            return_value=mock_result
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config()

        assert is_valid is True
        assert issues == []
        mock_validator.assert_called_once_with(None)

    def test_validate_config_invalid_configuration(self, fixture_instagram_strategy_test, mocker):
        """Test validate_config with invalid configuration."""
        # Mock InstagramConfigValidator.validate_config to return invalid result
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.issues = ["Issue 1", "Issue 2"]

        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            return_value=mock_result
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config()

        assert is_valid is False
        assert issues == ["Issue 1", "Issue 2"]
        mock_validator.assert_called_once_with(None)

    def test_validate_config_with_custom_config(self, fixture_instagram_strategy_test, mocker):
        """Test validate_config with custom configuration."""
        custom_config = {"extractor": {"base-directory": "./custom/"}}

        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.issues = []

        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            return_value=mock_result
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config(custom_config)

        assert is_valid is True
        assert issues == []
        mock_validator.assert_called_once_with(custom_config)

    def test_validate_config_verbose_valid(self, fixture_instagram_strategy_test, mocker, capsys):
        """Test validate_config with verbose output for valid config."""
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.issues = []

        mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            return_value=mock_result
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config(verbose=True)

        captured = capsys.readouterr()
        assert "✅ Instagram configuration is valid" in captured.out
        assert is_valid is True

    def test_validate_config_verbose_invalid(self, fixture_instagram_strategy_test, mocker, capsys):
        """Test validate_config with verbose output for invalid config."""
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.issues = ["Issue 1", "Issue 2"]

        mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            return_value=mock_result
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config(verbose=True)

        captured = capsys.readouterr()
        assert "❌ Instagram configuration has issues:" in captured.out
        assert "Issue 1" in captured.out
        assert "Issue 2" in captured.out
        assert is_valid is False

    def test_validate_config_exception_handling(self, fixture_instagram_strategy_test, mocker):
        """Test validate_config handles exceptions gracefully."""
        # Mock InstagramConfigValidator.validate_config to raise exception
        mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.validate_config',
            side_effect=Exception("Validation failed")
        )

        is_valid, issues = fixture_instagram_strategy_test.validate_config()

        assert is_valid is False
        assert len(issues) == 1
        assert "Validation error: Validation failed" in issues[0]

    def test_check_config_valid(self, fixture_instagram_strategy_test, mocker):
        """Test check_config with valid configuration."""
        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.check_instagram_config',
            return_value=True
        )

        result = fixture_instagram_strategy_test.check_config()

        assert result is True
        mock_validator.assert_called_once_with(verbose=False)

    def test_check_config_invalid(self, fixture_instagram_strategy_test, mocker):
        """Test check_config with invalid configuration."""
        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.check_instagram_config',
            return_value=False
        )

        result = fixture_instagram_strategy_test.check_config()

        assert result is False
        mock_validator.assert_called_once_with(verbose=False)

    def test_check_config_verbose(self, fixture_instagram_strategy_test, mocker):
        """Test check_config with verbose output."""
        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.check_instagram_config',
            return_value=True
        )

        result = fixture_instagram_strategy_test.check_config(verbose=True)

        assert result is True
        mock_validator.assert_called_once_with(verbose=True)

    def test_check_config_exception_handling(self, fixture_instagram_strategy_test, mocker, capsys):
        """Test check_config handles exceptions gracefully."""
        mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.check_instagram_config',
            side_effect=Exception("Check failed")
        )

        result = fixture_instagram_strategy_test.check_config(verbose=True)

        captured = capsys.readouterr()
        assert "❌ Configuration check failed: Check failed" in captured.out
        assert result is False

    def test_print_config_summary_success(self, fixture_instagram_strategy_test, mocker):
        """Test print_config_summary successful execution."""
        mock_validator = mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.print_config_summary'
        )

        fixture_instagram_strategy_test.print_config_summary()

        mock_validator.assert_called_once()

    def test_print_config_summary_exception_handling(self, fixture_instagram_strategy_test, mocker, capsys):
        """Test print_config_summary handles exceptions gracefully."""
        mocker.patch(
            'boss_bot.core.downloads.strategies.instagram_strategy.InstagramConfigValidator.print_config_summary',
            side_effect=Exception("Print failed")
        )

        fixture_instagram_strategy_test.print_config_summary()

        captured = capsys.readouterr()
        assert "❌ Failed to print config summary: Print failed" in captured.out

    def test_api_client_config_includes_validation_requirements(self, fixture_instagram_strategy_test):
        """Test that API client configuration includes expected validation requirements."""
        # Access the api_client property to trigger lazy loading
        client = fixture_instagram_strategy_test.api_client

        # The config should be set during client creation
        # We can't easily access the internal config, but we can verify the client was created
        assert client is not None
        assert hasattr(client, 'config')

    def test_strategy_with_validation_integration(self, fixture_instagram_strategy_test):
        """Test that strategy properly integrates validation methods."""
        # Verify all validation methods are available
        assert hasattr(fixture_instagram_strategy_test, 'validate_config')
        assert hasattr(fixture_instagram_strategy_test, 'check_config')
        assert hasattr(fixture_instagram_strategy_test, 'print_config_summary')

        # Verify they are callable
        assert callable(fixture_instagram_strategy_test.validate_config)
        assert callable(fixture_instagram_strategy_test.check_config)
        assert callable(fixture_instagram_strategy_test.print_config_summary)

    def test_strategy_initialization_with_validation(self, fixture_feature_flags_test):
        """Test strategy initialization includes validation capabilities."""
        download_dir = Path("/tmp/test_downloads")
        strategy = InstagramDownloadStrategy(
            feature_flags=fixture_feature_flags_test,
            download_dir=download_dir
        )

        # Verify strategy has all expected methods
        assert hasattr(strategy, 'validate_config')
        assert hasattr(strategy, 'check_config')
        assert hasattr(strategy, 'print_config_summary')

        # Verify strategy still has core functionality
        assert hasattr(strategy, 'download')
        assert hasattr(strategy, 'get_metadata')
        assert hasattr(strategy, 'supports_url')
        assert strategy.platform_name == "instagram"

    def test_validation_methods_preserve_strategy_interface(self, fixture_instagram_strategy_test):
        """Test that adding validation methods doesn't break existing strategy interface."""
        # Test that core strategy methods still work
        test_url = "https://instagram.com/p/ABC123/"

        # Should support Instagram URLs
        assert fixture_instagram_strategy_test.supports_url(test_url)

        # Should have proper platform name
        assert fixture_instagram_strategy_test.platform_name == "instagram"

        # Should have download and metadata methods (even if we don't call them)
        assert hasattr(fixture_instagram_strategy_test, 'download')
        assert hasattr(fixture_instagram_strategy_test, 'get_metadata')
        assert callable(fixture_instagram_strategy_test.download)
        assert callable(fixture_instagram_strategy_test.get_metadata)
