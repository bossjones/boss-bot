# Boss-Bot LangGraph Multi-Agent Testing Strategy

## Overview

This document outlines a comprehensive Test-Driven Development (TDD) strategy for Boss-Bot's LangGraph multi-agent system. The strategy incorporates LangSmith evaluation patterns, pytest-recording for integration testing, and specialized testing approaches for each agent type in the hybrid hierarchical-swarm architecture.

## Testing Philosophy

### Core Principles
1. **Test-Driven Development**: Write tests before implementing agent functionality
2. **Hierarchical Testing**: Test individual agents, agent teams, and full workflows
3. **Deterministic Testing**: Use recorded interactions to ensure reproducible results
4. **Performance-Aware Testing**: Validate response times and resource usage
5. **Behavioral Testing**: Focus on agent decision-making and workflow outcomes

---

## Testing Architecture

### Test Layer Structure

| **Layer** | **Scope** | **Framework** | **Purpose** |
|-----------|-----------|---------------|-------------|
| **Unit Tests** | Individual agent methods | pytest | Test isolated agent logic and decision-making |
| **Agent Integration** | Agent-to-agent communication | pytest + LangSmith | Test handoffs and swarm coordination |
| **Workflow Tests** | End-to-end agent workflows | pytest + agentevals | Test complete download-to-upload scenarios |
| **Performance Tests** | System performance and scaling | pytest + benchmark | Validate response times and resource usage |
| **Evaluation Tests** | Agent behavior and quality | LangSmith + openevals | Assess agent decision accuracy and output quality |

---

## TDD Implementation Strategy

### Phase 1: Agent Foundation Testing

#### 1.1 Base Agent Interface Testing
```python
# tests/ai/agents/test_base_agent.py
import pytest
from boss_bot.ai.agents.base_agent import BaseAgent
from boss_bot.ai.interfaces import AgentRequest, AgentState

class TestBaseAgent:
    @pytest.fixture
    def mock_agent(self, mocker):
        """Create a mock implementation of BaseAgent for testing"""
        agent = mocker.Mock(spec=BaseAgent)
        agent.agent_id = "test_agent"
        agent.config = {"model": "gpt-4", "timeout": 30}
        return agent

    def test_agent_initialization(self, mock_agent):
        """Test agent properly initializes with required attributes"""
        assert mock_agent.agent_id == "test_agent"
        assert mock_agent.config["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_process_request_interface(self, mock_agent):
        """Test agent request processing interface"""
        request = AgentRequest(
            request_type="download",
            payload={"url": "https://twitter.com/test"}
        )
        state = AgentState(workflow_id="test_workflow")

        mock_agent.process_request.return_value = mocker.Mock()
        response = await mock_agent.process_request(request, state)

        assert response is not None
        mock_agent.process_request.assert_called_once_with(request, state)
```

#### 1.2 Strategy Selector Agent Testing
```python
# tests/ai/agents/test_strategy_selector.py
import pytest
from unittest.mock import AsyncMock
from boss_bot.ai.agents.strategy_selector import StrategySelector

class TestStrategySelector:
    @pytest.fixture
    def strategy_selector(self, mocker):
        config = {"model": "gpt-4", "confidence_threshold": 0.8}
        agent = StrategySelector("strategy_selector", config)
        agent.analyze_url = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_twitter_url_selection(self, strategy_selector):
        """Test strategy selection for Twitter URLs"""
        # Arrange
        url = "https://twitter.com/user/status/123456789"
        user_context = {"preferences": {"quality": "high"}}

        strategy_selector.analyze_url.return_value = {
            "platform": "twitter",
            "confidence": 0.95,
            "recommended_strategy": "twitter_api"
        }

        # Act
        result = await strategy_selector.select_strategy(url, user_context)

        # Assert
        assert result.strategy == "twitter_api"
        assert result.confidence >= 0.8
        strategy_selector.analyze_url.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_fallback_strategy_selection(self, strategy_selector):
        """Test fallback to CLI strategy when API confidence is low"""
        # Arrange
        url = "https://obscure-platform.com/content/123"

        strategy_selector.analyze_url.return_value = {
            "platform": "unknown",
            "confidence": 0.3,
            "recommended_strategy": "generic_cli"
        }

        # Act
        result = await strategy_selector.select_strategy(url, {})

        # Assert
        assert result.strategy == "generic_cli"
        assert result.confidence < 0.8
```

### Phase 2: Integration Testing with pytest-recording

#### 2.1 Content Analysis Integration Tests
```python
# tests/ai/agents/test_content_analyzer_integration.py
import pytest
from vcr import VCR
from boss_bot.ai.agents.content_analyzer import ContentAnalyzer

# Configure VCR for deterministic API recording
vcr = VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='new_episodes',
    match_on=['uri', 'method', 'body'],
    filter_headers=['authorization', 'x-api-key']
)

class TestContentAnalyzerIntegration:
    @pytest.fixture
    def content_analyzer(self):
        config = {
            "model": "gpt-4-vision-preview",
            "max_tokens": 1000,
            "timeout": 60
        }
        return ContentAnalyzer("content_analyzer", config)

    @vcr.use_cassette('content_analysis_twitter_video.yaml')
    @pytest.mark.asyncio
    async def test_analyze_twitter_video_content(self, content_analyzer):
        """Test real Twitter video content analysis with recorded interactions"""
        # Arrange
        url = "https://twitter.com/user/status/123456789"

        # Act - This will use recorded API responses
        result = await content_analyzer.analyze_content(url)

        # Assert
        assert result.content_type == "video"
        assert result.platform == "twitter"
        assert result.duration > 0
        assert len(result.available_qualities) > 0
        assert result.confidence_score >= 0.7

    @vcr.use_cassette('content_analysis_reddit_image.yaml')
    @pytest.mark.asyncio
    async def test_analyze_reddit_image_content(self, content_analyzer):
        """Test Reddit image analysis with appropriate quality recommendations"""
        # Arrange
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Act
        result = await content_analyzer.analyze_content(url)

        # Assert
        assert result.content_type == "image"
        assert result.platform == "reddit"
        assert result.resolution is not None
        assert "1080p" in result.available_qualities or "original" in result.available_qualities
```

#### 2.2 Discord Integration Tests
```python
# tests/bot/cogs/test_ai_commands_integration.py
import pytest
import discord.ext.test as dpytest
from vcr import VCR
from boss_bot.bot.cogs.ai_commands import AiCommandsCog

vcr = VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes/discord',
    record_mode='new_episodes'
)

class TestAiCommandsIntegration:
    @pytest.fixture
    async def setup_bot(self, bot_test_fixture):
        """Setup bot with AI commands cog for testing"""
        await bot_test_fixture.add_cog(AiCommandsCog(bot_test_fixture))
        return bot_test_fixture

    @vcr.use_cassette('smart_download_twitter.yaml')
    @pytest.mark.asyncio
    async def test_smart_download_command_twitter(self, setup_bot):
        """Test smart download command with Twitter URL"""
        # Arrange
        url = "https://twitter.com/user/status/123456789"

        # Act
        await dpytest.message(f"$smart-download {url}")

        # Assert - Check for expected response patterns
        messages = dpytest.get_message()
        assert "🤖 AI-Enhanced Download" in messages.content
        assert "twitter" in messages.content.lower()

        # Verify embed contains analysis results
        assert len(messages.embeds) > 0
        embed = messages.embeds[0]
        assert "Content Analysis" in embed.title
        assert "Strategy Selected" in str(embed.fields)
```

### Phase 3: Agent Workflow Testing with LangSmith

#### 3.1 Multi-Agent Workflow Evaluation
```python
# tests/ai/workflows/test_download_workflow.py
import pytest
from langsmith import Client
from langsmith.evaluation import evaluate
from boss_bot.ai.workflows.download_workflow import DownloadWorkflow

class TestDownloadWorkflow:
    @pytest.fixture
    def langsmith_client(self):
        """Initialize LangSmith client for evaluation"""
        return Client()

    @pytest.fixture
    def download_workflow(self):
        """Create download workflow for testing"""
        return DownloadWorkflow()

    def test_workflow_evaluation_dataset(self, langsmith_client):
        """Create evaluation dataset for download workflows"""
        dataset_name = "boss_bot_download_scenarios"

        # Test scenarios covering different platforms and complexity levels
        test_cases = [
            {
                "input": {
                    "url": "https://twitter.com/user/status/123",
                    "user_preferences": {"quality": "high"}
                },
                "expected_output": {
                    "strategy": "twitter_api",
                    "quality": "1080p",
                    "success": True
                }
            },
            {
                "input": {
                    "url": "https://reddit.com/r/videos/comments/abc/title/",
                    "user_preferences": {"format": "mp4"}
                },
                "expected_output": {
                    "strategy": "reddit_api",
                    "format": "mp4",
                    "success": True
                }
            },
            # Edge cases
            {
                "input": {
                    "url": "https://invalid-url.com/content",
                    "user_preferences": {}
                },
                "expected_output": {
                    "strategy": "fallback",
                    "success": False,
                    "error_type": "unsupported_platform"
                }
            }
        ]

        # Create dataset in LangSmith
        dataset = langsmith_client.create_dataset(dataset_name, test_cases)
        return dataset

    @pytest.mark.asyncio
    async def test_agent_trajectory_evaluation(self, download_workflow, langsmith_client):
        """Evaluate agent decision-making trajectory using agentevals"""
        from agentevals import TrajectoryEvaluator

        # Define evaluation criteria
        evaluator = TrajectoryEvaluator(
            criteria=[
                "strategy_selection_accuracy",
                "content_analysis_completeness",
                "error_handling_robustness",
                "user_preference_adherence"
            ]
        )

        # Test scenario
        test_input = {
            "url": "https://twitter.com/user/status/123456789",
            "user_context": {
                "user_id": "test_user",
                "preferences": {"quality": "high", "format": "mp4"}
            }
        }

        # Execute workflow and capture trajectory
        result = await download_workflow.execute(test_input)

        # Evaluate trajectory
        evaluation_result = await evaluator.evaluate(
            inputs=test_input,
            outputs=result,
            trajectory=result.get('agent_trajectory', [])
        )

        # Assert evaluation metrics
        assert evaluation_result['strategy_selection_accuracy'] >= 0.8
        assert evaluation_result['content_analysis_completeness'] >= 0.7
        assert evaluation_result['overall_score'] >= 0.75
```

#### 3.2 LLM-as-Judge Evaluation
```python
# tests/ai/evaluation/test_llm_judge.py
import pytest
from langsmith.evaluation import LangChainStringEvaluator
from boss_bot.ai.evaluation.judges import ContentQualityJudge

class TestLLMJudgeEvaluation:
    @pytest.fixture
    def content_quality_judge(self):
        """Create LLM judge for content quality assessment"""
        return ContentQualityJudge(model="gpt-4")

    @pytest.mark.asyncio
    async def test_content_analysis_quality_evaluation(self, content_quality_judge):
        """Test LLM judge evaluation of content analysis quality"""
        # Sample content analysis result
        analysis_result = {
            "content_type": "video",
            "duration": 120.5,
            "resolution": "1920x1080",
            "available_qualities": ["720p", "1080p", "1440p"],
            "tags": ["technology", "tutorial"],
            "confidence_score": 0.92
        }

        # Original content URL for reference
        original_url = "https://twitter.com/user/status/123456789"

        # Evaluate quality using LLM judge
        evaluation = await content_quality_judge.evaluate(
            input_url=original_url,
            analysis_result=analysis_result,
            criteria=[
                "accuracy",
                "completeness",
                "relevance",
                "technical_correctness"
            ]
        )

        # Assert evaluation results
        assert evaluation.overall_score >= 0.8
        assert evaluation.accuracy_score >= 0.85
        assert evaluation.completeness_score >= 0.8
        assert len(evaluation.feedback) > 0
```

### Phase 4: Performance and Load Testing

#### 4.1 Agent Performance Testing
```python
# tests/performance/test_agent_performance.py
import pytest
import asyncio
import time
from statistics import mean, median
from boss_bot.ai.agents.main_supervisor import MainSupervisor

class TestAgentPerformance:
    @pytest.fixture
    def main_supervisor(self):
        """Create main supervisor for performance testing"""
        return MainSupervisor("main_supervisor", {})

    @pytest.mark.asyncio
    async def test_response_time_requirements(self, main_supervisor):
        """Test agent response time meets requirements"""
        test_urls = [
            "https://twitter.com/user/status/1",
            "https://reddit.com/r/test/comments/abc/title/",
            "https://instagram.com/p/ABC123/",
            "https://youtube.com/watch?v=VIDEO_ID"
        ]

        response_times = []

        for url in test_urls:
            start_time = time.time()

            # Execute agent workflow
            result = await main_supervisor.process_download_request(url)

            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)

        # Performance assertions
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        max_response_time = max(response_times)

        assert avg_response_time <= 10.0  # Average under 10 seconds
        assert median_response_time <= 8.0  # Median under 8 seconds
        assert max_response_time <= 15.0  # No request over 15 seconds

    @pytest.mark.asyncio
    async def test_concurrent_agent_handling(self, main_supervisor):
        """Test agent performance under concurrent load"""
        concurrent_requests = 10
        test_url = "https://twitter.com/user/status/123456789"

        # Create concurrent tasks
        tasks = [
            main_supervisor.process_download_request(test_url)
            for _ in range(concurrent_requests)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Verify all requests completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == concurrent_requests

        # Performance requirements
        assert total_time <= 20.0  # All concurrent requests under 20 seconds

        # Check for resource exhaustion
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        assert memory_usage <= 1000  # Under 1GB memory usage
```

#### 4.2 Error Handling and Resilience Testing
```python
# tests/resilience/test_error_handling.py
import pytest
from unittest.mock import AsyncMock, patch
from boss_bot.ai.agents.fallback_handler import FallbackHandler

class TestErrorHandlingResilience:
    @pytest.fixture
    def fallback_handler(self):
        """Create fallback handler for error testing"""
        return FallbackHandler("fallback_handler", {})

    @pytest.mark.asyncio
    async def test_api_failure_fallback(self, fallback_handler):
        """Test graceful fallback when AI API fails"""
        # Simulate API failure
        with patch('openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.side_effect = Exception("API rate limit exceeded")

            # Test fallback mechanism
            result = await fallback_handler.handle_api_failure(
                original_request="download twitter video",
                error_context={"error": "API failure", "agent": "content_analyzer"}
            )

            # Verify fallback to traditional strategy
            assert result.fallback_strategy == "traditional_cli"
            assert result.success is True
            assert "Using traditional download method" in result.message

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, fallback_handler):
        """Test handling of agent timeouts"""
        # Simulate slow agent response
        slow_agent = AsyncMock()
        slow_agent.process_request.side_effect = asyncio.TimeoutError()

        # Test timeout handling
        result = await fallback_handler.handle_agent_timeout(
            agent=slow_agent,
            timeout_seconds=30,
            fallback_options=["retry", "skip", "fallback"]
        )

        assert result.action == "fallback"
        assert result.timeout_occurred is True
```

---

## Testing Infrastructure

### Continuous Integration Pipeline

#### CI Testing Stages
```yaml
# .github/workflows/agent-testing.yml
name: Agent Testing Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: |
          uv sync
          uv add pytest pytest-asyncio pytest-mock dpytest pytest-recording
      - name: Run unit tests
        run: uv run pytest tests/ai/agents/ -v --tb=short
        env:
          VCR_RECORD_MODE: none  # Use recorded cassettes in CI

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3
      - name: Install system dependencies
        run: sudo apt-get update && sudo apt-get install -y ffmpeg imagemagick
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v --tb=short
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}

  evaluation-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3
      - name: Run evaluation tests
        run: uv run pytest tests/evaluation/ -v --tb=short
        env:
          LANGCHAIN_TRACING_V2: true
          LANGCHAIN_PROJECT: boss-bot-ci-testing
```

### Local Development Testing

#### Testing Commands
```bash
# Unit tests (fast, no external dependencies)
uv run pytest tests/ai/agents/ -v

# Integration tests (with recorded API interactions)
uv run pytest tests/integration/ -v --vcr-record=new_episodes

# Performance tests
uv run pytest tests/performance/ -v --benchmark-only

# Evaluation tests (requires API keys)
uv run pytest tests/evaluation/ -v

# Full test suite
uv run pytest tests/ -v --cov=boss_bot --cov-report=html

# Test specific agent
uv run pytest tests/ai/agents/test_strategy_selector.py -v

# Update VCR cassettes (record new API interactions)
uv run pytest tests/integration/ --vcr-record=all
```

### Test Data Management

#### VCR Cassette Organization
```
tests/fixtures/vcr_cassettes/
├── content_analysis/
│   ├── twitter_video_analysis.yaml
│   ├── reddit_image_analysis.yaml
│   ├── instagram_story_analysis.yaml
│   └── youtube_video_analysis.yaml
├── strategy_selection/
│   ├── platform_detection.yaml
│   └── quality_selection.yaml
├── discord_integration/
│   ├── smart_download_commands.yaml
│   └── error_responses.yaml
└── workflow_tests/
    ├── end_to_end_download.yaml
    └── multi_agent_handoffs.yaml
```

#### Test Configuration
```python
# tests/conftest.py
import pytest
import vcr
from boss_bot.core.env import BossSettings

@pytest.fixture(scope="session")
def vcr_config():
    """Global VCR configuration for all tests"""
    return {
        "cassette_library_dir": "tests/fixtures/vcr_cassettes",
        "record_mode": "new_episodes",
        "match_on": ["uri", "method", "body"],
        "filter_headers": [
            "authorization",
            "x-api-key",
            "x-openai-api-key",
            "anthropic-api-key"
        ],
        "filter_query_parameters": ["api_key", "token"]
    }

@pytest.fixture
def test_settings():
    """Test configuration with safe defaults"""
    return BossSettings(
        ai_enabled=True,
        ai_content_analysis_enabled=True,
        openai_api_key="test-key",
        langchain_tracing_v2=False  # Disable tracing in tests
    )
```

---

## Test Coverage Requirements

### Coverage Targets
- **Unit Tests**: 90% coverage for individual agent methods
- **Integration Tests**: 80% coverage for agent interactions
- **Workflow Tests**: 95% coverage for end-to-end scenarios
- **Error Handling**: 85% coverage for exception paths

### Critical Test Areas
1. **Agent Decision Logic**: Strategy selection, content analysis, quality optimization
2. **Handoff Mechanisms**: Swarm-style agent transfers and hierarchical routing
3. **Error Recovery**: Fallback mechanisms and graceful degradation
4. **Performance Boundaries**: Response time limits and resource constraints
5. **Discord Integration**: Command processing and user interaction flows

This comprehensive testing strategy ensures Boss-Bot's LangGraph multi-agent system is reliable, performant, and maintainable while providing confidence for continuous deployment and feature enhancement.
