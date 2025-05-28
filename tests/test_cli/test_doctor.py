"""Tests for the bossctl doctor command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from boss_bot.cli.main import APP, _check_gallery_dl_config


class TestDoctorCommand:
    """Test cases for the doctor command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_doctor_command_with_valid_config(self, tmp_path, monkeypatch):
        """Test doctor command with valid gallery-dl config."""
        # Copy the valid fixture to a temp location
        config_path = tmp_path / "gallery-dl.conf"
        fixture_config = self.fixtures_dir / "gallery_dl.conf"
        config_path.write_text(fixture_config.read_text())

        # Mock the config search paths to include our temp file
        with patch("boss_bot.cli.main._check_gallery_dl_config") as mock_check:
            mock_check.return_value = True

            result = self.runner.invoke(APP, ["doctor"])

            assert result.exit_code == 0
            assert "BossBot Doctor - Health Check" in result.stdout
            assert "Gallery-dl Configuration Validation" in result.stdout
            assert "All health checks passed!" in result.stdout

    def test_doctor_command_with_no_config(self, tmp_path, monkeypatch):
        """Test doctor command when no gallery-dl config is found."""
        # Mock the config search to return False (no config found)
        with patch("boss_bot.cli.main._check_gallery_dl_config") as mock_check:
            mock_check.return_value = False

            result = self.runner.invoke(APP, ["doctor"])

            assert result.exit_code == 1
            assert "BossBot Doctor - Health Check" in result.stdout
            assert "Gallery-dl Configuration Validation" in result.stdout
            assert "Some health checks failed" in result.stdout

    def test_check_gallery_dl_config_with_valid_fixture(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with valid fixture."""
        # Copy the valid fixture to the current working directory
        config_path = tmp_path / "gallery-dl.conf"
        fixture_config = self.fixtures_dir / "gallery_dl.conf"
        config_path.write_text(fixture_config.read_text())

        # Change to the temp directory so the config is found
        monkeypatch.chdir(tmp_path)

        result = _check_gallery_dl_config()
        assert result is True

    def test_check_gallery_dl_config_with_sample_fixture(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with sample fixture."""
        # Copy the sample fixture to the current working directory
        config_path = tmp_path / "gallery-dl.conf"
        fixture_config = self.fixtures_dir / "sample_gallery_dl.conf"
        config_path.write_text(fixture_config.read_text())

        # Change to the temp directory so the config is found
        monkeypatch.chdir(tmp_path)

        result = _check_gallery_dl_config()
        assert result is True

    def test_check_gallery_dl_config_with_invalid_json(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with invalid JSON."""
        # Create an invalid JSON config
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text('{"extractor": {"incomplete": json}')

        # Mock the config search paths to only look in the temp directory
        mock_paths = [config_path]
        with patch("boss_bot.cli.main.Path.cwd") as mock_cwd, \
             patch("boss_bot.cli.main.Path.home") as mock_home:
            mock_cwd.return_value = tmp_path
            mock_home.return_value = tmp_path / "nonexistent_home"

            result = _check_gallery_dl_config()
            assert result is False

    def test_check_gallery_dl_config_with_empty_file(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with empty config file."""
        # Create an empty config file
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text("")

        # Mock the config search paths to only look in the temp directory
        with patch("boss_bot.cli.main.Path.cwd") as mock_cwd, \
             patch("boss_bot.cli.main.Path.home") as mock_home:
            mock_cwd.return_value = tmp_path
            mock_home.return_value = tmp_path / "nonexistent_home"

            result = _check_gallery_dl_config()
            assert result is False

    def test_check_gallery_dl_config_with_non_object_json(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with non-object JSON."""
        # Create a JSON array instead of object
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text('["not", "an", "object"]')

        # Mock the config search paths to only look in the temp directory
        with patch("boss_bot.cli.main.Path.cwd") as mock_cwd, \
             patch("boss_bot.cli.main.Path.home") as mock_home:
            mock_cwd.return_value = tmp_path
            mock_home.return_value = tmp_path / "nonexistent_home"

            result = _check_gallery_dl_config()
            assert result is False

    def test_check_gallery_dl_config_with_minimal_valid_config(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with minimal valid config."""
        # Create a minimal but valid config
        minimal_config = {
            "extractor": {
                "base-directory": "./downloads/"
            }
        }
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text(json.dumps(minimal_config))

        # Change to the temp directory so the config is found
        monkeypatch.chdir(tmp_path)

        result = _check_gallery_dl_config()
        assert result is True

    def test_check_gallery_dl_config_no_extractor_section(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with config lacking common sections."""
        # Create a config without common sections
        config_without_sections = {
            "some_custom_section": {
                "custom_value": "test"
            }
        }
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text(json.dumps(config_without_sections))

        # Change to the temp directory so the config is found
        monkeypatch.chdir(tmp_path)

        # This should still return True (valid JSON) but with warnings
        result = _check_gallery_dl_config()
        assert result is True

    def test_check_gallery_dl_config_no_config_found(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function when no config file exists."""
        # Mock the config search paths to only look in empty temp directory
        with patch("boss_bot.cli.main.Path.cwd") as mock_cwd, \
             patch("boss_bot.cli.main.Path.home") as mock_home:
            mock_cwd.return_value = tmp_path
            mock_home.return_value = tmp_path / "nonexistent_home"

            result = _check_gallery_dl_config()
            assert result is False

    def test_check_gallery_dl_config_with_extractor_config(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with extractor configuration."""
        # Create a config with extractor settings
        config_with_extractors = {
            "extractor": {
                "base-directory": "./downloads/",
                "twitter": {
                    "videos": True,
                    "retweets": False
                },
                "reddit": {
                    "comments": 0,
                    "videos": True
                }
            }
        }
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text(json.dumps(config_with_extractors))

        # Change to the temp directory so the config is found
        monkeypatch.chdir(tmp_path)

        result = _check_gallery_dl_config()
        assert result is True

    def test_check_gallery_dl_config_file_read_error(self, tmp_path, monkeypatch):
        """Test _check_gallery_dl_config function with file read error."""
        # Create a config file with restricted permissions (only works on Unix-like systems)
        config_path = tmp_path / "gallery-dl.conf"
        config_path.write_text('{"extractor": {}}')

        # Try to make file unreadable (may not work on all systems)
        try:
            config_path.chmod(0o000)

            # Mock the config search paths to only look in the temp directory
            with patch("boss_bot.cli.main.Path.cwd") as mock_cwd, \
                 patch("boss_bot.cli.main.Path.home") as mock_home:
                mock_cwd.return_value = tmp_path
                mock_home.return_value = tmp_path / "nonexistent_home"

                result = _check_gallery_dl_config()
                # Should return False due to read error
                assert result is False

            # Restore permissions for cleanup
            config_path.chmod(0o644)
        except (OSError, PermissionError):
            # Skip this test if we can't change permissions
            pytest.skip("Cannot change file permissions on this system")

    def test_doctor_command_integration_with_fixtures(self, tmp_path, monkeypatch):
        """Integration test using both fixture files."""
        # Test with the main fixture
        config_path = tmp_path / "gallery-dl.conf"
        fixture_config = self.fixtures_dir / "gallery_dl.conf"
        config_path.write_text(fixture_config.read_text())

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Run the actual doctor command
        result = self.runner.invoke(APP, ["doctor"])

        assert result.exit_code == 0
        assert "Found config:" in result.stdout
        assert "Valid JSON configuration:" in result.stdout
        assert "Configured extractors:" in result.stdout
        assert "All health checks passed!" in result.stdout

    def test_doctor_command_shows_check_summary(self, tmp_path, monkeypatch):
        """Test that doctor command shows proper check summary."""
        # Use the sample fixture
        config_path = tmp_path / "gallery-dl.conf"
        fixture_config = self.fixtures_dir / "sample_gallery_dl.conf"
        config_path.write_text(fixture_config.read_text())

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = self.runner.invoke(APP, ["doctor"])

        assert result.exit_code == 0
        assert "Health Check Summary" in result.stdout
        assert "Checks passed: 1/1" in result.stdout
        assert "Your repository is ready to work properly" in result.stdout
