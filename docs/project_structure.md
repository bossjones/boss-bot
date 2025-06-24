# Boss-Bot Project Structure

This document provides a comprehensive overview of the Boss-Bot project structure with detailed explanations for each module.

## Table of Contents
- [Project Root Structure](#project-root-structure)
- [Source Code Structure](#source-code-structure)
- [Test Structure](#test-structure)
- [Technology Stack](#technology-stack)
- [Entry Points and Execution Flow](#entry-points-and-execution-flow)
- [Component Interactions](#component-interactions)
- [Development Workflow](#development-workflow)

## Project Root Structure

```
boss-bot/                               # Project root directory
├── .claude/                           # Claude AI configuration
│   └── commands/                      # Custom Claude commands
├── .github/                           # GitHub configuration
│   └── workflows/                     # CI/CD workflows
├── ai_docs/                           # AI-related documentation
│   └── plans/                         # AI agent planning documents
├── docs/                              # Project documentation
│   ├── EXPERIMENTAL.md               # Experimental features (Epic 5)
│   └── project_structure.md          # This file
├── scripts/                           # Development and deployment scripts
├── src/                               # Source code directory
│   └── boss_bot/                     # Main package
├── tests/                             # Test suite
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore patterns
├── CLAUDE.md                          # AI assistant instructions
├── justfile                           # Task automation (like Makefile)
├── pyproject.toml                     # Project configuration and dependencies
├── README.md                          # Project README
└── uv.lock                            # Dependency lock file (uv package manager)
```

## Source Code Structure

```
src/
└── boss_bot/                           # Main package directory for the Boss-Bot Discord bot
    ├── __init__.py                    # Package initialization file
    ├── __main__.py                    # Entry point for running the package with `python -m boss_bot`
    ├── __version__.py                 # Version information for the package
    ├── ai/                            # AI and LLM integration modules (LangChain/LangGraph)
    │   ├── __init__.py
    │   ├── agents/                    # LangGraph agents for multi-step AI workflows
    │   │   └── __init__.py
    │   ├── chains/                    # LangChain chains for composable AI operations
    │   │   └── __init__.py
    │   ├── memory/                    # Conversation and context memory management
    │   │   └── __init__.py
    │   ├── prompts/                   # Prompt templates and engineering
    │   │   └── __init__.py
    │   └── tools/                     # LangChain tools for AI agent capabilities
    │       └── __init__.py
    ├── api/                           # REST/GraphQL API layer (future implementation)
    │   ├── __init__.py
    │   ├── middleware/                # API middleware (auth, rate limiting, etc.)
    │   │   └── __init__.py
    │   ├── models/                    # API data models and schemas
    │   │   └── __init__.py
    │   └── routes/                    # API route definitions and handlers
    │       └── __init__.py
    ├── bot/                           # Discord bot core functionality
    │   ├── __init__.py
    │   ├── bot_help.py               # Custom help command implementation
    │   ├── client.py                 # Main BossBot client class extending discord.py Bot
    │   ├── cogs/                     # Discord command cogs (modular command groups)
    │   │   ├── __init__.py
    │   │   ├── admin.py             # Administrative commands (bot management)
    │   │   ├── downloads.py         # Download commands using strategy pattern
    │   │   └── queue.py             # Queue management commands
    │   ├── events/                   # Discord event handlers
    │   │   └── __init__.py
    │   └── middleware/               # Bot-specific middleware
    │       └── __init__.py
    ├── cli/                          # Command-line interface using Typer
    │   ├── __init__.py
    │   ├── commands/                 # CLI subcommands
    │   │   ├── __init__.py
    │   │   └── download.py          # Download-related CLI commands
    │   ├── config/                   # CLI configuration management
    │   │   └── __init__.py
    │   ├── main.py                  # Main CLI entry point and command router
    │   └── utils/                    # CLI utility functions
    │       └── __init__.py
    ├── cli.py                        # Legacy CLI module (to be removed)
    ├── commands/                      # Legacy commands directory (to be removed)
    │   └── __init__.py
    ├── core/                         # Core business logic and services
    │   ├── __init__.py
    │   ├── compression/              # Media compression and optimization
    │   │   ├── __init__.py
    │   │   ├── manager.py           # Main compression management logic
    │   │   ├── models.py            # Compression-related data models
    │   │   ├── processors/          # Media-specific compression processors
    │   │   │   ├── __init__.py
    │   │   │   ├── audio_processor.py    # Audio file compression
    │   │   │   ├── base_processor.py     # Abstract base processor
    │   │   │   ├── image_processor.py    # Image compression
    │   │   │   └── video_processor.py    # Video compression
    │   │   └── utils/               # Compression utility functions
    │   │       ├── __init__.py
    │   │       ├── bitrate_calculator.py  # Bitrate calculations for media
    │   │       ├── ffmpeg_utils.py       # FFmpeg wrapper utilities
    │   │       └── file_detector.py      # Media file type detection
    │   ├── core_queue.py            # Legacy queue module (use queue/manager.py)
    │   ├── downloads/               # Download management system
    │   │   ├── __init__.py
    │   │   ├── clients/             # Download client implementations
    │   │   │   ├── __init__.py
    │   │   │   ├── aio_gallery_dl.py         # Async gallery-dl client wrapper
    │   │   │   ├── aio_gallery_dl_utils.py   # Gallery-dl utility functions
    │   │   │   ├── aio_yt_dlp.py             # Async yt-dlp client wrapper
    │   │   │   └── config/                    # Client configuration
    │   │   │       ├── __init__.py
    │   │   │       ├── gallery_dl_config.py   # Gallery-dl configuration
    │   │   │       └── gallery_dl_validator.py # Configuration validation
    │   │   ├── feature_flags.py     # Feature flag management for strategies
    │   │   ├── handlers/            # Legacy platform-specific handlers
    │   │   │   ├── __init__.py
    │   │   │   ├── base_handler.py          # Abstract base handler
    │   │   │   ├── instagram_handler.py     # Instagram download handler
    │   │   │   ├── reddit_handler.py        # Reddit download handler
    │   │   │   ├── twitter_handler.py       # Twitter/X download handler
    │   │   │   └── youtube_handler.py       # YouTube download handler
    │   │   ├── manager.py           # Download manager coordinating strategies
    │   │   └── strategies/          # Strategy pattern implementations (Epic 5)
    │   │       ├── __init__.py
    │   │       ├── base_strategy.py         # Abstract strategy interface
    │   │       ├── instagram_strategy.py    # Instagram strategy (API/CLI modes)
    │   │       ├── reddit_strategy.py       # Reddit strategy (API/CLI modes)
    │   │       ├── twitter_strategy.py      # Twitter/X strategy (API/CLI modes)
    │   │       └── youtube_strategy.py      # YouTube strategy (API/CLI modes)
    │   ├── env.py                   # Environment configuration (BossSettings)
    │   ├── queue/                   # Queue management system
    │   │   ├── __init__.py
    │   │   └── manager.py           # QueueManager for download task management
    │   ├── services/                # Core service implementations
    │   │   └── __init__.py
    │   └── uploads/                 # Upload management system
    │       ├── __init__.py
    │       ├── config/              # Upload configuration
    │       │   └── __init__.py
    │       ├── manager.py           # Upload manager for Discord attachments
    │       ├── models.py            # Upload-related data models
    │       ├── processors/          # Upload processors
    │       │   ├── __init__.py
    │       │   └── discord_processor.py  # Discord-specific upload processing
    │       └── utils/               # Upload utility functions
    │           ├── __init__.py
    │           ├── batch_processor.py    # Batch upload processing
    │           ├── file_detector.py      # File type detection for uploads
    │           └── size_analyzer.py      # File size analysis and chunking
    ├── downloaders/                 # Legacy downloaders (to be removed)
    │   ├── __init__.py
    │   └── base.py                 # Legacy base downloader
    ├── global_cogs/                 # Legacy global cogs (to be removed)
    │   ├── __init__.py
    │   ├── downloads.py            # Legacy download cog
    │   └── queue.py                # Legacy queue cog
    ├── integrations/               # External service integrations
    │   ├── __init__.py
    │   ├── anthropic/              # Anthropic API integration
    │   │   └── __init__.py
    │   ├── langsmith/              # LangSmith monitoring integration
    │   │   └── __init__.py
    │   ├── openai/                 # OpenAI API integration
    │   │   └── __init__.py
    │   └── webhooks/               # Webhook integrations
    │       └── __init__.py
    ├── main_bot.py                 # Legacy bot entry point (use __main__.py)
    ├── monitoring/                 # Monitoring and observability
    │   ├── __init__.py
    │   ├── health/                 # Health check system
    │   │   ├── __init__.py
    │   │   ├── checker.py         # Health check coordinator
    │   │   └── checks/            # Individual health checks
    │   │       └── __init__.py
    │   ├── health.py              # Legacy health module
    │   ├── health_check.py        # Legacy health check module
    │   ├── health_checks/          # Legacy health checks directory
    │   │   └── __init__.py
    │   ├── logging/                # Logging configuration
    │   │   ├── __init__.py
    │   │   ├── interceptor.py    # Loguru interceptor for stdlib logging
    │   │   └── logging_config.py  # Main logging configuration
    │   ├── logging.py             # Legacy logging module
    │   ├── metrics/                # Metrics collection
    │   │   ├── __init__.py
    │   │   ├── collector.py       # Metrics collector implementation
    │   │   └── exporters/         # Metrics exporters (Prometheus, etc.)
    │   │       └── __init__.py
    │   └── metrics.py             # Legacy metrics module
    ├── schemas/                    # Data schemas and validation
    │   ├── __init__.py
    │   ├── ai/                    # AI-related schemas
    │   │   └── __init__.py
    │   ├── api/                   # API request/response schemas
    │   │   └── __init__.py
    │   └── discord/               # Discord-specific schemas
    │       └── __init__.py
    ├── storage/                    # Storage management system
    │   ├── __init__.py
    │   ├── backends/               # Storage backend implementations
    │   │   └── __init__.py
    │   ├── cleanup/                # Storage cleanup utilities
    │   │   └── __init__.py
    │   ├── managers/               # Storage managers
    │   │   ├── __init__.py
    │   │   ├── quota_manager.py   # User quota management
    │   │   └── validation_manager.py  # File validation manager
    │   ├── migrations/             # Database migrations (future)
    │   │   └── __init__.py
    │   ├── models/                 # Storage data models
    │   │   └── __init__.py
    │   ├── quotas/                 # Legacy quotas directory
    │   │   └── __init__.py
    │   ├── quotas_manager.py       # Legacy quota manager
    │   ├── validation_manager.py   # Legacy validation manager
    │   └── validations/            # Legacy validations directory
    │       └── __init__.py
    └── utils/                      # Shared utility functions
        ├── __init__.py
        └── asynctyper.py           # Async wrapper for Typer CLI
```

## Module Organization Notes

### Current Issues
1. **Duplicate modules**: Several modules have both legacy and new versions (e.g., health.py vs health/, logging.py vs logging/)
2. **Legacy directories**: `global_cogs/`, `downloaders/`, and `commands/` should be removed
3. **Inconsistent structure**: Some modules are split unnecessarily (e.g., storage has both directories and files for the same functionality)

### Key Architectural Components

#### Strategy Pattern (Epic 5) ✅
The download strategies in `core/downloads/strategies/` implement a flexible pattern for platform-specific downloads with:
- API-direct mode using gallery-dl/yt-dlp Python APIs
- CLI fallback mode using subprocess calls
- Feature flag control via environment variables
- Automatic fallback on API failures

#### Core Services
- **QueueManager**: Manages download task queue with priority and concurrency control
- **DownloadManager**: Coordinates download strategies and handles platform detection
- **BossSettings**: Centralized configuration management using pydantic-settings

#### Discord Integration
- Custom bot client extending discord.py Bot
- Modular cog system for command organization
- Event-driven architecture for Discord interactions

#### CLI Development
- Typer-based CLI with subcommand architecture
- Rich formatting for enhanced console output
- Async support via asynctyper utility

## Recommended Cleanup Actions
1. Remove legacy modules and consolidate duplicates
2. Complete migration from handlers to strategies
3. Implement planned AI components in the `ai/` directory
4. Develop the API layer for programmatic access
5. Expand storage backends beyond local filesystem

## Test Structure

```
tests/                                  # Test suite root
├── __init__.py
├── conftest.py                        # Global pytest fixtures
├── example_vcr_test.py               # VCR.py example test
├── fixtures/                          # Test data and configuration files
│   ├── gallery_dl.conf               # Test gallery-dl configuration
│   ├── info.json                     # Test metadata
│   └── *.json                        # Various test data files
├── test_bot/                          # Bot-related tests
│   ├── __init__.py
│   ├── conftest.py                   # Bot-specific fixtures
│   ├── test_client.py                # BossBot client tests
│   ├── test_cogs/                    # Cog tests (comprehensive)
│   │   ├── __init__.py
│   │   ├── test_admin_dpytest.py    # Admin cog tests with dpytest
│   │   ├── test_downloads.py        # Download cog unit tests
│   │   ├── test_downloads_direct.py # Direct download tests
│   │   ├── test_downloads_dpytest.py # Download tests with dpytest
│   │   ├── test_downloads_integration.py    # Download integration tests
│   │   ├── test_downloads_upload_integration.py # Upload integration tests
│   │   ├── test_downloads_vcr_integration.py    # VCR integration tests
│   │   ├── test_queue_dpytest.py    # Queue tests with dpytest
│   │   └── test_youtube_download_dpytest.py # YouTube-specific tests
│   ├── test_core.py                  # Core bot functionality tests
│   ├── test_download_cog.py         # Legacy download cog tests
│   ├── test_help.py                 # Help command tests
│   ├── test_queue.py                # Queue functionality tests
│   └── test_queue_cog.py            # Legacy queue cog tests
├── test_cli/                         # CLI tests
│   ├── __init__.py
│   ├── cassettes/                   # VCR.py recordings for CLI tests
│   │   └── test_fetch_vcr/         # Recorded HTTP interactions
│   ├── test_commands/              # CLI command tests
│   │   ├── __init__.py
│   │   ├── test_download.py       # General download command tests
│   │   └── test_download_reddit.py # Reddit-specific CLI tests
│   ├── test_doctor.py              # Doctor command tests
│   └── test_fetch_vcr.py           # VCR fetch tests
├── test_commands/                    # Legacy commands tests
│   └── __init__.py
├── test_core/                        # Core logic tests
│   ├── __init__.py
│   ├── test_compression/            # Compression system tests
│   │   ├── conftest.py             # Compression test fixtures
│   │   ├── test_bitrate_calculator.py # Bitrate calculation tests
│   │   └── test_file_detector.py   # File detection tests
│   ├── test_downloads/              # Download system tests
│   │   ├── test_strategies/        # Strategy pattern tests
│   │   │   ├── test_twitter_strategy.py
│   │   │   ├── test_reddit_strategy.py
│   │   │   ├── test_instagram_strategy.py
│   │   │   └── test_youtube_strategy.py
│   │   ├── test_clients/           # Download client tests
│   │   │   ├── test_aio_gallery_dl.py
│   │   │   └── test_aio_yt_dlp.py
│   │   └── test_manager.py         # Download manager tests
│   ├── test_env.py                 # Configuration tests
│   └── test_queue/                 # Queue system tests
│       └── test_manager.py         # Queue manager tests
└── test_integration/                # Full integration tests
    └── test_end_to_end.py          # End-to-end workflow tests
```

## Technology Stack

### Core Framework
- **Python 3.12+**: Modern Python with full type hints
- **discord.py**: Discord bot framework
- **Pydantic/Pydantic-Settings**: Data validation and settings management

### CLI & UI
- **Typer**: CLI framework with subcommand support
- **Rich**: Terminal formatting and progress bars
- **asynctyper**: Async wrapper for Typer

### Download Tools
- **gallery-dl**: Multi-platform media downloader (API and CLI modes)
- **yt-dlp**: YouTube and video platform downloader

### AI/ML Stack (Planned/In Development)
- **LangChain**: Framework for AI chain development
- **LangGraph**: Multi-step AI workflow orchestration
- **LangSmith**: LLM application monitoring
- **Anthropic/OpenAI**: LLM providers

### Development Tools
- **uv**: Fast Python package manager
- **ruff**: Python linter and formatter
- **pytest**: Testing framework with async support
- **dpytest**: Discord.py testing utilities
- **just**: Task runner (like Make)

### Infrastructure
- **Loguru**: Structured logging
- **FFmpeg**: Media processing
- **GitHub Actions**: CI/CD

## Entry Points and Execution Flow

### Discord Bot
```bash
# Main entry point
goobctl go                    # Starts the Discord bot
# OR
uv run python -m boss_bot     # Direct module execution
```

**Execution Flow:**
1. `__main__.py` → Entry point
2. `bot/client.py` → BossBot initialization
3. `core/env.py` → Load configuration from environment
4. Bot registers cogs from `bot/cogs/`
5. Bot connects to Discord and starts event loop

### CLI Interface
```bash
# CLI entry points
bossctl <command>             # Main CLI command (via pyproject.toml)
# OR
uv run python -m boss_bot.cli.main <command>
```

**CLI Commands:**
- `bossctl download <platform> <url>` → Download media
- `bossctl download strategies` → Show strategy configuration
- `bossctl download info` → Show platform information

## Component Interactions

### Download Flow
```
User Command → Discord Cog/CLI Command
     ↓
Download Manager (checks platform)
     ↓
Strategy Selection (based on URL pattern)
     ↓
Feature Flag Check (API vs CLI mode)
     ↓
Execute Strategy → API Client or Subprocess
     ↓
Queue Manager (tracks progress)
     ↓
Upload Manager (Discord file handling)
     ↓
Response to User
```

### Key Integration Points

1. **Settings Injection**: `BossSettings` is passed through constructors
2. **Queue System**: Centralized task management via `QueueManager`
3. **Strategy Pattern**: Platform-specific logic isolated in strategies
4. **Event-Driven**: Discord events trigger bot actions
5. **Async Throughout**: All I/O operations use async/await

## Development Workflow

### Setup
```bash
# Clone repository
git clone https://github.com/bossjones/boss-bot.git
cd boss-bot

# Install dependencies
just uv-update

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Common Tasks
```bash
# Run tests
just check-test

# Run specific test
just check-test "tests/test_bot/test_client.py::test_function"

# Format code
just format

# Lint and type check
just check-code
just check-type

# Full validation
just check

# Run bot locally
goobctl go
```

### Environment Variables

Key configuration via `.env`:
```bash
# Discord Configuration
DISCORD_TOKEN=your_token_here
DISCORD_COMMAND_PREFIX=$

# Feature Flags (Strategy Pattern)
TWITTER_USE_API_CLIENT=true
REDDIT_USE_API_CLIENT=true
INSTAGRAM_USE_API_CLIENT=true
YOUTUBE_USE_API_CLIENT=true
DOWNLOAD_API_FALLBACK_TO_CLI=true

# Paths
BOSS_BOT_DOWNLOAD_DIR=./downloads

# Logging
BOSS_BOT_LOG_LEVEL=INFO
```

### Testing Guidelines
- All tests use pytest with async support
- Fixtures follow `fixture_*` naming convention
- Mock Discord components with pytest-mock
- Integration tests validate full workflows
- Use `@pytest.mark.skip_until` for WIP features

### Code Style
- 120 character line length
- Google docstring style
- Type hints required
- Ruff for formatting/linting
- No inline comments unless necessary
