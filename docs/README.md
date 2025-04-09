# Boss-Bot

A powerful Discord bot with advanced AI capabilities and comprehensive development tooling.

## Overview

Boss-Bot is a sophisticated Discord bot that leverages cutting-edge AI models and provides robust development tools. Built with modern Python practices, it combines Discord.py with LangChain, various AI models, and extensive monitoring capabilities.

## Key Features

- **Advanced AI Integration**
  - LangChain integration with multiple providers (Anthropic, OpenAI, Google, Groq)
  - LangGraph for complex AI workflows
  - Embeddings and vector search capabilities
  - Structured AI outputs with advanced prompting

- **Discord Bot Capabilities**
  - Modern Discord.py implementation
  - Comprehensive command system
  - File and media handling
  - Customizable bot behaviors

- **Development Tools**
  - UV package management for deterministic builds
  - Comprehensive testing suite with pytest
  - Advanced monitoring and logging
  - Docker containerization
  - VSCode devcontainer support

- **Documentation and Quality**
  - MkDocs-based documentation
  - Extensive type checking with pyright
  - Code quality tools (ruff, pre-commit)
  - Continuous Integration/Deployment

## Quick Start

```bash
# Clone the repository
git clone https://github.com/bossjones/boss-bot.git
cd boss-bot

# Set up environment variables
cp .env.sample .env
# Edit .env with your configuration

# Install dependencies using UV
uv sync

# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Start the bot
uv run python -m boss_bot
```

## Project Structure

```
boss-bot/
├── src/boss_bot/          # Main bot package
│   ├── bot/              # Core bot functionality
│   ├── commands/         # Bot commands
│   ├── core/            # Core utilities
│   ├── monitoring/      # Monitoring tools
│   └── utils/           # Helper utilities
├── tests/               # Test suite
├── docs/               # Documentation
└── .cursor/rules/      # Cursor IDE automation rules
```

## Development

### Prerequisites

- Python 3.11+
- Discord Bot Token
- AI API Keys (Anthropic, OpenAI, etc.)
- Docker (optional)

### Local Development

1. Set up your development environment:
   ```bash
   # Install dev dependencies
   uv sync --dev

   # Install pre-commit hooks
   pre-commit install
   ```

2. Run tests:
   ```bash
   uv run pytest
   ```

3. Build documentation:
   ```bash
   uv run mkdocs serve
   ```

### Using Docker

```bash
# Build the container
docker compose build

# Run the bot
docker compose up
```****

## Documentation

### Local Development Documentation

1. Serve documentation with live reload:
   ```bash
   # Using mkdocs (recommended)
   uv run mkdocs serve

   # Using pdoc (API documentation)
   uv run pdoc --docformat=google --port=8088 src/boss_bot
   ```

2. Build documentation:
   ```bash
   # Using mkdocs
   uv run mkdocs build

   # Using pdoc
   uv run pdoc --docformat=google --output-directory=gh-docs src/boss_bot
   ```

3. Deploy to GitHub Pages:
   ```bash
   uv run mkdocs gh-deploy --force --message 'docs(mkdocs): update documentation [skip ci]'
   ```

- Visit the [full documentation](https://bossjones.github.io/boss-bot) for detailed guides
- Check [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines
- See [CHANGELOG.md](../../CHANGELOG.md) for version history

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
