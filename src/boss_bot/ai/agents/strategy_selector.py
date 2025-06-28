"""AI Strategy Selector Agent for intelligent download strategy selection."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict

from boss_bot.ai.agents.base_agent import BaseAgent
from boss_bot.ai.agents.context import AgentRequest, AgentResponse

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

    from boss_bot.core.env import BossSettings

logger = logging.getLogger(__name__)


class StrategySelector(BaseAgent):
    """AI-enhanced strategy selection agent.

    This agent intelligently selects the optimal download strategy
    based on URL analysis, user preferences, and historical success data.
    """

    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        system_prompt: str,
        settings: BossSettings,
    ):
        """Initialize the Strategy Selector agent.

        Args:
            name: Agent name for identification
            model: Language model for AI processing
            system_prompt: System prompt defining agent behavior
            settings: Boss-Bot settings containing feature flags
        """
        super().__init__(name, model, system_prompt)
        self.settings = settings

    async def _process_request(self, request: AgentRequest) -> AgentResponse:
        """Process strategy selection request.

        Args:
            request: AgentRequest containing URL and user preferences

        Returns:
            AgentResponse with selected strategy and confidence score
        """
        if request.action != "select_strategy":
            return AgentResponse(
                success=False,
                error=f"Unsupported action: {request.action}",
                confidence=0.0,
                reasoning="StrategySelector only handles 'select_strategy' actions",
            )

        url = request.data.get("url")
        user_preferences = request.data.get("user_preferences", {})

        if not url:
            return AgentResponse(
                success=False,
                error="URL is required for strategy selection",
                confidence=0.0,
                reasoning="Missing URL in request data",
            )

        # Check if AI strategy selection is enabled
        if not getattr(self.settings, "ai_strategy_selection_enabled", False):
            return await self._traditional_strategy_selection(url, user_preferences)

        try:
            # AI-enhanced strategy selection
            return await self._ai_select_strategy(url, user_preferences)
        except Exception as e:
            logger.warning(f"AI strategy selection failed: {e}, using fallback")
            return await self._traditional_strategy_selection(url, user_preferences)

    async def _ai_select_strategy(self, url: str, user_preferences: dict) -> AgentResponse:
        """AI-enhanced strategy selection logic.

        Args:
            url: URL to analyze
            user_preferences: User preferences and settings

        Returns:
            AgentResponse with AI-selected strategy
        """
        # Analyze URL patterns and content
        platform = self._detect_platform(url)
        confidence_score = self._calculate_confidence(url, platform)

        if platform == "unsupported":
            return AgentResponse(
                success=False,
                error="Unsupported platform URL",
                confidence=0.0,
                reasoning="URL does not match any supported platform patterns",
            )

        # Build result with platform strategy and recommendations
        result = {
            "platform": platform,
            "recommended_options": self._get_platform_options(platform, user_preferences),
            "strategy_type": "ai_enhanced",
            "url_confidence": confidence_score,
        }

        reasoning = f"AI analysis identified {platform} platform with {confidence_score:.2f} confidence"

        return AgentResponse(
            success=True,
            result=result,
            confidence=confidence_score,
            reasoning=reasoning,
            metadata={"ai_enhanced": True, "platform": platform, "user_preferences_applied": bool(user_preferences)},
        )

    async def _traditional_strategy_selection(self, url: str, user_preferences: dict) -> AgentResponse:
        """Traditional pattern-based strategy selection.

        Args:
            url: URL to analyze
            user_preferences: User preferences (not used in traditional mode)

        Returns:
            AgentResponse with traditionally-selected strategy
        """
        platform = self._detect_platform(url)

        if platform == "unsupported":
            return AgentResponse(
                success=False,
                error="Unsupported platform URL",
                confidence=0.0,
                reasoning="URL does not match any supported platform patterns",
            )

        # Traditional selection has standard confidence based on pattern matching
        confidence_score = 0.7  # Fixed confidence for traditional pattern matching

        result = {
            "platform": platform,
            "recommended_options": {},
            "strategy_type": "traditional",
            "url_confidence": confidence_score,
        }

        reasoning = f"Traditional pattern matching identified {platform} platform"

        return AgentResponse(
            success=True,
            result=result,
            confidence=confidence_score,
            reasoning=reasoning,
            metadata={"ai_enhanced": False, "platform": platform, "fallback_used": True},
        )

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL patterns.

        Args:
            url: URL to analyze

        Returns:
            Platform name or 'unsupported'
        """
        url_lower = url.lower()

        # Twitter/X patterns
        if re.search(r"(twitter\.com|x\.com)", url_lower):
            return "twitter"

        # Reddit patterns
        if re.search(r"reddit\.com", url_lower):
            return "reddit"

        # YouTube patterns
        if re.search(r"(youtube\.com|youtu\.be)", url_lower):
            return "youtube"

        # Instagram patterns
        if re.search(r"instagram\.com", url_lower):
            return "instagram"

        return "unsupported"

    def _calculate_confidence(self, url: str, platform: str) -> float:
        """Calculate confidence score for platform detection.

        Args:
            url: Original URL
            platform: Detected platform

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if platform == "unsupported":
            return 0.0

        url_lower = url.lower()

        # High confidence patterns
        high_confidence_patterns = {
            "twitter": [r"twitter\.com/\w+/status/\d+", r"x\.com/\w+/status/\d+"],
            "reddit": [r"reddit\.com/r/\w+/comments/\w+"],
            "youtube": [r"youtube\.com/watch\?v=[\w-]+", r"youtu\.be/[\w-]+"],
            "instagram": [r"instagram\.com/p/[\w-]+"],
        }

        # Check for high-confidence patterns
        if platform in high_confidence_patterns:
            for pattern in high_confidence_patterns[platform]:
                if re.search(pattern, url_lower):
                    return 0.95

        # Medium confidence for basic domain match
        if platform in ["twitter", "reddit", "youtube", "instagram"]:
            return 0.85

        return 0.3

    def _get_platform_options(self, platform: str, user_preferences: dict) -> dict:
        """Get recommended options for platform based on user preferences.

        Args:
            platform: Target platform
            user_preferences: User preferences and settings

        Returns:
            Dictionary of recommended options
        """
        base_options = {}

        # Apply user preferences if available
        if user_preferences.get("quality"):
            base_options["quality"] = user_preferences["quality"]

        if user_preferences.get("format"):
            base_options["format"] = user_preferences["format"]

        # Platform-specific defaults
        if platform == "youtube":
            base_options.setdefault("quality", "best")
            base_options.setdefault("format", "mp4")
        elif platform == "twitter":
            base_options.setdefault("include_retweets", False)
        elif platform == "reddit":
            base_options.setdefault("include_comments", True)

        return base_options

    def can_handle_action(self, action: str) -> bool:
        """Check if this agent can handle a specific action.

        Args:
            action: Action name to check

        Returns:
            True if action is supported
        """
        return action == "select_strategy"

    def validate_request(self, request: AgentRequest) -> bool:
        """Validate strategy selection request.

        Args:
            request: AgentRequest to validate

        Returns:
            True if request is valid
        """
        if not super().validate_request(request):
            return False

        # Ensure required data fields exist
        if "url" not in request.data:
            return False

        return True
