# Boss-Bot Project Structure Migration

This document outlines the migration plan from the current project structure to a more organized, scalable architecture that better supports AI capabilities, CLI expansion, and future growth.

## Current Structure Issues

1. **Mixed Responsibilities**: `core/`, `bot/`, and `global_cogs/` have overlapping concerns
2. **No AI Organization**: No dedicated structure for LangChain/LangGraph components
3. **CLI Limitations**: Single `cli.py` file doesn't scale for multiple subcommands
4. **Monitoring Scattered**: Health checks and metrics are mixed together
5. **Storage Disorganization**: Storage logic mixed with quota and validation concerns
6. **Missing Integration Layer**: No structure for external service integrations
7. **Module Name Conflicts**: Risk of conflicts with third-party libraries (e.g., `discord.py` library vs local `discord.py` file)

## Current Project Structure

```
src/boss_bot/
├── __init__.py
├── __main__.py
├── __version__.py
├── main_bot.py                    # Entry point (legacy)
├── cli.py                         # Monolithic CLI file
├── bot/
│   ├── __init__.py
│   ├── bot_help.py
│   ├── client.py
│   └── cogs/
│       ├── __init__.py
│       ├── downloads.py
│       ├── queue.py               # Unused duplicate
│       └── task_queue.py
├── commands/
│   └── __init__.py                # Empty module
├── core/
│   ├── __init__.py
│   ├── core_queue.py              # Queue management
│   └── env.py                     # Environment config
├── downloaders/
│   ├── __init__.py
│   └── base.py                    # Download manager
├── global_cogs/                   # Duplicate of bot/cogs/
│   ├── __init__.py
│   ├── downloads.py
│   └── queue.py
├── monitoring/
│   ├── __init__.py
│   ├── health.py
│   ├── health_check.py
│   ├── health_checks/
│   │   └── __init__.py
│   ├── logging.py
│   ├── logging/
│   │   └── __init__.py
│   ├── metrics.py
│   └── metrics/
│       └── __init__.py
├── schemas/
│   └── __init__.py                # Empty module
├── storage/
│   ├── __init__.py
│   ├── cleanup/
│   │   └── __init__.py
│   ├── quotas/
│   │   └── __init__.py
│   ├── quotas_manager.py
│   ├── validation_manager.py
│   └── validations/
│       └── __init__.py
└── utils/
    └── __init__.py                # Empty module
```

## Proposed Project Structure

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
│   │   └── discord_integration.py # Discord integration tools
│   ├── prompts/                  # Prompt templates
│   │   ├── __init__.py
│   │   └── templates.py         # Prompt template definitions
│   └── memory/                   # Conversation and context memory
│       ├── __init__.py
│       └── managers.py          # Memory management
│
├── bot/                          # 🤖 Discord Bot Components
│   ├── __init__.py
│   ├── client.py                # Main bot client (from current bot/client.py)
│   ├── bot_help.py             # Custom help command (from current bot/bot_help.py)
│   ├── cogs/                   # Discord command cogs
│   │   ├── __init__.py
│   │   ├── downloads.py        # Download commands (from current bot/cogs/downloads.py)
│   │   ├── task_queue.py      # Queue management commands (from current bot/cogs/task_queue.py)
│   │   ├── ai_commands.py     # AI-powered commands (new)
│   │   └── admin.py           # Admin commands (new)
│   ├── events/                 # Discord event handlers (new)
│   │   ├── __init__.py
│   │   ├── message_handler.py  # Message processing
│   │   └── error_handler.py    # Error handling
│   └── middleware/             # Bot middleware (new)
│       ├── __init__.py
│       ├── rate_limiting.py    # Rate limiting middleware
│       └── authentication.py  # User authentication
│
├── cli/                          # 🖥️ CLI Components (Typer)
│   ├── __init__.py
│   ├── main.py                  # Main CLI entry point (from current cli.py)
│   ├── commands/               # CLI subcommands (new)
│   │   ├── __init__.py
│   │   ├── bot.py             # Bot management commands
│   │   ├── queue.py           # Queue management commands
│   │   ├── download.py        # Download commands
│   │   ├── ai.py              # AI workflow commands
│   │   └── cli_config.py      # Configuration commands
│   ├── utils/                  # CLI utilities (new)
│   │   ├── __init__.py
│   │   ├── formatters.py      # Rich formatting utilities
│   │   └── validators.py      # Input validation
│   └── config/                 # CLI configuration (new)
│       ├── __init__.py
│       └── settings.py        # CLI-specific settings
│
├── core/                         # 🏗️ Core Business Logic
│   ├── __init__.py
│   ├── env.py                   # Environment configuration (from current core/env.py)
│   ├── queue/                   # Queue management (new organization)
│   │   ├── __init__.py
│   │   ├── manager.py          # Queue manager (from current core/core_queue.py)
│   │   ├── models.py           # Queue data models (extracted)
│   │   └── processors.py       # Queue processing logic (extracted)
│   ├── downloads/              # Download management (new organization)
│   │   ├── __init__.py
│   │   ├── manager.py          # Download manager (from current downloaders/base.py)
│   │   ├── handlers/           # Protocol-specific handlers (new)
│   │   │   ├── __init__.py
│   │   │   ├── youtube_handler.py # YouTube handling
│   │   │   ├── twitter_handler.py # Twitter/X handling
│   │   │   └── generic_handler.py # Generic URL handling
│   │   └── models.py           # Download data models (new)
│   └── services/               # Core services (new)
│       ├── __init__.py
│       ├── content_service.py  # Content analysis service
│       └── notification_service.py # Notification service
│
├── storage/                      # 💾 Storage & Data Management
│   ├── __init__.py
│   ├── managers/               # Storage managers (reorganized)
│   │   ├── __init__.py
│   │   ├── file_manager.py     # File storage management (new)
│   │   ├── quota_manager.py    # Quota management (from current storage/quotas_manager.py)
│   │   └── validation_manager.py # File validation (from current storage/validation_manager.py)
│   ├── backends/               # Storage backends (new)
│   │   ├── __init__.py
│   │   ├── local_storage.py   # Local filesystem
│   │   ├── s3_storage.py      # AWS S3 (future)
│   │   └── azure_storage.py   # Azure Storage (future)
│   ├── models/                 # Data models (new)
│   │   ├── __init__.py
│   │   └── file_models.py     # File metadata models
│   └── migrations/             # Database migrations (future)
│       └── __init__.py
│
├── monitoring/                   # 📊 Monitoring & Observability
│   ├── __init__.py
│   ├── health/                 # Health checks (reorganized)
│   │   ├── __init__.py
│   │   ├── checker.py         # Health check manager (from current monitoring/health_check.py)
│   │   └── checks/            # Individual health checks (reorganized)
│   │       ├── __init__.py
│   │       ├── discord_health.py # Discord connectivity
│   │       ├── storage_health.py # Storage health
│   │       └── ai_health.py   # AI service health (new)
│   ├── metrics/                # Metrics collection (reorganized)
│   │   ├── __init__.py
│   │   ├── collector.py       # Metrics collector (from current monitoring/metrics.py)
│   │   └── exporters/         # Metrics exporters (new)
│   │       ├── __init__.py
│   │       ├── prometheus.py  # Prometheus exporter
│   │       └── datadog.py     # Datadog exporter (future)
│   └── logging/                # Logging configuration (reorganized)
│       ├── __init__.py
│       ├── logging_config.py  # Logging setup (from current monitoring/logging.py)
│       └── formatters.py      # Log formatters (new)
│
├── schemas/                      # 📄 Data Schemas & Validation
│   ├── __init__.py
│   ├── api/                    # API schemas (new)
│   │   ├── __init__.py
│   │   ├── downloads.py       # Download API schemas
│   │   └── queue.py           # Queue API schemas
│   ├── discord/                # Discord-specific schemas (new)
│   │   ├── __init__.py
│   │   └── discord_events.py  # Discord event schemas
│   └── ai/                     # AI-related schemas (new)
│       ├── __init__.py
│       ├── prompts.py         # Prompt schemas
│       └── responses.py       # AI response schemas
│
├── integrations/                 # 🔌 External Integrations (new)
│   ├── __init__.py
│   ├── langsmith/              # LangSmith integration
│   │   ├── __init__.py
│   │   └── langsmith_client.py
│   ├── anthropic/              # Anthropic API integration
│   │   ├── __init__.py
│   │   └── anthropic_client.py
│   ├── openai/                 # OpenAI API integration
│   │   ├── __init__.py
│   │   └── openai_client.py
│   └── webhooks/               # Webhook handlers
│       ├── __init__.py
│       └── discord_webhook.py
│
├── utils/                        # 🔧 Shared Utilities
│   ├── __init__.py
│   ├── decorators.py           # Common decorators (new)
│   ├── validators.py           # Validation utilities (new)
│   ├── formatters.py           # Formatting utilities (new)
│   ├── async_utils.py          # Async helper functions (new)
│   └── security.py             # Security utilities (new)
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

## Naming Convention Guidelines

To avoid module name conflicts with third-party libraries and Python standard library modules, the following naming conventions are enforced:

### 🚫 **Avoided Names**
- `discord.py` → Use `discord_integration.py`, `discord_health.py`, etc.
- `storage.py` → Use `storage_health.py`, `storage_backend.py`, etc.
- `ai.py` → Use `ai_health.py`, `ai_service.py`, etc.
- `youtube.py` → Use `youtube_handler.py`
- `twitter.py` → Use `twitter_handler.py`
- `local.py` → Use `local_storage.py`
- `s3.py` → Use `s3_storage.py`
- `openai.py` → Use `openai_client.py`
- `anthropic.py` → Use `anthropic_client.py`
- `config.py` → Use `settings.py`, `cli_config.py`, `logging_config.py`

### ✅ **Naming Patterns**
- **Service-specific**: `{service}_{purpose}.py` (e.g., `discord_integration.py`)
- **Handler pattern**: `{protocol}_handler.py` (e.g., `youtube_handler.py`)
- **Backend pattern**: `{type}_storage.py` (e.g., `local_storage.py`)
- **Health checks**: `{component}_health.py` (e.g., `discord_health.py`)
- **Purpose suffix**: `{name}_{purpose}.py` (e.g., `discord_webhook.py`)
- **Client pattern**: `{service}_client.py` (e.g., `openai_client.py`, `anthropic_client.py`)

### 📋 **Module Conflict Checklist**
Before creating new modules, check against:
- Python standard library modules
- Third-party dependencies (discord.py, langchain, etc.)
- Common package names (boto3, azure, etc.)

## Dependencies & Environment Setup

### New Dependencies Required for Migration

The migration introduces new testing and AI capabilities that require additional dependencies. Follow UV package manager standards for all dependency management.

#### Testing Framework Dependencies
```bash
# Add testing dependencies with UV (dev dependencies)
uv add --dev pytest-vcr==1.0.2
uv add --dev vcrpy==4.4.0
uv add --dev pytest-asyncio==0.23.2
uv add --dev pytest-mock==3.12.0
uv add --dev pytest-freezegun==0.4.2
uv add --dev pytest-aioresponses==0.7.6

# Verify installation
uv sync
```

#### AI/LangChain Dependencies
```bash
# Core AI framework dependencies
uv add langchain==0.1.0
uv add langgraph==0.0.62
uv add langchain-openai==0.0.6
uv add langchain-anthropic==0.1.1

# Optional AI dependencies (for enhanced features)
uv add langsmith==0.0.87  # For AI workflow tracking
uv add tiktoken==0.5.2    # For token counting

# Verify AI dependencies
uv run python -c "import langchain; print('LangChain OK')"
```

#### pyproject.toml Updates
```toml
# Add to pyproject.toml [project.dependencies] for core features
dependencies = [
    # ... existing dependencies ...
    "langchain>=0.1.0,<0.2.0",
    "langgraph>=0.0.60,<0.1.0",
    "langchain-openai>=0.0.6,<0.1.0",
    "langchain-anthropic>=0.1.0,<0.2.0",
]

# Add to [project.optional-dependencies] for development
[project.optional-dependencies]
dev = [
    # ... existing dev dependencies ...
    "pytest-vcr>=1.0.2,<2.0.0",
    "vcrpy>=4.4.0,<5.0.0",
    "pytest-asyncio>=0.23.0,<0.24.0",
    "pytest-mock>=3.12.0,<4.0.0",
    "pytest-freezegun>=0.4.2,<0.5.0",
    "pytest-aioresponses>=0.7.6,<0.8.0",
]

ai-optional = [
    "langsmith>=0.0.87,<0.1.0",
    "tiktoken>=0.5.2,<0.6.0",
]

# UV-specific configuration for package sources
[tool.uv.sources]
# Example: If using custom forks or local packages
# pytest-vcr = { git = "https://github.com/organization/pytest-vcr.git" }
```

### Environment Variables for Testing

Create environment-specific configurations for the new testing approach:

```bash
# .env.test (for VCR testing)
OPENAI_API_KEY="test-key-for-vcr-recording"
ANTHROPIC_API_KEY="test-key-for-vcr-recording"
LANGSMITH_API_KEY="test-key-for-vcr-recording"

# VCR Configuration
VCR_RECORD_MODE="once"
PYTEST_VCR_CASSETTE_DIR="tests/cassettes"

# AI Testing Configuration
AI_TESTING_MODE="vcr"  # Options: vcr, mock, live
AI_RATE_LIMIT_ENABLED="true"
```

```bash
# .env.development
# Use real API keys for development
OPENAI_API_KEY="${OPENAI_API_KEY}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
LANGSMITH_API_KEY="${LANGSMITH_API_KEY}"

# Development AI settings
AI_TESTING_MODE="live"
AI_DEBUG_ENABLED="true"
```

### Development Environment Setup

```bash
# Initial setup for migration development
uv sync --extra ai-optional

# Verify all dependencies are working
uv run python -c "import pytest, langchain, discord; print('All core dependencies OK')"

# Install pre-commit hooks (important for VCR cassette management)
uv run pre-commit install

# Run test discovery to verify pytest configuration
uv run pytest --collect-only -q

# Verify VCR is working
uv run python -c "import vcr; print('VCR OK')"
```

### Dependency Upgrade Strategy During Migration

```bash
# Check for outdated packages before migration
uv sync --upgrade-package pytest
uv sync --upgrade-package discord.py

# Lock current working versions (recommended before migration)
uv lock

# After each migration phase, verify dependencies still work
uv sync --dev
uv run pytest tests/test_migration/ -v
```

### Package Management Best Practices for Migration

1. **Phase-by-Phase Dependency Addition**:
   ```bash
   # Phase 1: Testing framework
   uv add --dev pytest-vcr vcrpy pytest-asyncio
   uv sync

   # Phase 3: AI dependencies
   uv add langchain langgraph
   uv sync

   # Verify after each addition
   uv run pytest --collect-only
   ```

2. **Lock File Management**:
   ```bash
   # Always commit uv.lock after dependency changes
   git add uv.lock pyproject.toml
   git commit -m "deps: add VCR testing dependencies for migration"
   ```

3. **Rollback Strategy**:
   ```bash
   # If dependencies cause issues, rollback
   git checkout HEAD~1 -- pyproject.toml uv.lock
   uv sync
   ```

4. **CI/CD Considerations**:
   ```yaml
   # GitHub Actions example
   - name: Install dependencies
     run: |
       uv sync --extra ai-optional

   - name: Run tests with VCR
     run: |
       uv run pytest tests/ --vcr-record=none
     env:
       VCR_RECORD_MODE: none
   ```

### Dependency Validation Commands

```bash
# Pre-migration validation
uv run python -c "import boss_bot; print('Current codebase imports OK')"

# Post-migration validation for each phase
uv run python -c "import boss_bot.ai.agents; print('AI components OK')"  # Phase 3
uv run python -c "import boss_bot.cli.main; print('CLI components OK')"   # Phase 2

# Full system validation
uv run pytest tests/test_migration/test_dependencies.py -v
```

### Troubleshooting Common Dependency Issues

```bash
# If VCR cassettes fail to load
uv add --upgrade vcrpy
uv run pytest tests/cassettes/ --collect-only

# If LangChain imports fail
uv add --upgrade langchain
uv run python -c "from langchain.llms import OpenAI; print('LangChain OK')"

# If pytest discovery fails
uv run pytest --collect-only --tb=short
```

## Migration Plan

Each migration phase will create a dedicated Pull Request for review and testing. This ensures changes are isolated, reviewable, and can be rolled back independently if needed.

### Phase 1: Foundation Reorganization (Week 1-2) - PR #1

#### Step 1.1: Create New Directory Structure
```bash
# Create new top-level directories
mkdir -p src/boss_bot/{ai,cli,integrations,api}

# Create AI subdirectories
mkdir -p src/boss_bot/ai/{agents,chains,tools,prompts,memory}

# Create CLI subdirectories
mkdir -p src/boss_bot/cli/{commands,utils,config}

# Create core subdirectories
mkdir -p src/boss_bot/core/{queue,downloads,services}
mkdir -p src/boss_bot/core/downloads/handlers

# Reorganize storage
mkdir -p src/boss_bot/storage/{managers,backends,models,migrations}

# Reorganize monitoring
mkdir -p src/boss_bot/monitoring/{health,metrics,logging}
mkdir -p src/boss_bot/monitoring/health/checks
mkdir -p src/boss_bot/monitoring/metrics/exporters

# Create schemas subdirectories
mkdir -p src/boss_bot/schemas/{api,discord,ai}

# Create bot subdirectories
mkdir -p src/boss_bot/bot/{events,middleware}

# Create integrations subdirectories
mkdir -p src/boss_bot/integrations/{langsmith,anthropic,openai,webhooks}

# Create API subdirectories (for future)
mkdir -p src/boss_bot/api/{routes,middleware,models}
```

#### Step 1.2: Move and Refactor Core Components
```bash
# Move core queue management
mv src/boss_bot/core/core_queue.py src/boss_bot/core/queue/manager.py

# Move download manager
mv src/boss_bot/downloaders/base.py src/boss_bot/core/downloads/manager.py

# Move storage managers
mv src/boss_bot/storage/quotas_manager.py src/boss_bot/storage/managers/quota_manager.py
mv src/boss_bot/storage/validation_manager.py src/boss_bot/storage/managers/validation_manager.py

# Move monitoring components
mv src/boss_bot/monitoring/health_check.py src/boss_bot/monitoring/health/checker.py
mv src/boss_bot/monitoring/metrics.py src/boss_bot/monitoring/metrics/collector.py
mv src/boss_bot/monitoring/logging.py src/boss_bot/monitoring/logging/logging_config.py
```

#### Step 1.3: Add Backward Compatibility and Deprecation Warnings
```bash
# Instead of deleting, add deprecation warnings and backward compatibility
# This allows gradual migration without breaking existing code

# Create backward compatibility imports in old locations
```

**Create deprecation wrapper files instead of deleting:**

1. **`src/boss_bot/global_cogs/__init__.py`** (Backward compatibility):
```python
"""
Deprecated: This module has been moved to boss_bot.bot.cogs
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""
import warnings
from boss_bot.bot.cogs import *

warnings.warn(
    "boss_bot.global_cogs is deprecated. Use boss_bot.bot.cogs instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2
)
```

2. **`src/boss_bot/downloaders/__init__.py`** (Backward compatibility):
```python
"""
Deprecated: This module has been moved to boss_bot.core.downloads
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""
import warnings
from boss_bot.core.downloads import *

warnings.warn(
    "boss_bot.downloaders is deprecated. Use boss_bot.core.downloads instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2
)
```

3. **`src/boss_bot/core/core_queue.py`** (Backward compatibility):
```python
"""
Deprecated: This module has been moved to boss_bot.core.queue.manager
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""
import warnings
from boss_bot.core.queue.manager import *

warnings.warn(
    "boss_bot.core.core_queue is deprecated. Use boss_bot.core.queue.manager instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2
)
```

#### Step 1.4: Update Import Statements (Gradual)
**Instead of updating all imports at once, use a gradual approach:**

1. **Update core application imports first** (bot, CLI entry points)
2. **Leave test imports unchanged initially** (they'll use backward compatibility)
3. **Update imports in new code only**
4. **Create import migration tracking**

**Create an import migration tracker: `IMPORT_MIGRATION.md`**
```markdown
# Import Migration Status

## ✅ Migrated Modules
- [ ] bot/client.py
- [ ] cli/main.py
- [ ] __main__.py

## ⚠️ Pending Migration (Using Deprecation Warnings)
- [ ] All test files
- [ ] Legacy import paths in existing code

## 📋 Migration Checklist
- Update imports gradually, module by module
- Run tests after each migration batch
- Monitor deprecation warnings in logs
```

### Phase 2: CLI Expansion (Week 3) - PR #2

#### 🎯 Phase 2 Progress Tracker (Current Status: 50% Complete)

**Platform Implementation Status:**
- **✅ Twitter/X Handler** (COMPLETED in v0.3.0)
  - ✅ `twitter_handler.py` - Gallery-dl integration with metadata extraction
  - ✅ Discord bot integration with 🐦 emoji and like/retweet display
  - ✅ CLI command `goobctl download twitter` with async/metadata-only support
  - ✅ Comprehensive test coverage (18 handler + 6 cog + 15 CLI tests)
  - ✅ CI/CD compatibility verified

- **✅ Reddit Handler** (COMPLETED in PR #11 - feature/phase2-reddit-support)
  - ✅ `reddit_handler.py` - Gallery-dl with custom config and cookie support
  - ✅ Discord bot integration with 🤖 emoji and subreddit/score display
  - ✅ CLI command `goobctl download reddit` with config/cookies options
  - ✅ Comprehensive test coverage (18 handler + 5 cog + 14 CLI tests)
  - ✅ CI/CD compatibility verified

- **⏳ YouTube Handler** (PENDING - Next Priority)
  - ⏳ `youtube_handler.py` - Yt-dlp integration with fallback strategies
  - ⏳ Discord bot integration with 📹 emoji and view/like display
  - ⏳ CLI command `goobctl download youtube` with quality/format options
  - ⏳ Test coverage for yt-dlp mocking and fallback scenarios

- **⏳ Instagram Handler** (PENDING)
  - ⏳ `instagram_handler.py` - Gallery-dl with browser cookie extraction
  - ⏳ Discord bot integration with 📷 emoji and follower display
  - ⏳ CLI command `goobctl download instagram` with cookie extraction
  - ⏳ Test coverage for authentication and private content scenarios

**Estimated Remaining Work:**
- YouTube: ~3-4 days (complex yt-dlp integration + fallback strategies)
- Instagram: ~3-4 days (complex authentication + cookie extraction)
- **Total Phase 2 Completion**: ~1-2 weeks for remaining platforms

**Next Session Pickup Points:**
1. **Create new branch**: `feature/phase2-youtube-support`
2. **Implement YouTube handler** following Twitter/Reddit patterns
3. **Add yt-dlp integration** with multiple fallback strategies
4. **Create comprehensive tests** with yt-dlp mocking

#### Step 2.1: Refactor CLI Structure (Non-Destructive)
```bash
# Instead of moving, copy and create backward compatibility
# Copy cli.py content to new structure
cp src/boss_bot/cli.py src/boss_bot/cli/main.py

# Create backward compatibility wrapper in old location
```

**Update `src/boss_bot/cli.py` to be a backward compatibility wrapper:**
```python
"""
Deprecated: CLI functionality has been moved to boss_bot.cli.main
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""
import warnings
from boss_bot.cli.main import *

warnings.warn(
    "Importing from boss_bot.cli is deprecated. Use boss_bot.cli.main instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export main CLI function for backward compatibility
if __name__ == "__main__":
    from boss_bot.cli.main import main
    main()
```

#### Step 2.2: Create CLI Subcommands

##### Core CLI Commands
- `cli/commands/bot.py` - Bot management (start, stop, status, restart)
- `cli/commands/queue.py` - Queue operations (list, clear, pause, resume)
- `cli/commands/download.py` - Download management with platform-specific handlers
- `cli/commands/cli_config.py` - Configuration management (show, set, validate)
- `cli/commands/ai.py` - AI workflow commands (analyze, summarize, classify)

##### Download Command Implementation (`cli/commands/download.py`)

The download command supports multiple platforms with both synchronous and asynchronous operations:

**Platform Support Matrix:**
- **✅ Twitter/X**: `gallery-dl` with metadata extraction (COMPLETED v0.3.0)
- **✅ Reddit**: `gallery-dl` with custom config and cookies (COMPLETED PR #11)
- **⏳ YouTube**: `yt-dlp` with fallback strategies and thumbnail conversion (PENDING)
- **⏳ Instagram**: `gallery-dl` with browser cookie extraction (PENDING)

**Command Structure:**
```python
# CLI command examples that will be implemented
@download_app.command("twitter")
def download_twitter(url: str, async_mode: bool = False):
    """Download Twitter content using gallery-dl"""

@download_app.command("reddit")
def download_reddit(url: str, async_mode: bool = False):
    """Download Reddit content using gallery-dl"""

@download_app.command("youtube")
def download_youtube(url: str, async_mode: bool = False):
    """Download YouTube content using yt-dlp with fallback strategies"""

@download_app.command("instagram")
def download_instagram(url: str, async_mode: bool = False):
    """Download Instagram content using gallery-dl with browser cookies"""
```

**Handler Implementation Strategy:**
```python
# core/downloads/handlers/ structure
handlers/
├── __init__.py
├── base_handler.py          # Abstract base class for all handlers
├── twitter_handler.py       # gallery-dl implementation for Twitter
├── reddit_handler.py        # gallery-dl implementation for Reddit
├── youtube_handler.py       # yt-dlp implementation with fallback logic
├── instagram_handler.py     # gallery-dl implementation for Instagram
└── generic_handler.py       # Fallback for unrecognized URLs
```

**Base Handler Pattern:**
```python
# Abstract base for both sync and async operations
class BaseDownloadHandler(ABC):
    @abstractmethod
    def download(self, url: str, **options) -> DownloadResult:
        """Synchronous download"""
        pass

    @abstractmethod
    async def adownload(self, url: str, **options) -> DownloadResult:
        """Asynchronous download (prefixed with 'a')"""
        pass

    @abstractmethod
    def get_metadata(self, url: str) -> MediaMetadata:
        """Extract metadata without downloading"""
        pass

    @abstractmethod
    async def aget_metadata(self, url: str) -> MediaMetadata:
        """Async metadata extraction"""
        pass
```

**Platform-Specific Configurations:**
```python
# Handler configurations based on shell aliases
TWITTER_CONFIG = {
    "tool": "gallery-dl",
    "args": ["--no-mtime", "-v", "--write-info-json", "--write-metadata"]
}

REDDIT_CONFIG = {
    "tool": "gallery-dl",
    "args": ["--config", "~/.gallery-dl.conf", "--no-mtime", "-v",
             "--write-info-json", "--write-metadata"],
    "cookies": "~/.config/gallery-dl/wavy-cookies-instagram.txt"
}

YOUTUBE_CONFIG = {
    "tool": "yt-dlp",
    "primary_strategy": "thumbnail_first",  # dl-thumb-fork
    "fallback_strategies": ["best_quality", "basic_dlp"],  # yt-best-fork, yt-dlp
    "args": ["-v", "-f", "best", "-n", "--ignore-errors",
             "--restrict-filenames", "--write-thumbnail", "--no-mtime",
             "--embed-thumbnail", "--recode-video", "mp4",
             "--convert-thumbnails", "jpg"],
    "cookies": "~/Downloads/yt-cookies.txt"
}

INSTAGRAM_CONFIG = {
    "tool": "gallery-dl",
    "args": ["--cookies-from-browser", "Firefox", "--no-mtime",
             "--user-agent", "Wget/1.21.1", "-v", "--write-info-json",
             "--write-metadata"]
}
```

**MVP Implementation Focus:**
For Phase 2 MVP, implement basic functionality for each platform:
- ✅ URL parsing and platform detection
- ✅ Basic download execution with proper tool selection
- ✅ Metadata extraction and JSON output
- ✅ Error handling and fallback strategies (especially for YouTube)
- ✅ Both sync and async API support
- 🔄 Advanced features (cookie management, format selection) in later phases

#### Step 2.3: CLI Utilities
- `cli/utils/formatters.py` - Rich console formatting for download progress
- `cli/utils/validators.py` - URL validation and platform detection
- `cli/config/settings.py` - CLI-specific configuration for download tools

#### Step 2.4: Download Tool Integration
**Dependencies and Environment Setup:**
```python
# Required external tools (managed via UV dependencies)
EXTERNAL_TOOLS = {
    "gallery-dl": "Available in virtual environment via UV",
    "yt-dlp": "Available in virtual environment via UV",
    "youtube-dl": "Available in virtual environment via UV"  # fallback
}

# All tools run within the same virtual environment
# No pyenv switching required - everything managed by UV
```

**MVP Testing Strategy:**
- Mock external tool calls for unit tests
- VCR cassettes for tool output parsing tests
- Integration tests with real URLs (limited scope)
- Platform detection accuracy tests

### Phase 3: AI Integration Foundation (Week 4-5) - PR #3

#### Step 3.1: LangChain/LangGraph Setup
- `ai/agents/content_analyzer.py` - Media content analysis workflows
- `ai/chains/summarization.py` - Content summarization chains
- `ai/tools/media_tools.py` - Media analysis tools
- `ai/prompts/templates.py` - Prompt templates

#### Step 3.2: AI Service Integrations
- `integrations/langsmith/langsmith_client.py` - LangSmith tracking
- `integrations/anthropic/anthropic_client.py` - Claude API integration
- `integrations/openai/openai_client.py` - OpenAI API integration

#### Step 3.3: AI-Powered Discord Commands
- `bot/cogs/ai_commands.py` - AI-powered Discord commands
- Integration with existing download and queue systems

### Phase 4: Enhanced Monitoring & Storage (Week 6) - PR #4

#### Step 4.1: Monitoring Improvements
- Reorganize health checks into dedicated modules
- Add AI service health monitoring
- Implement structured logging with formatters
- Add Prometheus metrics exporter

#### Step 4.2: Storage Backend Abstraction
- `storage/backends/local_storage.py` - Local filesystem backend
- `storage/models/file_models.py` - File metadata models
- Prepare for future cloud storage backends (S3, Azure)

### Phase 5: API Layer Foundation (Week 7-8) - PR #5

#### Step 5.1: REST API Structure
- `api/routes/downloads.py` - Download management endpoints
- `api/routes/queue.py` - Queue management endpoints
- `api/middleware/auth.py` - Authentication middleware
- `api/middleware/rate_limit.py` - Rate limiting

#### Step 5.2: API Documentation & Testing
- OpenAPI/Swagger documentation
- API integration tests
- Authentication and authorization

### Phase 6: Gradual Import Migration (Week 9-10) - PR #6

#### Step 6.1: Create Import Migration Script
```python
# scripts/migrate_imports.py
"""
Script to gradually migrate imports from old paths to new paths.
Tracks progress and ensures no regressions.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List

IMPORT_MAPPING = {
    "boss_bot.core.core_queue": "boss_bot.core.queue.manager",
    "boss_bot.downloaders.base": "boss_bot.core.downloads.manager",
    "boss_bot.global_cogs": "boss_bot.bot.cogs",
    # Add more mappings as needed
}

def migrate_file_imports(file_path: Path) -> bool:
    """Migrate imports in a single file."""
    # Implementation details...
    pass

def verify_migration(file_path: Path) -> bool:
    """Verify that migrated imports work correctly."""
    # Implementation details...
    pass
```

#### Step 6.2: Migrate in Batches
1. **Batch 1**: Core application files (bot/client.py, __main__.py)
2. **Batch 2**: CLI modules (cli/main.py and subcommands)
3. **Batch 3**: Core business logic (queue, downloads, storage)
4. **Batch 4**: Monitoring and utilities
5. **Batch 5**: Test files (last, to catch any issues)

#### Step 6.3: Monitor Deprecation Warnings
```bash
# Add logging configuration to capture deprecation warnings
python -W error::DeprecationWarning -m pytest tests/
```

### Phase 7: Deprecation Cleanup (Week 11-12) - PR #7

#### Step 7.1: Final Migration Verification
- Ensure all imports have been migrated
- Run comprehensive tests with deprecation warnings as errors
- Verify no production code uses deprecated paths

#### Step 7.2: Remove Deprecated Files (Only After Full Migration)
```bash
# Only run this after 100% certain all imports are migrated
# and comprehensive testing has passed

# Remove deprecated wrapper files
rm src/boss_bot/cli.py  # Now points to cli/main.py
rm src/boss_bot/core/core_queue.py  # Now points to core/queue/manager.py

# Remove deprecated directories (only if completely empty)
# Check that these only contain __init__.py with deprecation warnings
rmdir src/boss_bot/global_cogs/  # If completely migrated
rmdir src/boss_bot/downloaders/  # If completely migrated
```

#### Step 7.3: Update Documentation
- Remove all references to old import paths
- Update examples and tutorials
- Update deployment and setup instructions

## Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Document current functionality
- [ ] Ensure all tests pass
- [ ] Review dependencies and compatibility

### Phase 1: Foundation (PR #1)
- [ ] Create new directory structure
- [ ] Move core components to new locations
- [ ] Update import statements throughout codebase
- [ ] Update tests for new import paths
- [ ] Remove duplicate and empty modules
- [ ] Verify all tests still pass
- [ ] Update documentation
- [ ] Create and merge PR #1

### Phase 2: CLI Expansion (PR #2)
- [ ] Refactor monolithic CLI to modular structure
- [ ] Implement bot management subcommands
- [ ] Implement queue management subcommands
- [ ] Implement download management subcommands
- [ ] Implement configuration subcommands
- [ ] Add Rich formatting utilities
- [ ] Add input validation utilities
- [ ] Test all CLI functionality
- [ ] Create and merge PR #2

### Phase 3: AI Integration (PR #3)
- [ ] Set up LangChain/LangGraph foundation
- [ ] Implement content analysis agents
- [ ] Create summarization chains
- [ ] Develop media analysis tools
- [ ] Set up prompt template system
- [ ] Integrate AI service clients (LangSmith, Anthropic, OpenAI)
- [ ] Create AI-powered Discord commands
- [ ] Test AI functionality end-to-end
- [ ] Create and merge PR #3

### Phase 4: Monitoring & Storage (PR #4)
- [ ] Reorganize health check system
- [ ] Implement AI service health monitoring
- [ ] Set up structured logging with formatters
- [ ] Add Prometheus metrics exporter
- [ ] Abstract storage backend system
- [ ] Implement file metadata models
- [ ] Test monitoring and storage improvements
- [ ] Create and merge PR #4

### Phase 5: API Layer (PR #5)
- [ ] Implement REST API foundation
- [ ] Create download management endpoints
- [ ] Create queue management endpoints
- [ ] Set up authentication middleware
- [ ] Implement rate limiting
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Create API integration tests
- [ ] Test API functionality
- [ ] Create and merge PR #5

### Phase 6: Import Migration (PR #6)
- [ ] Create import migration script
- [ ] Migrate imports in batches
- [ ] Monitor deprecation warnings
- [ ] Verify all migration paths work
- [ ] Create and merge PR #6

### Phase 7: Cleanup (PR #7)
- [ ] Final migration verification
- [ ] Remove deprecated files
- [ ] Update documentation
- [ ] Performance and security review
- [ ] Create and merge PR #7

### Post-Migration
- [ ] Update all documentation
- [ ] Update deployment scripts
- [ ] Update CI/CD pipelines
- [ ] Performance testing
- [ ] Security review
- [ ] User acceptance testing

## Risk Mitigation

### Backward Compatibility Strategy
- **Deprecation Warnings**: All old import paths show clear deprecation warnings
- **Parallel Code Existence**: Old and new code coexist during transition
- **Gradual Migration**: Imports updated incrementally, not all at once
- **Feature Flags**: New functionality behind feature flags during development
- **Version Planning**: Clear timeline for removal (v2.0.0) with advance notice

### Safe Migration Principles
1. **Copy, Don't Move**: Create new structure alongside old one
2. **Wrapper Files**: Old locations become import wrappers with warnings
3. **Incremental Updates**: Update imports module by module, not en masse
4. **Comprehensive Testing**: Full test suite runs after each phase
5. **Rollback Ready**: Each phase can be individually rolled back

### TDD-First Testing Strategy

This migration follows **Test-Driven Development (TDD)** principles using pytest and specialized plugins for comprehensive testing without high costs.

#### Core Testing Framework Stack
- **pytest**: Primary testing framework for all test types
- **pytest-asyncio**: Testing async/await patterns (Discord bot, AI chains)
- **pytest-mock**: Mocking without unittest.mock dependency
- **pytest-vcr** + **vcrpy**: Record/replay for LLM API calls (following LangChain patterns)
- **pytest-freezegun**: Time-based testing for queues and monitoring
- **pytest-aioresponses**: HTTP mocking for download handlers

#### VCR.py Integration (LangChain Pattern)
Following LangChain's approach for cost-effective AI testing:
- **Cassette-based testing**: Record real API responses once, replay forever
- **Integration test focus**: VCR for external API calls, mocks for unit tests
- **CI/CD optimization**: `--vcr-record=none` to prevent new recordings in CI

#### TDD Migration Approach
**Write tests BEFORE implementing new structure:**

1. **Red Phase**: Write failing tests for new module structure
2. **Green Phase**: Implement minimal code to pass tests
3. **Refactor Phase**: Improve code while keeping tests green
4. **MVP Focus**: Core functionality tests first, edge cases later

#### Testing Strategy by Component

##### 1. **AI Components Testing (pytest-vcr + vcrpy)**
```python
# tests/test_ai/test_agents/test_content_analyzer.py
import pytest
import vcr
from pytest_vcr import use_cassette

# Following LangChain's VCR pattern for AI testing
@use_cassette("tests/cassettes/ai/content_analyzer_basic.yaml")
@pytest.mark.asyncio
async def test_content_analyzer_basic_analysis():
    """Test basic content analysis functionality.

    MVP: Basic content classification only
    TODO: Add edge cases like malformed content, rate limits, API errors
    """
    analyzer = ContentAnalyzer()
    result = await analyzer.analyze("https://example.com/video")
    assert result.content_type in ["video", "image", "text"]
    # TODO: Add tests for unsupported formats
    # TODO: Add tests for large content handling
    # TODO: Add tests for content moderation flags

# LangChain-style context manager approach for dynamic cassettes
@pytest.mark.asyncio
async def test_langchain_summarization():
    """Test LangChain summarization functionality.

    MVP: Basic text summarization
    TODO: Add tests for different content types, languages, lengths
    """
    cassette_path = "tests/cassettes/ai/langchain_summarization.yaml"
    with vcr.use_cassette(cassette_path, record_mode='once'):
        # This will record on first run, replay on subsequent runs
        chain = SummarizationChain()
        result = await chain.run("Sample text to summarize")
        assert len(result) < len("Sample text to summarize")
        # TODO: Add tests for different content types, languages, lengths

# Provider-specific cassette organization (LangChain pattern)
@use_cassette("tests/cassettes/ai/openai/chat_completion.yaml")
@pytest.mark.asyncio
async def test_openai_integration():
    """Test OpenAI API integration via openai_client.py."""
    from boss_bot.integrations.openai.openai_client import OpenAIClient
    # Implementation will use recorded responses
    pass

@use_cassette("tests/cassettes/ai/anthropic/claude_completion.yaml")
@pytest.mark.asyncio
async def test_anthropic_integration():
    """Test Anthropic Claude API integration via anthropic_client.py."""
    from boss_bot.integrations.anthropic.anthropic_client import AnthropicClient
    # Implementation will use recorded responses
    pass
```

##### 2. **CLI Testing (pytest-mock, pytest-freezegun)**
```python
# tests/test_cli/test_commands/test_bot_commands.py
import pytest
from pytest_mock import MockerFixture
from freezegun import freeze_time

@pytest.mark.asyncio
async def test_bot_start_command(mocker: MockerFixture):
    """Test bot start command.

    MVP: Basic start/stop functionality
    TODO: Add tests for restart, graceful shutdown, error recovery
    """
    mock_bot = mocker.Mock()
    # Test implementation

@freeze_time("2024-01-01 12:00:00")
def test_bot_status_command_with_uptime(mocker: MockerFixture):
    """Test bot status shows correct uptime.

    MVP: Basic status display
    TODO: Add tests for detailed metrics, health status, resource usage
    """
    # Test implementation with frozen time
    pass
```

##### 3. **Download Handlers Testing (pytest-aioresponses)**
```python
# tests/test_core/test_downloads/test_handlers/test_youtube_handler.py
import pytest
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_youtube_handler_basic_download():
    """Test YouTube download handler.

    MVP: Basic YouTube URL parsing and metadata extraction
    TODO: Add tests for playlists, live streams, age-restricted content
    """
    with aioresponses() as mocked:
        mocked.get('https://youtube.com/api/video/info', payload={'title': 'Test Video'})

        handler = YouTubeHandler()
        result = await handler.extract_info("https://youtube.com/watch?v=test")
        assert result.title == "Test Video"
        # TODO: Add tests for video quality selection
        # TODO: Add tests for subtitle extraction
        # TODO: Add tests for playlist handling
```

##### 4. **Queue Management Testing (pytest-asyncio, pytest-freezegun)**
```python
# tests/test_core/test_queue/test_manager.py
import pytest
from freezegun import freeze_time

@pytest.mark.asyncio
async def test_queue_manager_basic_operations():
    """Test basic queue operations.

    MVP: Add, remove, pause, resume functionality
    TODO: Add tests for priority queues, queue persistence, error recovery
    """
    manager = QueueManager()
    item = QueueItem(url="https://example.com", user_id=123)

    await manager.add_to_queue(item)
    assert await manager.get_queue_size() == 1
    # TODO: Add tests for queue limits
    # TODO: Add tests for queue serialization
    # TODO: Add tests for concurrent access

@freeze_time("2024-01-01 12:00:00")
@pytest.mark.asyncio
async def test_queue_processing_timing():
    """Test queue processing respects timing constraints.

    MVP: Basic processing timing
    TODO: Add tests for rate limiting, retry logic, exponential backoff
    """
    # Test implementation
    pass
```

##### 5. **Backward Compatibility Testing**
```python
# tests/test_migration/test_deprecation_warnings.py
import pytest
import warnings

def test_deprecated_import_paths_show_warnings():
    """Test that deprecated import paths show proper warnings.

    MVP: Basic deprecation warnings
    TODO: Add tests for import path mapping, version-specific warnings
    """
    with pytest.warns(DeprecationWarning, match="boss_bot.global_cogs is deprecated"):
        from boss_bot.global_cogs import DownloadCog

    # TODO: Add tests for all deprecated paths
    # TODO: Add tests for warning suppression in production

def test_deprecated_functionality_still_works():
    """Test that deprecated code paths still function correctly.

    MVP: Basic functionality preservation
    TODO: Add comprehensive functional tests for all deprecated paths
    """
    # Test that old import paths work identically to new ones
    pass
```

#### MVP Testing Priorities

##### **Phase 1: Foundation Tests (Week 1)**
```python
# MVP Test Coverage Goals:
# - [ ] New directory structure imports work
# - [ ] Deprecation warnings are shown
# - [ ] Basic functionality preserved
# - [ ] Core bot client still initializes

# TODO for Post-MVP:
# - [ ] Comprehensive error handling tests
# - [ ] Performance regression tests
# - [ ] Memory usage tests
# - [ ] Concurrency stress tests
```

##### **Phase 2: CLI Tests (Week 2)**
```python
# MVP Test Coverage Goals:
# - [ ] Basic CLI commands work
# - [ ] Subcommand structure functions
# - [ ] Help text displays correctly
# - [ ] Basic error handling

# TODO for Post-MVP:
# - [ ] Complex command combinations
# - [ ] Configuration edge cases
# - [ ] Interactive command testing
# - [ ] CLI performance optimization
```

##### **Phase 3: AI Integration Tests (Week 3-4)**
```python
# MVP Test Coverage Goals:
# - [ ] Basic LangChain chain execution
# - [ ] Simple content analysis
# - [ ] AI tool integration with Discord
# - [ ] Cost-controlled testing with recordings

# TODO for Post-MVP:
# - [ ] Complex multi-step workflows
# - [ ] Error recovery and retry logic
# - [ ] Performance optimization
# - [ ] Multiple AI provider testing
```

#### Cost-Controlled Testing Strategy

##### **VCR Configuration for LLM Calls (LangChain Pattern)**
```python
# conftest.py additions for AI testing
import pytest
import vcr

@pytest.fixture(scope="session")
def vcr_config():
    """Configure VCR for LLM API recording (following LangChain approach)."""
    return {
        "cassette_library_dir": "tests/cassettes",
        "filter_headers": [
            "authorization",
            "x-api-key",
            "openai-api-key",
            "anthropic-api-key"
        ],
        "decode_compressed_response": True,
        "ignore_localhost": True,
        "record_mode": "once",  # Record once, replay forever
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
    }

@pytest.fixture(scope="session")
def vcr_cassette_dir():
    """Set VCR cassette directory (LangChain pattern)."""
    return "tests/cassettes"

# CI/CD command for cost control (LangChain approach):
# pytest tests/test_ai/ --vcr-record=none
```

##### **Cassette Organization (LangChain Structure)**
```python
# tests/cassettes/ directory structure following LangChain pattern
tests/cassettes/
├── ai/
│   ├── openai/
│   │   ├── chat_completion.yaml
│   │   ├── text_completion.yaml
│   │   └── embedding.yaml
│   ├── anthropic/
│   │   ├── claude_completion.yaml
│   │   └── claude_streaming.yaml
│   ├── langsmith/
│   │   ├── run_tracking.yaml
│   │   └── evaluation.yaml
│   └── chains/
│       ├── summarization_chain.yaml
│       └── classification_chain.yaml
├── downloads/
│   ├── youtube_api.yaml
│   ├── twitter_api.yaml
│   └── generic_metadata.yaml
└── integrations/
    ├── discord_webhooks.yaml
    └── health_checks.yaml
```

##### **Mock Strategy for Development (Hybrid Approach)**
```python
# tests/fixtures/ai_fixtures.py
@pytest.fixture
def mock_llm_response(mocker: MockerFixture):
    """Mock LLM responses for fast unit testing."""
    return mocker.patch("langchain.llms.base.LLM.generate",
                       return_value=mock_response_data)

# Hybrid approach: VCR for integration tests, mocks for unit tests
# Unit tests: Fast mocks for business logic testing
# Integration tests: VCR cassettes for real API interaction testing
```

##### **VCR Record Modes (LangChain Approach)**
```python
# Different record modes for different testing scenarios:

# record_mode='once' - Record once, replay forever (default)
@use_cassette("test.yaml", record_mode='once')

# record_mode='new_episodes' - Record new interactions, replay existing
@use_cassette("test.yaml", record_mode='new_episodes')

# record_mode='none' - Only replay, never record (CI/CD)
# pytest --vcr-record=none

# record_mode='all' - Always record (for cassette updates)
@use_cassette("test.yaml", record_mode='all')
```

##### **CI/CD Cost Control Commands**
```bash
# Development: Allow recording new cassettes
pytest tests/test_ai/

# CI/CD: Prevent new recordings, fail if cassette missing
pytest tests/test_ai/ --vcr-record=none

# Update cassettes: Force re-recording (use sparingly)
pytest tests/test_ai/ --vcr-record=all

# Integration tests only: Skip unit tests to save time
pytest tests/integration_tests/ --vcr-record=none
```

#### Testing Phase Timeline

##### **Week 1-2: Foundation TDD**
- Write tests for new structure before implementation
- Focus on import path testing and deprecation warnings
- Basic functionality preservation tests

##### **Week 3: CLI TDD**
- Test-driven CLI subcommand development
- Mock external dependencies with pytest-mock
- Time-based testing with pytest-freezegun

##### **Week 4-5: AI TDD**
- Record initial LLM interactions for playback
- Test-driven AI agent development
- Cost-controlled integration testing

##### **Week 6-8: Integration TDD**
- End-to-end workflow testing
- Performance baseline establishment
- Production readiness verification

#### Test Organization Structure (LangChain-Inspired)
```
tests/
├── fixtures/                    # Shared test fixtures and mocks
│   ├── ai_fixtures.py          # LLM mocks for unit tests
│   ├── bot_fixtures.py         # Discord bot test helpers
│   └── cli_fixtures.py         # CLI testing utilities
├── cassettes/                   # VCR cassettes (LangChain pattern)
│   ├── ai/                     # AI provider recordings
│   │   ├── openai/             # OpenAI API responses
│   │   ├── anthropic/          # Anthropic API responses
│   │   ├── langsmith/          # LangSmith tracking
│   │   └── chains/             # LangChain chain recordings
│   ├── downloads/              # Download service recordings
│   │   ├── youtube_api.yaml    # YouTube API responses
│   │   ├── twitter_api.yaml    # Twitter API responses
│   │   └── generic_metadata.yaml
│   └── integrations/           # External service recordings
│       ├── discord_webhooks.yaml
│       └── health_checks.yaml
├── unit_tests/                 # Fast unit tests (mocked)
│   ├── test_ai/               # AI component unit tests
│   ├── test_cli/              # CLI component unit tests
│   ├── test_core/             # Core business logic tests
│   └── test_migration/        # Migration-specific tests
├── integration_tests/          # Slower integration tests (VCR)
│   ├── test_ai_integrations/  # AI provider integration tests
│   ├── test_download_integrations/ # Download service tests
│   └── test_bot_integrations/ # Discord bot integration tests
└── end_to_end/                # Full workflow tests
    ├── test_bot_workflows.py
    ├── test_ai_workflows.py
    └── test_cli_workflows.py

# Following LangChain's testing philosophy:
# - unit_tests/: Fast, mocked, comprehensive coverage
# - integration_tests/: VCR-recorded, external service validation
# - end_to_end/: Full workflow validation with real components
```

#### MVP Success Criteria
- ✅ All existing tests pass with new structure
- ✅ New components have basic test coverage (>80%)
- ✅ AI components tested with VCR cassettes (cost-controlled, LangChain pattern)
- ✅ CLI components have command-level testing
- ✅ Deprecation warnings properly tested
- ✅ Performance baseline established
- ✅ VCR cassettes organized by provider (OpenAI, Anthropic, LangSmith)
- ✅ CI/CD configured with `--vcr-record=none` for cost control

#### Post-MVP Testing Expansion
- 🔄 Comprehensive edge case testing
- 🔄 Stress testing and performance optimization
- 🔄 Security testing for AI inputs
- 🔄 Comprehensive error recovery testing
- 🔄 Multi-provider AI testing
- 🔄 Advanced CLI interaction testing

### Rollback Plan
- **Git branches** for each migration phase
- **Deprecation wrapper removal** as simple rollback (delete new, restore old)
- **Database migration rollback** scripts (future phases)
- **Configuration backup** and restore procedures
- **Automated rollback triggers** for critical failures
- **Import path restoration** by removing wrapper files and restoring original imports

## Expected Benefits

### Short Term (Phases 1-2)
- Cleaner, more maintainable codebase
- Better separation of concerns
- More powerful and extensible CLI
- Easier testing and debugging

### Medium Term (Phases 3-4)
- AI-powered content analysis and moderation
- Enhanced monitoring and observability
- Better storage management and scalability
- Improved error handling and recovery

### Long Term (Phase 5+)
- REST API for external integrations
- Microservice architecture readiness
- Cloud-native deployment capabilities
- Enhanced security and authentication

## Dependencies

### New Dependencies (Phase 3)
- `langchain` - LangChain framework
- `langgraph` - LangGraph workflow engine
- `langsmith` - LangSmith tracking (optional)
- `anthropic` - Claude API client
- `openai` - OpenAI API client

### Enhanced Dependencies
- `typer` - CLI framework (already present)
- `rich` - Console formatting (already present)
- `prometheus_client` - Metrics collection (new)
- `fastapi` - REST API framework (Phase 5)

## Timeline

Each phase creates a dedicated Pull Request for isolated review and testing:

- **Week 1-2**: Phase 1 (Foundation Reorganization) - *Copy & create wrappers* - **PR #1**
- **Week 3**: Phase 2 (CLI Expansion) - *Modular CLI with backward compatibility* - **PR #2**
- **Week 4-5**: Phase 3 (AI Integration Foundation) - *LangChain/LangGraph setup* - **PR #3**
- **Week 6**: Phase 4 (Enhanced Monitoring & Storage) - *Infrastructure improvements* - **PR #4**
- **Week 7-8**: Phase 5 (API Layer Foundation) - *REST API groundwork* - **PR #5**
- **Week 9-10**: Phase 6 (Gradual Import Migration) - *Update imports incrementally* - **PR #6**
- **Week 11-12**: Phase 7 (Deprecation Cleanup) - *Remove old files after migration* - **PR #7**

Total estimated time: **12 weeks** for complete migration with safe deprecation period.

### Deprecation Timeline
- **v1.5.0** (PR #3 merge): AI integration, deprecation warnings active
- **v1.6.0** (PR #5 merge): API layer complete, warnings remain
- **v1.9.0** (PR #6 merge): Import migration complete, final warning
- **v2.0.0** (PR #7 merge): Remove deprecated paths entirely

### Pull Request Strategy
Each phase will have its own Pull Request to ensure:
- **Isolated Changes**: Each PR contains only one phase's changes
- **Independent Review**: Each phase can be reviewed and tested separately
- **Rollback Safety**: Individual phases can be rolled back without affecting others
- **Incremental Deployment**: Phases can be deployed incrementally based on stability
- **Clear Documentation**: Each PR includes phase-specific documentation and tests

## Common Migration Issues & Solutions

### Import and Module Errors

#### **Circular Import Issues**
```bash
# Problem: Circular imports during migration
# Solution: Break circular dependencies with forward references

# Error example:
# ImportError: cannot import name 'QueueManager' from partially initialized module

# Fix approach:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from boss_bot.core.queue.manager import QueueManager

# Use string annotations for type hints
def process_queue(manager: "QueueManager") -> None:
    pass
```

#### **Missing Module Errors During Migration**
```bash
# Problem: ModuleNotFoundError for new structure
# Solution: Verify __init__.py files and import paths

# Debug command:
python -c "import boss_bot.ai.agents; print('AI agents import OK')"

# Create missing __init__.py files:
touch src/boss_bot/ai/__init__.py
touch src/boss_bot/ai/agents/__init__.py
touch src/boss_bot/cli/__init__.py
touch src/boss_bot/cli/commands/__init__.py

# Verify package structure:
python -c "import pkgutil; print(list(pkgutil.walk_packages(['src/boss_bot'])))"
```

#### **Deprecation Warning Suppression (Production)**
```python
# Problem: Deprecation warnings flood production logs
# Solution: Selective warning suppression

# In production configuration:
import warnings
from boss_bot.core.env import BossSettings

settings = BossSettings()
if settings.environment == "production":
    # Suppress only migration-related deprecation warnings
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="boss_bot.global_cogs"
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="boss_bot.downloaders"
    )

# Keep other deprecation warnings visible
# Only suppress our own migration warnings
```

### VCR Cassette Issues

#### **Missing Cassettes in CI/CD**
```bash
# Problem: CI fails with "Cassette not found" errors
# Solution: Ensure cassettes are committed and paths are correct

# Check cassette files exist:
ls tests/cassettes/ai/openai/
ls tests/cassettes/ai/anthropic/

# Verify cassette paths in tests:
grep -r "use_cassette" tests/test_ai/

# Generate missing cassettes (dev only):
uv run pytest tests/test_ai/ --vcr-record=once
git add tests/cassettes/
git commit -m "Add missing VCR cassettes for AI tests"

# CI configuration to fail fast:
# pytest tests/ --vcr-record=none --tb=short
```

#### **API Keys in VCR Recordings**
```yaml
# Problem: Accidentally recorded API keys in cassettes
# Solution: Filter sensitive headers

# VCR configuration (conftest.py):
@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "openai-api-key",
            "anthropic-api-key",
            "x-anthropic-api-key",
            "bearer"
        ],
        "filter_query_parameters": ["api_key", "key"],
        "before_record_response": lambda response: response
    }

# Clean existing cassettes with exposed keys:
find tests/cassettes -name "*.yaml" -exec grep -l "sk-" {} \;
# Delete and re-record these cassettes
```

#### **VCR Cassette Version Conflicts**
```bash
# Problem: Cassettes recorded with different VCR versions are incompatible
# Solution: Standardize VCR version and re-record if needed

# Check VCR versions:
uv run python -c "import vcr; print(vcr.__version__)"

# Re-record all cassettes with current version:
uv run pytest tests/test_ai/ --vcr-record=all
git add tests/cassettes/
git commit -m "Re-record cassettes with VCR $(uv run python -c 'import vcr; print(vcr.__version__)')"
```

### CLI Migration Problems

#### **Command Not Found Errors**
```bash
# Problem: New CLI commands not discoverable
# Solution: Verify entry points and CLI registration

# Check entry points in pyproject.toml:
[project.scripts]
bossctl = "boss_bot.cli.main:main"
boss-bot = "boss_bot.cli.main:main"  # Backward compatibility

# Reinstall in development mode:
uv pip install -e .

# Test CLI discovery:
bossctl --help
boss-bot --help

# Debug CLI import issues:
python -c "from boss_bot.cli.main import main; main(['--help'])"
```

#### **CLI Entry Point Issues**
```bash
# Problem: Entry points not updating after migration
# Solution: Reinstall package and clear pip cache

# Reinstall package in development mode:
uv sync

# If issues persist, remove and reinstall:
rm -rf .venv
uv sync

# Verify entry points:
which bossctl
bossctl --version

# Alternative: Direct execution
uv run python -m boss_bot.cli --help
```

### AI Integration Issues

#### **LangChain Import Failures**
```bash
# Problem: LangChain components fail to import
# Solution: Verify versions and optional dependencies

# Check LangChain installation:
uv run python -c "import langchain; print(langchain.__version__)"
uv run python -c "import langgraph; print('LangGraph OK')"

# Install missing components:
uv add langchain-openai
uv add langchain-anthropic
uv add langchain-community

# Debug specific import failures:
uv run python -c "from langchain.llms import OpenAI; print('OpenAI OK')"
uv run python -c "from langchain_anthropic import ChatAnthropic; print('Anthropic OK')"
```

#### **AI Service Authentication Failures**
```bash
# Problem: AI services fail authentication during testing
# Solution: Verify environment variables and API key format

# Check environment variables:
echo $OPENAI_API_KEY | head -c 10  # Should start with 'sk-'
echo $ANTHROPIC_API_KEY | head -c 10  # Should start with 'sk-ant-'

# Test API connectivity:
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test in development environment:
uv run python -c "
from boss_bot.core.env import BossSettings
settings = BossSettings()
print(f'OpenAI key: {settings.openai_api_key[:10]}...')
print(f'Anthropic key: {settings.anthropic_api_key[:10]}...')
"
```

## Migration Validation & Testing

### Pre-Migration Validation

#### **Current System Health Check**
```bash
# Verify current system is stable before migration
just check  # Run full test suite
just check-coverage  # Ensure test coverage baseline

# Document current performance baseline:
time python -m boss_bot --version
time bossctl --help

# Memory usage baseline:
/usr/bin/time -v uv run python -c "import boss_bot; print('Import OK')"

# Save baseline metrics:
echo "Pre-migration baseline: $(date)" > migration-baseline.txt
just check 2>&1 | grep -E "(passed|failed|error)" >> migration-baseline.txt
```

#### **Dependency Compatibility Check**
```bash
# Verify all dependencies are compatible
uv pip check

# Check for conflicting versions:
uv tree

# Verify Python version compatibility:
python --version  # Should be >= 3.12
python -c "import sys; print(sys.version_info)"

# Check critical imports work:
uv run python -c "import discord, pytest, rich, typer; print('Core deps OK')"
```

### Post-Phase Validation

#### **Phase 1 Validation: Foundation**
```bash
# After Phase 1 completion, verify:

# 1. All new directories exist:
find src/boss_bot -type d -name "__pycache__" -prune -o -type d -print

# 2. All __init__.py files present:
find src/boss_bot -name "__init__.py" | wc -l  # Should be > 20

# 3. Deprecation warnings work:
uv run python -W error::DeprecationWarning -c "
try:
    from boss_bot.global_cogs import downloads
except DeprecationWarning:
    print('Deprecation warnings working correctly')
"

# 4. Import path mappings work:
uv run python -c "
from boss_bot.core.queue.manager import QueueManager
from boss_bot.core.core_queue import QueueManager as OldQueueManager
assert QueueManager is OldQueueManager
print('Import mapping working')
"

# 5. Tests still pass:
just check-test
```

#### **Phase 2 Validation: CLI**
```bash
# After Phase 2 completion, verify:

# 1. CLI commands discoverable:
bossctl --help | grep -E "(bot|queue|download|config)"

# 2. Subcommands work:
bossctl bot --help
bossctl queue --help
bossctl config --help

# 3. Backward compatibility:
uv run python -c "from boss_bot.cli import main; print('Old CLI import works')"

# 4. CLI performance:
time bossctl --help  # Should be < 2 seconds

# 5. CLI tests pass:
pytest tests/test_cli/ -v
```

#### **Phase 3 Validation: AI Integration**
```bash
# After Phase 3 completion, verify:

# 1. AI imports work:
uv run python -c "import boss_bot.ai.agents; print('AI agents OK')"
uv run python -c "import boss_bot.ai.chains; print('AI chains OK')"

# 2. LangChain integration:
uv run python -c "
from boss_bot.ai.chains.summarization import SummarizationChain
print('LangChain integration OK')
"

# 3. VCR cassettes exist:
find tests/cassettes/ai -name "*.yaml" | wc -l  # Should be > 5

# 4. AI tests pass with VCR:
pytest tests/test_ai/ --vcr-record=none -v

# 5. Cost control verification:
grep -r "ANTHROPIC_API_KEY" tests/cassettes/ && echo "WARNING: API keys in cassettes!"
```

### Performance Validation

#### **Import Performance Testing**
```bash
# Test import time doesn't regress
time uv run python -c "import boss_bot"  # Should be < 1 second
time uv run python -c "import boss_bot.bot.client"  # Should be < 0.5 seconds
time uv run python -c "import boss_bot.ai.agents"  # Should be < 2 seconds (AI deps)

# Memory usage testing:
/usr/bin/time -v uv run python -c "
import boss_bot
from boss_bot.bot.client import BossBot
bot = BossBot()
print('Bot initialized')
" 2>&1 | grep "Maximum resident set size"
```

#### **Runtime Performance Testing**
```bash
# Bot startup time:
time uv run python -c "
from boss_bot.bot.client import BossBot
bot = BossBot()
print('Bot ready')
"  # Should be < 3 seconds

# CLI responsiveness:
time bossctl bot status  # Should be < 1 second
time bossctl queue list  # Should be < 1 second

# AI chain performance (with VCR):
time uv run pytest tests/test_ai/test_chains/test_summarization.py::test_basic_summarization -v
```

### Automated Validation Scripts

#### **Migration Health Check Script**
```python
# scripts/migration_health_check.py
#!/usr/bin/env python3
"""
Migration health check script.
Run after each migration phase to verify system integrity.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List

def run_command(cmd: str) -> tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def check_imports() -> Dict[str, bool]:
    """Check critical imports work."""
    imports_to_test = [
        "boss_bot",
        "boss_bot.bot.client",
        "boss_bot.core.env",
        "boss_bot.core.queue.manager",
        "boss_bot.cli.main",
    ]

    results = {}
    for import_path in imports_to_test:
        code = f"import {import_path}"
        exit_code, _, _ = run_command(f"uv run python -c \"{code}\"")
        results[import_path] = exit_code == 0

    return results

def check_tests() -> bool:
    """Check that tests pass."""
    exit_code, _, _ = run_command("just check-test")
    return exit_code == 0

def check_cli() -> bool:
    """Check CLI functionality."""
    exit_code, _, _ = run_command("bossctl --help")
    return exit_code == 0

def main():
    """Run all health checks."""
    print("Running migration health checks...")

    # Check imports
    print("\n1. Testing imports...")
    import_results = check_imports()
    for import_path, success in import_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {import_path}")

    # Check tests
    print("\n2. Testing test suite...")
    tests_pass = check_tests()
    status = "✅" if tests_pass else "❌"
    print(f"  {status} Test suite")

    # Check CLI
    print("\n3. Testing CLI...")
    cli_works = check_cli()
    status = "✅" if cli_works else "❌"
    print(f"  {status} CLI functionality")

    # Summary
    all_good = all(import_results.values()) and tests_pass and cli_works
    print("\n" + "="*50)
    if all_good:
        print("✅ All health checks passed!")
        sys.exit(0)
    else:
        print("❌ Some health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### **Usage Example**
```bash
# Run after each migration phase:
uv run python scripts/migration_health_check.py

# Integrate into CI/CD:
# .github/workflows/migration.yml
- name: Migration Health Check
  run: |
    uv run python scripts/migration_health_check.py
```

## Production Deployment Strategy

### GitHub Release-Based Deployment

#### **Deployment Architecture**
Deployment is handled through GitHub releases with automated CI/CD workflows. Each migration phase is deployed as a new release version with feature flags controlling the rollout.

```yaml
# .github/workflows/release.yml
name: Release and Deploy

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup UV
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --extra ai-optional

      - name: Run tests
        run: uv run pytest tests/ --vcr-record=none

      - name: Build and deploy
        run: |
          # Build Docker image with release tag
          docker build -t boss-bot:${{ github.event.release.tag_name }} .

          # Deploy to production environment
          # This could be Kubernetes, Docker Compose, or other deployment target
          ./scripts/deploy-production.sh ${{ github.event.release.tag_name }}
        env:
          ENABLE_AI_FEATURES: ${{ secrets.ENABLE_AI_FEATURES }}
          AI_ROLLOUT_PERCENTAGE: ${{ secrets.AI_ROLLOUT_PERCENTAGE }}
```

#### **Feature Flags for Gradual AI Rollout**
```python
# src/boss_bot/core/env.py
class BossSettings(BaseSettings):
    # ... existing settings ...

    # Migration feature flags
    enable_ai_features: bool = Field(default=False, env="ENABLE_AI_FEATURES")
    enable_new_cli: bool = Field(default=False, env="ENABLE_NEW_CLI")
    enable_enhanced_monitoring: bool = Field(default=False, env="ENABLE_ENHANCED_MONITORING")

    # AI feature granular flags
    enable_content_analysis: bool = Field(default=False, env="ENABLE_CONTENT_ANALYSIS")
    enable_summarization: bool = Field(default=False, env="ENABLE_SUMMARIZATION")
    enable_moderation: bool = Field(default=False, env="ENABLE_MODERATION")

    # Rollout percentage (0-100)
    ai_rollout_percentage: int = Field(default=0, env="AI_ROLLOUT_PERCENTAGE")

# Feature flag usage in cogs:
class DownloadCog(commands.Cog):
    @commands.command()
    async def download(self, ctx, url: str):
        # ... existing download logic ...

        # AI-powered analysis (behind feature flag)
        if self.bot.settings.enable_ai_features and self.bot.settings.enable_content_analysis:
            # Check rollout percentage
            import random
            if random.randint(1, 100) <= self.bot.settings.ai_rollout_percentage:
                try:
                    from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
                    analyzer = ContentAnalyzer()
                    analysis = await analyzer.analyze(url)
                    await ctx.send(f"Content analysis: {analysis.summary}")
                except Exception as e:
                    # Graceful fallback - don't break existing functionality
                    logger.warning(f"AI analysis failed, continuing with download: {e}")
```

#### **Environment-Specific Configurations**
```bash
# Production environment (.env.production)
ENABLE_AI_FEATURES=true
ENABLE_NEW_CLI=true
ENABLE_ENHANCED_MONITORING=true

# AI feature rollout (start conservative)
ENABLE_CONTENT_ANALYSIS=true
ENABLE_SUMMARIZATION=false  # Not ready yet
ENABLE_MODERATION=true
AI_ROLLOUT_PERCENTAGE=10  # Start with 10% of users

# VCR for production testing
VCR_RECORD_MODE=none  # Never record in production
AI_TESTING_MODE=live  # Use real APIs in production

# Staging environment (.env.staging)
ENABLE_AI_FEATURES=true
ENABLE_NEW_CLI=true
ENABLE_ENHANCED_MONITORING=true

# More aggressive rollout in staging
AI_ROLLOUT_PERCENTAGE=50
VCR_RECORD_MODE=none
AI_TESTING_MODE=live

# Development environment (.env.development)
ENABLE_AI_FEATURES=true
ENABLE_NEW_CLI=true
ENABLE_ENHANCED_MONITORING=true

# Full features in development
AI_ROLLOUT_PERCENTAGE=100
VCR_RECORD_MODE=once  # Record new cassettes
AI_TESTING_MODE=vcr   # Use VCR for development
```

### Health Checks During Migration

#### **Migration-Aware Health Checks**
```python
# src/boss_bot/monitoring/health/migration_health.py
from typing import Dict, Any
from boss_bot.core.env import BossSettings

class MigrationHealthChecker:
    """Health checks specific to migration status."""

    def __init__(self, settings: BossSettings):
        self.settings = settings

    async def check_migration_status(self) -> Dict[str, Any]:
        """Check migration-specific health indicators."""
        checks = {}

        # Check import paths work
        checks["legacy_imports"] = await self._check_legacy_imports()
        checks["new_imports"] = await self._check_new_imports()

        # Check feature flags
        checks["feature_flags"] = self._check_feature_flags()

        # Check AI components (if enabled)
        if self.settings.enable_ai_features:
            checks["ai_components"] = await self._check_ai_health()

        # Check CLI availability
        checks["cli_health"] = await self._check_cli_health()

        return {
            "migration_status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks,
            "migration_phase": self._detect_migration_phase()
        }

    def _detect_migration_phase(self) -> str:
        """Detect which migration phase we're in."""
        try:
            # Check for new structure
            import boss_bot.ai.agents
            if self.settings.enable_ai_features:
                return "phase_3_ai_integration"
            return "phase_2_cli_expansion"
        except ImportError:
            try:
                import boss_bot.cli.main
                return "phase_2_cli_expansion"
            except ImportError:
                return "phase_1_foundation"

# Health check endpoint
@app.get("/health/migration")
async def migration_health_endpoint():
    checker = MigrationHealthChecker(settings)
    return await checker.check_migration_status()
```

#### **Automated Health Monitoring**
```bash
# Production health check script
#!/bin/bash
# scripts/production_health_check.sh

set -e

echo "Checking production health during migration..."

# Basic connectivity
curl -f http://localhost:8080/health || exit 1

# Migration-specific health
curl -f http://localhost:8080/health/migration || exit 1

# Discord bot responsiveness
timeout 30s uv run python -c "
import asyncio
from boss_bot.bot.client import BossBot

async def test_bot():
    bot = BossBot()
    # Test basic bot functionality
    print('Bot health check passed')

asyncio.run(test_bot())
" || exit 1

# CLI responsiveness
timeout 10s bossctl --version || exit 1

echo "✅ Production health check passed"
```

### Release Management and Rollback

#### **Commitizen-Based Release Workflow**

The project uses Commitizen for automated release management with conventional commits. Migration releases follow the same pattern but with migration-specific documentation.

##### **Step 1: Prepare Release (using existing script)**
```bash
# Use the existing cz-prepare-release.sh script
# This script handles version determination, branch creation, and PR creation
./scripts/ci/cz-prepare-release.sh

# For migration phases, you can use prerelease versions:
PRERELEASE_PHASE=beta ./scripts/ci/cz-prepare-release.sh
```

**What `cz-prepare-release.sh` does for migration:**
- ✅ Checks for uncommitted changes (stashes them safely)
- ✅ Determines next version from conventional commits
- ✅ Creates release branch (`task/prepare-release-{VERSION}`)
- ✅ Bumps version in all configured files
- ✅ Runs pre-commit hooks to ensure quality
- ✅ Creates pull request with release label
- ✅ Handles prerelease phases (alpha, beta, rc) for migration testing

##### **Step 2: Create GitHub Release (using existing script)**
```bash
# After the release PR is merged, create the GitHub release
./scripts/ci/cz-release.sh
```

**What `cz-release.sh` does:**
- ✅ Verifies GitHub CLI authentication
- ✅ Determines current version from Commitizen
- ✅ Pushes tags to remote
- ✅ Creates GitHub release with auto-generated notes
- ✅ Uses semantic versioning for proper release management

##### **Migration-Specific Release Process**
```bash
# Complete migration release workflow
#!/bin/bash
# Enhanced workflow for migration phases

set -e

PHASE=$1  # e.g., "phase-3-ai", "phase-2-cli"
PRERELEASE_TYPE=${2:-""}  # optional: alpha, beta, rc

echo "===== MIGRATION RELEASE WORKFLOW ====="
echo "Phase: $PHASE"
echo "Prerelease type: ${PRERELEASE_TYPE:-"none (stable release)"}"

# Step 1: Prepare release using existing script
if [ -n "$PRERELEASE_TYPE" ]; then
    echo "-- Preparing prerelease version --"
    PRERELEASE_PHASE=$PRERELEASE_TYPE ./scripts/ci/cz-prepare-release.sh
else
    echo "-- Preparing stable release --"
    ./scripts/ci/cz-prepare-release.sh
fi

echo "\n🎯 Next steps:"
echo "1. Review and merge the release PR"
echo "2. Run: ./scripts/ci/cz-release.sh"
echo "3. Update release notes with migration phase details"
echo "4. Monitor deployment via GitHub Actions"

# Step 2: After PR merge, create release (manual step)
echo "\n📋 Post-merge commands:"
echo "./scripts/ci/cz-release.sh"
echo "gh release edit v\$(uv run cz version -p) --notes-file migration-release-notes.md"
```

##### **Migration Release Notes Template**
```markdown
# migration-release-notes.md
# Use this template to enhance auto-generated release notes

## 🚀 Migration Phase: [Phase Name]

### ✨ What's New in This Phase
- [List migration-specific improvements]
- [New AI capabilities, CLI enhancements, etc.]
- [Infrastructure improvements]

### 🎛️ Feature Flags Available
```bash
# Control AI features rollout
ENABLE_AI_FEATURES=true/false
AI_ROLLOUT_PERCENTAGE=0-100

# Control CLI features
ENABLE_NEW_CLI=true/false

# Control monitoring enhancements
ENABLE_ENHANCED_MONITORING=true/false
```

### 🧪 Testing
- All existing functionality preserved
- VCR cassettes updated for AI testing
- Migration validation scripts included

### 📦 Deployment
- Automatic deployment via GitHub Actions
- Feature flags allow gradual rollout
- Health checks monitor migration status

### 🔄 Rollback
If issues occur:
```bash
# Quick rollback via environment variables
echo "ENABLE_AI_FEATURES=false" >> .env.production
echo "AI_ROLLOUT_PERCENTAGE=0" >> .env.production

# Full rollback to previous release
./scripts/rollback-release.sh v[current] v[previous]
```

### 📞 Support
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Migration Guide: MIGRATION.md
```

#### **Rollback via Commitizen Workflow**

##### **Quick Feature Flag Rollback**
```bash
#!/bin/bash
# scripts/quick-rollback.sh - Immediate feature disable

set -e

echo "🚨 QUICK ROLLBACK - DISABLING FEATURES"
echo "Timestamp: $(date)"

# 1. Disable problematic features immediately
echo "Disabling AI features..."
echo "ENABLE_AI_FEATURES=false" >> .env.production
echo "AI_ROLLOUT_PERCENTAGE=0" >> .env.production
echo "ENABLE_NEW_CLI=false" >> .env.production

# 2. Restart application to pick up new environment
echo "Restarting application..."
# This depends on your deployment method
# systemctl restart boss-bot
# kubectl rollout restart deployment/boss-bot
# docker-compose restart

# 3. Verify features are disabled
sleep 10
curl -f http://localhost:8080/health/migration || {
    echo "CRITICAL: Health check failed after rollback!"
    exit 1
}

echo "✅ Quick rollback completed - AI features disabled"
echo "Application should be running with previous functionality only"
```

##### **Full Version Rollback with Commitizen**
```bash
#!/bin/bash
# scripts/rollback-release.sh - Full version rollback

set -e

CURRENT_VERSION=$1
ROLLBACK_VERSION=$2

if [ -z "$CURRENT_VERSION" ] || [ -z "$ROLLBACK_VERSION" ]; then
    echo "Usage: $0 <current-version> <rollback-version>"
    echo "Example: $0 v1.5.0 v1.4.2"
    exit 1
fi

echo "🚨 FULL ROLLBACK INITIATED"
echo "Rolling back from $CURRENT_VERSION to $ROLLBACK_VERSION"
echo "Timestamp: $(date)"

# 1. Quick feature disable first
echo "Step 1: Disabling features immediately..."
./scripts/quick-rollback.sh

# 2. Create rollback branch and prepare emergency release
echo "Step 2: Creating rollback branch..."
ROLLBACK_BRANCH="emergency/rollback-to-$ROLLBACK_VERSION"
git checkout -b "$ROLLBACK_BRANCH"

# 3. Reset to rollback version
echo "Step 3: Resetting to $ROLLBACK_VERSION..."
git reset --hard "$ROLLBACK_VERSION"

# 4. Create emergency release using existing scripts
echo "Step 4: Creating emergency release..."
EMERGENCY_VERSION="$ROLLBACK_VERSION-emergency-$(date +%Y%m%d-%H%M)"

# Manually set version for emergency release
echo "$EMERGENCY_VERSION" > .emergency-version

# Create emergency release
gh release create "$EMERGENCY_VERSION" \
    --target "$ROLLBACK_BRANCH" \
    --title "🚨 Emergency Rollback to $ROLLBACK_VERSION" \
    --notes "$(cat <<EOF
## 🚨 Emergency Rollback

**Rolled back from:** $CURRENT_VERSION
**Rolled back to:** $ROLLBACK_VERSION
**Reason:** Production issues detected

### Changes
- All migration features disabled
- Reverted to stable functionality
- Emergency deployment triggered

### Next Steps
1. Monitor application stability
2. Investigate root cause
3. Plan fix and re-deployment
EOF
)" \
    --prerelease

# 5. Verify rollback
echo "Step 5: Verifying rollback..."
sleep 30
curl -f http://localhost:8080/health || {
    echo "CRITICAL: Rollback verification failed!"
    exit 1
}

# 6. Alert team
echo "Step 6: Alerting team..."
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST $SLACK_WEBHOOK_URL -d '{
        "text": "🚨 Emergency rollback from '$CURRENT_VERSION' to '$ROLLBACK_VERSION' completed. Release: '$EMERGENCY_VERSION'"
    }'
fi

echo "✅ Full rollback completed successfully"
echo "Emergency release: $EMERGENCY_VERSION"
echo "\nNext steps:"
echo "1. Monitor logs for stability"
echo "2. Investigate issue that caused rollback"
echo "3. Fix issues in development"
echo "4. Test thoroughly before next migration attempt"
echo "5. Update migration documentation with lessons learned"
```

### Integration with Existing Release Process

#### **Commitizen Integration for Migration Releases**

The migration leverages the existing Commitizen-based release process with migration-specific enhancements:

##### **Conventional Commits for Migration**
```bash
# Migration commits should follow conventional commit format
# to ensure proper version bumping

# Examples:
feat(ai): add content analysis agent for migration phase 3
feat(cli): implement modular CLI structure for migration phase 2
fix(migration): resolve import path conflicts in backward compatibility
chore(migration): update feature flags for gradual AI rollout

# Breaking changes (major version bump)
feat(core)!: restructure project layout for migration

# The existing cz-prepare-release.sh will automatically:
# - Determine version bump based on these commits
# - Generate appropriate changelog
# - Create proper release branch and PR
```

##### **Release Labels and Tracking**
```bash
# The existing scripts automatically handle:

# 1. Release label creation (via cz-prepare-release.sh)
gh label create release --description "Label for marking official releases" --color 28a745

# 2. PR creation with proper labels
gh pr create --label "release" --label "migration" \
    --title "Prepare for release of v1.4.0 to v1.5.0" \
    --body "Migration phase 3: AI integration release"

# 3. Automatic release creation (via cz-release.sh)
gh release create "v1.5.0" --generate-notes
```

##### **Migration Release Communication**
```bash
# Enhanced release notes for migration phases
#!/bin/bash
# scripts/enhance-migration-release.sh

VERSION=$(uv run cz version -p)
PHASE=$1  # e.g., "phase-3-ai"

if [ -z "$PHASE" ]; then
    echo "Usage: $0 <migration-phase>"
    echo "Example: $0 phase-3-ai"
    exit 1
fi

# After release creation, enhance with migration details
gh release edit "v$VERSION" --notes-file <(cat <<EOF
$(gh release view "v$VERSION" --json body -q .body)

---

## 🔄 Migration Information

**Migration Phase:** $PHASE
**Previous Version:** $(git describe --tags --abbrev=0 HEAD^)
**Migration Guide:** [MIGRATION.md](MIGRATION.md)

### 🎛️ Feature Flags
\`\`\`bash
# Gradual rollout controls
ENABLE_AI_FEATURES=true
AI_ROLLOUT_PERCENTAGE=10  # Start with 10%
ENABLE_ENHANCED_MONITORING=true
\`\`\`

### 🚨 Rollback Commands
\`\`\`bash
# Quick feature disable
./scripts/quick-rollback.sh

# Full version rollback
./scripts/rollback-release.sh v$VERSION v$(git describe --tags --abbrev=0 HEAD^)
\`\`\`

### 📋 Post-Release Checklist
- [ ] Monitor health checks for 24 hours
- [ ] Gradually increase AI_ROLLOUT_PERCENTAGE
- [ ] Update documentation
- [ ] Plan next migration phase
EOF
)

echo "✅ Enhanced release v$VERSION with migration details"
```

##### **Complete Migration Release Workflow**
```bash
# Complete workflow combining existing scripts with migration enhancements
#!/bin/bash
# scripts/migration-release-workflow.sh

set -e

PHASE=$1
PRERELEASE_TYPE=${2:-""}

if [ -z "$PHASE" ]; then
    echo "Usage: $0 <phase> [prerelease-type]"
    echo "Example: $0 phase-3-ai beta"
    exit 1
fi

echo "===== MIGRATION RELEASE WORKFLOW ====="
echo "Phase: $PHASE"
echo "Prerelease: ${PRERELEASE_TYPE:-"none"}"

# Step 1: Prepare release using existing Commitizen workflow
echo "\n🔄 Step 1: Preparing release..."
if [ -n "$PRERELEASE_TYPE" ]; then
    PRERELEASE_PHASE=$PRERELEASE_TYPE ./scripts/ci/cz-prepare-release.sh
else
    ./scripts/ci/cz-prepare-release.sh
fi

echo "\n✅ Release preparation complete!"
echo "\n📋 Next steps:"
echo "1. Review the release PR created by cz-prepare-release.sh"
echo "2. Merge the PR when ready"
echo "3. Run: ./scripts/ci/cz-release.sh"
echo "4. Run: ./scripts/enhance-migration-release.sh $PHASE"
echo "5. Monitor deployment and health checks"

echo "\n🔗 PR URL: Check GitHub for the release PR"
echo "🔗 Release process: Uses existing Commitizen workflow"
echo "🔗 Migration guide: MIGRATION.md"
```

This approach maintains consistency with the existing release process while adding migration-specific enhancements.

## Success Metrics

- All existing functionality preserved
- Test coverage maintained or improved
- CLI usability significantly enhanced
- AI capabilities successfully integrated
- Performance maintained or improved
- Code maintainability significantly improved
- Documentation completeness: 100%
