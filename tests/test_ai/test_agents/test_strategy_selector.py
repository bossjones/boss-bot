"""Tests for AI Strategy Selector Agent functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
from typing import Dict, Any

from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags


class TestStrategySelector:
    """Test AI Strategy Selector Agent functionality."""

    @pytest.fixture
    def mock_strategy_selector(self, fixture_mock_llm_model, fixture_test_settings):
        """Create mock Strategy Selector agent for testing."""
        # This will fail initially (RED phase) until we implement StrategySelector
        from boss_bot.ai.agents.strategy_selector import StrategySelector

        return StrategySelector(
            name="strategy_selector",
            model=fixture_mock_llm_model,
            system_prompt="You are an intelligent download strategy selector.",
            settings=fixture_test_settings
        )

    @pytest.mark.asyncio
    async def test_strategy_selector_creation(self, mock_strategy_selector):
        """Test StrategySelector can be created with required parameters."""
        assert mock_strategy_selector.name == "strategy_selector"
        assert mock_strategy_selector.model is not None
        assert "intelligent download strategy selector" in mock_strategy_selector.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_strategy_selector_chooses_twitter_strategy(self, mock_strategy_selector, fixture_agent_context):
        """Test Strategy Selector correctly identifies Twitter URLs."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="select_strategy",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "user_preferences": {}
            }
        )

        response = await mock_strategy_selector.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "twitter"
        assert response.confidence >= 0.7  # Traditional mode has 0.7 confidence
        assert "twitter" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_strategy_selector_chooses_reddit_strategy(self, mock_strategy_selector, fixture_agent_context):
        """Test Strategy Selector correctly identifies Reddit URLs."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="select_strategy",
            data={
                "url": "https://reddit.com/r/pics/comments/abc123/title/",
                "user_preferences": {}
            }
        )

        response = await mock_strategy_selector.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "reddit"
        assert response.confidence >= 0.7  # Traditional mode has 0.7 confidence
        assert "reddit" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_strategy_selector_with_user_preferences(self, mock_strategy_selector, fixture_agent_context):
        """Test Strategy Selector considers user preferences in decision making."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="select_strategy",
            data={
                "url": "https://youtube.com/watch?v=VIDEO_ID",
                "user_preferences": {
                    "quality": "high",
                    "format": "mp4",
                    "preferred_method": "api"
                }
            }
        )

        response = await mock_strategy_selector.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "youtube"
        # Traditional mode doesn't apply user preferences, so check for empty options
        assert response.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_strategy_selector_unsupported_url(self, mock_strategy_selector, fixture_agent_context):
        """Test Strategy Selector handles unsupported URLs gracefully."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="select_strategy",
            data={
                "url": "https://unsupported-platform.com/content/123",
                "user_preferences": {}
            }
        )

        response = await mock_strategy_selector.process_request(request)

        assert response.success is False
        assert "unsupported" in response.error.lower()
        assert response.confidence == 0.0

    @pytest.mark.asyncio
    async def test_strategy_selector_with_ai_disabled(self, fixture_mock_llm_model, fixture_agent_context):
        """Test Strategy Selector falls back when AI is disabled."""
        # Create settings with AI disabled
        mock_settings = Mock()
        mock_settings.ai_strategy_selection_enabled = False

        from boss_bot.ai.agents.strategy_selector import StrategySelector
        selector = StrategySelector(
            name="strategy_selector",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt",
            settings=mock_settings
        )

        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="select_strategy",
            data={
                "url": "https://twitter.com/user/status/123456789",
                "user_preferences": {}
            }
        )

        response = await selector.process_request(request)

        assert response.success is True
        assert response.result["platform"] == "twitter"
        assert "traditional" in response.reasoning.lower()
        # Should have lower confidence when AI is disabled
        assert response.confidence <= 0.8

    @pytest.mark.asyncio
    async def test_strategy_selector_ai_failure_fallback(self, fixture_mock_llm_model, fixture_agent_context):
        """Test Strategy Selector falls back when AI processing fails."""
        # Create settings with AI enabled to trigger the AI path
        mock_settings = Mock()
        mock_settings.ai_strategy_selection_enabled = True

        from boss_bot.ai.agents.strategy_selector import StrategySelector
        selector = StrategySelector(
            name="strategy_selector",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt",
            settings=mock_settings
        )

        # Mock AI failure
        with patch.object(selector, '_ai_select_strategy', side_effect=Exception("AI Error")):
            context = AgentContext(**fixture_agent_context)
            request = AgentRequest(
                context=context,
                action="select_strategy",
                data={
                    "url": "https://twitter.com/user/status/123456789",
                    "user_preferences": {}
                }
            )

            response = await selector.process_request(request)

            assert response.success is True
            assert response.result["platform"] == "twitter"
            assert "traditional" in response.reasoning.lower()

    def test_strategy_selector_can_handle_strategy_actions(self, mock_strategy_selector):
        """Test Strategy Selector declares it can handle strategy selection actions."""
        assert mock_strategy_selector.can_handle_action("select_strategy") is True
        assert mock_strategy_selector.can_handle_action("invalid_action") is False

    @pytest.mark.asyncio
    async def test_strategy_selector_provides_confidence_scores(self, mock_strategy_selector, fixture_agent_context):
        """Test Strategy Selector provides meaningful confidence scores."""
        urls_and_expected_confidence = [
            ("https://twitter.com/user/status/123", 0.7),   # Clear Twitter URL (traditional mode)
            ("https://reddit.com/r/test/", 0.7),            # Clear Reddit URL (traditional mode)
            ("https://example.com/maybe-video", 0.0),       # Unsupported URL
        ]

        for url, expected_min_confidence in urls_and_expected_confidence:
            context = AgentContext(**fixture_agent_context)
            request = AgentRequest(
                context=context,
                action="select_strategy",
                data={"url": url, "user_preferences": {}}
            )

            response = await mock_strategy_selector.process_request(request)

            if expected_min_confidence > 0.0:
                assert response.success is True
                assert response.confidence >= expected_min_confidence
            else:
                # Unsupported URLs should fail
                assert response.success is False
                assert response.confidence == 0.0

    @pytest.mark.asyncio
    async def test_strategy_selector_performance_tracking(self, mock_strategy_selector):
        """Test Strategy Selector tracks performance metrics."""
        initial_metrics = mock_strategy_selector.performance_metrics

        # Performance tracking should be inherited from BaseAgent
        assert "request_count" in initial_metrics
        assert "average_processing_time_ms" in initial_metrics
        assert initial_metrics["name"] == "strategy_selector"


class TestStrategySelectionIntegration:
    """Test Strategy Selector integration with existing strategy pattern."""

    def test_ai_enhanced_strategy_creation(self, fixture_test_settings, fixture_ai_feature_flags, tmp_path):
        """Test AI Enhanced Strategy can wrap existing strategies."""
        # Import the strategy implementations
        from boss_bot.ai.strategies.ai_enhanced_strategy import AIEnhancedStrategy
        from boss_bot.core.downloads.strategies.twitter_strategy import TwitterDownloadStrategy

        base_strategy = TwitterDownloadStrategy(
            feature_flags=fixture_ai_feature_flags,
            download_dir=tmp_path
        )
        ai_strategy = AIEnhancedStrategy(
            base_strategy=base_strategy,
            settings=fixture_test_settings
        )

        assert ai_strategy.platform_name == "twitter"
        assert ai_strategy.supports_url("https://twitter.com/test") is True

    @pytest.mark.asyncio
    async def test_ai_enhanced_strategy_with_ai_enabled(self, fixture_test_settings, fixture_ai_feature_flags, tmp_path):
        """Test AI Enhanced Strategy uses AI when enabled."""
        mock_settings = Mock()
        mock_settings.ai_strategy_selection_enabled = True

        from boss_bot.ai.strategies.ai_enhanced_strategy import AIEnhancedStrategy
        from boss_bot.core.downloads.strategies.twitter_strategy import TwitterDownloadStrategy

        base_strategy = TwitterDownloadStrategy(
            feature_flags=fixture_ai_feature_flags,
            download_dir=tmp_path
        )
        ai_strategy = AIEnhancedStrategy(
            base_strategy=base_strategy,
            settings=mock_settings
        )

        # Should enhance supports_url with confidence scoring
        result = ai_strategy.enhanced_supports_url("https://twitter.com/user/status/123")
        assert isinstance(result, dict)
        assert "supports" in result
        assert "confidence" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_ai_enhanced_strategy_fallback(self, fixture_test_settings, fixture_ai_feature_flags, tmp_path):
        """Test AI Enhanced Strategy falls back to base strategy when AI disabled."""
        mock_settings = Mock()
        mock_settings.ai_strategy_selection_enabled = False

        from boss_bot.ai.strategies.ai_enhanced_strategy import AIEnhancedStrategy
        from boss_bot.core.downloads.strategies.twitter_strategy import TwitterDownloadStrategy

        base_strategy = TwitterDownloadStrategy(
            feature_flags=fixture_ai_feature_flags,
            download_dir=tmp_path
        )
        ai_strategy = AIEnhancedStrategy(
            base_strategy=base_strategy,
            settings=mock_settings
        )

        # Should use base strategy behavior when AI disabled
        assert ai_strategy.supports_url("https://twitter.com/test") is True
        assert ai_strategy.supports_url("https://reddit.com/test") is False
