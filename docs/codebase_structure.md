# Boss-Bot Codebase Structure

This document provides a comprehensive overview of the boss-bot project structure, including all directories, major components, and architectural patterns.

Generated on: 2024-05-27

## 📁 Project Overview

The boss-bot project follows modern Python development practices with comprehensive tooling and documentation:

```
.
├── 📋 Core Documentation
│   ├── CHANGELOG.md                     # Automated changelog via towncrier
│   ├── CLAUDE.md                        # Claude Code AI assistant instructions
│   ├── CONTRIBUTING.md                  # Contributor guidelines and workflows
│   ├── EXPERIMENTAL.md                  # Experimental features architecture guide
│   ├── MIGRATION.md                     # Project structure migration documentation
│   ├── README.md                        # Main project documentation
│   └── VCR_SETUP_SUMMARY.md            # VCR testing implementation guide
│
├── 🐳 Container & Deployment
│   ├── Dockerfile                       # Multi-stage Python container build
│   └── docker-compose.yml              # Development environment orchestration
│
├── ⚙️ Build & Configuration
│   ├── Justfile                         # Main build system entry point
│   ├── justfiles/                       # Modular build recipes (20+ files)
│   ├── pyproject.toml                   # Python project configuration
│   ├── pyrightconfig.json              # Type checking configuration
│   ├── taplo.toml                       # TOML formatting configuration
│   └── sample.env                       # Environment variable template
│
├── 📊 Testing & Quality Assurance
│   ├── tests/                           # Comprehensive test suite (65% coverage)
│   ├── codecov.yml                      # Code coverage reporting configuration
│   ├── cov_annotate/                    # Line-by-line coverage annotations (100+ files)
│   ├── detect_pytest_live_logging.sh   # Security check for test logging
│   └── junit/                           # JUnit XML test results
│
├── 📚 Documentation System
│   ├── docs/                            # MkDocs documentation site
│   ├── docs_templates/                  # Jinja2 templates for auto-generated docs
│   ├── mkdocs.yml                       # Documentation site configuration
│   └── mkdocs_macro_plugin.py          # Custom macros for dynamic content
│
├── 🧠 AI & Development Intelligence
│   ├── ai_docs/                         # AI-assisted development documentation
│   │   └── audit-cursor-rules/          # Cursor IDE rule analysis and optimization
│   └── hack/                            # Advanced development configurations (100+ files)
│
├── 🛠️ Development Environment
│   ├── boss-bot.code-workspace          # VS Code workspace configuration
│   ├── configure_claude_ignore.sh       # Claude Code ignore pattern setup
│   └── .claude/                         # Claude Code custom slash commands
│
├── 📄 Legal & Licensing
│   ├── LICENSE                          # Main license file
│   └── LICENSE.txt                      # Additional licensing information
│
└── 📦 Source Code & Scripts
    ├── src/                             # Main application source code
    └── scripts/                         # Development automation scripts (30+ utilities)
```

### Key File Details:

#### 📋 **Core Documentation**
- **`CLAUDE.md`** - Comprehensive instructions for Claude Code AI assistant including build commands, architecture patterns, testing guidelines, and project context
- **`EXPERIMENTAL.md`** - 1,300+ line architecture document detailing API-direct download strategies, feature flags, and implementation roadmap for 4 platforms
- **`VCR_SETUP_SUMMARY.md`** - Complete guide for VCR (Video Cassette Recorder) testing setup with security-first approach for API interaction testing
- **`MIGRATION.md`** - Detailed project structure migration plan addressing current issues and proposing scalable AI-ready architecture

#### 🧠 **AI & Development Intelligence**
- **`ai_docs/audit-cursor-rules/`** - Production environment analysis of 29 cursor rules with distribution metrics and optimization recommendations
- **`mkdocs_macro_plugin.py`** - Custom MkDocs macros for dynamic documentation generation with Jinja2 templating support

#### 🛠️ **Development Environment**
- **`boss-bot.code-workspace`** - VS Code workspace with pytest integration, YAML formatting rules, and JSON schema validation
- **`configure_claude_ignore.sh`** - Script that synchronizes .gitignore patterns with Claude Code's ignore settings for consistent file filtering
- **`detect_pytest_live_logging.sh`** - Security validation script ensuring live logging is disabled in commits to prevent secret leakage

#### 📊 **Testing & Quality Infrastructure**
- **`cov_annotate/`** - Contains 100+ `.cover` files providing line-by-line coverage annotations for every source file, enabling detailed coverage analysis
- **`codecov.yml`** - Advanced code coverage configuration with thresholds, ignore patterns, and integration settings

#### 📚 **Documentation Templates**
- **`docs_templates/`** - Jinja2 templates for automated documentation generation:
  - `person.jinja` - Staff/contributor profile template with photo, contact, and timezone info
  - `project.jinja` - Project documentation template
  - `service.jinja` - Service documentation template

#### ⚙️ **Configuration Excellence**
- **`pyproject.toml`** - Comprehensive Python project configuration with build system, dependencies, testing, linting, and development tool settings
- **`pyrightconfig.json`** - Type checking configuration optimized for Discord bot development with async patterns
- **`taplo.toml`** - TOML file formatting and validation configuration

This structure demonstrates a **mature, production-ready project** with enterprise-grade development practices, comprehensive testing infrastructure, AI-assisted development workflows, and automated quality assurance systems.

## 🏗️ Core Architecture

### Source Code (`src/boss_bot/`)

The main application code follows a modular architecture with clear separation of concerns:

```
src/boss_bot/
├── __init__.py
├── __main__.py
├── __version__.py
├── main_bot.py                    # Legacy entry point
├── cli.py                         # CLI interface
├── ai/                           # 🤖 AI Components
├── api/                          # 🌐 REST API (Future)
├── bot/                          # 🤖 Discord Bot Core
├── cli/                          # 🖥️ CLI Components
├── commands/                     # Legacy commands
├── core/                         # 🏗️ Core Business Logic
├── downloaders/                  # Legacy downloaders
├── global_cogs/                  # Global Discord cogs
├── integrations/                 # 🔌 External Integrations
├── monitoring/                   # 📊 Monitoring & Observability
├── schemas/                      # 📄 Data Schemas
├── storage/                      # 💾 Storage & Data Management
└── utils/                        # 🔧 Shared Utilities
```

### Key Component Details

#### Discord Bot (`bot/`)
```
bot/
├── __init__.py
├── bot_help.py                   # Custom help system
├── client.py                     # Main BossBot class
├── cogs/                         # Command modules
│   ├── downloads.py              # Download commands (✅ Strategy Pattern)
│   ├── queue.py                  # Queue management
│   └── task_queue.py             # Task queue operations
├── events/                       # Event handlers
└── middleware/                   # Bot middleware
```

#### Core Business Logic (`core/`)
```
core/
├── core_queue.py                 # Legacy queue (deprecated)
├── env.py                        # Environment configuration
├── downloads/                    # Download system
│   ├── clients/                  # API-direct clients
│   │   ├── aio_gallery_dl.py     # Async gallery-dl wrapper
│   │   ├── aio_yt_dlp.py         # Async yt-dlp wrapper
│   │   └── config/               # Client configurations
│   ├── feature_flags.py          # Feature flag management
│   ├── handlers/                 # Platform-specific handlers
│   │   ├── base_handler.py       # Abstract base handler
│   │   ├── instagram_handler.py  # Instagram downloads
│   │   ├── reddit_handler.py     # Reddit downloads
│   │   ├── twitter_handler.py    # Twitter/X downloads
│   │   └── youtube_handler.py    # YouTube downloads
│   ├── manager.py                # Download manager
│   └── strategies/               # Strategy pattern implementation
│       ├── base_strategy.py      # Strategy interface
│       ├── instagram_strategy.py # Instagram strategy (✅ Complete)
│       ├── reddit_strategy.py    # Reddit strategy (✅ Complete)
│       ├── twitter_strategy.py   # Twitter strategy (✅ Complete)
│       └── youtube_strategy.py   # YouTube strategy (✅ Complete)
├── queue/                        # Queue management
│   └── manager.py                # Queue manager
└── services/                     # Core services
```

#### CLI Interface (`cli/`)
```
cli/
├── __init__.py
├── main.py                       # Main CLI entry point
├── commands/                     # CLI subcommands
│   └── download.py               # Download commands
├── config/                       # CLI configuration
└── utils/                        # CLI utilities
```

#### AI Components (`ai/`)
```
ai/
├── __init__.py
├── agents/                       # LangGraph agents
├── chains/                       # LangChain chains
├── memory/                       # Conversation memory
├── prompts/                      # Prompt templates
└── tools/                        # LangChain tools
```

#### Storage System (`storage/`)
```
storage/
├── __init__.py
├── backends/                     # Storage backends
├── cleanup/                      # Cleanup operations
├── managers/                     # Storage managers
│   ├── quota_manager.py          # Quota management
│   └── validation_manager.py     # File validation
├── migrations/                   # Database migrations
├── models/                       # Data models
├── quotas/                       # Quota system
├── quotas_manager.py             # Legacy quota manager
├── validation_manager.py         # Legacy validation
└── validations/                  # Validation rules
```

#### Monitoring (`monitoring/`)
```
monitoring/
├── __init__.py
├── health/                       # Health check system
│   ├── checker.py                # Health check manager
│   └── checks/                   # Individual checks
├── health.py                     # Legacy health
├── health_check.py               # Health check implementation
├── logging/                      # Logging configuration
│   └── logging_config.py         # Logging setup
├── metrics/                      # Metrics collection
│   ├── collector.py              # Metrics collector
│   └── exporters/                # Metrics exporters
└── metrics.py                    # Legacy metrics
```

## 🧪 Testing Structure (`tests/`)

Comprehensive test suite with excellent coverage:

```
tests/
├── __init__.py
├── conftest.py                   # Shared test fixtures
├── example_vcr_test.py           # VCR testing example
├── cassettes/                    # VCR cassettes for HTTP testing
├── fixtures/                     # Test data files
├── test_bot/                     # Discord bot tests
│   ├── conftest.py               # Bot-specific fixtures
│   ├── test_client.py            # Bot client tests
│   ├── test_cogs/                # Cog testing
│   │   ├── test_downloads.py     # Download cog tests
│   │   ├── test_downloads_reddit.py
│   │   └── test_downloads_twitter.py
│   ├── test_core.py              # Core functionality tests
│   ├── test_download_cog.py      # Download cog integration
│   ├── test_help.py              # Help system tests
│   ├── test_queue.py             # Queue tests
│   └── test_queue_cog.py         # Queue cog tests
├── test_cli/                     # CLI testing
│   └── test_commands/            # CLI command tests
├── test_core/                    # Core logic testing
│   ├── test_downloads/           # Download system tests
│   │   ├── test_clients/         # API client tests
│   │   ├── test_handlers/        # Handler tests
│   │   └── test_strategies/      # Strategy tests (✅ All platforms)
│   ├── test_env.py               # Environment tests
│   ├── test_project_structure.py # Structure validation
│   └── test_queue_manager.py     # Queue manager tests
├── test_downloaders/             # Legacy downloader tests
├── test_monitoring/              # Monitoring tests
└── test_storage/                 # Storage tests
```

## 📚 Documentation (`docs/`)

Comprehensive documentation system:

```
docs/
├── README.md                     # Documentation index
├── agile-readme.md               # Agile development guide
├── ai.md                         # AI integration docs
├── contributors/                 # Contributor guides
│   └── dpytest_example.md        # Discord bot testing guide
├── css/                          # Documentation styling
├── cursor-rules-reference.md     # Development rules
├── development/                  # Development guides
├── environment.md                # Environment setup
├── images/                       # Documentation images
├── img/                          # Additional images
├── vcr.md                        # VCR testing guide
├── versioning.md                 # Version management
└── workflow-rules.md             # Workflow guidelines
```

## 🔧 Development Tools

### Build System (`justfiles/`)
Modular Justfile-based build system:

```
justfiles/
├── audit.just                   # Security auditing
├── changelog.just               # Changelog management
├── check.just                   # Code quality checks
├── clean.just                   # Cleanup operations
├── common.just                  # Common functions
├── convert.just                 # File conversions
├── cz.just                      # Conventional commits
├── doc.just                     # Documentation
├── firecrawl.just               # Web scraping
├── format.just                  # Code formatting
├── install.just                 # Installation
├── monkeytype.just              # Type inference
├── package.just                 # Package management
├── release.just                 # Release management
├── security.just                # Security scanning
├── taplo.just                   # TOML formatting
├── test.just                    # Testing
├── towncrier.just               # News fragments
├── uv.just                      # UV package manager
├── validate.just                # Validation
└── variables.just               # Build variables
```

### Scripts (`scripts/`)
Development and automation scripts organized by functionality:

```
scripts/
├── 🔍 Code Quality & Analysis
│   ├── audit_cursor_rules_headers.py    # Validates YAML frontmatter in cursor rules
│   ├── blame.py                         # Git blame analysis and code attribution
│   ├── check_rule_lines.py              # Validates cursor rule formatting
│   ├── mock_patch_checker.py            # Checks proper mock/patch usage in tests
│   └── validate_frontmatter.py          # YAML frontmatter validation
│
├── 🤖 AI & Content Analysis
│   ├── bboxes.py                        # Object detection with Google Gemini AI
│   ├── token_counter.py                 # Counts tokens for AI model context windows
│   └── q_a.json                         # Q&A data for AI training
│
├── 📚 Documentation
│   ├── docs/
│   │   └── gen_ref_pages.py             # Auto-generates API reference pages
│   ├── serve_docs.py                    # MkDocs server with port conflict resolution
│   ├── download_readthedocs.sh          # Downloads documentation from ReadTheDocs
│   ├── update-docs.sh                   # Updates documentation build
│   ├── jekyll_build.sh                  # Jekyll documentation builder
│   └── jekyll_run.sh                    # Jekyll development server
│
├── 🚀 CI/CD & Release Management
│   ├── ci/
│   │   ├── cz-prepare-release.sh        # Prepares release with Commitizen
│   │   ├── cz-release.sh                # Creates GitHub releases
│   │   ├── increase_version_number.py   # Automated version bumping
│   │   ├── prepare-release.sh           # Release preparation automation
│   │   ├── release-manually.sh          # Manual release process
│   │   └── release.sh                   # Main release automation
│   ├── publish-pypi                     # PyPI package publishing
│   └── init-changelog.sh               # Initializes changelog format
│
├── 🛠️ Development Tools
│   ├── createstubs.sh                   # Generates type stubs with pyright
│   ├── cursor-logs.sh                   # Cursor IDE log analysis
│   ├── migration_health_check.py        # Verifies system integrity after migrations
│   ├── open-browser.py                  # Cross-platform browser launcher
│   ├── retry                            # Command retry utility
│   ├── unittest-local                   # Local unit test runner
│   └── manhole-shell                    # Debug shell for running processes
│
├── 📦 Package & Environment Management
│   ├── uv-workspace-init-package.sh     # UV workspace package initialization
│   └── update_changelog.py             # Automated changelog updates
│
├── 🎬 Media Processing
│   ├── compress-discord.sh              # Video compression for Discord uploads
│   └── Dockerfile.jekyll               # Jekyll documentation container
│
└── 📊 Project Management
    └── update_changelog.py             # Maintains project changelog
```

#### Key Script Details:

**🔍 Code Quality Scripts:**
- `audit_cursor_rules_headers.py` - Ensures all cursor rules have proper YAML frontmatter with required fields (description, globs, alwaysApply)
- `mock_patch_checker.py` - AST-based analysis tool from Yelp/Tron that finds incomplete mocked objects in tests
- `blame.py` - Advanced git blame analysis for code attribution and ownership tracking

**🤖 AI Integration Scripts:**
- `bboxes.py` - Uses Google Gemini AI for object detection and bounding box analysis in images
- `token_counter.py` - Counts tokens for various AI models (GPT-4, Claude, etc.) to manage context windows
- Supports multiple model encodings: `o200k_base`, `cl100k_base`, `p50k_base`

**📚 Documentation Automation:**
- `gen_ref_pages.py` - Auto-generates MkDocs API reference pages from source code (adapted from Hikari project)
- `serve_docs.py` - Smart MkDocs server that handles port conflicts and process management
- Jekyll integration for alternative documentation builds

**🚀 Release Management:**
- Full Commitizen integration for semantic versioning and changelog generation
- Automated GitHub release creation with release notes
- PyPI publishing automation with proper version management
- Multi-stage release pipeline with health checks

**🛠️ Development Utilities:**
- `createstubs.sh` - Generates type stubs using pyright for better IDE support
- `migration_health_check.py` - Runs comprehensive system integrity checks after code migrations
- `retry` - Robust command retry utility for flaky operations
- `manhole-shell` - Debug shell for introspecting running processes

**📦 Package Management:**
- UV workspace integration for modern Python package management
- Automated dependency updates and conflict resolution
- Container-based build environments

**🎬 Media Processing:**
- `compress-discord.sh` - Video compression pipeline optimized for Discord's file size limits
- Handles various video formats and compression settings

### Development Configuration (`hack/`)
Advanced development configurations and rules:

```
hack/
├── README.md
├── drafts/                      # Draft configurations
│   ├── cursor_rules/            # Cursor IDE rules (100+ files)
│   ├── cursor_rules_v2/         # Next-generation rules
│   └── disabled/                # Disabled configurations
├── ide-configs/                 # IDE configurations
│   └── vscode/                  # VS Code settings
├── jsonschema/                  # JSON schemas
└── schemas/                     # Configuration schemas
```

## ⚙️ Configuration Files

### Core Configuration
- `pyproject.toml` - Python project configuration
- `pyrightconfig.json` - Type checking configuration
- `taplo.toml` - TOML formatting configuration
- `mkdocs.yml` - Documentation site configuration
- `codecov.yml` - Code coverage configuration
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container build instructions

### Package Management
- `uv.lock` - Lock file for uv package manager
- `sample.env` - Environment variable template

### Documentation Templates
- `docs_templates/` - Jinja2 templates for documentation generation

## 🎯 Key Features & Status

### ✅ Implemented Features
- **Discord Bot Core** - Full discord.py bot with cogs
- **Download System** - 4 platform support (Twitter, Reddit, YouTube, Instagram)
- **Strategy Pattern** - CLI/API switching with feature flags
- **Queue Management** - Async download queue with priority
- **CLI Interface** - Typer-based command-line interface
- **Monitoring** - Health checks, metrics, logging
- **Storage System** - File management with quotas and validation
- **Testing** - Comprehensive test suite with 65% coverage
- **Documentation** - MkDocs-based documentation system

### 🔄 In Development
- **AI Integration** - LangChain/LangGraph components
- **REST API** - FastAPI-based web interface
- **Advanced Monitoring** - Prometheus metrics export

### 📋 Architecture Patterns

1. **Strategy Pattern** - Download implementations (CLI vs API)
2. **Cog Pattern** - Discord command organization
3. **Factory Pattern** - Handler creation and management
4. **Observer Pattern** - Event handling and monitoring
5. **Repository Pattern** - Data access abstraction
6. **Command Pattern** - CLI command structure

## 🚀 Quick Start Locations

- **Main Bot Entry**: `src/boss_bot/bot/client.py`
- **Download Commands**: `src/boss_bot/bot/cogs/downloads.py`
- **Strategy Implementation**: `src/boss_bot/core/downloads/strategies/`
- **Configuration**: `src/boss_bot/core/env.py`
- **Testing Examples**: `tests/test_bot/test_cogs/`
- **CLI Commands**: `src/boss_bot/cli/commands/`

## 📊 Project Statistics

- **Total Files**: 551
- **Total Directories**: 112
- **Test Coverage**: 65%
- **Platform Support**: 4 (Twitter, Reddit, YouTube, Instagram)
- **Test Cases**: 328 passing, 9 skipped
- **Lines of Code**: ~15,000+ (estimated)

This structure demonstrates a well-organized, production-ready Discord bot with modern Python practices, comprehensive testing, and extensible architecture.
