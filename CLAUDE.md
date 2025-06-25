# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Boss-Bot is an AI-powered Discord bot that enables intelligent downloading and managing of media files from social media platforms. The bot uses discord.py and follows a modular architecture with cogs for different functionality. It leverages advanced AI capabilities through LangChain, LangGraph, and multi-agent orchestration for intelligent content analysis, strategy selection, and workflow optimization.

## Build & Test Commands
- Run all tests: `just check-test`
- Run single test: `just check-test "tests/test_bot/test_client.py::test_function_name"`
- Run tests with coverage: `just check-coverage`
- Lint code: `just check-code`
- Type check: `just check-type`
- Format code: `just format`
- Full check suite: `just check`
- Manage dependencies: `just uv-update`
- Run bot: `goobctl go`

**Important**: All Python commands should be prefixed with `uv run` when running outside of just commands:
- Run pytest directly: `uv run python -m pytest <test_path>`
- Run CLI commands: `uv run python -m boss_bot.cli.main <command>`
- Run Python scripts: `uv run python <script.py>`

## Code Architecture
- `BossBot` (in `src/boss_bot/bot/client.py`) is the main bot class extending discord.ext.commands.Bot
- `BossSettings` (in `src/boss_bot/core/env.py`) manages configuration via pydantic-settings
- Discord commands are organized into cogs (src/boss_bot/bot/cogs/)
- CLI interface using Typer in `src/boss_bot/cli.py` (currently in development)
- Core services:
  - `QueueManager`: Manages download queue
  - `DownloadManager`: Handles concurrent downloads
- All settings are accessible via dependency injection from the bot instance

## Technology Stack
- **Discord.py**: Core framework for Discord bot functionality
- **Pydantic/Pydantic-Settings**: Data validation and environment configuration
- **Typer**: CLI interface (partially implemented)
- **Rich**: Console output formatting for CLI
- **AI & LangChain Ecosystem**:
  - **LangChain**: Framework for AI chain development and agent coordination
  - **LangGraph**: Multi-agent orchestration and workflow state management
  - **LangSmith**: Monitoring, debugging, and tracing LLM applications
  - **LangChain Integrations**: OpenAI, Anthropic, Google (Gemini) model providers
  - **Multi-Agent Architecture**: StrategySelector, ContentAnalyzer, SocialMediaAgent
- **Testing**: pytest, pytest-asyncio, dpytest, pytest-recording (VCR for AI)
- **Storage**: Support for various storage mechanisms
- **Build System**: Just, uv, ruff

## Epic 5: Strategy Pattern Integration ✅ COMPLETED
The project has successfully implemented the experimental strategy pattern architecture for download operations, providing both CLI and API-direct modes with feature flag control.

### ✅ Completed Platforms & Strategies
- **Twitter/X Strategy** (`twitter_strategy.py`): Full CLI/API switching with feature flags, comprehensive test coverage
- **Reddit Strategy** (`reddit_strategy.py`): Complete implementation with API-direct support and fallback mechanisms
- **Instagram Strategy** (`instagram_strategy.py`): Full implementation with user CLI preferences (Firefox cookies, Wget/1.21.1 user agent)
- **YouTube Strategy** (`youtube_strategy.py`): Complete yt-dlp integration with quality selection and comprehensive metadata support

### Strategy Architecture (EXPERIMENTAL.md Epic 5)
- **Base Strategy**: `BaseDownloadStrategy` defines abstract interface for all download strategies
- **Feature Flag Control**: Environment variable-driven configuration for API vs CLI choice
- **Platform Detection**: URL pattern matching for automatic strategy selection
- **Integration Points**: Discord cog integration ✅, CLI command integration ✅, comprehensive test coverage ✅
- **Technology**: Uses gallery-dl/yt-dlp APIs directly (API mode) or subprocess calls (CLI mode)
- **Fallback System**: API failures automatically fallback to CLI when enabled

### Epic 5 Implementation Status
- ✅ **Story 5.1**: Discord cogs updated to use strategy pattern (`src/boss_bot/bot/cogs/downloads.py`)
- ✅ **Story 5.2**: CLI commands updated to use strategies (`src/boss_bot/cli/commands/download.py`)
- ✅ **Story 5.3**: Configuration documentation and usage examples (this section)
- ✅ **Story 5.4**: Gradual rollout via environment variables (feature flags system)

## 🤖 AI Multi-Agent System ✅ COMPLETED

Boss-Bot now includes a sophisticated AI multi-agent system powered by LangGraph for intelligent content analysis, strategy selection, and workflow orchestration.

### ✅ Implemented AI Agents

#### **1. StrategySelector Agent** (`src/boss_bot/ai/agents/strategy_selector.py`)
- **Purpose**: Intelligent platform detection and optimal strategy selection
- **Capabilities**:
  - URL analysis with confidence scoring (0.0-1.0)
  - User preference integration
  - Fallback to traditional pattern matching
- **Integration**: Seamlessly enhances existing Epic 5 strategy pattern
- **Test Coverage**: 13 comprehensive tests

#### **2. ContentAnalyzer Agent** (`src/boss_bot/ai/agents/content_analyzer.py`)
- **Purpose**: Advanced content quality assessment and metadata enrichment
- **Capabilities**:
  - Content quality scoring and categorization
  - Engagement potential prediction
  - Audience insights and targeting suggestions
  - Format optimization recommendations
- **Integration**: Enhances metadata commands with AI insights
- **Test Coverage**: 11 comprehensive tests

#### **3. SocialMediaAgent** (`src/boss_bot/ai/agents/social_media_agent.py`)
- **Purpose**: Specialized social media content processing and analysis
- **Capabilities**:
  - Sentiment analysis and trend detection
  - Cross-platform content coordination
  - Engagement optimization strategies
  - Content classification and moderation
- **Integration**: Multi-agent coordination with ContentAnalyzer
- **Test Coverage**: 12 comprehensive tests

### ✅ LangGraph Workflow Orchestration

#### **DownloadWorkflow** (`src/boss_bot/ai/workflows/download_workflow.py`)
- **Purpose**: Multi-agent coordination for complex download workflows
- **Features**:
  - State machine implementation with LangGraph StateGraph
  - Error handling and retry logic
  - Agent handoff and communication protocols
  - Fallback mechanisms when LangGraph unavailable
- **Test Coverage**: 20 workflow tests including LangGraph-specific functionality

### 🎯 **New AI-Powered Discord Commands**

Boss-Bot now includes three powerful AI-enhanced Discord commands:

#### **`$smart-analyze <url>`** - AI Content Analysis
```
$smart-analyze https://twitter.com/user/status/123456789
$smart-analyze https://youtube.com/watch?v=VIDEO_ID
```
- Uses ContentAnalyzer agent for deep content insights
- Provides quality scores (0-10), engagement predictions, target audience analysis
- Shows AI confidence levels and reasoning
- Includes processing time metrics

#### **`$smart-download <url> [upload]`** - AI-Enhanced Download
```
$smart-download https://twitter.com/user/status/123456789
$smart-download https://youtube.com/watch?v=VIDEO_ID false
```
- Uses StrategySelector agent for optimal platform detection
- Displays AI reasoning and confidence scores
- Provides download strategy recommendations
- Falls back to regular download when AI disabled

#### **`$ai-status`** - AI Agent Status & Monitoring
```
$ai-status
```
- Shows real-time agent performance metrics (request count, response times)
- Displays feature flag status and availability
- Provides troubleshooting information for AI setup
- Shows agent activation status and capabilities

### 🔧 **Enhanced Existing Commands**

All existing Discord commands now include optional AI enhancements:

#### **`$download <url>`** - AI-Enhanced Strategy Selection
- Automatically uses AI strategy selection when enabled
- Shows AI confidence and reasoning when available
- Maintains full backward compatibility

#### **`$metadata <url>`** - AI-Enriched Metadata
- Enhanced with AI content analysis insights
- Shows "AI Enhanced" indicator when active
- Includes AI-generated content recommendations

#### **`$strategies`** - AI Feature Status
- Displays current AI feature flag configuration
- Shows AI agent availability and status
- Includes setup instructions for AI features

## Configuration Options & Usage Examples

### Environment Variables for Strategy & AI Control
Control download strategy and AI behavior using these environment variables:

```bash
# Download Strategy Feature Flags - Enable API-direct mode per platform
export TWITTER_USE_API_CLIENT=true          # Enable API-direct for Twitter/X
export REDDIT_USE_API_CLIENT=true           # Enable API-direct for Reddit
export INSTAGRAM_USE_API_CLIENT=true        # Enable API-direct for Instagram
export YOUTUBE_USE_API_CLIENT=true          # Enable API-direct for YouTube

# AI Enhancement Feature Flags - Enable AI capabilities (NEW!)
export AI_STRATEGY_SELECTION_ENABLED=true   # Enable AI-powered strategy selection
export AI_CONTENT_ANALYSIS_ENABLED=true     # Enable AI content analysis and insights
export AI_WORKFLOW_ORCHESTRATION_ENABLED=true  # Enable LangGraph workflow coordination

# LLM Model Provider Configuration (choose one)
export OPENAI_API_KEY="your-openai-api-key"        # For GPT-4, GPT-3.5 models
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For Claude models
export GOOGLE_API_KEY="your-google-api-key"        # For Gemini models

# Fallback Control
export DOWNLOAD_API_FALLBACK_TO_CLI=true    # Auto-fallback to CLI on API errors (recommended)

# Download Configuration
export BOSS_BOT_DOWNLOAD_DIR="./downloads"  # Download directory (default: .downloads/)
```

### Discord Bot Usage
The Discord bot now includes AI-powered commands alongside traditional functionality:

#### **Traditional Commands (Enhanced with AI when enabled)**
```bash
# Basic download command (now uses AI strategy selection when enabled)
$download https://twitter.com/user/status/123456789

# Get metadata without downloading (enhanced with AI insights when enabled)
$metadata https://reddit.com/r/pics/comments/abc123/title/

# Check current strategy & AI configuration
$strategies

# View download status
$status
```

#### **NEW: AI-Powered Commands** 🤖
```bash
# AI-powered content analysis with advanced insights
$smart-analyze https://twitter.com/user/status/123456789
$smart-analyze https://youtube.com/watch?v=VIDEO_ID

# AI-enhanced download with strategy optimization
$smart-download https://twitter.com/user/status/123456789
$smart-download https://youtube.com/watch?v=VIDEO_ID false

# Show AI agent status and performance metrics
$ai-status
```

#### **Enhanced Commands with AI Integration**
```bash
# Download with AI strategy selection (when AI enabled)
$download https://instagram.com/p/POST_ID/
# Shows: "🤖 AI selected Instagram strategy (confidence: 95%)"

# Metadata with AI content analysis (when AI enabled)
$metadata https://youtube.com/watch?v=VIDEO_ID
# Shows: "📊 AI Enhanced Content Info" with quality scores and insights
```

### CLI Usage Examples
The CLI commands now use the strategy pattern with enhanced features:

```bash
# Twitter/X downloads with strategy pattern
bossctl download twitter https://twitter.com/user/status/123456789
bossctl download twitter https://x.com/user --metadata-only

# Reddit downloads with config support
bossctl download reddit https://reddit.com/r/pics/comments/abc123/title/
bossctl download reddit <url> --cookies cookies.txt --config custom.json

# Instagram downloads with experimental features
bossctl download instagram https://instagram.com/p/ABC123/
bossctl download instagram <url> --cookies-browser Chrome --user-agent "Custom Agent"

# YouTube downloads with quality control
bossctl download youtube https://youtube.com/watch?v=VIDEO_ID --quality 720p
bossctl download youtube <url> --audio-only

# Show strategy configuration
bossctl download strategies

# Show platform info
bossctl download info
```

### Strategy Status Messages
Both Discord and CLI interfaces show the current strategy mode:

- 🚀 **API-Direct Mode**: Using experimental direct API integration
- 🖥️ **CLI Mode**: Using stable subprocess-based approach (default)
- 🔄 **Auto-Fallback**: API failures automatically fallback to CLI when enabled

### Gradual Rollout Configuration
Enable experimental features gradually per platform:

```bash
# Conservative rollout - Enable one platform at a time
export TWITTER_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=true

# Aggressive rollout - Enable all platforms
export TWITTER_USE_API_CLIENT=true
export REDDIT_USE_API_CLIENT=true
export INSTAGRAM_USE_API_CLIENT=true
export YOUTUBE_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=false  # No fallback for testing
```

### Configuration Validation
The system validates configuration at startup:

```python
from boss_bot.core.env import BossSettings
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags

# Settings are validated via Pydantic
settings = BossSettings()
feature_flags = DownloadFeatureFlags(settings)

# Check strategy status
info = feature_flags.get_strategy_info()
print(f"Twitter API enabled: {info['twitter_api']}")
print(f"AI strategy selection enabled: {info['ai_strategy_selection']}")
print(f"AI content analysis enabled: {info['ai_content_analysis']}")
```

## 🏗️ AI Architecture & Integration

### **Multi-Agent System Architecture**

Boss-Bot implements a sophisticated multi-agent architecture using LangGraph for orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                    Discord Bot Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   $download     │  │ $smart-analyze  │  │ $ai-status  │  │
│  │ (AI enhanced)   │  │  (AI powered)   │  │ (AI status) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                LangGraph Workflow Layer                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              DownloadWorkflow                           │ │
│  │   ┌─────────────────────────────────────────────────┐   │ │
│  │   │  State Machine: URL → Strategy → Analysis →    │   │ │
│  │   │  Download → Validation → Upload                 │   │ │
│  │   └─────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ StrategySelector│  │ ContentAnalyzer │  │SocialMedia  │  │
│  │   Agent         │  │     Agent       │  │   Agent     │  │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────┐ │  │
│  │ │URL Analysis │ │  │ │Quality Score│ │  │ │Sentiment│ │  │
│  │ │Confidence   │ │  │ │Engagement   │ │  │ │Trends   │ │  │
│  │ │Reasoning    │ │  │ │Insights     │ │  │ │Analysis │ │  │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────┘ │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Model Provider Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │     OpenAI      │  │   Anthropic     │  │   Google    │  │
│  │  (GPT-4, 3.5)   │  │    (Claude)     │  │  (Gemini)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Epic 5 Strategy Pattern Layer                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ TwitterStrategy │  │ RedditStrategy  │  │YouTubeStrat │  │
│  │ (API/CLI)       │  │ (API/CLI)       │  │ (API/CLI)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### **Agent Communication Protocol**

```python
# Agent Request/Response Pattern
from boss_bot.ai.agents.context import AgentRequest, AgentResponse, AgentContext

# Create request context
context = AgentContext(
    request_id="unique_id",
    user_id="discord_user_id",
    guild_id="discord_guild_id"
)

# Create agent request
request = AgentRequest(
    context=context,
    action="select_strategy",  # or "analyze_content"
    data={"url": "https://twitter.com/...", "user_preferences": {}}
)

# Process with AI agent
response = await strategy_selector.process_request(request)

# Response includes confidence, reasoning, and results
if response.success:
    platform = response.result.get("platform")
    confidence = response.confidence  # 0.0-1.0
    reasoning = response.reasoning    # AI explanation
```

### **Feature Flag Integration**

AI capabilities are controlled by feature flags for safe gradual rollout:

```python
# Feature flags control AI activation
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags

flags = DownloadFeatureFlags(settings)

# Check AI availability
if flags.ai_strategy_selection_enabled:
    # Use AI for strategy selection
    strategy, ai_metadata = await get_ai_enhanced_strategy(url, ctx)
else:
    # Fall back to traditional pattern matching
    strategy = get_traditional_strategy(url)

if flags.ai_content_analysis_enabled:
    # Enhance metadata with AI insights
    enhanced_data = await content_analyzer.process_request(request)
```

### **Error Handling & Fallback**

The system includes robust error handling:

```python
try:
    # Try AI-enhanced processing
    response = await ai_agent.process_request(request)
    if response.success:
        return response.result
except Exception as ai_error:
    logger.warning(f"AI processing failed: {ai_error}")

# Always fall back to traditional methods
return traditional_processing(url)
```

### **Performance Monitoring**

AI agents include built-in performance tracking:

```python
# Access agent performance metrics
metrics = strategy_selector.performance_metrics
print(f"Requests processed: {metrics['request_count']}")
print(f"Average response time: {metrics['average_processing_time_ms']}ms")
print(f"Success rate: {metrics['success_rate']:.2%}")
```

## Testing Guidelines
- Use pytest for all tests with proper module organization matching src structure
- Test async code with `@pytest.mark.asyncio` decorator
- Use fixtures from conftest.py for test setup/teardown
- Mock Discord components with pytest-mock and dpytest
- Use function-scoped fixtures to ensure test isolation
- Include type hints in fixture definitions and test functions
- Use proper assertions and test both success and error cases
- Check for proper exception handling and error responses
- Use skipping with `@pytest.mark.skip_until` for in-progress features
- Always clean up resources with fixture teardown logic

### AI Testing Patterns 🤖
- **AI Agent Testing**: Use `pytest-recording` for VCR-style AI interaction testing
- **Mock AI Responses**: Create structured mock responses with confidence scores and reasoning
- **Feature Flag Testing**: Test both AI-enabled and AI-disabled scenarios
- **Fallback Testing**: Verify graceful degradation when AI fails
- **Performance Testing**: Assert AI response times meet requirements (<500ms)

#### AI Test Examples
```python
# Test AI agent with mock responses
@pytest.mark.asyncio
async def test_strategy_selector_with_ai_enabled(fixture_strategy_selector):
    """Test AI strategy selection with mocked LLM response."""
    request = AgentRequest(
        context=AgentContext(request_id="test", user_id="123"),
        action="select_strategy",
        data={"url": "https://twitter.com/user/status/123"}
    )

    response = await fixture_strategy_selector.process_request(request)

    assert response.success
    assert response.confidence > 0.8
    assert response.result["platform"] == "twitter"

# Test fallback when AI disabled
@pytest.mark.asyncio
async def test_download_fallback_when_ai_disabled(fixture_ai_disabled_cog):
    """Test command falls back to traditional methods when AI disabled."""
    ctx = mocker.Mock(spec=commands.Context)
    ctx.send = mocker.AsyncMock()

    await fixture_ai_disabled_cog.smart_download.callback(
        fixture_ai_disabled_cog, ctx, "https://twitter.com/test"
    )

    # Should call regular download method
    fixture_ai_disabled_cog.download.assert_called_once()
```

### Fixture Naming and Organization Conventions
Based on analysis of existing conftest.py files and .cursor/rules, follow these patterns:

#### Fixture Naming Patterns
- **Standardized Prefix**: All custom fixtures use `fixture_` prefix (e.g., `fixture_settings_test`, `fixture_bot_test`)
- **Descriptive Suffixes**: Add context-specific suffixes like `_test`, `_mock`, `_data`
- **Environment Variables**: Use `fixture_env_vars_test` pattern for environment setup
- **Bot/Discord**: Use `fixture_discord_bot`, `fixture_mock_bot_test` patterns
- **Avoid Collisions**: Never create fixtures with generic names like `bot`, `settings`, `client`

#### Conftest.py Organization Structure
```python
# Standard organization pattern found in tests/conftest.py:

"""Test configuration and fixtures for boss-bot."""

import pytest
from unittest.mock import AsyncMock, Mock
# ... other imports

# ============================================================================
# Environment and Settings Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_env_vars_test() -> dict[str, str]:
    """Provide test environment variables."""
    # Implementation here

# ============================================================================
# Bot and Discord Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_mock_bot_test(mocker) -> Mock:
    """Create a mocked BossBot instance for testing."""
    # Implementation here

# ============================================================================
# Storage and Manager Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def fixture_queue_manager_test(fixture_settings_test) -> QueueManager:
    """Create QueueManager instance for testing."""
    # Implementation here
```

#### Fixture Documentation Standards
- **Comprehensive Docstrings**: Every fixture must have a docstring explaining its purpose
- **Type Hints**: All fixtures must include proper return type annotations
- **Scope Declaration**: Explicitly declare scope (prefer `scope="function"` for isolation)
- **Dependencies**: Document fixture dependencies in docstring

#### pytest-mock Usage Patterns
- **Always use `mocker` fixture**: Never import `unittest.mock` directly
- **AsyncMock for async methods**: Use `mocker.AsyncMock()` for async Discord methods
- **Spec parameter**: Use `spec=` parameter when mocking complex objects
```python
# Correct pattern:
ctx = mocker.Mock(spec=commands.Context)
ctx.send = mocker.AsyncMock()

# Never do this:
from unittest.mock import Mock, AsyncMock
```

#### Built-in Fixture Usage
- **tmp_path**: Use for temporary file operations (preferred over custom temp directories)
- **monkeypatch**: Use for environment variable patching
- **caplog**: Use for testing logging output

#### Test File Organization
- Match src directory structure in tests/
- One test file per source module
- Use descriptive test function names with `test_` prefix
- Group related tests in classes when appropriate

### Discord.py Testing Patterns
- **Command Testing Approaches**:
  1. **Direct Testing (Mock-Based)**:
     - Direct method calls to cog commands won't work (e.g., `cog.download(ctx, url)`) because they're decorated with `@commands.command`
     - Instead, call the command's callback directly: `await cog.download.callback(cog, ctx, url)`
     - Always include `ctx.send = mocker.AsyncMock()` when mocking a Context
     - When working with context objects, ensure they're fully mocked:
     ```python
     # Create context
     ctx = mocker.Mock(spec=commands.Context)
     ctx.send = mocker.AsyncMock()
     ctx.author = mocker.Mock()
     ctx.author.id = 12345
     ctx.channel = mocker.Mock()
     ctx.channel.id = 67890
     ```

  2. **Integration Testing (dpytest)**:
     - When using dpytest for integration testing, avoid using custom-created user objects
     - Instead, use the built-in configuration helpers:
     ```python
     # Configure dpytest with the bot
     dpytest.configure(bot)

     # Access pre-configured objects
     config = dpytest.get_config()
     guild = config.guilds[0]
     channel = config.channels[0]
     member = config.members[0]

     # Send message with existing member
     message = await dpytest.message("$command", channel=channel, member=member)
     ```
     - Ensure the bot has commands registered with `await bot._async_setup_hook()` before testing
     - Call `await dpytest.empty_queue()` after tests to prevent message leakage

  3. **Error Handling in Commands**:
     - Discord commands should handle exceptions gracefully and send user-friendly error messages
     - When testing exception scenarios, use `side_effect` to simulate failures:
     ```python
     # Test queue full scenario
     fixture_mock_bot_test.queue_manager.add_to_queue.side_effect = Exception("Queue is currently full")
     await cog.download.callback(cog, ctx, url)
     # Verify error message is sent to user
     assert "Queue is currently full" in ctx.send.call_args[0][0]
     ```
     - Commands should wrap risky operations in try/except blocks
     - Always use `await ctx.send(str(e))` to send exception messages to users

### Test Status and Recent Fixes ✅
**Current Test Status**: All tests passing (407 tests total) with comprehensive coverage.

#### **Core Test Suite** (326 tests)
- All traditional functionality tests passing
- 66% code coverage for core functionality
- 9 tests skipped (legacy or environment-dependent)

#### **🤖 AI Test Suite** (82 tests) - **NEW!**
- ✅ **All AI tests passing** (81 passed, 1 skipped)
- ✅ **Agent Tests**: 53 tests covering all AI agents
  - BaseAgent: 17 tests (lifecycle, performance, LangGraph integration)
  - StrategySelector: 13 tests (platform detection, confidence scoring)
  - ContentAnalyzer: 11 tests (quality assessment, metadata enrichment)
  - SocialMediaAgent: 12 tests (sentiment analysis, trend detection)
- ✅ **Workflow Tests**: 20 tests covering LangGraph coordination
- ✅ **Discord Integration Tests**: 12 tests covering AI-powered commands
- ✅ **Feature Flag Tests**: Comprehensive AI feature flag testing

#### **AI Integration Achievements**:
- ✅ **Complete LangGraph Integration**: Full state machine workflows implemented
- ✅ **Multi-Agent Coordination**: Agent communication protocols tested
- ✅ **Discord Command Integration**: All AI-powered commands (`$smart-analyze`, `$smart-download`, `$ai-status`) tested
- ✅ **Fallback Mechanisms**: Graceful degradation when AI disabled
- ✅ **Performance Monitoring**: Built-in metrics and tracking tested

**Recent AI Implementation Completed**:
- ✅ **AI Agent Infrastructure**: Complete multi-agent system with LangGraph orchestration
- ✅ **Discord AI Commands**: Three new AI-powered Discord commands implemented
- ✅ **Feature Flag System**: AI capabilities controlled by environment variables
- ✅ **Model Provider Support**: OpenAI, Anthropic, and Google model integration
- ✅ **Comprehensive Testing**: 82 AI tests ensuring reliability and performance

**Previous Test Patterns Fixed**:
- **Queue Tests Pattern**: Use `await cog.command_name.callback(cog, ctx, *args)` for testing Discord command cogs
- **Discord Embed Testing**: Access embed via `call_args.kwargs['embed']` instead of positional arguments
- **String Handling**: Use `.strip().split('\n')` to avoid empty strings from trailing newlines
- **Exception Handling**: Commands properly handle exceptions and send user-friendly error messages via `await ctx.send(str(e))`
- **AI Agent Testing**: Structured testing of AI responses with confidence scores and reasoning validation

## Code Style Guidelines
- Python 3.12+ with type hints throughout
- Use Discord.py and Pydantic patterns for Discord bot and data validation
- Imports: Use `ruff` import sorting (sorted, grouped by stdlib/third-party/local)
- Formatting: 120 character line length with Google docstring style
- Error handling: Use proper exception handling and logging
- File organization: Follow the existing module structure in src/boss_bot/
- Use dependency injection patterns with settings passed via constructor
- Add linter directives at top of files when necessary
- Use SecretStr for sensitive values and proper validation in Pydantic models

## Common Patterns
- Command handling: Use discord.ext.commands decorators in cogs
- Error handling: Implement specific handlers for different command errors
- Configuration: Use environment variables via BossSettings
- Resource management: Clean up resources in close() or teardown methods
- Testing: Create isolated fixtures with appropriate scope and teardown logic
- Async/await: Use async for all I/O operations and Discord API calls

## 🤖 AI Capabilities (✅ IMPLEMENTED)

### **Current AI Features** (Production Ready)
- ✅ **Multi-Agent Architecture**: Complete LangGraph-based agent coordination system
- ✅ **Intelligent Strategy Selection**: AI-powered platform detection with confidence scoring
- ✅ **Advanced Content Analysis**: Quality assessment, engagement prediction, audience insights
- ✅ **Discord AI Commands**: 3 new AI-powered commands (`$smart-analyze`, `$smart-download`, `$ai-status`)
- ✅ **LangGraph Workflows**: State machine orchestration for complex multi-step AI processes
- ✅ **Model Provider Support**: OpenAI, Anthropic, Google integration with automatic fallback
- ✅ **Feature Flag Control**: Gradual AI rollout with environment variable configuration
- ✅ **Performance Monitoring**: Built-in metrics tracking and agent performance analysis
- ✅ **Graceful Degradation**: Robust fallback to traditional methods when AI unavailable

### **AI Agent Ecosystem**
- ✅ **StrategySelector Agent**: Optimal download strategy selection with reasoning
- ✅ **ContentAnalyzer Agent**: Content quality scoring and metadata enrichment
- ✅ **SocialMediaAgent**: Sentiment analysis, trend detection, cross-platform coordination
- ✅ **DownloadWorkflow**: LangGraph state machine for multi-agent coordination

### **Testing & Reliability**
- ✅ **82 AI Tests**: Comprehensive test coverage including LangGraph workflows
- ✅ **VCR Testing**: pytest-recording for AI interaction replay
- ✅ **Mock Testing**: Structured AI response testing with confidence validation
- ✅ **Integration Testing**: Discord command integration with AI agents
- ✅ **Performance Testing**: Response time and reliability validation

### **Future AI Enhancements** (Planned)
- 🔄 **Vision Models**: Image and video content analysis
- 🔄 **Advanced Workflows**: Complex multi-agent coordination scenarios
- 🔄 **User Learning**: Personalized recommendations based on usage patterns
- 🔄 **Content Moderation**: AI-powered safety and compliance checking
- 🔄 **Batch Processing**: Intelligent queue optimization and prioritization

## Project Structure

### **🎯 Current AI-Enhanced Structure** (✅ IMPLEMENTED)

The project now features a complete AI-enhanced structure with all LangGraph components implemented:

```
src/boss_bot/
├── __init__.py
├── __main__.py
├── __version__.py
├── main_bot.py                    # Legacy entry point (to be phased out)
│
├── ai/                           # 🤖 AI Components (✅ COMPLETED)
│   ├── __init__.py
│   ├── agents/                   # ✅ LangGraph agents implemented
│   │   ├── __init__.py
│   │   ├── base_agent.py         # ✅ Base agent with LangGraph integration
│   │   ├── content_analyzer.py   # ✅ Content analysis agent
│   │   ├── social_media_agent.py # ✅ Social media processing agent
│   │   ├── strategy_selector.py  # ✅ Strategy selection agent
│   │   └── context.py           # ✅ Agent communication protocol
│   ├── strategies/               # ✅ AI-enhanced strategies
│   │   ├── __init__.py
│   │   └── ai_enhanced_strategy.py # ✅ Strategy wrapper with AI
│   ├── workflows/                # ✅ LangGraph workflows
│   │   ├── __init__.py
│   │   └── download_workflow.py  # ✅ Multi-agent coordination
│   ├── chains/                   # 🔄 Future: LangChain chains
│   │   └── __init__.py
│   ├── tools/                    # 🔄 Future: LangChain tools
│   │   └── __init__.py
│   ├── prompts/                  # 🔄 Future: Prompt templates
│   │   └── __init__.py
│   └── memory/                   # 🔄 Future: Advanced memory
│       └── __init__.py
│
├── bot/                          # 🤖 Discord Bot Components
│   ├── __init__.py
│   ├── client.py                # Main bot client
│   ├── bot_help.py             # Custom help command
│   ├── cogs/                   # Discord command cogs
│   │   ├── __init__.py
│   │   ├── downloads.py        # Download commands
│   │   ├── task_queue.py      # Queue management commands
│   │   ├── ai_commands.py     # AI-powered commands (future)
│   │   └── admin.py           # Admin commands (future)
│   ├── events/                 # Discord event handlers
│   │   ├── __init__.py
│   │   ├── message_handler.py  # Message processing
│   │   └── error_handler.py    # Error handling
│   └── middleware/             # Bot middleware
│       ├── __init__.py
│       ├── rate_limiting.py    # Rate limiting middleware
│       └── authentication.py  # User authentication
│
├── cli/                          # 🖥️ CLI Components (Typer)
│   ├── __init__.py
│   ├── main.py                  # Main CLI entry point
│   ├── commands/               # CLI subcommands
│   │   ├── __init__.py
│   │   ├── bot.py             # Bot management commands
│   │   ├── queue.py           # Queue management commands
│   │   ├── download.py        # Download commands
│   │   ├── ai.py              # AI workflow commands
│   │   └── config.py          # Configuration commands
│   ├── utils/                  # CLI utilities
│   │   ├── __init__.py
│   │   ├── formatters.py      # Rich formatting utilities
│   │   └── validators.py      # Input validation
│   └── config/                 # CLI configuration
│       ├── __init__.py
│       └── settings.py        # CLI-specific settings
│
├── core/                         # 🏗️ Core Business Logic
│   ├── __init__.py
│   ├── env.py                   # Environment configuration
│   ├── queue/                   # Queue management
│   │   ├── __init__.py
│   │   ├── manager.py          # Queue manager (renamed from core_queue.py)
│   │   ├── models.py           # Queue data models
│   │   └── processors.py       # Queue processing logic
│   ├── downloads/              # Download management
│   │   ├── __init__.py
│   │   ├── manager.py          # Download manager
│   │   ├── handlers/           # Protocol-specific handlers
│   │   │   ├── __init__.py
│   │   │   ├── base_handler.py # Abstract base handler
│   │   │   ├── twitter_handler.py # Twitter/X handling (✅ implemented)
│   │   │   ├── reddit_handler.py  # Reddit handling (✅ implemented)
│   │   │   ├── youtube.py      # YouTube handling (🔄 planned)
│   │   │   ├── instagram.py    # Instagram handling (🔄 planned)
│   │   │   └── generic.py      # Generic URL handling (🔄 planned)
│   │   └── models.py           # Download data models
│   └── services/               # Core services
│       ├── __init__.py
│       ├── content_service.py  # Content analysis service
│       └── notification_service.py # Notification service
│
├── storage/                      # 💾 Storage & Data Management
│   ├── __init__.py
│   ├── managers/               # Storage managers
│   │   ├── __init__.py
│   │   ├── file_manager.py     # File storage management
│   │   ├── quota_manager.py    # Quota management
│   │   └── validation_manager.py # File validation
│   ├── backends/               # Storage backends
│   │   ├── __init__.py
│   │   ├── local.py           # Local filesystem
│   │   ├── s3.py              # AWS S3 (future)
│   │   └── azure.py           # Azure Storage (future)
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── file_models.py     # File metadata models
│   └── migrations/             # Database migrations (future)
│       └── __init__.py
│
├── monitoring/                   # 📊 Monitoring & Observability
│   ├── __init__.py
│   ├── health/                 # Health checks
│   │   ├── __init__.py
│   │   ├── checker.py         # Health check manager
│   │   └── checks/            # Individual health checks
│   │       ├── __init__.py
│   │       ├── discord.py     # Discord connectivity
│   │       ├── storage.py     # Storage health
│   │       └── ai.py          # AI service health
│   ├── metrics/                # Metrics collection
│   │   ├── __init__.py
│   │   ├── collector.py       # Metrics collector
│   │   └── exporters/         # Metrics exporters
│   │       ├── __init__.py
│   │       ├── prometheus.py  # Prometheus exporter
│   │       └── datadog.py     # Datadog exporter (future)
│   └── logging/                # Logging configuration
│       ├── __init__.py
│       ├── config.py          # Logging setup
│       └── formatters.py      # Log formatters
│
├── schemas/                      # 📄 Data Schemas & Validation
│   ├── __init__.py
│   ├── api/                    # API schemas
│   │   ├── __init__.py
│   │   ├── downloads.py       # Download API schemas
│   │   └── queue.py           # Queue API schemas
│   ├── discord/                # Discord-specific schemas
│   │   ├── __init__.py
│   │   └── events.py          # Discord event schemas
│   └── ai/                     # AI-related schemas
│       ├── __init__.py
│       ├── prompts.py         # Prompt schemas
│       └── responses.py       # AI response schemas
│
├── integrations/                 # 🔌 External Integrations
│   ├── __init__.py
│   ├── langsmith/              # LangSmith integration
│   │   ├── __init__.py
│   │   └── client.py
│   ├── anthropic/              # Anthropic API integration
│   │   ├── __init__.py
│   │   └── client.py
│   ├── openai/                 # OpenAI API integration
│   │   ├── __init__.py
│   │   └── client.py
│   └── webhooks/               # Webhook handlers
│       ├── __init__.py
│       └── discord.py
│
├── utils/                        # 🔧 Shared Utilities
│   ├── __init__.py
│   ├── decorators.py           # Common decorators
│   ├── validators.py           # Validation utilities
│   ├── formatters.py           # Formatting utilities
│   ├── async_utils.py          # Async helper functions
│   └── security.py             # Security utilities
│
└── api/                          # 🌐 REST/GraphQL API (Future)
    ├── __init__.py
    ├── routes/                 # API routes
    │   ├── __init__.py
    │   ├── downloads.py       # Download endpoints
    │   └── queue.py           # Queue endpoints
    ├── middleware/             # API middleware
    │   ├── __init__.py
    │   ├── auth.py            # Authentication
    │   └── rate_limit.py      # Rate limiting
    └── models/                 # API response models
        ├── __init__.py
        └── responses.py       # Response schemas
```

### Key Organizational Principles

1. **Separation of Concerns**: Each top-level module has a clear, single responsibility
2. **AI-First Design**: Dedicated `ai/` module for LangChain/LangGraph components
3. **CLI Modularity**: Expandable CLI with subcommands for different operations
4. **Bot Isolation**: Discord-specific code contained in `bot/` module
5. **Core Services**: Business logic separated from interface layers
6. **Monitoring**: Comprehensive observability with health checks and metrics
7. **Future-Proof**: Structure accommodates planned features (API, additional storage backends)

### Migration Path

1. **Phase 1**: Reorganize existing code into new structure
2. **Phase 2**: Implement AI components (agents, chains, tools)
3. **Phase 3**: Expand CLI with subcommands
4. **Phase 4**: Add REST API layer
5. **Phase 5**: Implement additional integrations and storage backends

### CLI Development
The CLI (`src/boss_bot/cli/`) provides command-line control of the bot:
- Main entry point: `goobctl` → `boss_bot.cli.main`
- Subcommand structure using Typer with dedicated command modules
- Rich formatting for console output
- Commands for bot management, queue operations, AI workflows, and configuration
- Pluggable subcommand architecture for extensibility
