"""Feature flags for download implementations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boss_bot.core.env import BossSettings

logger = logging.getLogger(__name__)


class DownloadFeatureFlags:
    """Feature flags for download implementations.

    This class provides a centralized way to control which download
    implementation (CLI vs API) is used for each platform.
    """

    def __init__(self, settings: BossSettings):
        """Initialize feature flags with settings.

        Args:
            settings: BossSettings instance with configuration
        """
        self.settings = settings

    @property
    def use_api_twitter(self) -> bool:
        """Use API-direct approach for Twitter downloads.

        Returns:
            True if API-direct Twitter downloads are enabled
        """
        return getattr(self.settings, "twitter_use_api_client", False)

    @property
    def use_api_reddit(self) -> bool:
        """Use API-direct approach for Reddit downloads.

        Returns:
            True if API-direct Reddit downloads are enabled
        """
        return getattr(self.settings, "reddit_use_api_client", False)

    @property
    def use_api_youtube(self) -> bool:
        """Use API-direct approach for YouTube downloads.

        Returns:
            True if API-direct YouTube downloads are enabled
        """
        return getattr(self.settings, "youtube_use_api_client", False)

    @property
    def use_api_instagram(self) -> bool:
        """Use API-direct approach for Instagram downloads.

        Returns:
            True if API-direct Instagram downloads are enabled
        """
        return getattr(self.settings, "instagram_use_api_client", False)

    @property
    def api_fallback_to_cli(self) -> bool:
        """Fallback to CLI if API fails.

        Returns:
            True if API failures should fallback to CLI approach
        """
        return getattr(self.settings, "download_api_fallback_to_cli", True)

    def is_api_enabled_for_platform(self, platform: str) -> bool:
        """Check if API is enabled for a specific platform.

        Args:
            platform: Platform name (e.g., 'twitter', 'reddit', 'youtube')

        Returns:
            True if API is enabled for the platform
        """
        platform_lower = platform.lower()

        if platform_lower == "twitter":
            return self.use_api_twitter
        elif platform_lower == "reddit":
            return self.use_api_reddit
        elif platform_lower == "youtube":
            return self.use_api_youtube
        elif platform_lower == "instagram":
            return self.use_api_instagram
        else:
            logger.warning(f"Unknown platform for API check: {platform}")
            return False

    def get_strategy_info(self) -> dict[str, bool]:
        """Get current strategy configuration.

        Returns:
            Dictionary with current feature flag states
        """
        return {
            "twitter_api": self.use_api_twitter,
            "reddit_api": self.use_api_reddit,
            "youtube_api": self.use_api_youtube,
            "instagram_api": self.use_api_instagram,
            "api_fallback": self.api_fallback_to_cli,
        }

    def __repr__(self) -> str:
        """String representation."""
        info = self.get_strategy_info()
        enabled_apis = [k for k, v in info.items() if v and k != "api_fallback"]
        return f"DownloadFeatureFlags(enabled_apis={enabled_apis}, fallback={info['api_fallback']})"
