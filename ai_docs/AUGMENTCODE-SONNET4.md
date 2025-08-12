# AUGMENTCODE-SONNET4.md

This file provides comprehensive guidance to Augment Code's Sonnet 4 AI assistant when working with the Boss-Bot codebase.

## Project Overview

**Boss-Bot** is a sophisticated AI-powered Discord bot that combines intelligent media downloading capabilities with advanced multi-agent orchestration. Built with modern Python practices, it leverages LangChain, LangGraph, and cutting-edge AI models to provide intelligent content analysis, strategy selection, and workflow optimization.

### Core Purpose
- **Primary Function**: AI-enhanced Discord bot for intelligent media downloads from social platforms (Twitter, Reddit, YouTube, Instagram)
- **AI Integration**: Multi-agent system using LangGraph for complex decision-making and workflow orchestration
- **Architecture**: Modular, event-driven design with comprehensive testing and monitoring
- **Development Focus**: Test-driven development with 407+ comprehensive tests ensuring reliability

### Key Features

#### 🤖 AI-Powered Intelligence
- **Multi-Agent System**: LangGraph-based agent orchestration with supervisor patterns
- **Strategy Selection**: AI-enhanced platform detection and optimal download strategy selection
- **Content Analysis**: Multi-modal content analysis for quality assessment and safety validation
- **Natural Language Processing**: Intent classification and entity extraction for user commands
- **Workflow Optimization**: Intelligent workflow routing and error recovery

#### 📥 Media Download Capabilities
- **Platform Support**: Twitter/X, Reddit, YouTube, Instagram with extensible handler architecture
- **Quality Options**: Configurable quality settings (low/good/high/best) with AI recommendations
- **Concurrent Processing**: Async download manager with configurable concurrency limits
- **Queue Management**: Intelligent queue system with priority handling and status tracking
- **Error Recovery**: Robust error handling with retry mechanisms and fallback strategies

#### 🔧 Discord Integration
- **Command System**: Comprehensive Discord.py cogs with AI-enhanced commands
- **User Experience**: Intuitive command interface with natural language support
- **Permissions**: Role-based access control and admin functionality
- **Real-time Updates**: Live status updates and progress tracking
- **Help System**: Context-aware help with AI-powered suggestions

#### 🏗️ Technical Excellence
- **Modern Python**: Python 3.12+ with type hints, async/await, and modern patterns
- **Package Management**: UV for fast, reliable dependency management
- **Testing**: 407+ tests with pytest, including AI agent testing and integration tests
- **Code Quality**: Ruff linting, pre-commit hooks, and comprehensive CI/CD
- **Monitoring**: Structured logging with Loguru, metrics, and observability

### Project Status
- ✅ **Core Functionality**: Complete and stable media download system
- ✅ **AI Integration**: Production-ready multi-agent system with LangGraph
- ✅ **Testing**: 407 tests with 100% passing rate and comprehensive coverage
- ✅ **Documentation**: Extensive documentation and development guides
- 🔄 **Active Development**: Ongoing enhancements and new AI features

## Quick Start Commands

### Essential Development Commands
```bash
# Setup and Installation
uv sync --dev                    # Install all dependencies
just install                     # Install project + git hooks
cp .env.example .env            # Setup environment configuration

# Testing and Quality
just test                       # Run full test suite (407 tests)
just check                      # Run all quality checks (lint, type, format, security)
just test-ci                    # CI-style testing with coverage
just test-ai                    # Run AI-specific tests (82 tests)

# Development Workflow
just format                     # Format code with Ruff
just check-code                 # Lint with Ruff
just check-type                 # Type checking
just check-security             # Security audit with Bandit

# Running the Bot
uv run python -m boss_bot       # Start Discord bot
uv run bossctl --help          # CLI interface
uv run bossctl version         # Check version
```

### Testing Commands
```bash
# Core Tests (326 tests)
uv run pytest tests/test_core/ tests/test_bot/ -v

# AI Tests (82 tests)
uv run pytest tests/test_ai/ -v

# Specific Test Categories
uv run pytest tests/test_ai/test_agents/ -v                    # Agent tests
uv run pytest tests/test_ai/test_workflows/ -v                # Workflow tests
uv run pytest tests/test_bot/test_discord_ai_integration.py -v # Discord AI integration

# Test with Coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# VCR Testing (for API interactions)
uv run pytest --record-mode=once --verbose                    # Record new interactions
uv run pytest --record-mode=rewrite --verbose                 # Update existing recordings
```

## Architecture Overview

### High-Level Architecture
```
boss-bot/
├── src/boss_bot/           # Main package
│   ├── ai/                 # 🤖 AI Components (LangGraph Multi-Agent System)
│   │   ├── agents/         # AI agents (strategy, content analysis, etc.)
│   │   ├── workflows/      # LangGraph workflows
│   │   ├── strategies/     # AI-enhanced strategies
│   │   └── assistants/     # LangGraph Cloud integration
│   ├── bot/                # Discord bot functionality
│   │   ├── client.py       # Main BossBot class
│   │   └── cogs/           # Discord command modules
│   ├── core/               # Core business logic
│   │   ├── downloads/      # Download system (managers, handlers, strategies)
│   │   ├── queue/          # Queue management
│   │   └── env.py          # Configuration management
│   ├── monitoring/         # Logging, metrics, and observability
│   ├── storage/            # File storage management
│   └── utils/              # Utility functions
├── tests/                  # Comprehensive test suite (407 tests)
│   ├── test_ai/           # AI system tests (82 tests)
│   ├── test_bot/          # Discord bot tests
│   └── test_core/         # Core functionality tests
└── docs/                   # Documentation
```

### Core Components

#### 1. BossBot Client (`src/boss_bot/bot/client.py`)
The main Discord bot class extending `discord.ext.commands.Bot`:
- **Dependency Injection**: Clean separation of concerns with injected services
- **AI Integration**: Seamless integration with AI agents and workflows
- **Event Handling**: Comprehensive Discord event handling
- **Command Management**: Dynamic cog loading and command registration

#### 2. AI Multi-Agent System (`src/boss_bot/ai/`)
LangGraph-powered multi-agent architecture:
- **BaseAgent**: Abstract base class for all AI agents with standardized interfaces
- **StrategySelector**: AI-enhanced platform detection and strategy selection
- **ContentAnalyzer**: Multi-modal content analysis and safety validation
- **DownloadWorkflow**: LangGraph workflow orchestrating the entire download process
- **LangGraph Integration**: State machines, checkpointing, and agent coordination

#### 3. Download System (`src/boss_bot/core/downloads/`)
Robust, extensible download architecture:
- **DownloadManager**: Async download orchestration with concurrency control
- **Strategy Pattern**: Platform-specific handlers (Twitter, Reddit, YouTube, Instagram)
- **Queue System**: Intelligent queue management with priority and status tracking
- **Error Handling**: Comprehensive error recovery and retry mechanisms

#### 4. Configuration Management (`src/boss_bot/core/env.py`)
Pydantic-based settings with environment variable support:
- **Type Safety**: Full type checking for all configuration options
- **Environment Integration**: Seamless .env file and environment variable support
- **AI Configuration**: Dedicated AI model and behavior settings
- **Validation**: Automatic validation and error reporting for invalid configurations

## Technical Architecture Deep Dive

### AI Multi-Agent System Architecture

#### LangGraph Integration
Boss-Bot implements a sophisticated multi-agent system using LangGraph for state management and workflow orchestration:

```python
# Agent Request/Response Pattern
from boss_bot.ai.agents.context import AgentRequest, AgentResponse, AgentContext

# Create request context
context = AgentContext(
    request_id="unique_id",
    user_id="discord_user_id",
    guild_id="discord_guild_id"
)

# Process with AI agent
response = await strategy_selector.process_request(request)
```

#### Agent Hierarchy
1. **BaseAgent** (`src/boss_bot/ai/agents/base_agent.py`)
   - Abstract base class with standardized interfaces
   - Request validation and response formatting
   - Performance metrics and logging
   - LangGraph react agent integration

2. **StrategySelector** (`src/boss_bot/ai/agents/strategy_selector.py`)
   - AI-enhanced platform detection (Twitter, Reddit, YouTube, Instagram)
   - Confidence scoring and reasoning
   - User preference integration
   - Fallback to traditional pattern matching

3. **ContentAnalyzer** (`src/boss_bot/ai/agents/content_analyzer.py`)
   - Multi-modal content analysis
   - Quality assessment and safety validation
   - Metadata extraction and enrichment
   - Policy compliance checking

4. **DownloadWorkflow** (`src/boss_bot/ai/workflows/download_workflow.py`)
   - LangGraph state machine orchestration
   - Error handling and recovery
   - Progress tracking and status updates
   - Parallel processing coordination

### Download System Architecture

#### Strategy Pattern Implementation
```python
# Platform-specific handlers with AI enhancement
class TwitterHandler(BaseDownloadHandler):
    async def download(self, url: str, **options) -> DownloadResult:
        # AI-enhanced download logic with quality optimization

class RedditHandler(BaseDownloadHandler):
    async def download(self, url: str, **options) -> DownloadResult:
        # Reddit-specific download implementation
```

#### Handler Capabilities
- **TwitterHandler**: X/Twitter media extraction with API fallbacks
- **RedditHandler**: Reddit post and media download with gallery support
- **YouTubeHandler**: YouTube video/audio download via yt-dlp integration
- **InstagramHandler**: Instagram media extraction (planned)

#### Download Manager
- **Async Orchestration**: Concurrent download management with configurable limits
- **Queue Integration**: Seamless integration with queue system for job management
- **Progress Tracking**: Real-time progress updates and status reporting
- **Error Recovery**: Automatic retry with exponential backoff

### Discord Bot Architecture

#### Command System (Cogs)
```python
# AI-enhanced Discord commands
@commands.command(name="smart-download")
async def smart_download(self, ctx, url: str):
    """AI-powered download with automatic strategy selection."""
    # Integrates with AI agents for intelligent processing
```

#### Cog Organization
- **DownloadCog**: Core download commands with AI integration
- **QueueCog**: Queue management and status commands
- **AdminCog**: Administrative functions and bot management
- **AICog**: AI-specific commands and diagnostics

#### Event Handling
- **Message Processing**: Natural language command interpretation
- **Error Handling**: Graceful error reporting with user-friendly messages
- **Status Updates**: Real-time progress and completion notifications

### Data Flow Architecture

#### Request Processing Flow
1. **Discord Command** → User issues command via Discord
2. **Command Parsing** → Discord.py processes and validates command
3. **AI Agent Routing** → Request routed to appropriate AI agent
4. **Strategy Selection** → AI selects optimal download strategy
5. **Content Analysis** → AI analyzes content for quality/safety
6. **Download Execution** → Download manager executes with selected strategy
7. **Progress Updates** → Real-time status updates to Discord
8. **Completion** → Final result delivery and cleanup

#### State Management
- **LangGraph State**: Persistent state across agent interactions
- **Queue State**: Download queue status and job tracking
- **User State**: User preferences and historical data
- **System State**: Bot health, metrics, and configuration

### Integration Patterns

#### AI Service Integration
```python
# Multiple AI provider support
SUPPORTED_PROVIDERS = {
    "openai": OpenAI,
    "anthropic": Anthropic,
    "google": GoogleGenerativeAI,
    "cohere": Cohere,
    "groq": Groq
}
```

#### External Service Integration
- **LangChain**: Core AI framework and model abstraction
- **LangGraph**: Workflow orchestration and state management
- **LangSmith**: AI observability and debugging
- **Redis**: Optional caching and state persistence
- **FFmpeg**: Media processing and format conversion

## Development Workflow and Tools

### Package Management with UV

Boss-Bot uses **UV** as the primary package manager for fast, reliable dependency management:

#### Core UV Commands
```bash
# Dependency Management
uv add package_name              # Add runtime dependency
uv add --dev package_name        # Add development dependency
uv remove package_name           # Remove dependency
uv sync                          # Install all dependencies from lock file
uv sync --dev                    # Install with development dependencies
uv lock                          # Generate/update lock file
uv lock --upgrade                # Upgrade all dependencies

# Environment Management
uv venv                          # Create virtual environment
uv run command                   # Run command in UV environment
uv run python script.py         # Execute Python scripts
uv run pytest                   # Run tests
uv tree                          # Show dependency tree
```

#### UV Configuration
```toml
# pyproject.toml - UV workspace configuration
[tool.uv.workspace]
members = ["src/boss_bot"]

[tool.uv.sources]
pytest-freezegun = { git = "https://github.com/bossjones/pytest-freezegun" }
```

### Task Automation with Just

**Just** serves as the primary task runner, replacing traditional Makefiles:

#### Essential Just Commands
```bash
# Development Workflow
just install                     # Install project + git hooks
just check                       # Run all quality checks
just format                      # Format code with Ruff
just test                        # Run full test suite
just clean                       # Clean build artifacts

# Testing Commands
just test-ci                     # CI-style testing with coverage
just test-vcr                    # Run tests with VCR recording
just test-fix                    # Fix code via pre-commit
just check-coverage              # Check test coverage

# Package Management
just uv-add package              # Add dependency via UV
just uv-sync                     # Sync dependencies
just uv-update                   # Update all dependencies
just uv-tree                     # Show dependency tree

# Code Quality
just check-code                  # Lint with Ruff
just check-type                  # Type checking
just check-format                # Check code formatting
just check-security              # Security audit with Bandit
```

#### Just Configuration Structure
```
justfiles/
├── variables.just               # Global variables and settings
├── uv.just                      # UV package management commands
├── test.just                    # Testing commands
├── check.just                   # Code quality checks
├── format.just                  # Code formatting
├── clean.just                   # Cleanup commands
├── install.just                 # Installation commands
└── package.just                 # Package building
```

### Code Quality and Formatting

#### Ruff Integration
Primary linter and formatter with comprehensive rule coverage:

```toml
# pyproject.toml - Ruff configuration
[tool.ruff]
target-version = "py312"
line-length = 120
select = ["E", "F", "W", "C90", "I", "N", "D", "UP", "YTT", "ANN", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "DJ", "EM", "EXE", "FA", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "TD", "FIX", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "AIR", "PERF", "FURB", "LOG", "RUF"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

#### Pre-commit Hooks
Automated code quality enforcement:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

### Development Environment Setup

#### Quick Setup Process
```bash
# 1. Clone repository
git clone https://github.com/bossjones/boss-bot.git
cd boss-bot

# 2. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies and setup
uv sync --dev                    # Install all dependencies
just install                     # Install git hooks
cp .env.example .env            # Setup environment

# 4. Verify installation
uv run bossctl version          # Check CLI works
just test                       # Run test suite
```

#### Environment Configuration
```bash
# .env - Essential configuration
DISCORD_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_SERVER_ID=your_server_id

# AI Configuration (Optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
LANGCHAIN_API_KEY=your_langchain_key
ENABLE_AI=true

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_REDIS=false
ENABLE_SENTRY=false
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: uv sync --dev
      - name: Run tests
        run: just ci
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### CI Environment Variables
```bash
# Required for CI
OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
DISCORD_TOKEN: "fake-token"  # For testing
UV_FROZEN: true              # Use exact lock file versions
FORCE_COLOR: 1               # Colored output in CI
```

## Testing Strategy and Practices

### Comprehensive Test Suite (407 Tests)

Boss-Bot maintains a robust testing strategy with **407 comprehensive tests** ensuring reliability and quality:

#### Test Organization
```
tests/
├── conftest.py                 # Global test fixtures and configuration
├── test_ai/                    # AI system tests (82 tests)
│   ├── test_agents/           # Individual agent testing
│   ├── test_workflows/        # Workflow integration testing
│   └── test_integration/      # AI-Discord integration tests
├── test_bot/                   # Discord bot tests (150+ tests)
│   ├── test_client.py         # BossBot client testing
│   └── test_cogs/             # Discord command testing
├── test_core/                  # Core functionality tests (175+ tests)
│   ├── test_downloads/        # Download system testing
│   ├── test_queue/            # Queue management testing
│   └── test_handlers/         # Platform handler testing
└── fixtures/                   # Test data and mock responses
```

#### Test Categories and Coverage

##### 1. Core Tests (326 tests)
```bash
# Download System Tests
uv run pytest tests/test_core/test_downloads/ -v
# - Handler tests (Twitter, Reddit, YouTube, Instagram)
# - Strategy pattern validation
# - Download manager functionality
# - Error handling and recovery

# Queue Management Tests
uv run pytest tests/test_core/test_queue/ -v
# - Queue operations (add, remove, status)
# - Priority handling
# - Concurrent access safety
# - Persistence and recovery

# Configuration Tests
uv run pytest tests/test_core/test_env.py -v
# - Environment variable parsing
# - Validation and type checking
# - Default value handling
# - Configuration inheritance
```

##### 2. AI Tests (82 tests)
```bash
# Agent Testing
uv run pytest tests/test_ai/test_agents/ -v
# - BaseAgent functionality (17 tests)
# - StrategySelector AI logic (13 tests)
# - ContentAnalyzer capabilities (11 tests)
# - SocialMediaAgent integration (12 tests)

# Workflow Testing
uv run pytest tests/test_ai/test_workflows/ -v
# - LangGraph workflow execution (20 tests)
# - State management and transitions
# - Error handling and recovery
# - Performance and timeout handling

# Integration Testing
uv run pytest tests/test_ai/test_integration/ -v
# - Discord-AI integration (12 tests)
# - End-to-end workflow testing
# - Multi-agent coordination
# - Real-world scenario simulation
```

##### 3. Discord Bot Tests (150+ tests)
```bash
# Bot Client Testing
uv run pytest tests/test_bot/test_client.py -v
# - Bot initialization and configuration
# - Event handling and command processing
# - Dependency injection validation
# - Error handling and recovery

# Cog Testing (using dpytest)
uv run pytest tests/test_bot/test_cogs/ -v
# - Command execution and validation
# - Permission and access control
# - User interaction simulation
# - Response formatting and delivery
```

### Testing Frameworks and Tools

#### Primary Testing Stack
```python
# Core testing dependencies
pytest>=8.3.4                   # Primary testing framework
pytest-asyncio>=0.25.0         # Async test support
pytest-mock>=3.14.0            # Mocking and fixtures
pytest-cov>=6.0.0              # Coverage reporting
pytest-timeout>=2.2.0          # Test timeout handling

# Discord testing
dpytest>=0.7.0                  # Discord.py testing utilities

# AI testing
pytest-recording>=0.13.2       # VCR for API interactions
agentevals>=0.0.8              # AI agent evaluation framework

# Performance testing
pytest-benchmark>=4.0.0        # Performance benchmarking
pytest-memray>=1.7.0          # Memory profiling
```

#### Testing Patterns and Best Practices

##### 1. Pytest-Mock Exclusive Usage
```python
# ✅ CORRECT: Use mocker fixture
@pytest.mark.asyncio
async def test_download_command(mocker: MockerFixture):
    mock_handler = mocker.Mock(spec=TwitterHandler)
    mock_handler.download.return_value = MediaMetadata(platform="twitter")

    # Test implementation
    result = await download_manager.process(url, handler=mock_handler)
    assert result.success is True
```

##### 2. Discord Command Testing with dpytest
```python
# Discord command testing pattern
@pytest.mark.asyncio
async def test_download_command_success(mock_bot):
    """Test successful download command execution."""
    await dpytest.message("$download https://twitter.com/example")

    # Verify response
    assert dpytest.verify().message().contains().content("Download started")
    assert dpytest.verify().message().contains().embed()
```

##### 3. AI Agent Testing
```python
# AI agent testing with mocked LLM responses
@pytest.mark.asyncio
async def test_strategy_selector_ai_enhanced(mocker: MockerFixture):
    """Test AI-enhanced strategy selection."""
    # Mock LLM response
    mock_llm = mocker.Mock()
    mock_llm.ainvoke.return_value = {"platform": "twitter", "confidence": 0.95}

    # Test agent
    agent = StrategySelector("test", mock_llm, "system prompt", settings)
    response = await agent.process_request(request)

    assert response.success is True
    assert response.confidence >= 0.9
```

##### 4. VCR Testing for API Interactions
```bash
# Record new API interactions
uv run pytest --record-mode=once tests/test_core/test_handlers/

# Update existing recordings
uv run pytest --record-mode=rewrite tests/test_core/test_handlers/

# Use recorded interactions (default)
uv run pytest tests/test_core/test_handlers/
```

### Test Configuration and Fixtures

#### Global Test Configuration
```python
# tests/conftest.py - Global fixtures
@pytest.fixture(scope="function")
def fixture_env_vars_test(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123456789")
    monkeypatch.setenv("ENABLE_AI", "true")
    monkeypatch.setenv("ENABLE_REDIS", "false")
    # ... additional test environment setup

@pytest.fixture(scope="function")
def settings(fixture_env_vars_test):
    """Create test settings instance."""
    return BossSettings(
        discord_token="test_token",
        enable_ai=True,
        enable_redis=False,
        # ... test configuration
    )
```

#### Pytest Configuration
```toml
# pyproject.toml - Pytest settings
[tool.pytest.ini_options]
addopts = [
    '--cov-branch',
    '--cov-report=html:htmlcov',
    '--cov-report=term-missing',
    '--cov-report=xml:cov.xml',
    '--cov=src',
    '--durations=10',
    '--junitxml=junit/test-results.xml',
    '--timeout=30',
    '--timeout_method=thread',
]
testpaths = ["tests"]
markers = [
    "asyncio: mark test as async",
    "integration: mark test as integration test",
    "slow: mark test as slow running",
]
```

## AI System and Agent Architecture

### LangGraph Multi-Agent System

Boss-Bot implements a sophisticated multi-agent architecture using **LangGraph** for workflow orchestration and state management:

#### Core AI Components

##### 1. BaseAgent Foundation
```python
# src/boss_bot/ai/agents/base_agent.py
class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, name: str, model: BaseLanguageModel, system_prompt: str):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self._request_count = 0
        self._total_processing_time = 0.0

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process agent request with validation and metrics."""
        # Request validation, processing, and response formatting

    def create_react_agent(self):
        """Create LangGraph react agent with tools and handoff capabilities."""
        # LangGraph integration for multi-agent coordination
```

##### 2. StrategySelector Agent
```python
# AI-enhanced platform detection and strategy selection
class StrategySelector(BaseAgent):
    """Intelligently selects optimal download strategy based on URL analysis."""

    async def _ai_select_strategy(self, url: str, user_preferences: dict) -> AgentResponse:
        """AI-enhanced strategy selection with confidence scoring."""
        platform = self._detect_platform(url)
        confidence_score = self._calculate_confidence(url, platform)

        return AgentResponse(
            success=True,
            result={
                "platform": platform,
                "recommended_options": self._get_platform_options(platform, user_preferences),
                "strategy_type": "ai_enhanced",
                "url_confidence": confidence_score,
            },
            confidence=confidence_score,
            reasoning=f"AI analysis identified {platform} with {confidence_score:.2f} confidence"
        )
```

##### 3. ContentAnalyzer Agent
```python
# Multi-modal content analysis and safety validation
class ContentAnalyzer(BaseAgent):
    """Analyzes content for quality, safety, and compliance."""

    def __init__(self, name: str, model: BaseLanguageModel, system_prompt: str):
        super().__init__(name, model, system_prompt)
        self.quality_chain = self._build_quality_chain()
        self.safety_chain = self._build_safety_chain()
        self.metadata_chain = self._build_metadata_chain()

    async def analyze(self, media_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run parallel content analysis chains."""
        # Concurrent execution of quality, safety, and metadata analysis
```

#### LangGraph Workflow Integration

##### DownloadWorkflow State Machine
```python
# src/boss_bot/ai/workflows/download_workflow.py
class DownloadWorkflow:
    """LangGraph-powered download workflow orchestration."""

    async def execute(self, url: str, user_preferences: dict = None) -> dict[str, Any]:
        """Execute complete download workflow using LangGraph state machine."""

        if self._has_langgraph():
            return await self._run_langgraph_workflow(state)
        else:
            return await self._run_simple_workflow(state)

    async def _run_langgraph_workflow(self, state: WorkflowState) -> dict[str, Any]:
        """Run workflow using LangGraph state machine."""
        from langgraph.graph import END, StateGraph

        # Create workflow graph
        workflow = StateGraph(WorkflowState)

        # Add workflow nodes
        workflow.add_node("select_strategy", self._strategy_selection_node)
        workflow.add_node("analyze_content", self._content_analysis_node)
        workflow.add_node("execute_download", self._download_node)
        workflow.add_node("handle_error", self._error_handler_node)

        # Define conditional edges
        workflow.add_conditional_edges(
            "select_strategy",
            self._should_analyze_content,
            {
                "analyze": "analyze_content",
                "download": "execute_download",
                "error": "handle_error"
            }
        )

        # Compile and execute
        app = workflow.compile()
        return await app.ainvoke(state)
```

#### Agent Request/Response Pattern
```python
# Standardized agent communication
from boss_bot.ai.agents.context import AgentRequest, AgentResponse, AgentContext

# Create request context
context = AgentContext(
    request_id="unique_id",
    user_id="discord_user_id",
    guild_id="discord_guild_id",
    metadata={"source": "discord_command"}
)

# Create agent request
request = AgentRequest(
    context=context,
    action="select_strategy",
    data={
        "url": "https://twitter.com/example/status/123",
        "user_preferences": {"quality": "high", "format": "mp4"}
    }
)

# Process with AI agent
response = await strategy_selector.process_request(request)

# Response includes confidence, reasoning, and results
if response.success:
    platform = response.result.get("platform")
    confidence = response.confidence  # 0.0-1.0
    reasoning = response.reasoning    # AI explanation
    metadata = response.metadata      # Additional context
```

### AI Integration Patterns

#### Multi-Provider Support
```python
# src/boss_bot/core/env.py - AI provider configuration
SUPPORTED_AI_PROVIDERS = {
    "openai": {
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_env": "OPENAI_API_KEY"
    },
    "anthropic": {
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "google": {
        "models": ["gemini-pro", "gemini-pro-vision"],
        "api_key_env": "GOOGLE_API_KEY"
    },
    "cohere": {
        "models": ["command", "command-light"],
        "api_key_env": "COHERE_API_KEY"
    }
}
```

#### AI-Enhanced Strategy Selection
```python
# Enhanced strategy pattern with AI integration
class AIEnhancedStrategy:
    """AI-enhanced strategy with confidence scoring and reasoning."""

    def enhanced_supports_url(self, url: str) -> dict:
        """AI-enhanced URL support detection."""
        if not self.settings.ai_strategy_selection_enabled:
            # Fallback to traditional pattern matching
            supports = self.base_strategy.supports_url(url)
            return {
                "supports": supports,
                "confidence": 0.7 if supports else 0.0,
                "reasoning": f"Traditional pattern matching for {self.platform_name}"
            }

        # AI-enhanced analysis with confidence scoring
        base_supports = self.base_strategy.supports_url(url)
        if base_supports:
            ai_analysis = await self._ai_analyze_url(url)
            return {
                "supports": True,
                "confidence": ai_analysis.confidence,
                "reasoning": ai_analysis.reasoning,
                "ai_enhanced": True
            }
```

#### LangSmith Integration
```python
# AI observability and debugging
from langsmith import traceable

@traceable
async def ai_enhanced_download(url: str, preferences: dict) -> DownloadResult:
    """Traceable AI-enhanced download process."""
    # Automatic tracing of AI agent interactions
    # Performance monitoring and debugging
    # Error tracking and analysis
```

### AI Configuration and Feature Flags

#### AI Settings Management
```python
# src/boss_bot/core/env.py - AI configuration
class BossSettings(BaseSettings):
    """Comprehensive settings with AI configuration."""

    # AI Feature Flags
    enable_ai: bool = Field(default=True, description="Enable AI features")
    ai_strategy_selection_enabled: bool = Field(default=True, description="Enable AI strategy selection")
    ai_content_analysis_enabled: bool = Field(default=True, description="Enable AI content analysis")

    # AI Model Configuration
    ai_model: str = Field(default="gpt-4", description="Primary AI model")
    ai_temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="AI model temperature")
    ai_max_tokens: int = Field(default=1000, gt=0, description="Maximum AI response tokens")
    ai_timeout_seconds: int = Field(default=30, gt=0, description="AI request timeout")

    # Provider API Keys
    openai_api_key: SecretStr = Field(default="", description="OpenAI API key")
    anthropic_api_key: SecretStr = Field(default="", description="Anthropic API key")
    google_api_key: SecretStr = Field(default="", description="Google AI API key")
    cohere_api_key: SecretStr = Field(default="", description="Cohere API key")

    # LangChain Integration
    langchain_api_key: SecretStr = Field(default="", description="LangChain API key")
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_project: str = Field(default="boss-bot", description="LangSmith project name")
```

## Configuration and Deployment

### Environment Configuration

#### Essential Configuration Files

##### 1. Environment Variables (.env)
```bash
# Discord Configuration (Required)
DISCORD_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=123456789012345678
DISCORD_SERVER_ID=987654321098765432
DISCORD_ADMIN_USER_ID=111222333444555666

# AI Provider Configuration (Optional but Recommended)
OPENAI_API_KEY=sk-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
GOOGLE_API_KEY=your_google_ai_key
COHERE_API_KEY=your_cohere_key

# LangChain Integration (Optional)
LANGCHAIN_API_KEY=your_langchain_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=boss-bot
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Feature Flags
ENABLE_AI=true
ENABLE_REDIS=false
ENABLE_SENTRY=false

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
BETTER_EXCEPTIONS=false

# Storage Configuration
STORAGE_ROOT=/app/storage
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_DOWNLOADS=3
MAX_QUEUE_SIZE=100

# Performance Settings
DOWNLOAD_TIMEOUT_SECONDS=300
AI_TIMEOUT_SECONDS=30
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.3
```

##### 2. Configuration Validation
```python
# Automatic validation with Pydantic
class BossSettings(BaseSettings):
    """Type-safe configuration with automatic validation."""

    # Required Discord settings
    discord_token: SecretStr = Field(..., description="Discord bot token")
    discord_client_id: int = Field(..., description="Discord application client ID")

    # Optional AI settings with defaults
    enable_ai: bool = Field(default=True, description="Enable AI features")
    ai_model: str = Field(default="gpt-4", description="Primary AI model")

    # Automatic environment variable loading
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = "BOSS_BOT_CONFIG_"  # Optional prefix
```

### Docker Deployment

#### Production Dockerfile
```dockerfile
# Multi-stage build for optimal image size
FROM python:3.12-slim AS builder

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /deps/boss-bot

# Copy dependency files for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies only
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --compile-bytecode

# Copy project source
COPY . /deps/boss-bot

# Install project with compiled bytecode
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --compile-bytecode --no-editable

# Production stage
FROM python:3.12-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /deps/boss-bot/.venv /deps/boss-bot/.venv

# Copy application code
COPY --from=builder /deps/boss-bot /deps/boss-bot

# Set working directory and PATH
WORKDIR /deps/boss-bot
ENV PATH="/deps/boss-bot/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash bossbot
USER bossbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import boss_bot; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "boss_bot"]
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  boss-bot:
    build: .
    container_name: boss-bot
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENABLE_AI=true
      - LOG_LEVEL=INFO
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    networks:
      - boss-bot-network
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: boss-bot-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - boss-bot-network
    command: redis-server --appendonly yes

volumes:
  redis_data:

networks:
  boss-bot-network:
    driver: bridge
```

### Deployment Options

#### 1. Local Development
```bash
# Quick local setup
git clone https://github.com/bossjones/boss-bot.git
cd boss-bot
uv sync --dev
cp .env.example .env
# Edit .env with your configuration
uv run python -m boss_bot
```

#### 2. Docker Deployment
```bash
# Build and run with Docker
docker build -t boss-bot .
docker run -d --name boss-bot \
  --env-file .env \
  -v $(pwd)/storage:/app/storage \
  boss-bot

# Or use Docker Compose
docker-compose up -d
```

#### 3. Production Deployment
```bash
# Production deployment with optimizations
docker build -t boss-bot:production \
  --target production \
  --build-arg BUILDKIT_INLINE_CACHE=1 .

# Run with production settings
docker run -d --name boss-bot-prod \
  --restart unless-stopped \
  --env-file .env.production \
  -v /opt/boss-bot/storage:/app/storage \
  -v /opt/boss-bot/logs:/app/logs \
  boss-bot:production
```

### Operational Considerations

#### Monitoring and Logging
```python
# Structured logging with Loguru
from loguru import logger

# Automatic log configuration
logger.add(
    "logs/boss-bot.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    serialize=True  # JSON output for log aggregation
)

# Performance monitoring
@logger.catch
async def monitored_download(url: str) -> DownloadResult:
    """Download with automatic error logging and metrics."""
    with logger.contextualize(url=url, operation="download"):
        start_time = time.time()
        try:
            result = await download_manager.download(url)
            logger.info(f"Download completed in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
```

#### Health Checks and Metrics
```python
# Health check endpoint
async def health_check() -> dict:
    """Comprehensive health check."""
    return {
        "status": "healthy",
        "version": "0.12.0",
        "uptime": get_uptime(),
        "ai_enabled": settings.enable_ai,
        "queue_size": queue_manager.size(),
        "active_downloads": download_manager.active_count(),
        "memory_usage": get_memory_usage(),
        "last_error": get_last_error()
    }

# Prometheus metrics (optional)
from aioprometheus import Counter, Histogram, Gauge

download_counter = Counter("downloads_total", "Total downloads processed")
download_duration = Histogram("download_duration_seconds", "Download processing time")
queue_size_gauge = Gauge("queue_size", "Current queue size")
```

#### Security Considerations
```python
# Security best practices
class SecuritySettings:
    """Security configuration and validation."""

    # Token validation
    @validator("discord_token")
    def validate_discord_token(cls, v):
        if not v.startswith(("Bot ", "Bearer ")):
            raise ValueError("Invalid Discord token format")
        return v

    # API key masking in logs
    def mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive information in logs."""
        sensitive_keys = ["token", "key", "secret", "password"]
        return {
            k: "***MASKED***" if any(s in k.lower() for s in sensitive_keys) else v
            for k, v in data.items()
        }
```

#### Backup and Recovery
```bash
# Backup strategy
# 1. Configuration backup
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# 2. Storage backup
rsync -av --progress storage/ backup/storage-$(date +%Y%m%d)/

# 3. Database backup (if using persistent storage)
docker exec boss-bot-redis redis-cli BGSAVE
docker cp boss-bot-redis:/data/dump.rdb backup/redis-$(date +%Y%m%d).rdb

# 4. Log backup
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Development Best Practices

### Code Quality Standards

#### Type Safety and Modern Python
```python
# Use type hints throughout the codebase
from typing import Optional, Dict, List, Union, Any
from pathlib import Path

async def download_media(
    url: str,
    quality: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> DownloadResult:
    """Type-safe function with comprehensive annotations."""
    pass

# Use dataclasses and Pydantic models for data structures
from pydantic import BaseModel, Field
from dataclasses import dataclass

@dataclass
class DownloadRequest:
    url: str
    user_id: int
    quality: str = "high"

class DownloadResponse(BaseModel):
    success: bool
    file_path: Optional[Path] = None
    error_message: Optional[str] = None
```

#### Error Handling Patterns
```python
# Comprehensive error handling with custom exceptions
class BossBotError(Exception):
    """Base exception for Boss-Bot errors."""
    pass

class DownloadError(BossBotError):
    """Download-specific errors."""
    pass

class AIAgentError(BossBotError):
    """AI agent processing errors."""
    pass

# Graceful error handling in async contexts
async def safe_download(url: str) -> DownloadResult:
    """Download with comprehensive error handling."""
    try:
        return await download_manager.download(url)
    except DownloadError as e:
        logger.error(f"Download failed for {url}: {e}")
        return DownloadResult(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error downloading {url}")
        return DownloadResult(success=False, error="Internal error")
```

### Testing Best Practices

#### Test-Driven Development (TDD)
```python
# 1. Write failing test first (RED)
@pytest.mark.asyncio
async def test_twitter_download_success():
    """Test successful Twitter download."""
    # This test will fail initially - that's expected in TDD
    url = "https://twitter.com/example/status/123"
    result = await download_manager.download(url)

    assert result.success is True
    assert result.file_path is not None
    assert result.metadata.platform == "twitter"

# 2. Implement minimal code to pass (GREEN)
async def download(self, url: str) -> DownloadResult:
    """Minimal implementation to pass test."""
    if "twitter.com" in url:
        return DownloadResult(
            success=True,
            file_path=Path("/tmp/test.mp4"),
            metadata=MediaMetadata(platform="twitter")
        )
    return DownloadResult(success=False, error="Unsupported platform")

# 3. Refactor and improve (REFACTOR)
# Enhance implementation while keeping tests green
```

#### Mock and Fixture Patterns
```python
# Use pytest fixtures for consistent test setup
@pytest.fixture
async def mock_download_manager(mocker):
    """Mock download manager for testing."""
    manager = mocker.Mock(spec=DownloadManager)
    manager.download.return_value = DownloadResult(success=True)
    return manager

# Mock external dependencies
@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for AI testing."""
    client = mocker.Mock()
    client.chat.completions.create.return_value = MockResponse(
        choices=[MockChoice(message=MockMessage(content="twitter"))]
    )
    return client
```

### Performance Optimization

#### Async Best Practices
```python
# Use asyncio.gather for concurrent operations
async def download_multiple(urls: List[str]) -> List[DownloadResult]:
    """Download multiple URLs concurrently."""
    tasks = [download_manager.download(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Use semaphores for concurrency control
class DownloadManager:
    def __init__(self, max_concurrent: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def download(self, url: str) -> DownloadResult:
        async with self._semaphore:
            return await self._do_download(url)
```

#### Memory Management
```python
# Use context managers for resource cleanup
from contextlib import asynccontextmanager

@asynccontextmanager
async def download_context(url: str):
    """Context manager for download resource management."""
    temp_file = None
    try:
        temp_file = await create_temp_file()
        yield temp_file
    finally:
        if temp_file:
            await cleanup_temp_file(temp_file)

# Stream large files to avoid memory issues
async def stream_download(url: str, output_path: Path):
    """Stream download for large files."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async with aiofiles.open(output_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
```

## Important Notes for AI Assistants

### When Working with Boss-Bot Code

#### 1. Always Use Package Managers
- **NEVER** manually edit `pyproject.toml` for dependencies
- **ALWAYS** use `uv add package_name` or `just uv-add package_name`
- **NEVER** use `pip install` - use UV exclusively

#### 2. Testing Requirements
- **ALWAYS** write tests for new functionality
- **USE** pytest-mock exclusively (never unittest.mock directly)
- **RUN** tests before submitting changes: `just test`
- **MAINTAIN** the 407+ test count - don't break existing tests

#### 3. Code Quality Standards
- **FORMAT** code with Ruff: `just format`
- **LINT** code before commits: `just check-code`
- **USE** type hints for all new functions
- **FOLLOW** existing patterns and conventions

#### 4. AI Integration Guidelines
- **UNDERSTAND** the multi-agent architecture before making changes
- **TEST** AI components with mocked LLM responses
- **RESPECT** the BaseAgent interface for new agents
- **USE** AgentRequest/AgentResponse patterns consistently

#### 5. Discord Bot Development
- **USE** dpytest for Discord command testing
- **FOLLOW** the cog pattern for new commands
- **HANDLE** errors gracefully with user-friendly messages
- **VALIDATE** user input and permissions

#### 6. Configuration Management
- **USE** Pydantic settings for all configuration
- **VALIDATE** environment variables with proper types
- **DOCUMENT** new configuration options
- **PROVIDE** sensible defaults

### Common Pitfalls to Avoid

1. **Don't** bypass the UV package manager
2. **Don't** write tests without using pytest-mock
3. **Don't** ignore type hints or linting errors
4. **Don't** break the existing AI agent interfaces
5. **Don't** commit code without running the full test suite
6. **Don't** hardcode configuration values
7. **Don't** ignore async/await patterns in Discord commands

### Getting Help

If you encounter issues or need clarification:
1. **Check** the existing test patterns in `tests/`
2. **Review** similar implementations in the codebase
3. **Run** `just check` to validate your changes
4. **Consult** the comprehensive documentation in `docs/`
5. **Ask** specific questions about patterns or architecture

---

**Boss-Bot** represents a sophisticated integration of modern Python development practices, AI-powered intelligence, and robust Discord bot functionality. This documentation should serve as your comprehensive guide to understanding, developing, and maintaining this advanced system.
