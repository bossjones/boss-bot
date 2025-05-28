# CLAUDE.md

## About This Documentation

**Origin**: This documentation was originally generated for the [Cog-Creators/Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) repository using Claude Code to provide AI-assisted development guidance.

**Portability**: While created for Red-DiscordBot, this documentation can be adapted for other Discord bot projects or Python projects that share similar patterns:
- Replace project-specific commands and paths with your own
- Adapt the architecture patterns to match your project structure
- Use the testing and development workflow patterns as templates
- Modify tool commands to match your build system (replace `make` with `just`, `npm`, etc.)

**Usage in Other Projects**: To use this in your own repository:
1. Copy this file to your project as `CLAUDE.md` or similar
2. Update project-specific references (commands, paths, cog names)
3. Adapt the architecture section to describe your project's structure
4. Modify development commands to match your toolchain

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Code Formatting and Style
- `make reformat` - Format all .py files tracked by git using Black
- `make stylecheck` - Check which files need reformatting
- `make stylediff` - Show formatting diff without modifying files

### Testing
- `pytest` - Run the test suite
- `python -m pytest tests/path/to/specific_test.py` - Run specific test file
- `tox` - Run tests across multiple Python versions (3.8, 3.9, 3.10, 3.11)
- `tox -e postgres` - Run tests with PostgreSQL backend
- `python -m compileall ./redbot/cogs` - Compile all cog files to check for syntax errors

### Documentation
- `tox -e docs` - Build documentation with Sphinx

### Development Environment
- `make newenv` - Create new virtual environment in `.venv/`
- `make syncenv` - Sync environment to latest dependencies from `tools/dev-requirements.txt`

### Translation Management
- `make gettext` - Generate translation template files
- `make upload_translations` - Upload to Crowdin
- `make download_translations` - Download from Crowdin

## Project Architecture

### Core Structure
Red-DiscordBot is a modular Discord bot framework built on discord.py with the following key architecture:

**Entry Points:**
- `redbot/__main__.py` - Main bot runner and CLI handling
- `redbot/setup.py` - Bot setup and configuration utility
- `redbot/core/bot.py` - Core bot class extending discord.py's Bot

**Core Framework (`redbot/core/`):**
- `config.py` - Configuration system with driver abstraction (JSON, PostgreSQL)
- `commands/` - Extended command framework built on discord.py
- `data_manager.py` - Handles bot data storage and paths
- `modlog.py` - Moderation logging system
- `bank.py` - Virtual economy system
- `tree.py` - Application command (slash command) integration
- `_drivers/` - Storage backend drivers (JSON, MongoDB, PostgreSQL)

**Cog System (`redbot/cogs/`):**
- Modular plugin system where each cog is self-contained
- Each cog has its own directory with main module, localization files
- Built-in cogs: admin, alias, audio, cleanup, customcom, downloader, economy, filter, general, image, mod, modlog, mutes, permissions, reports, streams, trivia, warnings

**Key Patterns:**
- Async/await throughout (built on asyncio)
- Configuration via `Config` class with automatic driver selection
- Internationalization via gettext with per-cog locale files
- Event-driven architecture using discord.py events
- Plugin loading/unloading via the `downloader` cog

### Testing Framework
- Uses pytest with async support (`asyncio_mode = 'auto'`)
- Custom pytest fixtures in `redbot/pytest/` provide mocked Red components for testing
- Integration tests in `tests/` mirror the `redbot/` structure
- Custom pytest entry point for Red-specific test utilities

**Red pytest fixtures (`redbot/pytest/`):**
- `redbot/pytest/core.py` - Core fixtures for testing Red components:
  - `config`, `config_fr` - Mocked Config objects with temporary storage
  - `driver` - Isolated storage driver for tests
  - `red` - Mocked Red bot instance
  - Discord.py mock objects: `empty_guild`, `empty_channel`, `empty_member`, `empty_user`, `empty_message`
  - Factory fixtures: `guild_factory`, `member_factory`, `user_factory` for generating test objects
- `redbot/pytest/cog_manager.py` - Fixtures for cog management testing
- `redbot/pytest/economy.py` - Bank/economy system fixtures
- `redbot/pytest/data_manager.py` - Data management fixtures
- Other cog-specific fixture modules for alias, downloader, mod, permissions, etc.

These fixtures automatically handle temporary directories, database connections, and provide isolated test environments. Import them in tests using `from redbot.pytest.module_name import *`.

### Configuration System
Red uses a powerful configuration system (`redbot.core.Config`) that:
- Abstracts storage backends (JSON files, PostgreSQL, etc.)
- Provides per-guild, per-user, and global configuration scopes
- Handles automatic migration between Red versions
- Supports nested configuration structures with type hints

### Bot Instance Management
- Multiple bot instances can be configured and run independently
- Each instance has separate data directories and configurations
- Setup via `redbot-setup` command, run via `redbot <instance_name>`
- Configuration stored in JSON files managed by `data_manager`

## Code Style
- Uses Black code formatter (line length: 99)
- Python 3.8+ compatibility required
- Async/await preferred over callback patterns
- Type hints encouraged throughout
- Docstrings follow standard Python conventions

## Localization
- All user-facing strings should be wrapped with translation functions
- Each cog has its own `locales/` directory with .po files
- Use `redgettext` tool to extract translatable strings
- Translations managed via Crowdin platform
