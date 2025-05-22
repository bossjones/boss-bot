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
- Run bot: `goobctl go`

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

## CLI Development
The CLI (`src/boss_bot/cli.py`) is being developed to provide command-line control of the bot:
- Main entry point: `goobctl`
- Subcommand structure using Typer
- Rich formatting for console output
- Commands for version info, dependency checking, and bot management
- Support for pluggable subcommands (future)
