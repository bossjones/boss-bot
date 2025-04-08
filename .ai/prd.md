# Title: PRD for Boss-Bot: A Discord Media Download and RAG Assistant

<version>1.0.0</version>

## Status: Draft

## Intro

Boss-Bot is a Discord bot designed to enhance server productivity by providing robust media download capabilities and future RAG (Retrieval-Augmented Generation) features. The initial MVP focuses on reliable media downloading from popular platforms like Twitter and Reddit, with a strong foundation for future AI-powered features. The bot emphasizes test-driven development, clean code practices, and modular design to ensure maintainability and extensibility.

## Goals

- Create a reliable and efficient Discord bot for media downloads with >99% uptime
- Implement comprehensive test coverage (>90%) using pytest and dpytest
- Ensure all modules follow clean code practices and stay under 120 lines
- Build a foundation for future RAG capabilities
- Provide clear progress tracking and queue management for downloads
- Maintain clear documentation and type hints for junior developer onboarding

## Features and Requirements

### Functional Requirements
- Discord bot integration using discord.py
- Media download commands ($dlt, $dlr) with progress tracking
- Queue management system for multiple download requests
- Temporary file storage and cleanup mechanism
- Error handling and user feedback system
- Command help and documentation

### Non-functional Requirements
- Response time <2s for command acknowledgment
- Download queue processing time <5min per item
- Maximum module size of 120 lines
- Type hints for all functions and classes
- Comprehensive docstrings following Google style
- Test coverage >90% (measured with coverage[toml])
- Adherence to DRY (Don't Repeat Yourself) and YAGNI (You Aren't Gonna Need It) principles
- Performance testing requirements:
  * Load testing for concurrent downloads (minimum 10 simultaneous)
  * Memory usage monitoring (max 500MB under load)
  * CPU usage monitoring (max 50% under load)
  * Network bandwidth monitoring and throttling capabilities
- Code quality requirements:
  * All code must pass ruff linting and formatting
  * Zero tolerance for unhandled exceptions
  * Comprehensive error handling with better-exceptions
  * All HTTP interactions must be tested with respx mocking
  * Flaky tests must be identified and managed with pytest-ignore-flaky
  * Critical tests must use pytest-retry for reliability

### User Experience Requirements
- Clear progress indicators for downloads
- Intuitive command syntax
- Helpful error messages
- Command usage examples
- Queue status visibility

### Integration Requirements
- Discord API integration
- Twitter API integration via gallery_dl
- Reddit API integration via gallery_dl
- File system management
- Future: Vector store integration

## Epic List

### Epic-1: Core Bot Infrastructure
- Discord bot setup and configuration
- Command handling framework
- Error handling and logging
- Testing infrastructure

### Epic-2: Media Download System
- Download queue implementation
- Progress tracking
- File management
- Platform-specific downloaders

### Epic-3: Future RAG Enhancement (Beyond Current PRD)
- LangChain and LangGraph integration
- Redis vector store setup
- Extended command set
- CLI interface

## Epic 1: Story List

- Story 1: Bot Infrastructure Setup
  Status: ''
  Requirements:
  - Initialize Python project with uv
  - Set up Discord bot with basic command handling
  - Implement logging system with loguru and better-exceptions
  - Create test infrastructure with pytest and all testing dependencies
  - Set up performance monitoring
  - Configure ruff for linting and formatting
  - Set up tox-uv for test automation

- Story 2: Download Queue System
  Status: ''
  Requirements:
  - Implement download queue manager
  - Create progress tracking system
  - Set up temporary file storage
  - Add queue status commands

## Technology Stack

| Technology | Description |
|------------|-------------|
| Python 3.12 | Primary development language |
| uv | Package management and dependency resolution |
| discord.py | Discord bot framework |
| pytest | Testing framework with powerful fixture support and assertion introspection |
| dpytest | Discord.py testing utilities |
| gallery-dl | Reddit, instagram, twitter, other social media media download utility |
| yt-dlp | youtube/video download utility |
| httpx | Fully featured HTTP client for Python 3, with sync and async APIs, and HTTP/1.1 and HTTP/2 support |
| pydantic | Data validation |
| pydantic-settings | Configuration management |
| loguru | Logging utility |
| aiofiles | Asynchronous file I/O operations using asyncio |
| better-exceptions | Enhanced exception handling with more informative error messages |

### Testing Dependencies
| Technology | Description |
|------------|-------------|
| pytest-mock | Thin-wrapper around the unittest.mock package for easier mock creation |
| respx | Modern, elegant HTTP mocking for Python tests |
| pytest-recording | Record and replay test interactions for reliable testing |
| pytest-retry | Retry flaky tests to improve reliability |
| pytest-skip-slow | Skip slow tests for faster development cycles |
| pytest-ignore-flaky | Manage and track flaky tests separately |
| tox-uv | Tox plugin for UV package manager integration |
| ruff | Fast Python linter and code formatter written in Rust |
| coverage[toml] | Code coverage measurement with TOML configuration support |

### Future Dependencies
| Technology | Description |
|------------|-------------|
| LangChain | RAG framework |
| LangGraph | RAG workflow management |
| OpenAI | Embeddings and LLM via LangChain |
| Redis | Vector store |
| Typer | CLI interface |

## Project Structure

```text
boss-bot/
├── src/
│   ├── boss_bot/
│   │   ├── bot/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Discord client setup
│   │   │   ├── events.py          # Event handlers
│   │   │   └── cogs/             # Discord cogs directory
│   │   │       ├── __init__.py
│   │   │       ├── download_cog.py    # Media download commands
│   │   │       ├── queue_cog.py       # Queue management commands
│   │   │       ├── rag_cog.py         # RAG-related commands
│   │   │       └── admin_cog.py       # Admin/utility commands
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   ├── app.py            # Typer CLI application
│   │   │   └── commands/         # CLI command modules
│   │   ├── commands/             # Shared command logic
│   │   │   ├── __init__.py
│   │   │   ├── download.py       # Download command business logic
│   │   │   ├── queue.py          # Queue management logic
│   │   │   └── rag.py           # RAG-related logic
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Configuration management
│   │   │   ├── queue.py         # Queue implementation
│   │   │   └── storage.py       # File storage management
│   │   ├── downloaders/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base downloader class
│   │   │   ├── twitter.py       # Twitter downloader
│   │   │   └── reddit.py        # Reddit downloader
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── chains/         # LangChain components
│   │   │   ├── graphs/         # LangGraph workflows
│   │   │   ├── embeddings.py   # Embedding configurations
│   │   │   └── models.py       # LLM configurations
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── indexer.py      # Document indexing
│   │   │   ├── retriever.py    # Vector store retrieval
│   │   │   └── store.py        # Redis vector store management
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── download.py     # Download-related models
│   │   │   ├── queue.py        # Queue-related models
│   │   │   └── rag.py          # RAG-related models
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logging.py      # Logging configuration
│   │       └── metrics.py      # Performance monitoring
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_bot/
│   ├── test_cli/
│   ├── test_commands/
│   ├── test_downloaders/
│   ├── test_llm/
│   └── test_rag/
├── docs/                       # Documentation directory
├── scripts/                    # Utility scripts
├── .devcontainer/             # Development container config
├── pyproject.toml
└── README.md
```

## Data Models

### Download Item Schema
```
