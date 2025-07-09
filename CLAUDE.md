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

## Typer CLI Testing Patterns
- **ANSI Code Handling**: Typer CLI output includes ANSI escape codes for colors and formatting
- **Strip ANSI Codes**: Always use `strip_ansi_codes()` function when asserting CLI output
- **Pattern**: Import the function and wrap `result.stdout` before assertions
- **Example**:
  ```python
  from tests.utils import strip_ansi_codes

  result = cli_runner.invoke(app, ["command"])
  clean_output = strip_ansi_codes(result.stdout)
  assert "Expected text" in clean_output
  ```
- **Why**: CI environments and terminal formatting can cause test failures without stripping ANSI codes
- **Location**: The `strip_ansi_codes` function is available in `tests/utils.py`

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

## 📚 Memory Files

For detailed documentation on specific topics, reference these memory files when needed:

### **Testing & Development**
- **`@ai_docs/memory/testing_guidelines.md`** - Comprehensive testing patterns, AI testing, fixtures
- **`@ai_docs/memory/project_structure.md`** - Complete project structure and organization

### **AI & Architecture**
- **`@ai_docs/memory/ai_architecture.md`** - AI multi-agent system, LangGraph workflows, Discord commands
- **`ai_docs/memory/epic5_strategy_pattern.md`** - Download strategy pattern implementation

### **Configuration & Usage**
- **`@ai_docs/memory/configuration_usage.md`** - Environment variables, Discord/CLI usage examples

These memory files contain detailed information that was previously in this file. Include them in context when working on related features.
