# Project Structure

This memory file contains the complete project structure documentation for Boss-Bot.

**When to include this context:**
- When creating new modules or features
- When understanding where to place new code
- When discussing architectural decisions
- When planning refactoring or reorganization
- When documenting new components

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
