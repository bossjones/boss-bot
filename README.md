# Boss-Bot

A powerful Discord bot for media downloads and RAG (Retrieval-Augmented Generation) capabilities. Built with security, monitoring, and scalability in mind.

## Features

- Media download capabilities
- RAG-based interactions
- Secure file handling and validation
- Comprehensive monitoring and metrics
- Rate limiting and quota management
- Modern async architecture

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

5. Start the bot:
   ```bash
   uv run python -m boss_bot
   ```

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
│   ├── bot/            # Core bot functionality
│   ├── commands/       # Bot commands
│   ├── core/          # Core utilities
│   ├── downloaders/   # Media download handlers
│   ├── monitoring/    # Logging and metrics
│   ├── schemas/       # Data models
│   ├── storage/       # File storage management
│   └── utils/         # Utility functions
├── tests/             # Test suite
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

## Testing

- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest tests/path/to/test.py`
- Generate coverage: `uv run pytest --cov=boss_bot`

## Documentation

- Build docs: `uv run mkdocs build`
- Serve docs locally: `uv run mkdocs serve`
- View at: http://localhost:8000

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Monitoring

The bot includes comprehensive monitoring:
- Logging via Loguru
- Metrics via Prometheus
- Health checks
- Performance profiling

## Security

- File validation and sanitization
- Rate limiting
- Secure environment variable handling
- Regular dependency updates
- Automated security scanning

## License

[MIT License](LICENSE)
