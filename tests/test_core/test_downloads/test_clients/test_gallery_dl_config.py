"""Tests for GalleryDLConfig pydantic models."""

import json
import pytest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import mock_open, patch

from boss_bot.core.downloads.clients.config.gallery_dl_config import GalleryDLConfig


class TestGalleryDLConfig:
    """Test GalleryDLConfig functionality."""

    @pytest.fixture
    def fixture_gallery_dl_conf_path(self) -> Path:
        """Path to the test fixture gallery_dl.conf file."""
        return Path(__file__).parent.parent.parent.parent / "fixtures" / "gallery_dl.conf"

    @pytest.fixture
    def expected_config_data(self) -> dict[str, Any]:
        """Expected configuration data from the fixture file."""
        return {
            "extractor": {
                "base-directory": "./gallery-dl/",
                "postprocessors": None,
                "archive": None,
                "cookies": None,
                "cookies-update": True,
                "proxy": None,
                "skip": True,
                "sleep": 0,
                "sleep-request": 0,
                "sleep-extractor": 0,
                "path-restrict": "auto",
                "path-replace": "_",
                "path-remove": "\\u0000-\\u001f\\u007f",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                "path-strip": "auto",
                "path-extended": True,
                "extension-map": {
                    "jpeg": "jpg",
                    "jpe": "jpg",
                    "jfif": "jpg",
                    "jif": "jpg",
                    "jfi": "jpg"
                },
                "instagram": {
                    "highlights": False,
                    "videos": True,
                    "include": "all",
                    "directory": ["Instagram", "{username}", "Posts"],
                    "stories": {"directory": ["Instagram", "{username}", "Stories"]},
                    "channel": {"directory": ["Instagram", "{username}", "IGTV"]},
                    "tagged": {"directory": ["Instagram", "{username}", "Tagged"]},
                    "reels": {"directory": ["Instagram", "{username}", "Reels"]},
                    "filename": "{username}_{num}.{extension}",
                    "date-format": "%Y-%m-%dT%H:%M:%S",
                    "cookies": "cookies.txt",
                    "username": "testuser",
                    "password": "testpass",
                    "sleep-request": 8.0
                },
                "twitter": {
                    "quoted": True,
                    "replies": True,
                    "retweets": True,
                    "twitpic": False,
                    "videos": True,
                    "cookies": None,
                    "filename": "{tweet_id}_{num}.{extension}"
                },
                "deviantart": {
                    "extra": False,
                    "flat": True,
                    "folders": False,
                    "journals": "html",
                    "mature": True,
                    "metadata": False,
                    "original": True,
                    "quality": 100,
                    "wait-min": 0
                },
                "pixiv": {
                    "username": None,
                    "password": None,
                    "avatar": False,
                    "ugoira": True
                },
                "reddit": {
                    "client-id": "test_client_id",
                    "user-agent": "Python:gdl:v1.0 (by /u/testuser)",
                    "browser": "firefox",
                    "refresh-token": None,
                    "comments": 0,
                    "morecomments": False,
                    "date-min": 0,
                    "date-max": 253402210800,
                    "date-format": "%Y-%m-%dT%H:%M:%S",
                    "id-min": None,
                    "id-max": None,
                    "recursion": 0,
                    "videos": True,
                    "parent-directory": True,
                    "directory": ["reddit", "{subreddit}"],
                    "filename": "{id}_{num}.{extension}"
                }
            },
            "downloader": {
                "filesize-min": None,
                "filesize-max": None,
                "part": True,
                "part-directory": None,
                "http": {
                    "adjust-extensions": True,
                    "mtime": True,
                    "rate": None,
                    "retries": 4,
                    "timeout": 30.0,
                    "verify": True
                },
                "ytdl": {
                    "format": None,
                    "forward-cookies": False,
                    "logging": True,
                    "mtime": True,
                    "outtmpl": None,
                    "rate": None,
                    "retries": 4,
                    "timeout": 30.0,
                    "verify": True
                }
            },
            "output": {
                "mode": "auto",
                "progress": True,
                "shorten": True,
                "log": "[{name}][{levelname}] {message}",
                "logfile": None,
                "unsupportedfile": None
            },
            "netrc": False
        }

    def test_from_file_with_override_config(self, fixture_gallery_dl_conf_path: Path, expected_config_data: dict[str, Any]):
        """Test loading configuration from a specific file using override_config parameter."""
        # Verify the fixture file exists
        assert fixture_gallery_dl_conf_path.exists(), f"Fixture file not found: {fixture_gallery_dl_conf_path}"

        # Load configuration from the fixture file
        config = GalleryDLConfig.from_file(override_config=fixture_gallery_dl_conf_path)

        # Verify the configuration was loaded correctly
        assert isinstance(config, GalleryDLConfig)

        # Convert to dict for easier comparison
        config_dict = config.to_dict()

        # Check main sections exist
        assert "extractor" in config_dict
        assert "downloader" in config_dict
        assert "output" in config_dict

        # Check some specific values from the extractor section
        extractor = config_dict["extractor"]
        assert extractor["base-directory"] == "./gallery-dl/"
        assert extractor["user-agent"] == "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"

        # Check for essential configuration that should be loaded
        assert "instagram" in extractor
        assert "twitter" in extractor
        assert "reddit" in extractor

        # Check Instagram configuration
        instagram = extractor.get("instagram", {})
        assert instagram["videos"] is True
        assert instagram["filename"] == "{username}_{num}.{extension}"

        # Check Twitter configuration
        twitter = extractor.get("twitter", {})
        assert twitter["quoted"] is True
        assert twitter["videos"] is True
        assert twitter["filename"] == "{tweet_id}_{num}.{extension}"

        # Check Reddit configuration
        reddit = extractor.get("reddit", {})
        # Note: The model expects SecretStr for client-id, so it might be filtered out
        assert reddit["user-agent"] == "Python:gdl:v1.0 (by /u/testuser)"
        assert reddit["videos"] is True

        # Check downloader configuration
        downloader = config_dict["downloader"]
        assert downloader["retries"] == 4
        assert downloader["timeout"] == 30.0

        # Check output configuration
        output = config_dict["output"]
        assert output["mode"] == "auto"
        assert output["progress"] is True

    def test_from_file_with_string_path(self, fixture_gallery_dl_conf_path: Path):
        """Test loading configuration using a string path."""
        config = GalleryDLConfig.from_file(override_config=str(fixture_gallery_dl_conf_path))

        assert isinstance(config, GalleryDLConfig)
        config_dict = config.to_dict()
        assert config_dict["extractor"]["base-directory"] == "./gallery-dl/"

    def test_from_file_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            GalleryDLConfig.from_file(override_config="/nonexistent/path/config.json")

    def test_from_file_invalid_json(self, tmp_path: Path):
        """Test that ValueError is raised for invalid JSON."""
        invalid_config = tmp_path / "invalid_config.json"
        invalid_config.write_text("{ invalid json ")

        with pytest.raises(ValueError, match="Invalid JSON in configuration file"):
            GalleryDLConfig.from_file(override_config=invalid_config)

    def test_from_file_empty_file(self, tmp_path: Path):
        """Test that empty files return default configuration."""
        empty_config = tmp_path / "empty_config.json"
        empty_config.write_text("")

        config = GalleryDLConfig.from_file(override_config=empty_config)

        # Should return default configuration
        assert isinstance(config, GalleryDLConfig)
        # Default base directory should be different from fixture
        assert config.extractor.base_directory == "./downloads/"

    def test_from_file_non_dict_json(self, tmp_path: Path):
        """Test that ValueError is raised for non-dict JSON."""
        array_config = tmp_path / "array_config.json"
        array_config.write_text('["not", "a", "dict"]')

        with pytest.raises(ValueError, match="Configuration must be a JSON object"):
            GalleryDLConfig.from_file(override_config=array_config)

    @patch("boss_bot.core.downloads.clients.aio_gallery_dl_utils.get_default_gallery_dl_config_locations")
    def test_from_file_default_search_found(self, mock_get_locations, fixture_gallery_dl_conf_path: Path):
        """Test loading from default locations when file is found."""
        # Mock the default locations to return our fixture path
        mock_get_locations.return_value = [fixture_gallery_dl_conf_path]

        config = GalleryDLConfig.from_file()

        assert isinstance(config, GalleryDLConfig)
        config_dict = config.to_dict()
        assert config_dict["extractor"]["base-directory"] == "./gallery-dl/"

    @patch("boss_bot.core.downloads.clients.aio_gallery_dl_utils.get_default_gallery_dl_config_locations")
    def test_from_file_default_search_not_found(self, mock_get_locations):
        """Test that default configuration is returned when no files found in default locations."""
        # Mock default locations to return non-existent paths
        mock_get_locations.return_value = [Path("/nonexistent1"), Path("/nonexistent2")]

        config = GalleryDLConfig.from_file()

        # Should return default configuration
        assert isinstance(config, GalleryDLConfig)
        assert config.extractor.base_directory == "./downloads/"  # Default value

    def test_from_dict_compatibility(self, expected_config_data: dict[str, Any]):
        """Test that from_file works with from_dict for the same data."""
        # Create config from dict
        config_from_dict = GalleryDLConfig.from_dict(expected_config_data)

        # Create config from file (which uses from_dict internally)
        fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / "gallery_dl.conf"
        config_from_file = GalleryDLConfig.from_file(override_config=fixture_path)

        # Both should produce equivalent configurations
        dict1 = config_from_dict.to_dict()
        dict2 = config_from_file.to_dict()

        # Compare key sections
        assert dict1["extractor"]["base-directory"] == dict2["extractor"]["base-directory"]
        assert dict1["output"]["mode"] == dict2["output"]["mode"]
