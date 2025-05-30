"""Gallery-dl configuration validation utilities.

This module provides functions to validate gallery-dl configuration
for Instagram video downloads and other platform requirements.

Based on validation scripts from ai_docs/plans/incorporate_check_instagram.md
"""

from __future__ import annotations

import logging
from typing import Any, NamedTuple

# Try to import gallery_dl for testing purposes
try:
    import gallery_dl
except ImportError:
    gallery_dl = None

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of configuration validation."""

    is_valid: bool
    issues: list[str]
    config_summary: dict[str, Any]


class InstagramConfigValidator:
    """Validator for Instagram-specific gallery-dl configuration."""

    # Expected Instagram configuration values
    EXPECTED_CONFIG = {
        ("extractor", "base-directory"): "./downloads/",
        ("extractor", "archive"): "./downloads/.archive.sqlite3",
        ("extractor", "path-restrict"): "auto",
        ("extractor", "path-extended"): True,
        ("extractor", "instagram", "videos"): True,
        ("extractor", "instagram", "include"): "all",
        ("extractor", "instagram", "filename"): "{username}_{shortcode}_{num}.{extension}",
        ("extractor", "instagram", "directory"): ["instagram", "{username}"],
        ("extractor", "instagram", "sleep-request"): 8.0,
        ("downloader", "retries"): 4,
        ("downloader", "timeout"): 30.0,
        ("downloader", "part"): True,
        ("output", "progress"): True,
        ("output", "mode"): "auto",
    }

    @classmethod
    def validate_config(cls, config: dict[str, Any] | None = None) -> ValidationResult:
        """Validate gallery-dl config for Instagram video downloads.

        Args:
            config: Configuration dict to validate. If None, loads from gallery-dl.

        Returns:
            ValidationResult tuple with validation status, issues, and config summary
        """
        if config is None:
            config = cls._load_gallery_dl_config()

        issues = []
        config_summary = {}

        # Check each expected value
        for config_path, expected in cls.EXPECTED_CONFIG.items():
            actual = cls._get_config_value(config, config_path)
            config_summary[" -> ".join(config_path)] = actual

            if actual != expected:
                path_str = " -> ".join(config_path)
                issues.append(f"{path_str}: expected {expected}, got {actual}")

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            config_summary=config_summary,
        )

    @classmethod
    def check_instagram_config(cls, config: dict[str, Any] | None = None, verbose: bool = False) -> bool:
        """Check that gallery-dl config is properly set for Instagram video downloads.

        Args:
            config: Configuration dict to check. If None, loads from gallery-dl.
            verbose: If True, prints detailed configuration information

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if config is None:
                config = cls._load_gallery_dl_config()

            if verbose:
                logger.info("=== Gallery-dl Config Validation for Instagram ===")

            issues = []

            # Check base extractor settings
            if verbose:
                logger.info("📁 Base Extractor Settings:")

            base_dir = cls._get_config_value(config, ("extractor", "base-directory"))
            if verbose:
                logger.info(f"  base-directory: {base_dir}")
            if base_dir != "./downloads/":
                issues.append("base-directory should be './downloads/'")

            archive = cls._get_config_value(config, ("extractor", "archive"))
            if verbose:
                logger.info(f"  archive: {archive}")
            if archive != "./downloads/.archive.sqlite3":
                issues.append("archive should be './downloads/.archive.sqlite3'")

            user_agent = cls._get_config_value(config, ("extractor", "user-agent"))
            if verbose:
                logger.info(f"  user-agent: {user_agent}")
                logger.warning("  ⚠️  NOTE: Command line --user-agent 'Wget/1.21.1' will override this")

            path_restrict = cls._get_config_value(config, ("extractor", "path-restrict"))
            if verbose:
                logger.info(f"  path-restrict: {path_restrict}")
            if path_restrict != "auto":
                issues.append("path-restrict should be 'auto'")

            path_extended = cls._get_config_value(config, ("extractor", "path-extended"))
            if verbose:
                logger.info(f"  path-extended: {path_extended}")
            if not path_extended:
                issues.append("path-extended should be true")

            if verbose:
                logger.info("📷 Instagram-specific Settings:")

            # Check Instagram videos setting
            instagram_videos = cls._get_config_value(config, ("extractor", "instagram", "videos"))
            if verbose:
                logger.info(f"  videos: {instagram_videos}")
            if not instagram_videos:
                issues.append("Instagram videos should be enabled (true)")

            # Check Instagram include setting
            instagram_include = cls._get_config_value(config, ("extractor", "instagram", "include"))
            if verbose:
                logger.info(f"  include: {instagram_include}")
            if instagram_include != "all":
                issues.append("Instagram include should be 'all'")

            # Check Instagram filename pattern
            instagram_filename = cls._get_config_value(config, ("extractor", "instagram", "filename"))
            if verbose:
                logger.info(f"  filename: {instagram_filename}")
            expected_filename = "{username}_{shortcode}_{num}.{extension}"
            if instagram_filename != expected_filename:
                issues.append(f"Instagram filename should be '{expected_filename}'")

            # Check Instagram directory pattern
            instagram_directory = cls._get_config_value(config, ("extractor", "instagram", "directory"))
            if verbose:
                logger.info(f"  directory: {instagram_directory}")
            expected_directory = ["instagram", "{username}"]
            if instagram_directory != expected_directory:
                issues.append(f"Instagram directory should be {expected_directory}")

            # Check Instagram sleep setting
            instagram_sleep = cls._get_config_value(config, ("extractor", "instagram", "sleep-request"))
            if verbose:
                logger.info(f"  sleep-request: {instagram_sleep}")
            if instagram_sleep != 8.0:
                issues.append("Instagram sleep-request should be 8.0")

            if verbose:
                logger.info("⬇️ Downloader Settings:")

            # Check downloader retries
            dl_retries = cls._get_config_value(config, ("downloader", "retries"))
            if verbose:
                logger.info(f"  retries: {dl_retries}")
            if dl_retries != 4:
                issues.append("downloader retries should be 4")

            # Check downloader timeout
            dl_timeout = cls._get_config_value(config, ("downloader", "timeout"))
            if verbose:
                logger.info(f"  timeout: {dl_timeout}")
            if dl_timeout != 30.0:
                issues.append("downloader timeout should be 30.0")

            # Check part downloads
            dl_part = cls._get_config_value(config, ("downloader", "part"))
            if verbose:
                logger.info(f"  part: {dl_part}")
            if not dl_part:
                issues.append("downloader part should be true")

            if verbose:
                logger.info("📤 Output Settings:")

            # Check output progress
            output_progress = cls._get_config_value(config, ("output", "progress"))
            if verbose:
                logger.info(f"  progress: {output_progress}")
            if not output_progress:
                issues.append("output progress should be true")

            # Check output mode
            output_mode = cls._get_config_value(config, ("output", "mode"))
            if verbose:
                logger.info(f"  mode: {output_mode}")
            if output_mode != "auto":
                issues.append("output mode should be 'auto'")

            if verbose:
                logger.info("🍪 Cookie Settings:")

            # Check cookies setting (should be null since using --cookies-from-browser)
            cookies = cls._get_config_value(config, ("extractor", "cookies"))
            instagram_cookies = cls._get_config_value(config, ("extractor", "instagram", "cookies"))
            if verbose:
                logger.info(f"  global cookies: {cookies}")
                logger.info(f"  instagram cookies: {instagram_cookies}")
                logger.warning("  ⚠️  NOTE: Command line --cookies-from-browser Firefox will override these")

                logger.info("🔧 Command Line Overrides to Note:")
                logger.info("  --cookies-from-browser Firefox: Will load cookies from Firefox browser")
                logger.info("  --no-mtime: Will disable setting file modification times")
                logger.info("  --user-agent 'Wget/1.21.1': Will override config user-agent")
                logger.info("  -v: Verbose output")
                logger.info("  --write-info-json: Will write metadata JSON files")
                logger.info("  --write-metadata: Will write metadata to files")

            if issues:
                if verbose:
                    logger.error(f"❌ Found {len(issues)} configuration issues:")
                    for i, issue in enumerate(issues, 1):
                        logger.error(f"  {i}. {issue}")
                return False
            else:
                if verbose:
                    logger.info("✅ All Instagram configuration settings are correct!")
                return True
        except Exception as e:
            logger.error(f"Error checking Instagram config: {e}")
            return False

    @classmethod
    def print_config_summary(cls, config: dict[str, Any] | None = None) -> None:
        """Print a summary of current Instagram-related config values.

        Args:
            config: Configuration dict to summarize. If None, loads from gallery-dl.
        """
        if config is None:
            config = cls._load_gallery_dl_config()

        logger.info("Current Instagram Config Values:")
        logger.info(f"  Base directory: {cls._get_config_value(config, ('extractor', 'base-directory'))}")
        logger.info(f"  Archive: {cls._get_config_value(config, ('extractor', 'archive'))}")
        logger.info(f"  Instagram videos: {cls._get_config_value(config, ('extractor', 'instagram', 'videos'))}")
        logger.info(f"  Instagram include: {cls._get_config_value(config, ('extractor', 'instagram', 'include'))}")
        logger.info(f"  Instagram filename: {cls._get_config_value(config, ('extractor', 'instagram', 'filename'))}")
        logger.info(f"  Instagram directory: {cls._get_config_value(config, ('extractor', 'instagram', 'directory'))}")
        logger.info(f"  Sleep request: {cls._get_config_value(config, ('extractor', 'instagram', 'sleep-request'))}")

    @staticmethod
    def _load_gallery_dl_config() -> dict[str, Any]:
        """Load configuration from gallery-dl.

        Returns:
            Configuration dictionary from gallery-dl
        """
        try:
            if gallery_dl is None:
                raise ImportError("gallery-dl not available")

            from gallery_dl import config as gdl_config

            gdl_config.load()
            return gdl_config._config or {}
        except ImportError:
            logger.warning("gallery-dl not available for config loading")
            return {}
        except Exception as e:
            logger.warning(f"Failed to load gallery-dl config: {e}")
            return {}

    @staticmethod
    def _get_config_value(config: dict[str, Any], path: tuple[str, ...]) -> Any:
        """Get nested configuration value by path.

        Args:
            config: Configuration dictionary
            path: Tuple of keys to traverse

        Returns:
            Configuration value or None if not found
        """
        current = config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


def validate_instagram_config(config: dict[str, Any] | None = None) -> ValidationResult:
    """Validate gallery-dl config for Instagram video downloads.

    Args:
        config: Configuration dict to validate. If None, loads from gallery-dl.

    Returns:
        ValidationResult tuple with validation status, issues, and config summary
    """
    return InstagramConfigValidator.validate_config(config)


def check_instagram_config(config: dict[str, Any] | None = None, verbose: bool = False) -> bool:
    """Check that gallery-dl config is properly set for Instagram video downloads.

    Args:
        config: Configuration dict to check. If None, loads from gallery-dl.
        verbose: If True, prints detailed configuration information

    Returns:
        True if configuration is valid, False otherwise
    """
    return InstagramConfigValidator.check_instagram_config(config, verbose)


def print_config_summary(config: dict[str, Any] | None = None) -> None:
    """Print a summary of current Instagram-related config values.

    Args:
        config: Configuration dict to summarize. If None, loads from gallery-dl.
    """
    InstagramConfigValidator.print_config_summary(config)


# For backward compatibility and script-like usage
if __name__ == "__main__":
    result = validate_instagram_config()

    if result.is_valid:
        logger.info("✅ Instagram config validation passed!")
    else:
        logger.error("❌ Instagram config validation failed:")
        for issue in result.issues:
            logger.error(f"  - {issue}")

    logger.info("-" * 40)
    print_config_summary()
