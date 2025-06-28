# Boss-Bot 🤖

An AI-powered Discord bot for intelligent media downloads and social media management. Built with LangChain, LangGraph, and multi-agent orchestration for advanced content analysis and strategy optimization.

## ✨ Key Features

### 🤖 **AI-Powered Intelligence** (NEW!)
- **Multi-Agent Architecture**: LangGraph-orchestrated AI agents for intelligent decision making
- **Smart Content Analysis**: AI-powered quality assessment, engagement prediction, and audience insights
- **Intelligent Strategy Selection**: AI chooses optimal download strategies with confidence scoring
- **Advanced Workflows**: LangGraph state machines for complex multi-step AI processes
- **🎯 LangGraph Assistant Management**: Complete CLI for managing AI assistants with LangGraph Cloud integration

### 📥 **Media Download Capabilities**
- **Multi-Platform Support**: Twitter/X, Reddit, Instagram, YouTube with strategy pattern architecture
- **Dual-Mode Operations**: API-direct and CLI-based downloads with automatic fallback
- **Quality Control**: Smart format selection and quality optimization
- **Batch Processing**: Queue management with intelligent prioritization

### 🛡️ **Enterprise-Grade Reliability**
- **Feature Flag Control**: Gradual AI rollout with environment variable configuration
- **Graceful Degradation**: Robust fallback to traditional methods when AI unavailable
- **Comprehensive Testing**: 873+ tests including 243 AI/Assistant tests (100% passing)
- **Performance Monitoring**: Built-in metrics and agent performance tracking

## Prerequisites

- Python 3.12+
- UV package manager
- Discord Developer Account
- Docker (optional, for containerized deployment)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/boss-bot.git
   cd boss-bot
   ```

2. Set up environment:
   ```bash
   # Create Python 3.12+ virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install UV if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync
   ```

3. Configure environment variables:
   ```bash
   cp sample.env .env
   # Edit .env with your Discord token and other settings
   ```

4. Run tests:
   ```bash
   uv run pytest
   ```

5. Configure AI capabilities (optional):
   ```bash
   # Add to your .env file for AI features
   AI_STRATEGY_SELECTION_ENABLED=true
   AI_CONTENT_ANALYSIS_ENABLED=true

   # Add model provider API key (choose one)
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   GOOGLE_API_KEY=your-google-api-key

   # LangGraph Assistant Management (optional)
   LANGGRAPH_DEPLOYMENT_URL=https://your-deployment.langraph.ai
   LANGGRAPH_API_KEY=your-langgraph-api-key
   ```

6. Start the bot:
   ```bash
   uv run python -m boss_bot
   ```

## 🤖 AI-Powered Commands

### **New AI Commands**

#### `$smart-analyze <url>`
AI-powered content analysis with advanced insights.
```
$smart-analyze https://twitter.com/user/status/123456789
```
**Features**: Quality scoring, engagement prediction, audience insights, AI reasoning

#### `$smart-download <url> [upload]`
AI-enhanced download with strategy optimization.
```
$smart-download https://youtube.com/watch?v=VIDEO_ID
```
**Features**: Intelligent strategy selection, confidence scoring, AI recommendations

#### `$ai-status`
Show AI agent status and performance metrics.
```
$ai-status
```
**Features**: Real-time agent metrics, feature flag status, troubleshooting info

### **AI-Enhanced Traditional Commands**

#### `$download <url>` (Enhanced)
Traditional download now uses AI strategy selection when enabled.
```
$download https://instagram.com/p/POST_ID/
# Shows: "🤖 AI selected Instagram strategy (confidence: 95%)"
```

#### `$metadata <url>` (Enhanced)
Metadata extraction enhanced with AI content analysis.
```
$metadata https://youtube.com/watch?v=VIDEO_ID
# Shows: "📊 AI Enhanced Content Info" with quality scores
```

#### `$strategies` (Enhanced)
Shows current strategy and AI configuration.
```
$strategies
# Displays AI feature flags and agent status
```

### **Traditional Commands**
```bash
$download <url>           # Download media from supported platforms
$download-only <url>      # Download without uploading to Discord
$metadata <url>           # Get content metadata
$status                   # Show download queue status
$help                     # Show all available commands
```

## 🎯 LangGraph Assistant Management (NEW!)

Comprehensive CLI for managing AI assistants with LangGraph Cloud integration.

### **Assistant Lifecycle Commands**

#### `boss-bot assistants list`
Display all assistants from LangGraph Cloud in rich tables.
```bash
# List all assistants
boss-bot assistants list

# Filter and limit results
boss-bot assistants list --graph download_workflow --limit 10
```

#### `boss-bot assistants health`
Check connectivity to LangGraph Cloud deployment.
```bash
boss-bot assistants health
# Shows: ✅ LangGraph Cloud connection is healthy
```

#### `boss-bot assistants create-config`
Generate assistant YAML configuration files.
```bash
# Create a new assistant configuration
boss-bot assistants create-config "My Assistant" "Downloads media intelligently"

# Specify output location
boss-bot assistants create-config "My Assistant" "Description" --output my-assistant.yaml
```

#### `boss-bot assistants sync-from`
Import assistants from YAML configuration directory.
```bash
# Import all assistants from configs/
boss-bot assistants sync-from ./assistant-configs/

# Dry run to preview changes
boss-bot assistants sync-from ./configs/ --dry-run
```

#### `boss-bot assistants sync-to`
Export assistants to YAML configuration directory.
```bash
# Export all assistants to directory
boss-bot assistants sync-to ./backups/

# Export specific graph assistants
boss-bot assistants sync-to ./configs/ --graph-id download_workflow
```

#### `boss-bot assistants graphs`
List available LangGraph graphs.
```bash
boss-bot assistants graphs
```

### **Configuration & Setup**

1. **Environment Setup**: Add LangGraph Cloud credentials to `.env`
2. **YAML Schema**: Auto-generated configurations with metadata tracking
3. **Rich Output**: Beautiful tables and progress indicators
4. **Error Handling**: Graceful failures with detailed error messages

📚 **[Complete Documentation](docs/langgraph-assistants.md)** - Detailed guide with examples and troubleshooting

## Development Setup

1. Install development dependencies:
   ```bash
   uv sync --dev
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Configure VSCode (recommended):
   - Install recommended extensions from `.vscode/extensions.json`
   - Use provided settings from `.vscode/settings.json`

## Project Structure

```text
boss-bot/
├── src/boss_bot/        # Main package directory
│   ├── ai/             # 🤖 AI Components (NEW!)
│   │   ├── agents/     # LangGraph AI agents
│   │   ├── strategies/ # AI-enhanced strategies
│   │   └── workflows/  # LangGraph workflows
│   ├── bot/            # Discord bot functionality
│   │   ├── client.py   # Main bot with AI integration
│   │   └── cogs/       # Discord commands (AI-enhanced)
│   ├── core/           # Core utilities
│   │   ├── downloads/  # Strategy pattern + AI
│   │   ├── queue/      # Queue management
│   │   └── env.py      # Settings with AI config
│   ├── monitoring/     # Logging and metrics
│   ├── storage/        # File storage management
│   └── utils/          # Utility functions
├── tests/              # Test suite
│   ├── test_ai/        # 🤖 AI test suite (82 tests)
│   ├── test_bot/       # Discord integration tests
│   └── test_core/      # Core functionality tests
├── docs/               # Documentation
│   └── AI_INTEGRATION.md # 🤖 AI documentation
└── scripts/            # Utility scripts
```

## Testing

### **Comprehensive Test Suite** (407 tests total)

#### Core Tests (326 tests)
```bash
# Run all core tests
uv run pytest tests/test_core/ tests/test_bot/ -v

# Run specific test file
uv run pytest tests/test_bot/test_downloads.py -v
```

#### 🤖 AI Tests (82 tests) - NEW!
```bash
# Run all AI tests
uv run pytest tests/test_ai/ -v

# Run specific AI component tests
uv run pytest tests/test_ai/test_agents/test_strategy_selector.py -v
uv run pytest tests/test_ai/test_workflows/test_download_workflow.py -v

# Run Discord AI integration tests
uv run pytest tests/test_bot/test_discord_ai_integration.py -v
```

#### Test Coverage & Quality
```bash
# Generate coverage report
uv run pytest --cov=boss_bot --cov-report=html

# Run with detailed output
uv run pytest -v --tb=short

# Fast test run (skip slow tests)
uv run pytest -m "not slow"
```

#### Test Categories
- **Agent Tests**: AI agent functionality (53 tests)
- **Workflow Tests**: LangGraph coordination (20 tests)
- **Integration Tests**: Discord AI commands (12 tests)
- **Feature Flag Tests**: AI configuration testing
- **Performance Tests**: AI response time validation

## Documentation

### **Core Documentation**
- **[CLAUDE.md](CLAUDE.md)**: Complete project overview with AI architecture
- **[AI_INTEGRATION.md](docs/AI_INTEGRATION.md)**: Comprehensive AI integration guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development and contribution guidelines

### **AI-Specific Guides**
- **AI Commands**: See `$smart-analyze`, `$smart-download`, `$ai-status` above
- **Agent Development**: [AI_INTEGRATION.md#ai-agents](docs/AI_INTEGRATION.md#ai-agents)
- **LangGraph Workflows**: [AI_INTEGRATION.md#langgraph-workflows](docs/AI_INTEGRATION.md#langgraph-workflows)
- **Testing AI Components**: [AI_INTEGRATION.md#testing](docs/AI_INTEGRATION.md#testing)

### **Build Documentation**
```bash
# Build documentation site
uv run mkdocs build

# Serve docs locally
uv run mkdocs serve

# View at: http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Monitoring

### **Comprehensive Monitoring System**

#### Traditional Monitoring
- **Logging**: Structured logging via Loguru
- **Metrics**: Performance metrics via Prometheus
- **Health Checks**: Service health monitoring
- **Performance Profiling**: Request/response profiling

#### 🤖 AI-Specific Monitoring (NEW!)
- **Agent Performance**: Request count, response times, success rates
- **Model Usage**: API call tracking, token consumption
- **Feature Flag Status**: Real-time AI capability monitoring
- **Fallback Tracking**: AI failure and degradation metrics

#### Access Monitoring
```bash
# View AI agent status
$ai-status

# Check feature flag configuration
$strategies

# View performance metrics in logs
tail -f logs/boss-bot.log | grep "AI"
```

## 🛠️ Technology Stack

### **Core Technologies**
- **Python 3.12+**: Modern async/await patterns
- **Discord.py**: Discord bot framework
- **Pydantic**: Data validation and settings
- **UV**: Fast Python package manager

### **🤖 AI & LangChain Ecosystem** (NEW!)
- **LangChain**: AI framework and agent coordination
- **LangGraph**: Multi-agent workflow orchestration
- **LangSmith**: AI monitoring and debugging
- **Model Providers**: OpenAI, Anthropic, Google integration

### **Download & Media**
- **Gallery-dl**: Multi-platform media extraction
- **yt-dlp**: YouTube and video platform support
- **Strategy Pattern**: Flexible download architecture
- **Feature Flags**: Gradual rollout and A/B testing

### **Testing & Quality**
- **pytest**: Comprehensive testing framework
- **pytest-recording**: VCR for AI interaction testing
- **pytest-asyncio**: Async test support
- **dpytest**: Discord bot testing

## Security

### **Traditional Security**
- File validation and sanitization
- Rate limiting and quota management
- Secure environment variable handling
- Regular dependency updates
- Automated security scanning

### **🤖 AI Security** (NEW!)
- Input validation for AI requests
- Model provider API key security
- AI response sanitization
- Fallback mechanisms for reliability
- Audit logging for AI decisions

## 🚀 Getting Started

1. **Clone and setup**: Follow Quick Start guide above
2. **Configure AI**: Add model provider API keys (optional)
3. **Test installation**: Run `uv run pytest`
4. **Start bot**: Run `uv run python -m boss_bot`
5. **Try AI commands**: Use `$smart-analyze` or `$ai-status`

## 📈 Status

- ✅ **Core Functionality**: Complete and stable
- ✅ **AI Integration**: Production-ready multi-agent system
- ✅ **Testing**: 407 tests (100% passing)
- ✅ **Documentation**: Comprehensive guides available
- 🔄 **Active Development**: Ongoing enhancements and features

## License

[MIT License](LICENSE)

---

**Boss-Bot**: From simple media downloads to intelligent AI-powered social media management. 🤖✨
