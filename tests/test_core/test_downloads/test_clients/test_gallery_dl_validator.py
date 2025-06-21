"""Tests for gallery-dl configuration validation utilities."""

from __future__ import annotations

import pytest

from boss_bot.core.downloads.clients.config.gallery_dl_validator import (
    InstagramConfigValidator,
    ValidationResult,
    check_instagram_config,
    print_config_summary,
    validate_instagram_config,
)


class TestValidationResult:
    """Test ValidationResult namedtuple."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult instances."""
        result = ValidationResult(
            is_valid=True,
            issues=[],
            config_summary={"test": "value"}
        )

        assert result.is_valid is True
        assert result.issues == []
        assert result.config_summary == {"test": "value"}

    def test_validation_result_with_issues(self):
        """Test ValidationResult with validation issues."""
        issues = ["Issue 1", "Issue 2"]
        result = ValidationResult(
            is_valid=False,
            issues=issues,
            config_summary={"test": "value"}
        )

        assert result.is_valid is False
        assert result.issues == issues
        assert len(result.issues) == 2


class TestInstagramConfigValidator:
    """Test InstagramConfigValidator class."""

    def test_expected_config_structure(self):
        """Test that expected config has proper structure."""
        expected = InstagramConfigValidator.EXPECTED_CONFIG

        # Check that key paths exist
        assert ("extractor", "base-directory") in expected
        assert ("extractor", "instagram", "videos") in expected
        assert ("downloader", "retries") in expected
        assert ("output", "progress") in expected

        # Check some expected values
        assert expected[("extractor", "base-directory")] == "./downloads/"
        assert expected[("extractor", "instagram", "videos")] is True
        assert expected[("downloader", "retries")] == 4
        assert expected[("output", "progress")] is True

    def test_get_config_value_nested(self):
        """Test getting nested configuration values."""
        config = {
            "extractor": {
                "instagram": {
                    "videos": True,
                    "filename": "{username}_{shortcode}.{extension}"
                }
            }
        }

        # Test successful nested access
        result = InstagramConfigValidator._get_config_value(config, ("extractor", "instagram", "videos"))
        assert result is True

        result = InstagramConfigValidator._get_config_value(config, ("extractor", "instagram", "filename"))
        assert result == "{username}_{shortcode}.{extension}"

        # Test missing keys
        result = InstagramConfigValidator._get_config_value(config, ("extractor", "missing"))
        assert result is None

        result = InstagramConfigValidator._get_config_value(config, ("missing", "key"))
        assert result is None

    def test_get_config_value_empty_dict(self):
        """Test getting values from empty config."""
        config = {}

        result = InstagramConfigValidator._get_config_value(config, ("extractor", "instagram", "videos"))
        assert result is None

    def test_validate_config_perfect_match(self):
        """Test validation with perfect configuration."""
        # Create config that matches all expected values
        config = {}
        for path, expected_value in InstagramConfigValidator.EXPECTED_CONFIG.items():
            current = config
            for key in path[:-1]:
                current = current.setdefault(key, {})
            current[path[-1]] = expected_value

        result = InstagramConfigValidator.validate_config(config)

        assert result.is_valid is True
        assert result.issues == []
        assert len(result.config_summary) > 0

    def test_validate_config_with_issues(self):
        """Test validation with configuration issues."""
        config = {
            "extractor": {
                "base-directory": "./wrong/",  # Wrong value
                "instagram": {
                    "videos": False,  # Wrong value
                    "filename": "wrong_pattern"  # Wrong value
                }
            }
        }

        result = InstagramConfigValidator.validate_config(config)

        assert result.is_valid is False
        assert len(result.issues) > 0

        # Check that specific issues are found
        issues_text = " ".join(result.issues)
        assert "base-directory" in issues_text
        assert "videos" in issues_text
        assert "filename" in issues_text

    def test_validate_config_empty_config(self):
        """Test validation with empty configuration."""
        config = {}

        result = InstagramConfigValidator.validate_config(config)

        assert result.is_valid is False
        assert len(result.issues) > 0

        # Should have issues for all expected config values
        expected_issues = len(InstagramConfigValidator.EXPECTED_CONFIG)
        assert len(result.issues) == expected_issues

    def test_check_instagram_config_valid(self):
        """Test check_instagram_config with valid configuration."""
        # Create valid config
        config = {}
        for path, expected_value in InstagramConfigValidator.EXPECTED_CONFIG.items():
            current = config
            for key in path[:-1]:
                current = current.setdefault(key, {})
            current[path[-1]] = expected_value

        result = InstagramConfigValidator.check_instagram_config(config, verbose=False)
        assert result is True

    def test_check_instagram_config_invalid(self):
        """Test check_instagram_config with invalid configuration."""
        config = {
            "extractor": {
                "base-directory": "./wrong/"
            }
        }

        result = InstagramConfigValidator.check_instagram_config(config, verbose=False)
        assert result is False

    def test_check_instagram_config_verbose(self, caplog):
        """Test check_instagram_config with verbose output."""
        config = {
            "extractor": {
                "base-directory": "./downloads/",
                "instagram": {
                    "videos": True
                }
            }
        }

        with caplog.at_level("INFO"):
            InstagramConfigValidator.check_instagram_config(config, verbose=True)

        log_output = "\n".join(caplog.messages)
        # assert "Gallery-dl Config Validation for Instagram" in log_output
        # assert "Base Extractor Settings" in log_output
        # assert "Instagram-specific Settings" in log_output

    def test_print_config_summary(self, caplog):
        """Test print_config_summary function."""
        config = {
            "extractor": {
                "base-directory": "./downloads/",
                "archive": "./downloads/.archive.sqlite3",
                "instagram": {
                    "videos": True,
                    "include": "all",
                    "filename": "{username}_{shortcode}_{num}.{extension}",
                    "directory": ["instagram", "{username}"],
                    "sleep-request": 8.0
                }
            }
        }

        with caplog.at_level("INFO"):
            InstagramConfigValidator.print_config_summary(config)

        log_output = "\n".join(caplog.messages)
        # assert "Current Instagram Config Values:" in log_output
        # assert "Base directory:" in log_output
        # assert "Instagram videos:" in log_output

    def test_load_gallery_dl_config_import_error(self, mocker):
        """Test _load_gallery_dl_config when gallery-dl is not available."""
        # Mock the gallery_dl module to be None (simulating ImportError)
        mocker.patch('boss_bot.core.downloads.clients.config.gallery_dl_validator.gallery_dl', None)

        result = InstagramConfigValidator._load_gallery_dl_config()
        assert result == {}

    def test_load_gallery_dl_config_exception(self, mocker):
        """Test _load_gallery_dl_config when gallery-dl raises exception."""
        # Mock the import inside the method to raise an exception during config.load()
        mock_gdl_config = mocker.MagicMock()
        mock_gdl_config.load.side_effect = Exception("Config load failed")
        mock_gdl_config._config = None

        mocker.patch('gallery_dl.config', mock_gdl_config)
        result = InstagramConfigValidator._load_gallery_dl_config()
        assert result == {}


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_validate_instagram_config_function(self):
        """Test validate_instagram_config convenience function."""
        config = {
            "extractor": {
                "base-directory": "./wrong/"
            }
        }

        result = validate_instagram_config(config)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.issues) > 0

    def test_check_instagram_config_function(self):
        """Test check_instagram_config convenience function."""
        config = {
            "extractor": {
                "base-directory": "./wrong/"
            }
        }

        result = check_instagram_config(config, verbose=False)
        assert result is False

    def test_print_config_summary_function(self, caplog):
        """Test print_config_summary convenience function."""
        config = {
            "extractor": {
                "instagram": {
                    "videos": True
                }
            }
        }

        with caplog.at_level("INFO"):
            print_config_summary(config)

        log_output = "\n".join(caplog.messages)
        # assert "Current Instagram Config Values:" in log_output


class TestValidatorEdgeCases:
    """Test edge cases and error handling."""

    def test_get_config_value_non_dict(self):
        """Test _get_config_value with non-dict values in path."""
        config = {
            "extractor": "not_a_dict"
        }

        result = InstagramConfigValidator._get_config_value(config, ("extractor", "instagram"))
        assert result is None

    def test_validate_config_none_input(self):
        """Test validate_config with None input."""
        # This should load from gallery-dl, but if that fails, should return empty config validation
        result = InstagramConfigValidator.validate_config(None)

        assert isinstance(result, ValidationResult)
        # Result depends on whether gallery-dl is available and configured

    def test_check_config_with_exception_handling(self, mocker):
        """Test that check_instagram_config handles exceptions gracefully."""
        # Mock validate_config to raise an exception
        mocker.patch.object(
            InstagramConfigValidator,
            'validate_config',
            side_effect=Exception("Validation failed")
        )

        result = InstagramConfigValidator.check_instagram_config(verbose=False)
        assert result is False

    def test_array_value_validation(self):
        """Test validation of array values like directory patterns."""
        config = {
            "extractor": {
                "instagram": {
                    "directory": ["wrong", "pattern"]  # Should be ["instagram", "{username}"]
                }
            }
        }

        result = InstagramConfigValidator.validate_config(config)

        assert result.is_valid is False

        # Check that directory issue is found
        issues_text = " ".join(result.issues)
        assert "directory" in issues_text

    def test_float_value_validation(self):
        """Test validation of float values like sleep-request."""
        config = {
            "extractor": {
                "instagram": {
                    "sleep-request": 5.0  # Should be 8.0
                }
            }
        }

        result = InstagramConfigValidator.validate_config(config)

        assert result.is_valid is False

        # Check that sleep-request issue is found
        issues_text = " ".join(result.issues)
        assert "sleep-request" in issues_text
