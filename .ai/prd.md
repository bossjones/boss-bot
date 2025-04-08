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
