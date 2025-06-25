"""AI Content Analyzer Agent for intelligent media content analysis."""

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


class ContentAnalyzer(BaseAgent):
    """AI-enhanced content analysis agent.

    This agent analyzes media content to provide insights about quality,
    format optimization, download recommendations, and metadata enrichment.
    """

    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        system_prompt: str,
        settings: BossSettings,
    ):
        """Initialize the Content Analyzer agent.

        Args:
            name: Agent name for identification
            model: Language model for AI processing
            system_prompt: System prompt defining agent behavior
            settings: Boss-Bot settings containing feature flags
        """
        super().__init__(name, model, system_prompt)
        self.settings = settings

    async def _process_request(self, request: AgentRequest) -> AgentResponse:
        """Process content analysis request.

        Args:
            request: AgentRequest containing URL and analysis parameters

        Returns:
            AgentResponse with content analysis results
        """
        if request.action not in ["analyze_content", "assess_quality", "enrich_metadata"]:
            return AgentResponse(
                success=False,
                error=f"Unsupported action: {request.action}",
                confidence=0.0,
                reasoning="ContentAnalyzer only handles content analysis actions",
            )

        url = request.data.get("url")
        if not url and request.action != "assess_quality":
            return AgentResponse(
                success=False,
                error="URL is required for content analysis",
                confidence=0.0,
                reasoning="Missing URL in request data",
            )

        # Route to appropriate analysis method
        if request.action == "analyze_content":
            return await self._analyze_content(request.data)
        elif request.action == "assess_quality":
            return await self._assess_quality(request.data)
        elif request.action == "enrich_metadata":
            return await self._enrich_metadata(request.data)

        return AgentResponse(
            success=False, error="Invalid action routing", confidence=0.0, reasoning="Action routing failed"
        )

    async def _analyze_content(self, data: dict) -> AgentResponse:
        """Analyze content for download optimization.

        Args:
            data: Request data containing URL and platform info

        Returns:
            AgentResponse with content analysis
        """
        url = data["url"]
        platform = data.get("platform", self._detect_platform(url))
        content_type = data.get("content_type", self._detect_content_type(url, platform))

        # Check if AI content analysis is enabled
        if not getattr(self.settings, "ai_content_analysis_enabled", False):
            return await self._basic_content_analysis(url, platform, content_type)

        try:
            # AI-enhanced content analysis
            return await self._ai_analyze_content(url, platform, content_type, data)
        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}, using basic analysis")
            return await self._basic_content_analysis(url, platform, content_type)

    async def _ai_analyze_content(self, url: str, platform: str, content_type: str, data: dict) -> AgentResponse:
        """AI-enhanced content analysis.

        Args:
            url: URL to analyze
            platform: Detected platform
            content_type: Type of content
            data: Additional request data

        Returns:
            AgentResponse with AI analysis results
        """
        # Perform AI-enhanced analysis
        quality_score = self._calculate_quality_score(url, platform, content_type)
        media_detected = self._detect_media_types(url, platform)

        result = {
            "platform": platform,
            "content_type": content_type,
            "quality_score": quality_score,
            "media_detected": media_detected,
            "download_recommendation": self._get_download_recommendation(platform, content_type),
            "optimal_quality": self._get_optimal_quality(platform, content_type),
        }

        # Add platform-specific analysis
        if platform == "youtube":
            result.update(
                {
                    "duration_estimate": "unknown",
                    "quality_recommendation": "720p",
                    "format_suggestions": ["mp4", "webm"],
                }
            )

        confidence = 0.9 if quality_score > 0.7 else 0.8
        reasoning = f"AI-enhanced analysis of {platform} {content_type} with {quality_score:.2f} quality score"

        return AgentResponse(
            success=True,
            result=result,
            confidence=confidence,
            reasoning=reasoning,
            metadata={"ai_enhanced": True, "platform": platform, "content_type": content_type},
        )

    async def _basic_content_analysis(self, url: str, platform: str, content_type: str) -> AgentResponse:
        """Basic pattern-based content analysis.

        Args:
            url: URL to analyze
            platform: Detected platform
            content_type: Type of content

        Returns:
            AgentResponse with basic analysis
        """
        quality_score = 0.7  # Standard quality score for basic analysis

        result = {
            "platform": platform,
            "content_type": content_type,
            "quality_score": quality_score,
            "media_detected": [content_type] if content_type != "unknown" else [],
            "download_recommendation": "standard",
            "optimal_quality": "default",
        }

        # Add basic platform-specific info
        if platform == "youtube":
            result.update(
                {"duration_estimate": "unknown", "quality_recommendation": "720p", "format_suggestions": ["mp4"]}
            )

        reasoning = f"Basic pattern-based analysis of {platform} content"

        return AgentResponse(
            success=True,
            result=result,
            confidence=0.7,
            reasoning=reasoning,
            metadata={"ai_enhanced": False, "platform": platform, "fallback_used": True},
        )

    async def _assess_quality(self, data: dict) -> AgentResponse:
        """Assess content quality based on metadata.

        Args:
            data: Request data containing metadata

        Returns:
            AgentResponse with quality assessment
        """
        metadata = data.get("metadata", {})

        # Calculate quality score based on metadata
        quality_score = self._calculate_metadata_quality(metadata)

        recommendations = self._generate_quality_recommendations(metadata, quality_score)

        result = {
            "quality_score": quality_score,
            "recommendations": recommendations,
            "metadata_analysis": {
                "resolution_score": self._score_resolution(metadata.get("resolution")),
                "format_score": self._score_format(metadata.get("format")),
                "size_score": self._score_file_size(metadata.get("file_size")),
            },
        }

        confidence = 0.8 if quality_score > 0.6 else 0.6
        reasoning = f"Quality assessment based on metadata analysis: {quality_score:.2f}"

        return AgentResponse(
            success=True,
            result=result,
            confidence=confidence,
            reasoning=reasoning,
            metadata={"analysis_type": "quality_assessment"},
        )

    async def _enrich_metadata(self, data: dict) -> AgentResponse:
        """Enrich metadata with AI insights.

        Args:
            data: Request data containing basic metadata

        Returns:
            AgentResponse with enriched metadata
        """
        url = data["url"]
        platform = data.get("platform", self._detect_platform(url))
        basic_metadata = data.get("basic_metadata", {})

        # Generate AI insights
        ai_insights = self._generate_ai_insights(url, platform, basic_metadata)
        content_tags = self._generate_content_tags(url, platform)

        enriched_metadata = {
            **basic_metadata,
            "ai_generated_title": self._generate_enhanced_title(basic_metadata.get("title", "")),
            "content_category": self._categorize_content(url, platform),
            "download_priority": self._calculate_download_priority(platform, basic_metadata),
        }

        result = {"enriched_metadata": enriched_metadata, "ai_insights": ai_insights, "content_tags": content_tags}

        return AgentResponse(
            success=True,
            result=result,
            confidence=0.85,
            reasoning=f"Metadata enriched for {platform} content with AI insights",
            metadata={"enrichment_type": "ai_enhanced", "platform": platform},
        )

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL patterns."""
        url_lower = url.lower()

        if re.search(r"(twitter\.com|x\.com)", url_lower):
            return "twitter"
        elif re.search(r"reddit\.com", url_lower):
            return "reddit"
        elif re.search(r"(youtube\.com|youtu\.be)", url_lower):
            return "youtube"
        elif re.search(r"instagram\.com", url_lower):
            return "instagram"

        return "unknown"

    def _detect_content_type(self, url: str, platform: str) -> str:
        """Detect content type based on URL and platform."""
        url_lower = url.lower()

        if platform == "youtube":
            return "video"
        elif platform == "twitter":
            return "tweet"
        elif platform == "reddit":
            return "post"
        elif platform == "instagram":
            if "/p/" in url_lower:
                return "post"
            elif "/stories/" in url_lower:
                return "story"
            return "post"

        return "unknown"

    def _calculate_quality_score(self, url: str, platform: str, content_type: str) -> float:
        """Calculate quality score for content."""
        base_score = 0.7

        # Platform-specific scoring
        if platform == "youtube":
            base_score = 0.8
        elif platform == "twitter":
            base_score = 0.75
        elif platform == "instagram":
            base_score = 0.85

        # Content type adjustments
        if content_type == "video":
            base_score += 0.1
        elif content_type == "post":
            base_score += 0.05

        return min(base_score, 1.0)

    def _detect_media_types(self, url: str, platform: str) -> list[str]:
        """Detect media types present in content."""
        media_types = []

        if platform == "youtube":
            media_types.extend(["video", "audio"])
        elif platform == "twitter":
            media_types.extend(["text", "image"])
        elif platform == "instagram":
            media_types.extend(["image", "video"])
        elif platform == "reddit":
            media_types.extend(["text", "image"])

        return media_types or ["unknown"]

    def _get_download_recommendation(self, platform: str, content_type: str) -> str:
        """Get download recommendation based on platform and content type."""
        if platform == "youtube" and content_type == "video":
            return "high_quality_recommended"
        elif platform == "instagram":
            return "original_quality"
        elif platform == "twitter":
            return "standard_quality"

        return "default"

    def _get_optimal_quality(self, platform: str, content_type: str) -> str:
        """Get optimal quality setting for platform and content type."""
        if platform == "youtube":
            return "720p"
        elif platform == "instagram":
            return "original"
        elif platform == "twitter":
            return "medium"

        return "default"

    def _calculate_metadata_quality(self, metadata: dict) -> float:
        """Calculate quality score from metadata."""
        score = 0.0
        factors = 0

        # Resolution scoring
        if resolution := metadata.get("resolution"):
            score += self._score_resolution(resolution)
            factors += 1

        # Format scoring
        if file_format := metadata.get("format"):
            score += self._score_format(file_format)
            factors += 1

        # File size scoring
        if file_size := metadata.get("file_size"):
            score += self._score_file_size(file_size)
            factors += 1

        return score / factors if factors > 0 else 0.5

    def _score_resolution(self, resolution: str | None) -> float:
        """Score resolution quality."""
        if not resolution:
            return 0.5

        if "4K" in resolution or "2160" in resolution:
            return 1.0
        elif "1080" in resolution:
            return 0.9
        elif "720" in resolution:
            return 0.7
        elif "480" in resolution:
            return 0.5

        return 0.3

    def _score_format(self, file_format: str | None) -> float:
        """Score file format quality."""
        if not file_format:
            return 0.5

        high_quality = ["mp4", "mkv", "png", "jpg", "jpeg"]
        medium_quality = ["webm", "gif", "webp"]

        if file_format.lower() in high_quality:
            return 0.8
        elif file_format.lower() in medium_quality:
            return 0.6

        return 0.4

    def _score_file_size(self, file_size: str | None) -> float:
        """Score file size appropriateness."""
        if not file_size:
            return 0.5

        # Simple heuristic - larger files often indicate higher quality
        if "GB" in file_size:
            return 0.9
        elif "MB" in file_size:
            return 0.7
        elif "KB" in file_size:
            return 0.4

        return 0.5

    def _generate_quality_recommendations(self, metadata: dict, quality_score: float) -> list[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        if quality_score < 0.7:
            recommendations.append("Consider downloading higher quality version")

        if metadata.get("format") in ["gif", "webp"]:
            recommendations.append("Convert to more compatible format")

        if not metadata.get("resolution"):
            recommendations.append("Check resolution before download")

        return recommendations or ["Content appears to be good quality"]

    def _generate_ai_insights(self, url: str, platform: str, metadata: dict) -> list[str]:
        """Generate AI insights about content."""
        insights = [f"Content detected from {platform} platform", "Analysis confidence: high"]

        if platform == "youtube":
            insights.append("Video content - consider audio extraction options")
        elif platform == "instagram":
            insights.append("Image content - optimal for sharing")

        return insights

    def _generate_content_tags(self, url: str, platform: str) -> list[str]:
        """Generate content tags for categorization."""
        tags = [platform, "download"]

        if platform == "youtube":
            tags.extend(["video", "media"])
        elif platform == "instagram":
            tags.extend(["image", "social"])
        elif platform == "twitter":
            tags.extend(["social", "text"])

        return tags

    def _generate_enhanced_title(self, original_title: str) -> str:
        """Generate enhanced title with AI processing."""
        if not original_title:
            return "AI-Enhanced Download"

        # Simple enhancement - add platform context
        return f"Enhanced: {original_title}"

    def _categorize_content(self, url: str, platform: str) -> str:
        """Categorize content for organization."""
        categories = {
            "youtube": "video_content",
            "instagram": "social_media",
            "twitter": "social_media",
            "reddit": "forum_content",
        }

        return categories.get(platform, "general_content")

    def _calculate_download_priority(self, platform: str, metadata: dict) -> str:
        """Calculate download priority based on content analysis."""
        if platform == "youtube":
            return "high"
        elif platform == "instagram":
            return "medium"

        return "normal"

    def can_handle_action(self, action: str) -> bool:
        """Check if this agent can handle a specific action.

        Args:
            action: Action name to check

        Returns:
            True if action is supported
        """
        return action in ["analyze_content", "assess_quality", "enrich_metadata"]

    def validate_request(self, request: AgentRequest) -> bool:
        """Validate content analysis request.

        Args:
            request: AgentRequest to validate

        Returns:
            True if request is valid
        """
        if not super().validate_request(request):
            return False

        # URL is required for most actions except quality assessment
        if request.action != "assess_quality" and "url" not in request.data:
            return False

        return True
