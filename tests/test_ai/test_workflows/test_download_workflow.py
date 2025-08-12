"""Tests for download workflow coordination."""

from __future__ import annotations

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse
from boss_bot.ai.workflows.download_workflow import DownloadWorkflow, DownloadWorkflowConfig, ConfigSchema, create_download_workflow_graph


class TestDownloadWorkflow:
    """Test the LangGraph download workflow."""

    @pytest.fixture
    def fixture_mock_strategy_selector(self, mocker):
        """Create a mock strategy selector agent."""
        agent = mocker.Mock()
        agent.name = "strategy-selector"
        agent.process_request = AsyncMock()
        return agent

    @pytest.fixture
    def fixture_mock_content_analyzer(self, mocker):
        """Create a mock content analyzer agent."""
        agent = mocker.Mock()
        agent.name = "content-analyzer"
        agent.process_request = AsyncMock()
        return agent

    @pytest.fixture
    def fixture_mock_strategy(self, mocker):
        """Create a mock download strategy."""
        strategy = mocker.Mock()
        strategy.supports_url = mocker.Mock(return_value=True)
        strategy.download = AsyncMock()
        return strategy

    @pytest.fixture
    def fixture_workflow_config(self):
        """Create workflow configuration for testing."""
        return DownloadWorkflowConfig(
            max_retries=2,
            timeout_seconds=60,
            enable_content_analysis=True,
            enable_ai_strategy_selection=True,
        )

    @pytest.fixture
    def fixture_download_workflow(
        self,
        fixture_mock_strategy_selector,
        fixture_mock_content_analyzer,
        fixture_workflow_config,
    ):
        """Create download workflow instance for testing."""
        workflow = DownloadWorkflow(
            strategy_selector=fixture_mock_strategy_selector,
            content_analyzer=fixture_mock_content_analyzer,
            config=fixture_workflow_config,
        )
        return workflow

    @pytest.mark.asyncio
    async def test_workflow_initialization(self, fixture_download_workflow):
        """Test workflow initialization."""
        workflow = fixture_download_workflow

        assert workflow.strategy_selector is not None
        assert workflow.content_analyzer is not None
        assert workflow.config.max_retries == 2
        assert workflow.config.enable_content_analysis is True
        assert workflow.config.enable_ai_strategy_selection is True

    @pytest.mark.asyncio
    async def test_workflow_without_agents(self):
        """Test workflow can run without AI agents."""
        workflow = DownloadWorkflow()

        # Add mock strategy
        mock_strategy = Mock()
        mock_strategy.supports_url = Mock(return_value=True)
        mock_strategy.download = AsyncMock(return_value={"title": "Test Video"})

        workflow.initialize_strategies({"twitter": mock_strategy})

        result = await workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["url"] == "https://twitter.com/test"
        assert result["strategy_selection"]["selected_strategy"] == "twitter"
        assert result["strategy_selection"]["ai_enhanced"] is False

    @pytest.mark.asyncio
    async def test_ai_strategy_selection_success(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test successful AI strategy selection."""
        # Setup strategy selector response
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="URL matches Twitter pattern with high confidence",
        )

        # Setup mock strategy
        fixture_mock_strategy.download.return_value = {"title": "Test Tweet"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["strategy_selection"]["selected_strategy"] == "twitter"
        assert result["strategy_selection"]["ai_enhanced"] is True
        assert result["strategy_selection"]["confidence"] == 0.95

        # Verify strategy selector was called
        fixture_mock_strategy_selector.process_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_strategy_selection_fallback(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test fallback to traditional selection when AI fails."""
        # Setup strategy selector failure
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=False,
            error="AI model unavailable",
            confidence=0.0,
            reasoning="Model connection failed",
        )

        # Setup mock strategy
        fixture_mock_strategy.download.return_value = {"title": "Test Tweet"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["strategy_selection"]["selected_strategy"] == "twitter"
        assert result["strategy_selection"]["ai_enhanced"] is False
        assert "URL pattern matches" in result["strategy_selection"]["reasoning"]

    @pytest.mark.asyncio
    async def test_content_analysis_integration(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_content_analyzer,
        fixture_mock_strategy,
    ):
        """Test content analysis integration in workflow."""
        # Setup strategy selector response
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        # Setup content analyzer response
        fixture_mock_content_analyzer.process_request.return_value = AgentResponse(
            success=True,
            result={
                "content_type": "video",
                "quality_score": 0.85,
                "duration": 120,
            },
            confidence=0.90,
            reasoning="High-quality video content detected",
        )

        # Setup mock strategy
        fixture_mock_strategy.download.return_value = {"title": "Test Video"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/video")

        assert result["success"] is True
        assert result["content_analysis"] is not None
        assert result["content_analysis"]["analysis"]["content_type"] == "video"
        assert result["content_analysis"]["confidence"] == 0.90

        # Verify content analyzer was called
        fixture_mock_content_analyzer.process_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_analysis_optional(
        self,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test workflow continues when content analysis is disabled."""
        config = DownloadWorkflowConfig(enable_content_analysis=False)
        workflow = DownloadWorkflow(
            strategy_selector=fixture_mock_strategy_selector,
            content_analyzer=None,
            config=config,
        )

        # Setup strategy selector
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected strategy",
        )

        # Setup mock strategy
        fixture_mock_strategy.download.return_value = {"title": "Test"}
        workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["content_analysis"] is None

    @pytest.mark.asyncio
    async def test_download_execution(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test download execution through workflow."""
        # Setup strategy selector to return a proper strategy name
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        # Setup strategy to return metadata
        expected_metadata = {
            "title": "Test Video",
            "duration": 180,
            "format": "mp4",
            "file_path": "/downloads/test.mp4",
        }
        fixture_mock_strategy.download.return_value = expected_metadata

        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["download_result"]["success"] is True
        assert result["download_result"]["metadata"] == expected_metadata
        assert result["download_result"]["strategy_used"] == "twitter"

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once_with("https://twitter.com/test")

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, fixture_download_workflow):
        """Test workflow error handling."""
        # Don't initialize any strategies to force error
        # Disable AI strategy selection to force traditional fallback
        fixture_download_workflow.config.enable_ai_strategy_selection = False

        result = await fixture_download_workflow.run_workflow("https://example.com/test")

        assert result["success"] is False
        assert "No strategy found" in result["error"]

    @pytest.mark.asyncio
    async def test_download_failure_with_retry(
        self,
        fixture_download_workflow,
        fixture_mock_strategy,
    ):
        """Test download retry logic on failure."""
        # Disable AI strategy selection to use traditional fallback
        fixture_download_workflow.config.enable_ai_strategy_selection = False

        # Setup strategy to fail then succeed
        fixture_mock_strategy.download.side_effect = [
            Exception("Network error"),
            {"title": "Success on retry"},
        ]

        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        # This test would need LangGraph for retry logic
        # For now, test that error is handled
        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        # In simple workflow, first failure would cause overall failure
        assert result["success"] is False
        assert "Download failed" in result["error"]

    @pytest.mark.asyncio
    async def test_workflow_with_user_context(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test workflow with user context and preferences."""
        # Setup strategy selector
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        user_context = {
            "user_id": "123456",
            "guild_id": "789012",
            "preferences": {"quality": "high", "format": "mp4"},
        }

        fixture_mock_strategy.download.return_value = {"title": "Test"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow(
            "https://twitter.com/test",
            user_context=user_context,
        )

        assert result["success"] is True
        assert result["url"] == "https://twitter.com/test"

    @pytest.mark.asyncio
    async def test_workflow_state_tracking(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_content_analyzer,
        fixture_mock_strategy,
    ):
        """Test workflow state tracking through steps."""
        # Setup strategy selector
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        # Setup content analyzer
        fixture_mock_content_analyzer.process_request.return_value = AgentResponse(
            success=True,
            result="High quality content",
            confidence=0.9,
            reasoning="Content analysis successful",
        )

        fixture_mock_strategy.download.return_value = {"title": "Test"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        # In simple workflow, final step should be complete
        assert "complete" in str(result.get("workflow_steps", ""))

    @pytest.mark.asyncio
    async def test_multiple_strategy_selection(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test strategy selection when multiple strategies are available."""
        # Setup strategy selector to choose Twitter
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        # Create multiple strategies
        twitter_strategy = Mock()
        twitter_strategy.supports_url = Mock(return_value=True)
        twitter_strategy.download = AsyncMock(return_value={"title": "Twitter"})

        reddit_strategy = Mock()
        reddit_strategy.supports_url = Mock(return_value=False)  # Doesn't support Twitter URL
        reddit_strategy.download = AsyncMock(return_value={"title": "Reddit"})

        fixture_download_workflow.initialize_strategies({
            "twitter": twitter_strategy,
            "reddit": reddit_strategy,
        })

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert result["strategy_selection"]["selected_strategy"] == "twitter"

    @pytest.mark.asyncio
    async def test_workflow_config_validation(self):
        """Test workflow configuration validation."""
        config = DownloadWorkflowConfig(
            max_retries=5,
            timeout_seconds=120,
            enable_content_analysis=False,
            enable_ai_strategy_selection=False,
        )

        workflow = DownloadWorkflow(config=config)

        assert workflow.config.max_retries == 5
        assert workflow.config.timeout_seconds == 120
        assert workflow.config.enable_content_analysis is False
        assert workflow.config.enable_ai_strategy_selection is False

    @pytest.mark.asyncio
    async def test_langgraph_availability_check(self, fixture_download_workflow):
        """Test LangGraph availability detection."""
        # This will test the _has_langgraph method
        has_langgraph = fixture_download_workflow._has_langgraph()

        # Result depends on whether langgraph is installed
        assert isinstance(has_langgraph, bool)

    @pytest.mark.asyncio
    async def test_request_id_generation(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test automatic request ID generation."""
        # Setup strategy selector
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        fixture_mock_strategy.download.return_value = {"title": "Test"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        assert "request_id" in result
        assert len(result["request_id"]) > 0  # Should have generated UUID

    @pytest.mark.asyncio
    async def test_custom_request_id(
        self,
        fixture_download_workflow,
        fixture_mock_strategy_selector,
        fixture_mock_strategy,
    ):
        """Test workflow with custom request ID."""
        # Setup strategy selector
        fixture_mock_strategy_selector.process_request.return_value = AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI selected Twitter strategy",
        )

        custom_request_id = "custom-request-123"

        fixture_mock_strategy.download.return_value = {"title": "Test"}
        fixture_download_workflow.initialize_strategies({"twitter": fixture_mock_strategy})

        result = await fixture_download_workflow.run_workflow(
            "https://twitter.com/test",
            request_id=custom_request_id,
        )

        assert result["success"] is True
        assert result["request_id"] == custom_request_id


class TestConfigSchema:
    """Test the ConfigSchema for workflow configuration."""

    def test_config_schema_creation(self):
        """Test creating a ConfigSchema with all parameters."""
        config: ConfigSchema = {
            # AI Configuration
            "enable_ai_strategy_selection": True,
            "enable_content_analysis": True,
            "ai_model": "gpt-4",
            "ai_temperature": 0.7,

            # Download Configuration
            "max_retries": 3,
            "timeout_seconds": 300,
            "download_quality": "best",

            # Platform Specific Settings
            "youtube_quality": "1080p",
            "twitter_include_replies": False,
            "instagram_include_stories": True,
            "reddit_include_comments": False,
        }

        # Verify all keys are accessible
        assert config["enable_ai_strategy_selection"] is True
        assert config["ai_model"] == "gpt-4"
        assert config["max_retries"] == 3
        assert config["youtube_quality"] == "1080p"

    def test_config_schema_partial_creation(self):
        """Test creating a ConfigSchema with only some parameters."""
        config: ConfigSchema = {
            "enable_ai_strategy_selection": False,
            "max_retries": 5,
        }

        assert config["enable_ai_strategy_selection"] is False
        assert config["max_retries"] == 5

    def test_config_schema_type_safety(self):
        """Test ConfigSchema type safety (compile-time check)."""
        # This test verifies that TypedDict provides type safety
        # The actual type checking happens at development time via mypy
        config: ConfigSchema = {
            "enable_ai_strategy_selection": True,
            "ai_temperature": 0.3,
            "max_retries": 2,
        }

        assert isinstance(config["enable_ai_strategy_selection"], bool)
        assert isinstance(config["ai_temperature"], float)
        assert isinstance(config["max_retries"], int)


class TestConfigurableWorkflow:
    """Test workflow with configuration support."""

    @pytest.fixture
    def fixture_sample_config(self):
        """Create a sample configuration for testing."""
        return ConfigSchema(
            enable_ai_strategy_selection=True,
            enable_content_analysis=True,
            ai_model="gpt-4",
            ai_temperature=0.5,
            max_retries=2,
            timeout_seconds=120,
            download_quality="high",
            youtube_quality="720p",
            twitter_include_replies=True,
            instagram_include_stories=False,
            reddit_include_comments=True,
        )

    def test_create_workflow_graph_with_config(self, fixture_sample_config):
        """Test creating workflow graph with configuration."""
        # This test verifies the function signature accepts config
        # We can't test full functionality without LangGraph installed
        try:
            graph = create_download_workflow_graph(config_schema=fixture_sample_config)
            # If LangGraph is available, graph should be created
            assert graph is not None
        except ImportError:
            # If LangGraph is not available, that's expected in test environment
            pytest.skip("LangGraph not available for testing")

    def test_create_workflow_graph_without_config(self):
        """Test creating workflow graph without configuration."""
        try:
            graph = create_download_workflow_graph()
            assert graph is not None
        except ImportError:
            pytest.skip("LangGraph not available for testing")

    @pytest.mark.asyncio
    async def test_workflow_with_config_applied(self, fixture_sample_config):
        """Test that configuration is properly applied in workflow."""
        config = DownloadWorkflowConfig(
            max_retries=fixture_sample_config.get("max_retries", 3),
            timeout_seconds=fixture_sample_config.get("timeout_seconds", 300),
            enable_content_analysis=fixture_sample_config.get("enable_content_analysis", True),
            enable_ai_strategy_selection=fixture_sample_config.get("enable_ai_strategy_selection", True),
        )

        workflow = DownloadWorkflow(config=config)

        # Verify configuration is applied
        assert workflow.config.max_retries == 2
        assert workflow.config.timeout_seconds == 120
        assert workflow.config.enable_content_analysis is True
        assert workflow.config.enable_ai_strategy_selection is True

    @pytest.mark.asyncio
    async def test_workflow_config_affects_behavior(self, mocker):
        """Test that configuration changes affect workflow behavior."""
        # Test with AI disabled
        ai_disabled_config = DownloadWorkflowConfig(
            enable_ai_strategy_selection=False,
            enable_content_analysis=False,
        )

        workflow = DownloadWorkflow(config=ai_disabled_config)

        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.supports_url = Mock(return_value=True)
        mock_strategy.download = AsyncMock(return_value={"title": "Test"})
        workflow.initialize_strategies({"twitter": mock_strategy})

        result = await workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        # Should use traditional strategy selection (not AI)
        assert result["strategy_selection"]["ai_enhanced"] is False
        # Should not have content analysis
        assert result.get("content_analysis") is None

    @pytest.mark.asyncio
    async def test_workflow_ai_config_integration(self, mocker):
        """Test AI configuration integration in workflow."""
        # Test with specific AI settings
        ai_config = DownloadWorkflowConfig(
            enable_ai_strategy_selection=True,
            enable_content_analysis=True,
        )

        # Mock AI agents
        mock_strategy_selector = Mock()
        mock_strategy_selector.process_request = AsyncMock(return_value=AgentResponse(
            success=True,
            result="twitter",
            confidence=0.95,
            reasoning="AI strategy selection",
        ))

        mock_content_analyzer = Mock()
        mock_content_analyzer.process_request = AsyncMock(return_value=AgentResponse(
            success=True,
            result={"quality": "high"},
            confidence=0.9,
            reasoning="AI content analysis",
        ))

        workflow = DownloadWorkflow(
            strategy_selector=mock_strategy_selector,
            content_analyzer=mock_content_analyzer,
            config=ai_config,
        )

        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.supports_url = Mock(return_value=True)
        mock_strategy.download = AsyncMock(return_value={"title": "Test"})
        workflow.initialize_strategies({"twitter": mock_strategy})

        result = await workflow.run_workflow("https://twitter.com/test")

        assert result["success"] is True
        # Should use AI strategy selection
        assert result["strategy_selection"]["ai_enhanced"] is True
        # Should have content analysis
        assert result["content_analysis"] is not None
