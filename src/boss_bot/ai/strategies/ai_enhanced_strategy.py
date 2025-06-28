"""AI-enhanced wrapper for existing download strategies."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
    from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy
    from boss_bot.core.env import BossSettings

logger = logging.getLogger(__name__)


class AIEnhancedStrategy:
    """AI-enhanced wrapper for existing download strategies.

    This class wraps existing download strategies to provide AI-enhanced
    capabilities while maintaining full backward compatibility.
    """

    def __init__(self, base_strategy: BaseDownloadStrategy, settings: BossSettings):
        """Initialize AI-enhanced strategy wrapper.

        Args:
            base_strategy: The base strategy to enhance
            settings: Boss-Bot settings containing feature flags
        """
        self.base_strategy = base_strategy
        self.settings = settings

    @property
    def platform_name(self) -> str:
        """Get platform name from base strategy.

        Returns:
            Platform name (e.g., 'twitter', 'reddit')
        """
        return self.base_strategy.platform_name

    @property
    def download_dir(self) -> Path:
        """Get download directory from base strategy.

        Returns:
            Download directory path
        """
        return self.base_strategy.download_dir

    def supports_url(self, url: str) -> bool:
        """Check if strategy supports URL using base strategy.

        Args:
            url: URL to check

        Returns:
            True if URL is supported by base strategy
        """
        return self.base_strategy.supports_url(url)

    def enhanced_supports_url(self, url: str) -> dict:
        """AI-enhanced URL support detection with confidence scoring.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with supports, confidence, and reasoning
        """
        if not getattr(self.settings, "ai_strategy_selection_enabled", False):
            # Fall back to base strategy when AI disabled
            supports = self.base_strategy.supports_url(url)
            return {
                "supports": supports,
                "confidence": 0.7 if supports else 0.0,
                "reasoning": f"Traditional pattern matching for {self.platform_name}",
            }

        # AI-enhanced analysis
        base_supports = self.base_strategy.supports_url(url)

        if not base_supports:
            return {
                "supports": False,
                "confidence": 0.0,
                "reasoning": f"URL not supported by {self.platform_name} strategy",
            }

        # Enhanced confidence scoring based on URL patterns
        confidence = self._calculate_ai_confidence(url)

        return {
            "supports": True,
            "confidence": confidence,
            "reasoning": f"AI-enhanced analysis for {self.platform_name} with {confidence:.2f} confidence",
        }

    async def download(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Download using base strategy.

        Args:
            url: URL to download from
            **kwargs: Additional download options

        Returns:
            MediaMetadata object with download results
        """
        return await self.base_strategy.download(url, **kwargs)

    async def get_metadata(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Get metadata using base strategy.

        Args:
            url: URL to get metadata from
            **kwargs: Additional metadata options

        Returns:
            MediaMetadata object with metadata
        """
        return await self.base_strategy.get_metadata(url, **kwargs)

    def _calculate_ai_confidence(self, url: str) -> float:
        """Calculate AI confidence score for URL support.

        Args:
            url: URL to analyze

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Simple heuristic-based confidence calculation
        # In a real implementation, this would use AI analysis

        url_lower = url.lower()
        platform = self.platform_name.lower()

        # Check for high-confidence patterns
        if platform == "twitter":
            if "/status/" in url_lower:
                return 0.95
            elif "twitter.com" in url_lower or "x.com" in url_lower:
                return 0.85
        elif platform == "reddit":
            if "/comments/" in url_lower:
                return 0.95
            elif "reddit.com" in url_lower:
                return 0.85
        elif platform == "youtube":
            if "watch?v=" in url_lower or "youtu.be/" in url_lower:
                return 0.95
            elif "youtube.com" in url_lower:
                return 0.85
        elif platform == "instagram":
            if "/p/" in url_lower:
                return 0.95
            elif "instagram.com" in url_lower:
                return 0.85

        # Default confidence for supported URLs
        return 0.7

    def __repr__(self) -> str:
        """String representation."""
        ai_status = "AI-enhanced" if getattr(self.settings, "ai_strategy_selection_enabled", False) else "Traditional"
        return f"AIEnhancedStrategy({self.base_strategy!r}, mode={ai_status})"
