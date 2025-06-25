"""Tests for AI Content Analyzer Agent functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
from typing import Dict, Any

from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse


class TestContentAnalyzer:
    """Test AI Content Analyzer Agent functionality."""

    @pytest.fixture
    def mock_content_analyzer(self, fixture_mock_llm_model, fixture_test_settings):
        """Create mock Content Analyzer agent for testing."""
        # This will fail initially (RED phase) until we implement ContentAnalyzer
        from boss_bot.ai.agents.content_analyzer import ContentAnalyzer

        return ContentAnalyzer(
            name="content_analyzer",
            model=fixture_mock_llm_model,
            system_prompt="You are an intelligent content analyzer for media downloads.",
            settings=fixture_test_settings
        )

    @pytest.mark.asyncio
    async def test_content_analyzer_creation(self, mock_content_analyzer):
        """Test ContentAnalyzer can be created with required parameters."""
        assert mock_content_analyzer.name == "content_analyzer"
        assert mock_content_analyzer.model is not None
        assert "intelligent content analyzer" in mock_content_analyzer.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_content_analyzer_analyzes_twitter_url(self, mock_content_analyzer, fixture_agent_context):
        """Test Content Analyzer analyzes Twitter content correctly."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_content",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "platform": "twitter",
                "content_type": "tweet"
            }
        )

        response = await mock_content_analyzer.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "twitter"
        assert response.result["content_type"] == "tweet"
        assert "quality_score" in response.result
        assert "media_detected" in response.result
        assert response.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_content_analyzer_handles_video_content(self, mock_content_analyzer, fixture_agent_context):
        """Test Content Analyzer handles video content analysis."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_content",
            data={
                "url": "https://youtube.com/watch?v=VIDEO_ID",
                "platform": "youtube",
                "content_type": "video"
            }
        )

        response = await mock_content_analyzer.process_request(request)

        assert response.success is True
        assert response.result["content_type"] == "video"
        assert "duration_estimate" in response.result
        assert "quality_recommendation" in response.result
        assert "format_suggestions" in response.result

    @pytest.mark.asyncio
    async def test_content_analyzer_quality_assessment(self, mock_content_analyzer, fixture_agent_context):
        """Test Content Analyzer provides quality assessment."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="assess_quality",
            data={
                "url": "https://reddit.com/r/pics/comments/abc123/title/",
                "metadata": {
                    "resolution": "1920x1080",
                    "file_size": "2.5MB",
                    "format": "jpg"
                }
            }
        )

        response = await mock_content_analyzer.process_request(request)

        assert response.success is True
        assert "quality_score" in response.result
        assert "recommendations" in response.result
        assert response.result["quality_score"] >= 0.0
        assert response.result["quality_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_content_analyzer_with_ai_disabled(self, fixture_mock_llm_model, fixture_agent_context):
        """Test Content Analyzer falls back when AI is disabled."""
        mock_settings = Mock()
        mock_settings.ai_content_analysis_enabled = False

        from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
        analyzer = ContentAnalyzer(
            name="content_analyzer",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt",
            settings=mock_settings
        )

        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_content",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "platform": "twitter"
            }
        )

        response = await analyzer.process_request(request)

        assert response.success is True
        assert "basic" in response.reasoning.lower()
        assert response.confidence <= 0.8

    @pytest.mark.asyncio
    async def test_content_analyzer_error_handling(self, mock_content_analyzer, fixture_agent_context):
        """Test Content Analyzer handles invalid requests gracefully."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_content",
            data={}  # Missing required URL
        )

        response = await mock_content_analyzer.process_request(request)

        assert response.success is False
        assert "invalid request" in response.error.lower()
        assert response.confidence == 0.0

    def test_content_analyzer_can_handle_actions(self, mock_content_analyzer):
        """Test Content Analyzer declares supported actions."""
        assert mock_content_analyzer.can_handle_action("analyze_content") is True
        assert mock_content_analyzer.can_handle_action("assess_quality") is True
        assert mock_content_analyzer.can_handle_action("invalid_action") is False

    @pytest.mark.asyncio
    async def test_content_analyzer_metadata_enrichment(self, mock_content_analyzer, fixture_agent_context):
        """Test Content Analyzer enriches metadata with AI insights."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="enrich_metadata",
            data={
                "url": "https://instagram.com/p/ABC123/",
                "platform": "instagram",
                "basic_metadata": {
                    "title": "Photo post",
                    "author": "user123"
                }
            }
        )

        response = await mock_content_analyzer.process_request(request)

        assert response.success is True
        assert "enriched_metadata" in response.result
        assert "ai_insights" in response.result
        assert "content_tags" in response.result

    @pytest.mark.asyncio
    async def test_content_analyzer_performance_tracking(self, mock_content_analyzer):
        """Test Content Analyzer tracks performance metrics."""
        initial_metrics = mock_content_analyzer.performance_metrics

        # Performance tracking should be inherited from BaseAgent
        assert "request_count" in initial_metrics
        assert "average_processing_time_ms" in initial_metrics
        assert initial_metrics["name"] == "content_analyzer"


class TestContentAnalysisIntegration:
    """Test Content Analyzer integration with strategy pattern."""

    @pytest.mark.asyncio
    async def test_content_analysis_in_download_flow(self, fixture_test_settings, fixture_agent_context):
        """Test Content Analyzer integration in download workflow."""
        # Create analyzer
        from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
        mock_model = AsyncMock()

        analyzer = ContentAnalyzer(
            name="content_analyzer",
            model=mock_model,
            system_prompt="Test prompt",
            settings=fixture_test_settings
        )

        # Simulate download workflow integration
        context = AgentContext(**fixture_agent_context)
        pre_download_request = AgentRequest(
            context=context,
            action="analyze_content",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "platform": "twitter",
                "download_intent": True
            }
        )

        response = await analyzer.process_request(pre_download_request)

        assert response.success is True
        assert "download_recommendation" in response.result
        assert "optimal_quality" in response.result

    @pytest.mark.asyncio
    async def test_content_analyzer_with_feature_flags(self, fixture_ai_feature_flags, fixture_agent_context):
        """Test Content Analyzer respects feature flags."""
        # Test with AI content analysis enabled
        mock_settings = Mock()
        mock_settings.ai_content_analysis_enabled = True

        from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
        mock_model = AsyncMock()

        analyzer = ContentAnalyzer(
            name="content_analyzer",
            model=mock_model,
            system_prompt="Test prompt",
            settings=mock_settings
        )

        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_content",
            data={
                "url": "https://youtube.com/watch?v=VIDEO_ID",
                "platform": "youtube"
            }
        )

        response = await analyzer.process_request(request)

        assert response.success is True
        assert response.metadata.get("ai_enhanced") is True
