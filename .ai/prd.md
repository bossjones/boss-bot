# Title: PRD for Boss-Bot: A Discord Media Download and RAG Assistant

<version>1.0.0</version>

## Status: Draft

## Intro

Boss-Bot is a Discord bot designed to enhance server productivity by providing robust media download capabilities and future RAG (Retrieval-Augmented Generation) features. The initial MVP focuses on reliable media downloads from popular platforms like Twitter and Reddit, with a strong foundation for future AI-powered features. The bot emphasizes test-driven development, clean code practices, and modular design to ensure maintainability and extensibility.

## Development Environment

### Setup Requirements
- Python 3.12 or higher
- UV package manager
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/bossjones/boss-bot.git
cd boss-bot

# Install dependencies
uv sync --dev
```

### Key Configuration Files

#### 1. Package Management (pyproject.toml)
```toml
[project]
name = "boss-bot"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "discord-py>=2.5.2",
    "gallery-dl>=1.29.3",
    "loguru>=0.7.3",
    "pydantic-settings>=2.8.1",
    # ... other dependencies
]
```

#### 2. Code Quality Tools
- **Ruff**: Primary linter and formatter
  ```yaml
  # .pre-commit-config.yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  ```

#### 3. Testing Framework
- pytest with extensions:
  - pytest-asyncio for async testing
  - pytest-recording for HTTP mocking
  - pytest-cov for coverage reporting
  - pytest-retry for flaky tests

#### 4. Documentation
- MkDocs with extensions:
  ```yaml
  # mkdocs.yml configuration
  plugins:
    - mkdocstrings
    - coverage
    - git-revision-date-localized
    - macros
  ```

### Development Workflow
1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Run pre-commit hooks
5. Submit PR

### CI/CD Pipeline
GitHub Actions workflow includes:
- Linting with Ruff
- Testing with pytest
- Documentation generation
- Coverage reporting

### Environment Variables
Required for development:
```bash
DISCORD_TOKEN=required                # Discord bot token
DISCORD_CLIENT_ID=required           # Discord application client ID
DISCORD_SERVER_ID=required           # Target Discord server ID
DISCORD_ADMIN_USER_ID=required       # Admin user ID
```

## Goals

- Create a reliable and efficient Discord bot for media downloads with >99% uptime
- Implement comprehensive test coverage (>90%) using pytest and dpytest
- Ensure all modules follow clean code practices and stay under 120 lines
- Build a foundation for future RAG capabilities
- Provide clear progress tracking and queue management for downloads
- Maintain clear documentation and type hints for junior developer onboarding

## Test-Driven Development Guidelines

### Core Principles
1. Write failing test first
2. Keep tests focused and small
3. Use descriptive test names that explain the behavior
4. Follow the Arrange-Act-Assert pattern
5. No implementation without a failing test

### Example Test Patterns

#### Command Testing
```python
async def test_download_command_validates_url():
    """Test that download command properly validates URLs."""
    # Arrange
    bot = await create_test_bot()
    invalid_url = "not-a-url"

    # Act
    await send_command(bot, f"$dlt {invalid_url}")

    # Assert
    assert_bot_replied_with(bot, "Invalid URL")

async def test_download_command_handles_valid_url():
    """Test that download command processes valid URLs."""
    # Arrange
    bot = await create_test_bot()
    valid_url = "https://twitter.com/user/status/123"

    # Act
    await send_command(bot, f"$dlt {valid_url}")

    # Assert
    assert_download_started(bot, valid_url)
```

#### Event Testing
```python
async def test_bot_handles_disconnect():
    """Test that bot properly handles disconnection events."""
    # Arrange
    bot = await create_test_bot()
    await ensure_bot_connected(bot)

    # Act
    await simulate_disconnect(bot)

    # Assert
    assert_reconnection_attempted(bot)
    assert_event_logged(bot, "disconnect")
```

### Best Practices
1. **Test Isolation**
   - Each test should be independent
   - Clean up resources after each test
   - Use fresh fixtures for each test

2. **Meaningful Names**
   - Test names should describe behavior
   - Use consistent naming patterns
   - Include success and failure cases

3. **Test Organization**
   - Group related tests in classes
   - Use descriptive test class names
   - Keep test files focused and small

4. **Mocking and Fixtures**
   - Mock external dependencies
   - Use fixtures for common setup
   - Keep mocks simple and focused

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

<data_models>
## Data Models

All data models will be implemented using Pydantic for validation and serialization. Models are organized by domain and include comprehensive type hints and validation rules.

### Core Models

#### BotConfig
```python
class BotConfig(BaseSettings):
    """Bot configuration settings."""
    token: SecretStr
    command_prefix: str = "$"
    max_concurrent_downloads: int = 5
    max_queue_size: int = 50
    temp_file_retention_hours: int = 24
    max_file_size_mb: int = 50
    log_level: str = "INFO"

    class Config:
        env_prefix = "BOSS_BOT_"
```

#### DownloadItem
```python
class DownloadStatus(str, Enum):
    """Status of a download item."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DownloadPriority(int, Enum):
    """Priority levels for downloads."""
    LOW = 0
    NORMAL = 1
    HIGH = 2

class DownloadItem(BaseModel):
    """Represents a single download request."""
    id: UUID
    url: HttpUrl
    status: DownloadStatus
    priority: DownloadPriority = DownloadPriority.NORMAL
    user_id: int
    guild_id: int
    channel_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_size: Optional[int] = None
    current_size: Optional[int] = None
    attempt_count: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
```

#### QueueState
```python
class QueueState(BaseModel):
    """Represents the current state of the download queue."""
    items: List[DownloadItem]
    active_downloads: int
    total_items: int
    queue_size: int

    @property
    def is_full(self) -> bool:
        return self.total_items >= self.queue_size
```

#### DownloadProgress
```python
class ProgressUpdate(BaseModel):
    """Progress update for a download."""
    item_id: UUID
    bytes_downloaded: int
    total_bytes: Optional[int]
    speed_bps: float
    eta_seconds: Optional[float]
    status_message: str
```

### User Management Models

#### UserPermissions
```python
class PermissionLevel(str, Enum):
    """User permission levels."""
    NORMAL = "normal"
    PREMIUM = "premium"
    ADMIN = "admin"

class UserSettings(BaseModel):
    """User-specific settings and permissions."""
    user_id: int
    permission_level: PermissionLevel = PermissionLevel.NORMAL
    max_concurrent_downloads: int = 2
    max_file_size_mb: int = 50
    total_downloads: int = 0
    created_at: datetime
    last_download: Optional[datetime] = None
```

### File Management Models

#### DownloadedFile
```python
class DownloadedFile(BaseModel):
    """Represents a downloaded file in temporary storage."""
    id: UUID
    download_item_id: UUID
    filename: str
    file_path: Path
    size_bytes: int
    mime_type: str
    created_at: datetime
    expires_at: datetime
    checksum: str

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
```

### Error Models

#### DownloadError
```python
class ErrorType(str, Enum):
    """Types of download errors."""
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_URL = "invalid_url"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"

class DownloadError(BaseModel):
    """Detailed error information for failed downloads."""
    item_id: UUID
    error_type: ErrorType
    message: str
    timestamp: datetime
    retry_after: Optional[float] = None
    is_permanent: bool = False
```

### Metrics Models

#### DownloadMetrics
```python
class DownloadMetrics(BaseModel):
    """Metrics for download performance monitoring."""
    total_downloads: int = 0
    failed_downloads: int = 0
    average_speed_bps: float = 0.0
    total_bytes_downloaded: int = 0
    queue_wait_time_seconds: float = 0.0
    active_downloads: int = 0
    success_rate: float = 100.0
```

### Prometheus Metrics Structure

The following metrics will be collected and exposed via Prometheus:

```python
from prometheus_client import Counter, Gauge, Histogram

# Core Download Metrics
DOWNLOAD_REQUESTS = Counter(
    'download_requests_total',
    'Total download requests',
    ['platform', 'status']  # platform: twitter/reddit, status: success/failed
)

DOWNLOAD_DURATION = Histogram(
    'download_duration_seconds',
    'Time spent downloading',
    ['platform'],
    buckets=[1, 5, 10, 30, 60, 120, 300]  # 1s to 5min buckets
)

QUEUE_SIZE = Gauge(
    'download_queue_size',
    'Current size of download queue'
)

# Performance Metrics
COMMAND_LATENCY = Histogram(
    'command_latency_seconds',
    'Command processing time',
    ['command'],
    buckets=[0.1, 0.5, 1, 2, 5]  # 100ms to 5s buckets
)

DISCORD_API_LATENCY = Gauge(
    'discord_api_latency_seconds',
    'Discord API latency'
)

# Error Metrics
ERROR_COUNT = Counter(
    'error_total',
    'Total errors by type',
    ['error_type', 'platform']
)

# Resource Usage Metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# File Management Metrics
FILE_SIZE = Histogram(
    'download_file_size_bytes',
    'Size of downloaded files',
    ['platform'],
    buckets=[1024*1024*x for x in [1, 5, 10, 25, 50]]  # 1MB to 50MB buckets
)

TEMP_FILES = Gauge(
    'temp_files_count',
    'Number of files in temporary storage'
)
```

These metrics provide comprehensive monitoring of:
- Download performance and success rates
- Command response times
- Resource utilization
- Error tracking
- File management statistics

Metrics will be exposed on `/metrics` endpoint for Prometheus scraping.

These models provide a strong foundation for type safety and data validation throughout the application. Each model includes:
- Comprehensive type hints
- Default values where appropriate
- Validation rules
- JSON serialization support
- Clear documentation
- Enum-based status and type fields

The models are designed to be:
- Immutable where possible
- Self-validating
- Easy to serialize/deserialize
- Well-documented
- Extensible for future features
</data_models>

<file_management>
## File Management Specifications

### Storage Architecture

#### Directory Structure
```text
/tmp/boss-bot/
├── downloads/
│   ├── {guild_id}/
│   │   ├── {yyyy-mm-dd}/
│   │   │   ├── {download_id}/
│   │   │   │   ├── metadata.json
│   │   │   │   └── content/
│   │   │   │       └── {filename}
│   │   │   └── .cleanup
│   │   └── .stats
│   └── .maintenance
├── temp/
│   └── {download_id}/
└── .locks/
```

### Storage Policies

#### Temporary Storage
- **Location**: All downloads initially go to `/tmp/boss-bot/temp/{download_id}/`
- **Retention**: Files in temp are deleted after:
  * Successful upload to Discord (immediate)
  * Failed download (30 minutes)
  * Abandoned download (1 hour)
- **Size Limits**:
  * Individual file: 50MB (Discord limit)
  * Total temp storage: 1GB
  * Per guild daily quota: 500MB

#### Organized Storage
- **Structure**: Downloads are organized by guild and date
- **Metadata**: Each download includes a metadata.json file containing:
  * Original URL
  * Download timestamp
  * User information
  * File checksums
  * Processing history
- **Retention Periods**:
  * Successful downloads: 24 hours
  * Failed downloads with retry potential: 6 hours
  * Premium guild downloads: 72 hours

### Cleanup Mechanisms

#### Scheduled Cleanup
```python
class CleanupSchedule:
    """Cleanup schedule configuration."""
    TEMP_SCAN_INTERVAL: int = 300  # 5 minutes
    MAIN_SCAN_INTERVAL: int = 3600  # 1 hour
    DEEP_SCAN_INTERVAL: int = 86400  # 24 hours
```

#### Cleanup Rules
1. **Temporary Files**:
   - Run every 5 minutes
   - Remove files older than their retention period
   - Remove files from completed/failed downloads
   - Clean partial downloads older than 1 hour

2. **Main Storage**:
   - Run every hour
   - Remove expired files based on retention policy
   - Clean empty directories
   - Update storage statistics

3. **Deep Cleanup**:
   - Run daily during low-usage hours
   - Perform integrity checks
   - Remove orphaned files
   - Compress and archive logs
   - Generate storage reports

### File Operations

#### Download Process
1. **Initial Download**:
   ```python
   async def download_flow(url: str, guild_id: int) -> Path:
       temp_path = get_temp_path(download_id)
       try:
           await download_to_temp(url, temp_path)
           await validate_download(temp_path)
           final_path = organize_download(temp_path, guild_id)
           return final_path
       except Exception as e:
           await cleanup_failed_download(temp_path)
           raise
   ```

2. **Validation Checks**:
   - File size limits
   - MIME type verification
   - Malware scanning
   - File integrity checks

3. **Organization Process**:
   - Create guild/date directories
   - Generate metadata
   - Move from temp to organized storage
   - Update storage statistics

### Error Handling

#### Storage Errors
```python
class StorageError(Enum):
    DISK_FULL = "Insufficient disk space"
    QUOTA_EXCEEDED = "Guild quota exceeded"
    INVALID_FILE = "File validation failed"
    CLEANUP_ERROR = "Cleanup process failed"
```

#### Recovery Procedures
1. **Disk Space Issues**:
   - Trigger emergency cleanup
   - Notify administrators
   - Temporarily reject new downloads

2. **Quota Exceeded**:
   - Notify guild administrators
   - Provide cleanup recommendations
   - Offer premium upgrade options

3. **Validation Failures**:
   - Log detailed error information
   - Notify user with specific reason
   - Clean up invalid files immediately

### Monitoring and Metrics

#### Storage Metrics
```python
class StorageMetrics(BaseModel):
    """Storage monitoring metrics."""
    total_space_used: int
    temp_space_used: int
    downloads_per_guild: Dict[int, int]
    cleanup_stats: CleanupStats
    error_counts: Dict[StorageError, int]
```

#### Alerts
- Disk space usage > 80%
- Cleanup job failures
- High error rates
- Quota approaching limits
- Suspicious file patterns

### File Types and Processing

#### Supported File Types
```python
class SupportedTypes(BaseModel):
    """Supported file types and their processors."""
    IMAGES: List[str] = ["jpg", "png", "gif", "webp"]
    VIDEOS: List[str] = ["mp4", "webm", "mov"]
    AUDIO: List[str] = ["mp3", "wav", "ogg"]
    MAX_SIZES: Dict[str, int] = {
        "image": 5_242_880,  # 5MB
        "video": 52_428_800,  # 50MB
        "audio": 10_485_760  # 10MB
    }
```

#### Processing Rules
1. **Images**:
   - Convert to Discord-optimal formats
   - Resize if exceeding limits
   - Strip metadata

2. **Videos**:
   - Transcode to Discord-compatible format
   - Adjust bitrate if needed
   - Generate thumbnail

3. **Audio**:
   - Convert to Discord-supported format
   - Adjust quality if size exceeds limits

This comprehensive file management system ensures:
- Efficient use of storage space
- Reliable cleanup of temporary files
- Clear organization of downloads
- Robust error handling
- Detailed monitoring and metrics
- Type-safe file processing
</file_management>

<user_experience>
## User Experience Specifications

### Command Interface

#### Command Structure
```python
class CommandFormat:
    """Standard command format specifications."""
    PREFIX: str = "$"
    COMMANDS: Dict[str, str] = {
        "dlt": "Download from Twitter",
        "dlr": "Download from Reddit",
        "dlq": "Show queue status",
        "dlc": "Cancel download",
        "dls": "Show settings",
        "dlh": "Show help"
    }
```

#### Progress Updates
```python
class ProgressFormat:
    """Progress message formatting."""
    TEMPLATE: str = """
    Downloading: {filename}
    Progress: {bar} {percentage}%
    Speed: {speed}/s
    ETA: {eta}
    Status: {status}
    """
    UPDATE_INTERVAL: int = 5  # seconds
    BAR_LENGTH: int = 20
```

Example Progress Message:
```
Downloading: funny_cat_video.mp4
Progress: [====================] 100%
Speed: 1.2 MB/s
ETA: Complete
Status: Processing for Discord upload
```

### User Interactions

#### Command Flow
1. **Download Initiation**:
   ```
   User: $dlt https://twitter.com/user/status/123
   Bot: Starting download...
        Queue position: 2
        Estimated start: 2 minutes
   ```

2. **Progress Updates**:
   ```
   Bot: [Progress message updates every 5 seconds]
        Updates merge into single message
        Uses reactions for user controls
   ```

3. **Completion/Error**:
   ```
   Bot: ✅ Download complete!
        File: funny_cat_video.mp4
        Size: 2.3MB
        Time: 45s
   ```

#### Interactive Elements
1. **Progress Control Reactions**:
   - ⏸️ Pause download
   - ▶️ Resume download
   - ⏹️ Cancel download
   - ℹ️ Show details
   - 🔄 Retry failed download

2. **Queue Management**:
   ```
   User: $dlq
   Bot: Current Queue Status:
        1. video1.mp4 [===>    ] 35%
        2. image.jpg [WAITING]
        3. video2.mp4 [WAITING]

        Your position: 2
        Estimated wait: 3 minutes
   ```

3. **Settings Management**:
   ```
   User: $dls
   Bot: Your Settings:
        Max concurrent downloads: 2
        Notification preference: Mentions
        Default priority: Normal
        Total downloads today: 5/10
   ```

### Notification System

#### Update Types
```python
class NotificationPreference(Enum):
    """User notification preferences."""
    NONE = "none"  # No updates
    MINIMAL = "minimal"  # Start/finish only
    NORMAL = "normal"  # Regular progress
    VERBOSE = "verbose"  # Detailed updates
```

#### Notification Rules
1. **Queue Position Updates**:
   - When moving up in queue
   - When about to start
   - On significant delays

2. **Download Progress**:
   - Start of download
   - Regular progress updates
   - Completion/failure
   - Processing status

3. **Error Notifications**:
   - Clear error description
   - Recommended actions
   - Retry instructions
   - Support information

### User Settings

#### Configurable Options
```python
class UserPreferences(BaseModel):
    """User-configurable settings."""
    notification_level: NotificationPreference
    progress_bar_style: str
    default_priority: DownloadPriority
    mention_on_complete: bool
    auto_retry: bool
    max_retries: int = 3
```

#### Default Values
```python
DEFAULT_PREFERENCES = UserPreferences(
    notification_level=NotificationPreference.NORMAL,
    progress_bar_style="standard",
    default_priority=DownloadPriority.NORMAL,
    mention_on_complete=True,
    auto_retry=True
)
```

### Help System

#### Command Help
```python
class HelpFormat:
    """Help message formatting."""
    TEMPLATE: str = """
    {command}: {description}
    Usage: {usage}
    Examples:
    {examples}
    Notes:
    {notes}
    """
```

Example Help Message:
```
$dlt: Download from Twitter
Usage: $dlt <url> [priority]

Examples:
  $dlt https://twitter.com/user/status/123
  $dlt https://twitter.com/user/status/123 high

Notes:
- Supports single tweets and threads
- Max file size: 50MB
- Supported formats: Images, Videos
```

### Error Messages

#### User-Friendly Errors
```python
class ErrorMessages:
    """User-friendly error messages."""
    TEMPLATES = {
        ErrorType.NETWORK: (
            "🔌 Connection issue! I couldn't reach {platform}.\n"
            "I'll retry {retry_count} more times.\n"
            "Try again in {retry_after} seconds."
        ),
        ErrorType.RATE_LIMIT: (
            "⏳ We're being rate limited by {platform}.\n"
            "Please wait {retry_after} seconds."
        ),
        ErrorType.FILE_TOO_LARGE: (
            "📦 File is too large ({size}MB)!\n"
            "Maximum size: {max_size}MB\n"
            "Try requesting a smaller version."
        )
    }
```

The user experience design focuses on:
- Clear and intuitive commands
- Real-time progress feedback
- Interactive controls
- Customizable notifications
- Helpful error messages
- Comprehensive help system

Would you like me to:
1. Add more command examples?
2. Expand the notification system?
3. Add more interactive features?
4. Detail the help system further?
</user_experience>

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

- Story 4a: Discord Connection Setup
  Status: ''
  Requirements:
  - Create Discord application and bot user
  - Implement basic bot client with required intents
  - Set up environment configuration with pydantic-settings
  - Implement connection handling and basic event loop
  - Add health check endpoint
  Acceptance Criteria:
  - Bot successfully connects to Discord
  - Bot responds to health check command
  - Bot handles connection state changes
  - Environment variables are properly loaded
  Dependencies: Story 1, Story 3

- Story 4b: Command Framework Base
  Status: ''
  Requirements:
  - Set up command registration system
  - Implement basic error handling for commands
  - Add help command structure
  - Create command testing utilities
  - Implement command cooldowns and rate limiting
  Acceptance Criteria:
  - Commands can be registered and respond
  - Error handling works for basic cases
  - Help command shows available commands
  - Command tests pass
  - Rate limiting prevents command spam
  Dependencies: Story 4a

- Story 4c: Event Handler Implementation
  Status: ''
  Requirements:
  - Add core event handlers (ready, disconnect, etc.)
  - Implement reconnection logic
  - Add basic event logging
  - Create event testing framework
  - Implement error recovery for events
  Acceptance Criteria:
  - All core events are handled and logged
  - Bot recovers from disconnections
  - Event tests pass
  - Error recovery works as expected
  Dependencies: Story 4b

- Story 5: Queue System Foundation
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

### Test Infrastructure

#### Directory Structure
```text
tests/
├── conftest.py              # Shared test configuration and fixtures
├── fixtures/               # Test data and mock responses
│   ├── tweet_data.py      # Twitter API mock responses
│   ├── reddit_data.py     # Reddit API mock responses
│   └── discord_data.py    # Discord API mock responses
├── unit/                  # Unit tests directory
│   ├── test_bot/         # Bot-specific tests
│   ├── test_commands/    # Command handler tests
│   └── test_downloaders/ # Download functionality tests
├── integration/          # Integration tests
│   ├── test_discord/    # Discord API integration tests
│   └── test_gallery_dl/ # Gallery-dl integration tests
└── eval/                # Future RAG evaluation tests
```

#### Test Data Management
```python
# Example test fixture in tests/fixtures/tweet_data.py
@pytest.fixture
def sample_tweet_data():
    """Sample tweet data for testing."""
    return {
        "url": "https://twitter.com/user/status/123",
        "media": ["video.mp4"],
        "text": "Sample tweet"
    }

# Example VCR configuration in conftest.py
@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for HTTP interaction recording."""
    return {
        "filter_headers": ["authorization"],
        "filter_post_data_parameters": ["token", "api_key"],
        "match_on": ["method", "scheme", "host", "port", "path", "query"]
    }
```

#### Coverage Requirements (MVP)
| Component          | Target Coverage |
|-------------------|-----------------|
| Core Download     | 30%            |
| Command Parsing   | 25%            |
| Discord Events    | 20%            |
| File Management   | 20%            |

Note: These are minimum targets for MVP. Higher coverage will be required for critical paths.
</test_strategy>

<technical_implementation>
## Technical Implementation Details

### Error Handling (MVP)

#### Core Error Types
```python
class BotErrorType(str, Enum):
    """Core error types for MVP."""
    DOWNLOAD_FAILED = "download_failed"
    INVALID_URL = "invalid_url"
    QUEUE_FULL = "queue_full"
    FILE_TOO_LARGE = "file_too_large"
    DISCORD_ERROR = "discord_error"
```

### Logging Configuration

The application uses Loguru for structured logging with the following configuration:

```python
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Configure Loguru
logger.configure(
    handlers=[
        {
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "level": "INFO",
            "colorize": True,
            "backtrace": True,
            "diagnose": True,
            "enqueue": True,
        }
    ]
)

# Add better exception handling
logger.add(
    sys.stderr,
    format="{time} | {level} | {message}",
    filter=lambda record: record["level"].name == "ERROR",
    level="ERROR",
    backtrace=True,
    diagnose=True,
)

# Example logging usage
logger.info("Bot starting up...")
logger.debug("Processing download request: {url}", url="https://example.com")
logger.warning("Rate limit approaching: {limit}", limit=10)
logger.error("Download failed: {error}", error="Network timeout")
```

#### Log Levels
- DEBUG: Detailed information for debugging
- INFO: General operational events
- WARNING: Unexpected but handled situations
- ERROR: Errors that need attention
- CRITICAL: System-level failures

#### Logging Guidelines
1. Use structured logging with context:
   ```python
   logger.info("Download started", url=url, user_id=user_id)
   ```

2. Include relevant context in errors:
   ```python
   try:
       await download_file(url)
   except Exception as e:
       logger.exception(f"Download failed: {str(e)}", url=url)
   ```

3. Use appropriate log levels:
   - DEBUG: Detailed flow information
   - INFO: Normal operations
   - WARNING: Potential issues
   - ERROR: Operation failures
   - CRITICAL: System failures

4. Log sensitive information appropriately:
   ```python
   logger.info(
       "Processing user request",
       user_id=user.id,  # OK to log
       # Never log tokens or passwords
   )
   ```

### Performance Metrics (MVP)

#### Key Metrics
1. **Essential Metrics**:
   ```python
   class CoreMetrics:
       """Essential performance metrics."""
       download_count: int = 0
       failed_downloads: int = 0
       queue_size: int = 0
       active_downloads: int = 0
   ```

2. **Basic Monitoring**:
   - Queue length tracking
   - Download success/failure rates
   - Basic response time logging

Nice to Have (Post-MVP):
- Detailed performance analytics
- Real-time monitoring dashboard
- Resource usage tracking
- Per-guild metrics

### API Documentation (MVP)

#### Documentation Approach
1. **Code Documentation**:
   - Google-style docstrings
   - Type hints for all functions
   - Basic README with setup instructions

2. **Command Documentation**:
   - Help command with usage examples
   - Basic command parameter descriptions
   - Error message documentation

Example Docstring Format:
```python
def download_media(url: str, user_id: int) -> DownloadResult:
    """Download media from supported platforms.

    Args:
        url: The URL to download from (Twitter or Reddit)
        user_id: Discord user ID requesting the download

    Returns:
        DownloadResult containing file path and metadata

    Raises:
        DownloadError: If download fails or URL is invalid
        QueueFullError: If download queue is full
    """
```

Nice to Have (Post-MVP):
- Auto-generated API documentation
- Interactive command examples
- Detailed troubleshooting guides
- API versioning documentation

### Deployment Strategy (MVP)

#### Initial Deployment
1. **Requirements**:
   - Python 3.11+
   - Discord Bot Token
   - Basic environment variables
   - Storage directory setup

2. **Deployment Steps**:
   ```bash
   # Setup
   uv venv
   source .venv/bin/activate
   uv sync --dev

   # Run
   uv run python -m boss_bot
   ```

3. **Environment Variables**:
   ```bash
   # Required for MVP
   DISCORD_TOKEN=required                # Discord bot authentication token
   DISCORD_CLIENT_ID=required           # Discord application client ID
   DISCORD_SERVER_ID=required           # Target Discord server ID
   DISCORD_ADMIN_USER_ID=required       # Admin user ID for bot management
   DISCORD_ADMIN_USER_INVITED=optional  # Track if admin user is invited

   # Debug and Development (Optional for MVP)
   BETTER_EXCEPTIONS=1                  # Enhanced exception formatting
   DEBUG_AIDER=0                        # Additional debug information
   LOCAL_TEST_DEBUG=0                   # Local testing mode
   LOCAL_TEST_ENABLE_EVALS=0           # Enable evaluation tests
   PYTHON_DEBUG=0                       # Python debug mode
   PYTHONASYNCIODEBUG=0                # AsyncIO debug mode

   # Monitoring and Error Tracking (Optional for MVP)
   ENABLE_SENTRY=0                      # Enable Sentry error tracking
   SENTRY_DSN=optional                  # Sentry DSN if enabled

   # Future Features (Post-MVP)
   ## AI Integration
   ENABLE_AI=0                          # Enable AI features
   ANTHROPIC_API_KEY=optional          # Anthropic API access
   COHERE_API_KEY=optional             # Cohere API access
   OPENAI_API_KEY=optional             # OpenAI API access

   ## LangChain Integration
   LANGCHAIN_API_KEY=optional          # LangChain API access
   LANGCHAIN_DEBUG_LOGS=0              # LangChain debug logging
   LANGCHAIN_ENDPOINT=optional         # LangChain API endpoint
   LANGCHAIN_HUB_API_KEY=optional      # LangChain Hub access
   LANGCHAIN_HUB_API_URL=optional      # LangChain Hub URL
   LANGCHAIN_PROJECT=optional          # LangChain project name
   LANGCHAIN_TRACING_V2=0             # LangChain tracing

   ## Vector Store
   ENABLE_REDIS=0                      # Enable Redis vector store
   PINECONE_API_KEY=optional          # Pinecone API access
   PINECONE_ENV=optional              # Pinecone environment
   PINECONE_INDEX=optional            # Pinecone index name

   ## Additional Services
   FIRECRAWL_API_KEY=optional         # Firecrawl API access
   TAVILY_API_KEY=optional            # Tavily API access
   UNSTRUCTURED_API_KEY=optional      # Unstructured API access
   UNSTRUCTURED_API_URL=optional      # Unstructured API endpoint
   ```

Nice to Have (Post-MVP):
- Docker deployment
- CI/CD pipeline
- Multiple environment support
- Automated backups
- Rolling updates
</technical_implementation>
