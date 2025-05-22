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
│   │   └── config.py          # Configuration commands
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
│       ├── config.py          # Logging setup (from current monitoring/logging.py)
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
│   │   └── client.py
│   ├── anthropic/              # Anthropic API integration
│   │   ├── __init__.py
│   │   └── client.py
│   ├── openai/                 # OpenAI API integration
│   │   ├── __init__.py
│   │   └── client.py
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

### ✅ **Naming Patterns**
- **Service-specific**: `{service}_{purpose}.py` (e.g., `discord_integration.py`)
- **Handler pattern**: `{protocol}_handler.py` (e.g., `youtube_handler.py`)
- **Backend pattern**: `{type}_storage.py` (e.g., `local_storage.py`)
- **Health checks**: `{component}_health.py` (e.g., `discord_health.py`)
- **Purpose suffix**: `{name}_{purpose}.py` (e.g., `discord_webhook.py`)

### 📋 **Module Conflict Checklist**
Before creating new modules, check against:
- Python standard library modules
- Third-party dependencies (discord.py, langchain, etc.)
- Common package names (boto3, azure, etc.)

## Migration Plan

### Phase 1: Foundation Reorganization (Week 1-2)

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
mv src/boss_bot/monitoring/logging.py src/boss_bot/monitoring/logging/config.py
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

### Phase 2: CLI Expansion (Week 3)

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
- `cli/commands/bot.py` - Bot management (start, stop, status, restart)
- `cli/commands/queue.py` - Queue operations (list, clear, pause, resume)
- `cli/commands/download.py` - Download management (start, cancel, status)
- `cli/commands/config.py` - Configuration management (show, set, validate)
- `cli/commands/ai.py` - AI workflow commands (analyze, summarize, classify)

#### Step 2.3: CLI Utilities
- `cli/utils/formatters.py` - Rich console formatting
- `cli/utils/validators.py` - Input validation
- `cli/config/settings.py` - CLI-specific configuration

### Phase 3: AI Integration Foundation (Week 4-5)

#### Step 3.1: LangChain/LangGraph Setup
- `ai/agents/content_analyzer.py` - Media content analysis workflows
- `ai/chains/summarization.py` - Content summarization chains
- `ai/tools/media_tools.py` - Media analysis tools
- `ai/prompts/templates.py` - Prompt templates

#### Step 3.2: AI Service Integrations
- `integrations/langsmith/client.py` - LangSmith tracking
- `integrations/anthropic/client.py` - Claude API integration
- `integrations/openai/client.py` - OpenAI API integration

#### Step 3.3: AI-Powered Discord Commands
- `bot/cogs/ai_commands.py` - AI-powered Discord commands
- Integration with existing download and queue systems

### Phase 4: Enhanced Monitoring & Storage (Week 6)

#### Step 4.1: Monitoring Improvements
- Reorganize health checks into dedicated modules
- Add AI service health monitoring
- Implement structured logging with formatters
- Add Prometheus metrics exporter

#### Step 4.2: Storage Backend Abstraction
- `storage/backends/local_storage.py` - Local filesystem backend
- `storage/models/file_models.py` - File metadata models
- Prepare for future cloud storage backends (S3, Azure)

### Phase 5: API Layer Foundation (Week 7-8)

#### Step 5.1: REST API Structure
- `api/routes/downloads.py` - Download management endpoints
- `api/routes/queue.py` - Queue management endpoints
- `api/middleware/auth.py` - Authentication middleware
- `api/middleware/rate_limit.py` - Rate limiting

#### Step 5.2: API Documentation & Testing
- OpenAPI/Swagger documentation
- API integration tests
- Authentication and authorization

### Phase 6: Gradual Import Migration (Week 9-10)

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

### Phase 7: Deprecation Cleanup (Week 11-12)

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

### Phase 1: Foundation
- [ ] Create new directory structure
- [ ] Move core components to new locations
- [ ] Update import statements throughout codebase
- [ ] Update tests for new import paths
- [ ] Remove duplicate and empty modules
- [ ] Verify all tests still pass
- [ ] Update documentation

### Phase 2: CLI Expansion
- [ ] Refactor monolithic CLI to modular structure
- [ ] Implement bot management subcommands
- [ ] Implement queue management subcommands
- [ ] Implement download management subcommands
- [ ] Implement configuration subcommands
- [ ] Add Rich formatting utilities
- [ ] Add input validation utilities
- [ ] Test all CLI functionality

### Phase 3: AI Integration
- [ ] Set up LangChain/LangGraph foundation
- [ ] Implement content analysis agents
- [ ] Create summarization chains
- [ ] Develop media analysis tools
- [ ] Set up prompt template system
- [ ] Integrate AI service clients (LangSmith, Anthropic, OpenAI)
- [ ] Create AI-powered Discord commands
- [ ] Test AI functionality end-to-end

### Phase 4: Monitoring & Storage
- [ ] Reorganize health check system
- [ ] Implement AI service health monitoring
- [ ] Set up structured logging with formatters
- [ ] Add Prometheus metrics exporter
- [ ] Abstract storage backend system
- [ ] Implement file metadata models
- [ ] Test monitoring and storage improvements

### Phase 5: API Layer
- [ ] Implement REST API foundation
- [ ] Create download management endpoints
- [ ] Create queue management endpoints
- [ ] Set up authentication middleware
- [ ] Implement rate limiting
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Create API integration tests
- [ ] Test API functionality

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

### Testing Strategy
- Run full test suite after each migration step
- Add integration tests for new AI components
- Performance benchmarking to ensure no regression
- User acceptance testing for CLI changes

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

- **Week 1-2**: Phase 1 (Foundation Reorganization) - *Copy & create wrappers*
- **Week 3**: Phase 2 (CLI Expansion) - *Modular CLI with backward compatibility*
- **Week 4-5**: Phase 3 (AI Integration Foundation) - *LangChain/LangGraph setup*
- **Week 6**: Phase 4 (Enhanced Monitoring & Storage) - *Infrastructure improvements*
- **Week 7-8**: Phase 5 (API Layer Foundation) - *REST API groundwork*
- **Week 9-10**: Phase 6 (Gradual Import Migration) - *Update imports incrementally*
- **Week 11-12**: Phase 7 (Deprecation Cleanup) - *Remove old files after migration*

Total estimated time: **12 weeks** for complete migration with safe deprecation period.

### Deprecation Timeline
- **v1.5.0** (Week 8): All new structure available, deprecation warnings active
- **v1.6.0** (Week 10): Import migration complete, warnings remain
- **v1.9.0** (Week 12): Final warning before removal
- **v2.0.0** (Future): Remove deprecated paths entirely

## Success Metrics

- All existing functionality preserved
- Test coverage maintained or improved
- CLI usability significantly enhanced
- AI capabilities successfully integrated
- Performance maintained or improved
- Code maintainability significantly improved
- Documentation completeness: 100%
