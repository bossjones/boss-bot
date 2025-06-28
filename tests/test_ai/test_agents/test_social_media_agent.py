"""Tests for AI Social Media Agent functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
from typing import Dict, Any

from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse


class TestSocialMediaAgent:
    """Test AI Social Media Agent functionality."""

    @pytest.fixture
    def mock_social_media_agent(self, fixture_mock_llm_model, fixture_test_settings):
        """Create mock Social Media agent for testing."""
        # This will fail initially (RED phase) until we implement SocialMediaAgent
        from boss_bot.ai.agents.social_media_agent import SocialMediaAgent

        return SocialMediaAgent(
            name="social_media_agent",
            model=fixture_mock_llm_model,
            system_prompt="You are an intelligent social media content specialist.",
            settings=fixture_test_settings
        )

    @pytest.mark.asyncio
    async def test_social_media_agent_creation(self, mock_social_media_agent):
        """Test SocialMediaAgent can be created with required parameters."""
        assert mock_social_media_agent.name == "social_media_agent"
        assert mock_social_media_agent.model is not None
        assert "social media content specialist" in mock_social_media_agent.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_social_media_agent_extracts_twitter_content(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent extracts Twitter content effectively."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="extract_content",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "platform": "twitter",
                "content_type": "tweet"
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "twitter"
        assert "extracted_text" in response.result
        assert "hashtags" in response.result
        assert "mentions" in response.result
        assert "engagement_metrics" in response.result

    @pytest.mark.asyncio
    async def test_social_media_agent_processes_reddit_thread(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent processes Reddit thread content."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="extract_content",
            data={
                "url": "https://reddit.com/r/pics/comments/abc123/title/",
                "platform": "reddit",
                "content_type": "post"
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "reddit"
        assert "thread_title" in response.result
        assert "subreddit" in response.result
        assert "comment_analysis" in response.result

    @pytest.mark.asyncio
    async def test_social_media_agent_sentiment_analysis(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent performs sentiment analysis."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_sentiment",
            data={
                "content": "This is an amazing video! Love it so much!",
                "platform": "youtube",
                "context": "comment"
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert "sentiment_score" in response.result
        assert "sentiment_label" in response.result
        assert "confidence" in response.result
        assert response.result["sentiment_score"] >= -1.0
        assert response.result["sentiment_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_social_media_agent_engagement_optimization(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent provides engagement optimization."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="optimize_engagement",
            data={
                "platform": "instagram",
                "content_type": "post",
                "target_audience": "tech_enthusiasts",
                "posting_time": "2025-06-24T18:00:00Z"
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert "optimization_suggestions" in response.result
        assert "best_posting_time" in response.result
        assert "hashtag_recommendations" in response.result
        assert "engagement_prediction" in response.result

    @pytest.mark.asyncio
    async def test_social_media_agent_with_ai_disabled(self, fixture_mock_llm_model, fixture_agent_context):
        """Test Social Media Agent falls back when AI is disabled."""
        mock_settings = Mock()
        mock_settings.ai_content_analysis_enabled = False

        from boss_bot.ai.agents.social_media_agent import SocialMediaAgent
        agent = SocialMediaAgent(
            name="social_media_agent",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt",
            settings=mock_settings
        )

        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="extract_content",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "platform": "twitter"
            }
        )

        response = await agent.process_request(request)

        assert response.success is True
        assert "basic" in response.reasoning.lower()
        assert response.confidence <= 0.8

    @pytest.mark.asyncio
    async def test_social_media_agent_trend_analysis(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent analyzes trends and viral potential."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_trends",
            data={
                "platform": "twitter",
                "hashtags": ["#AI", "#tech", "#innovation"],
                "time_period": "last_24h"
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert "trending_topics" in response.result
        assert "viral_potential" in response.result
        assert "trend_score" in response.result

    @pytest.mark.asyncio
    async def test_social_media_agent_content_classification(self, mock_social_media_agent, fixture_agent_context):
        """Test Social Media Agent classifies content types."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="classify_content",
            data={
                "url": "https://youtube.com/watch?v=VIDEO_ID",
                "title": "Amazing AI Tutorial - Learn Machine Learning in 10 Minutes",
                "description": "Complete guide to machine learning basics..."
            }
        )

        response = await mock_social_media_agent.process_request(request)

        assert response.success is True
        assert "content_category" in response.result
        assert "topics" in response.result
        assert "educational_value" in response.result
        assert "target_demographics" in response.result

    def test_social_media_agent_can_handle_actions(self, mock_social_media_agent):
        """Test Social Media Agent declares supported actions."""
        assert mock_social_media_agent.can_handle_action("extract_content") is True
        assert mock_social_media_agent.can_handle_action("analyze_sentiment") is True
        assert mock_social_media_agent.can_handle_action("optimize_engagement") is True
        assert mock_social_media_agent.can_handle_action("analyze_trends") is True
        assert mock_social_media_agent.can_handle_action("classify_content") is True
        assert mock_social_media_agent.can_handle_action("invalid_action") is False

    @pytest.mark.asyncio
    async def test_social_media_agent_performance_tracking(self, mock_social_media_agent):
        """Test Social Media Agent tracks performance metrics."""
        initial_metrics = mock_social_media_agent.performance_metrics

        # Performance tracking should be inherited from BaseAgent
        assert "request_count" in initial_metrics
        assert "average_processing_time_ms" in initial_metrics
        assert initial_metrics["name"] == "social_media_agent"


class TestSocialMediaTeamIntegration:
    """Test Social Media Agent integration with team coordination."""

    @pytest.mark.asyncio
    async def test_social_media_agent_coordinates_with_content_analyzer(self, fixture_test_settings, fixture_agent_context):
        """Test Social Media Agent coordinates with Content Analyzer."""
        # Create social media agent
        from boss_bot.ai.agents.social_media_agent import SocialMediaAgent
        mock_model = AsyncMock()

        agent = SocialMediaAgent(
            name="social_media_agent",
            model=mock_model,
            system_prompt="Test prompt",
            settings=fixture_test_settings
        )

        # Simulate coordination request
        context = AgentContext(**fixture_agent_context)
        coordination_request = AgentRequest(
            context=context,
            action="coordinate_analysis",
            data={
                "url": "https://instagram.com/p/ABC123/",
                "collaboration_type": "content_quality_assessment",
                "partner_agent": "content_analyzer"
            }
        )

        response = await agent.process_request(coordination_request)

        assert response.success is True
        assert "coordination_plan" in response.result
        assert "social_context" in response.result

    @pytest.mark.asyncio
    async def test_social_media_agent_multi_platform_analysis(self, fixture_test_settings, fixture_agent_context):
        """Test Social Media Agent handles multi-platform content analysis."""
        from boss_bot.ai.agents.social_media_agent import SocialMediaAgent
        mock_model = AsyncMock()

        agent = SocialMediaAgent(
            name="social_media_agent",
            model=mock_model,
            system_prompt="Test prompt",
            settings=fixture_test_settings
        )

        # Simulate multi-platform analysis
        context = AgentContext(**fixture_agent_context)
        multi_platform_request = AgentRequest(
            context=context,
            action="analyze_cross_platform",
            data={
                "urls": [
                    "https://twitter.com/user/status/123",
                    "https://instagram.com/p/ABC123/",
                    "https://youtube.com/watch?v=VIDEO_ID"
                ],
                "analysis_type": "content_consistency"
            }
        )

        response = await agent.process_request(multi_platform_request)

        assert response.success is True
        assert "platform_comparison" in response.result
        assert "consistency_score" in response.result
        assert "recommendations" in response.result
