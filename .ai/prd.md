# Title: PRD for Boss-Bot: A Discord Media Download and RAG Assistant

<version>1.0.0</version>

## Status: Draft

## Intro

Boss-Bot is a Discord bot designed to enhance server productivity by providing robust media download capabilities and future RAG (Retrieval-Augmented Generation) features. The initial MVP focuses on reliable media downloads from popular platforms like Twitter and Reddit, with a strong foundation for future AI-powered features. The bot emphasizes test-driven development, clean code practices, and modular design to ensure maintainability and extensibility.

## Goals

- Create a reliable and efficient Discord bot for media downloads with >99% uptime
- Implement comprehensive test coverage (>90%) using pytest and dpytest
- Ensure all modules follow clean code practices and stay under 120 lines
- Build a foundation for future RAG capabilities
- Provide clear progress tracking and queue management for downloads
- Maintain clear documentation and type hints for junior developer onboarding

<requirements>
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
</requirements>

<epic_list>
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
</epic_list>

<epic_1_stories>
## Epic 1: Story List

- Story 1: Project Initialization and Environment Setup
  Status: ''
  Requirements:
  - Initialize Python project with uv
  - Create project structure following the defined layout
  - Set up pyproject.toml with initial dependencies
  - Configure ruff for linting and formatting
  - Create initial README.md with setup instructions
  - Set up pre-commit hooks for code quality
  Acceptance Criteria:
  - Project can be cloned and installed with uv
  - Ruff runs successfully on empty project
  - README contains clear setup steps
  Dependencies: None

- Story 2: Test Infrastructure Setup
  Status: ''
  Requirements:
  - Set up pytest with all testing dependencies
  - Create basic test configuration in conftest.py
  - Set up coverage reporting with coverage[toml]
  - Configure tox-uv for test automation
  - Create test helper utilities and fixtures
  - Add example tests to validate setup
  Acceptance Criteria:
  - All test dependencies installed and configured
  - Example tests run successfully
  - Coverage reports generate correctly
  Dependencies: Story 1

- Story 3: Logging and Monitoring Setup
  Status: ''
  Requirements:
  - Implement logging system with loguru
  - Configure better-exceptions for error handling
  - Set up basic performance monitoring
  - Create logging configuration file
  - Add log rotation and management
  Acceptance Criteria:
  - Logs are properly formatted and stored
  - Better-exceptions shows detailed error traces
  - Basic metrics are collected
  Dependencies: Story 1

- Story 4: Basic Discord Bot Setup
  Status: ''
  Requirements:
  - Create Discord application and bot user
  - Implement basic bot client with required intents
  - Set up environment configuration with pydantic-settings
  - Create connection and basic event handling
  - Add health check command
  Acceptance Criteria:
  - Bot successfully connects to Discord
  - Basic events (ready, disconnect) are handled
  - Health check command responds
  Dependencies: Story 1, Story 3

- Story 5: Command Framework Implementation
  Status: ''
  Requirements:
  - Set up command handling framework using discord.py cogs
  - Implement basic command error handling
  - Create help command override
  - Add command registration system
  - Create command testing utilities
  Acceptance Criteria:
  - Commands can be registered and respond
  - Error handling works for basic cases
  - Help command shows available commands
  - Command tests pass
  Dependencies: Story 2, Story 4

- Story 6: Event System Implementation
  Status: ''
  Requirements:
  - Implement core event handlers
  - Add event logging and monitoring
  - Create event testing framework
  - Implement reconnection handling
  - Add event error recovery
  Acceptance Criteria:
  - All core events are handled and logged
  - Event tests pass
  - Bot recovers from disconnections
  Dependencies: Story 4, Story 5

- Story 7: Queue System Foundation
  Status: ''
  Requirements:
  - Design queue data structures
  - Implement basic queue manager
  - Add queue persistence
  - Create queue status command
  - Implement queue tests
  Acceptance Criteria:
  - Queue can add and remove items
  - Queue state persists across restarts
  - Queue status is queryable
  - Queue tests pass
  Dependencies: Story 5, Story 6

Each story includes clear dependencies, making it easier for junior developers to understand the progression. Stories are broken down into smaller, manageable tasks with clear acceptance criteria. 🏗️
</epic_1_stories>

<tech_stack>
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
</tech_stack>

<project_structure>
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
</project_structure>

## Data Models

### Download Item Schema
```

```

<implementation_timeline>
## Implementation Strategy and Timeline

Our implementation follows a strict TDD-first approach with two main phases:

### Phase 1 (MVP - Discord Core)
- Test infrastructure setup
- Basic Discord bot framework
- Download command implementation
- Queue management system

### Phase 2 (MVP - Download Features)
- Enhanced download capabilities
- Progress tracking
- File management
- Error handling

### Development Methodology
For each phase, we follow these steps:
1. Write comprehensive test suites first
2. Define clear acceptance criteria
3. Implement minimum code to pass tests
4. Refactor while maintaining coverage
5. Document all components

### Implementation Timeline

| Task | Status | Deadline |
|------|--------|----------|
| Test Infrastructure Setup | To Do | 2024-05-15 |
| Basic Discord Integration | To Do | 2024-05-22 |
| Download Commands (Twitter) | To Do | 2024-05-29 |
| Download Commands (Reddit) | To Do | 2024-06-05 |
| Queue Management | To Do | 2024-06-12 |
| Progress Tracking | To Do | 2024-06-19 |

### Testing Requirements
- Test coverage must be >= 90%
- All error cases must be covered
- Performance tests must be included
- Integration tests required for each feature
- External services must be mocked appropriately

### Quality Gates
Each task must pass these gates before being considered complete:
1. All tests passing (unit, integration, performance)
2. Code review completed
3. Documentation updated
4. Test coverage meets minimum threshold
5. Performance metrics within acceptable ranges
6. All error handling scenarios tested
7. Clean code principles verified
8. Type hints and docstrings complete
</implementation_timeline>

<discord_integration>
## Discord Integration and Download System

### 1. Discord Bot Configuration

#### Required Intents
- message_content
- guilds
- members
- messages
- reactions

#### Command Structure
| Command | Description |
|---------|-------------|
| $dlt <url> | Twitter/video downloads |
| $dlr <url> | Reddit downloads |
| $dlq | Show queue status |
| $dlc | Cancel download |

#### Permission Model
- Role-based access control
- Download size limits per role
- Queue priority handling

### 2. Download System Architecture

#### Download Manager
- Async download queue implementation
- Real-time progress tracking
- Rate limiting and throttling
- Concurrent download limits (max 5)

#### File Management
- Temporary storage handling with cleanup
- Automatic file cleanup after successful upload
- File size validation (max 50MB - Discord limit)
- Format verification and validation

### 3. Error Handling and Recovery
- Network failure recovery with automatic retries
- Invalid URL handling with user feedback
- File system error management
- Rate limit handling with exponential backoff
- Queue overflow management with priority system

### 4. Performance Requirements
- Download initiation response: < 1 second
- Queue status updates: Every 5 seconds
- Maximum queue size: 50 items
- Concurrent downloads: 5 max
- File size limits: 50MB (Discord limit)
- Memory usage: < 500MB under load
- CPU usage: < 50% under load

### 5. Integration Points
- Discord.py event system
- Gallery-dl integration for media downloads
- File system for temporary storage
- Discord CDN for file uploads
- Rate limiting systems
</discord_integration>

<test_strategy>
## Test-Driven Development Strategy

### 1. Core Test Infrastructure

#### Test Fixtures
```python
@pytest.fixture
async def test_bot():
    """Core bot fixture for Discord command testing."""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="$", intents=intents)
    await bot._async_setup_hook()
    dpytest.configure(bot)
    yield bot
    await dpytest.empty_queue()

@pytest.fixture
def mock_downloader():
    """Mock downloader for testing download functionality."""
    with patch('bot.download.Downloader') as mock:
        yield mock
```

### 2. Command Testing Strategy

#### Download Command Tests
```python
@pytest.mark.asyncio
class TestDownloadCommands:
    async def test_valid_twitter_url(self, test_bot, mock_downloader):
        url = "https://twitter.com/user/status/123"
        await dpytest.message(f"$dlt {url}")
        assert dpytest.verify().message().contains()
        mock_downloader.download.assert_called_once_with(url)

    async def test_invalid_url(self, test_bot):
        url = "not_a_url"
        await dpytest.message(f"$dlt {url}")
        assert dpytest.verify().message().contains("Invalid URL")

    async def test_queue_full(self, test_bot, mock_downloader):
        mock_downloader.queue_size.return_value = 50
        url = "https://twitter.com/user/status/123"
        await dpytest.message(f"$dlt {url}")
        assert dpytest.verify().message().contains("Queue full")
```

### 3. Integration Testing

```python
@pytest.mark.integration
class TestDownloadFlow:
    async def test_download_to_completion(self, test_bot, mock_downloader):
        # Given
        url = "https://twitter.com/user/status/123"
        mock_downloader.download.return_value = "file.mp4"

        # When
        await dpytest.message(f"$dlt {url}")

        # Then
        assert dpytest.verify().message().contains("Started")
        await asyncio.sleep(1)
        assert dpytest.verify().message().contains("Complete")
        assert os.path.exists("file.mp4")
```

### 4. Error Case Testing

```python
@pytest.mark.asyncio
class TestErrorHandling:
    async def test_network_failure(self, test_bot, mock_downloader):
        mock_downloader.download.side_effect = NetworkError
        url = "https://twitter.com/user/status/123"
        await dpytest.message(f"$dlt {url}")
        assert dpytest.verify().message().contains("Network error")

    async def test_rate_limit(self, test_bot, mock_downloader):
        mock_downloader.download.side_effect = RateLimitError
        url = "https://twitter.com/user/status/123"
        await dpytest.message(f"$dlt {url}")
        assert dpytest.verify().message().contains("Rate limited")
```

### 5. Performance Testing

```python
@pytest.mark.performance
class TestPerformance:
    async def test_response_time(self, test_bot):
        start = time.time()
        await dpytest.message("$dlt url")
        response_time = time.time() - start
        assert response_time < 1.0

    async def test_concurrent_downloads(self, test_bot):
        urls = [f"url{i}" for i in range(10)]
        tasks = [dpytest.message(f"$dlt {url}") for url in urls]
        await asyncio.gather(*tasks)
        assert mock_downloader.active_downloads <= 5
```

### 6. Test Coverage Requirements

- Unit Tests:
  * All command handlers
  * Queue management
  * File operations
  * Error handlers
  * Permission checks

- Integration Tests:
  * End-to-end download flows
  * Discord message handling
  * File upload process
  * Queue management system

- Performance Tests:
  * Response times
  * Concurrent operations
  * Memory usage
  * CPU utilization
  * Network bandwidth

### 7. Testing Best Practices

- Use pytest markers for test categorization
- Implement proper cleanup in fixtures
- Mock external dependencies
- Use parameterized tests for edge cases
- Maintain test isolation
- Follow AAA pattern (Arrange-Act-Assert)
- Document test purposes and scenarios
- Regular test execution in CI/CD pipeline
</test_strategy>
