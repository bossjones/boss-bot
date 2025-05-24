# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Boss-Bot is a Discord bot that enables downloading and managing media files. The bot uses discord.py and follows a modular architecture with cogs for different functionality. It also leverages AI capabilities through LangChain, LangGraph, and other AI frameworks.

## Build & Test Commands
- Run all tests: `just check-test`
- Run single test: `just check-test "tests/test_bot/test_client.py::test_function_name"`
- Run tests with coverage: `just check-coverage`
- Lint code: `just check-code`
- Type check: `just check-type`
- Format code: `just format`
- Full check suite: `just check`
- Manage dependencies: `just uv-update`
- Run bot: `bossctl go`

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
- **LangChain Ecosystem**:
  - **LangChain**: Framework for AI chain development
  - **LangGraph**: Orchestration of multi-step AI workflows
  - **LangSmith**: Monitoring and debugging LLM applications
  - **LangChain Integrations**: Various services (OpenAI, Anthropic, etc.)
- **Testing**: pytest, pytest-asyncio, dpytest
- **Storage**: Support for various storage mechanisms
- **Build System**: Just, uv, ruff

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

### Known Test Failures and Fixes
- `test_download_command_queue_full`: Fixed by adding exception handling in download command (src/boss_bot/bot/cogs/downloads.py:22-26)
- **Queue Tests (tests/test_bot/test_queue.py)**: All tests failed with `TypeError: QueueCog.show_queue() missing 1 required positional argument: 'ctx'`
  - **Root Cause**: Tests were calling command methods directly instead of using the `.callback()` pattern for decorated commands
  - **Fix**: Replace direct calls like `await cog.show_queue(ctx)` with `await cog.show_queue.callback(cog, ctx)`
  - **Additional Issue**: Discord embed calls use keyword arguments (`embed=...`) not positional arguments
  - **Fix**: Access embed via `call_args.kwargs['embed']` instead of `call_args[0][0]`
  - **String Splitting Issue**: Tests failed due to trailing newlines creating empty strings when splitting
  - **Fix**: Use `.strip().split('\n')` instead of `.split('\n')` when counting lines
- **Queue Cog Tests (tests/test_bot/test_queue_cog.py)**: All tests failed with dpytest integration issues
  - **Root Cause**: Tests were written as integration tests expecting full Discord command functionality, but commands weren't properly configured
  - **Original Error**: `AttributeError: 'str' object has no attribute 'id'` when trying to create Discord user objects
  - **Solution**: Rewrote as unit tests using `.callback()` pattern to test cog commands directly
  - **Pattern**: Use `await cog.command_name.callback(cog, ctx, *args)` instead of integration testing
  - **Result**: All 5 tests now pass, testing clear_queue, remove_from_queue (success/failure), pause_queue, and resume_queue commands

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

## AI Capabilities (Current & Planned)
- Media content analysis using LangChain and vision models
- LangGraph for multi-step workflows and task orchestration
- LangSmith for tracking and debugging AI components
- AI assistant integration for Discord interactions
- Content moderation and filtering

## Project Structure

### Current Structure Analysis
The current structure has some organizational issues that can be improved for better maintainability and scalability, especially with the planned AI capabilities expansion.

### Recommended Project Structure
Based on the project's goals and technology stack, here's the recommended structure:

```
src/boss_bot/
├── __init__.py
├── __main__.py
├── __version__.py
├── main_bot.py                    # Legacy entry point (to be phased out)
│
├── ai/                           # 🤖 AI Components (LangChain/LangGraph)
│   ├── __init__.py
│   ├── agents/                   # LangGraph agents and workflows
│   │   ├── __init__.py
│   │   ├── content_analyzer.py   # Media content analysis agent
│   │   ├── download_assistant.py # Download decision agent
│   │   └── moderation_agent.py   # Content moderation workflows
│   ├── chains/                   # LangChain chains
│   │   ├── __init__.py
│   │   ├── summarization.py     # Content summarization chains
│   │   └── classification.py    # Content classification chains
│   ├── tools/                    # LangChain tools
│   │   ├── __init__.py
│   │   ├── media_tools.py       # Media analysis tools
│   │   └── discord_tools.py     # Discord integration tools
│   ├── prompts/                  # Prompt templates
│   │   ├── __init__.py
│   │   └── templates.py         # Prompt template definitions
│   └── memory/                   # Conversation and context memory
│       ├── __init__.py
│       └── managers.py          # Memory management
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
│   │   │   ├── youtube.py      # YouTube handling
│   │   │   ├── twitter.py      # Twitter/X handling
│   │   │   └── generic.py      # Generic URL handling
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
- Main entry point: `bossctl` → `boss_bot.cli.main`
- Subcommand structure using Typer with dedicated command modules
- Rich formatting for console output
- Commands for bot management, queue operations, AI workflows, and configuration
- Pluggable subcommand architecture for extensibility
