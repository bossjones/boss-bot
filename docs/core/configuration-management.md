# Configuration Management

This document covers Boss-Bot's configuration system, including Pydantic settings, environment variables, feature flags, and security considerations for managing bot configuration across environments.

## Configuration Architecture

Boss-Bot uses a **layered configuration approach** with clear precedence rules:

```mermaid
graph TB
    subgraph "Configuration Sources (Precedence Order)"
        ENV[Environment Variables] --> DOTENV[.env File]
        DOTENV --> DEFAULTS[Default Values]
        DEFAULTS --> COMPUTED[Computed Properties]
    end

    subgraph "Configuration Categories"
        DISCORD[Discord Settings]
        DOWNLOAD[Download Settings]
        FEATURES[Feature Flags]
        STORAGE[Storage Settings]
        MONITORING[Monitoring Settings]
    end

    ENV --> VALIDATION[Pydantic Validation]
    VALIDATION --> SETTINGS[BossSettings Instance]
    SETTINGS --> DISCORD
    SETTINGS --> DOWNLOAD
    SETTINGS --> FEATURES
    SETTINGS --> STORAGE
    SETTINGS --> MONITORING
```

## BossSettings Core Configuration

### Base Settings Class

```python
# src/boss_bot/core/env.py
from pydantic import BaseSettings, Field, SecretStr, validator
from pathlib import Path
from typing import Optional, List
from enum import Enum

class LogLevel(str, Enum):
    """Logging level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class BossSettings(BaseSettings):
    """Central configuration for Boss-Bot using Pydantic settings.

    All configuration comes from environment variables with sensible defaults.
    Uses SecretStr for sensitive values and proper validation.
    """

    # ==========================================
    # Discord Configuration
    # ==========================================

    discord_token: SecretStr = Field(
        ...,  # Required
        description="Discord bot token from Discord Developer Portal"
    )

    command_prefix: str = Field(
        default="$",
        description="Command prefix for Discord bot commands"
    )

    guild_ids: Optional[List[int]] = Field(
        default=None,
        description="Specific guild IDs for development (slash commands)"
    )

    # ==========================================
    # Download System Configuration
    # ==========================================

    download_dir: Path = Field(
        default=Path("./downloads"),
        description="Base directory for downloaded media files"
    )

    max_file_size: int = Field(
        default=100_000_000,  # 100MB
        description="Maximum file size in bytes"
    )

    max_concurrent_downloads: int = Field(
        default=3,
        description="Maximum concurrent download operations"
    )

    download_timeout: int = Field(
        default=300,  # 5 minutes
        description="Download timeout in seconds"
    )

    # ==========================================
    # Feature Flags (Experimental)
    # ==========================================

    twitter_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for Twitter downloads"
    )

    reddit_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for Reddit downloads"
    )

    instagram_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for Instagram downloads"
    )

    youtube_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for YouTube downloads"
    )

    download_api_fallback_to_cli: bool = Field(
        default=True,
        description="Fallback to CLI if API client fails"
    )

    # ==========================================
    # External Tool Configuration
    # ==========================================

    gallery_dl_config_file: Path = Field(
        default=Path("~/.gallery-dl.conf"),
        description="Path to gallery-dl configuration file"
    )

    gallery_dl_cookies_file: Optional[Path] = Field(
        default=None,
        description="Path to Netscape format cookies file"
    )

    gallery_dl_cookies_from_browser: Optional[str] = Field(
        default=None,
        description="Browser to extract cookies from (firefox, chrome, etc.)"
    )

    gallery_dl_user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        description="User agent for gallery-dl requests"
    )

    yt_dlp_config_file: Optional[Path] = Field(
        default=None,
        description="Path to yt-dlp configuration file"
    )

    # ==========================================
    # Storage and Quota Configuration
    # ==========================================

    storage_quota_per_user: int = Field(
        default=1_000_000_000,  # 1GB
        description="Storage quota per user in bytes"
    )

    storage_quota_per_guild: int = Field(
        default=10_000_000_000,  # 10GB
        description="Storage quota per guild in bytes"
    )

    cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic file cleanup"
    )

    cleanup_after_days: int = Field(
        default=30,
        description="Days to keep files before cleanup"
    )

    # ==========================================
    # Monitoring and Logging
    # ==========================================

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )

    log_file: Optional[Path] = Field(
        default=None,
        description="Log file path (stdout if not specified)"
    )

    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection"
    )

    health_check_enabled: bool = Field(
        default=True,
        description="Enable health check endpoints"
    )

    # ==========================================
    # Database Configuration (Future)
    # ==========================================

    database_url: Optional[SecretStr] = Field(
        default=None,
        description="Database connection URL"
    )

    redis_url: Optional[SecretStr] = Field(
        default=None,
        description="Redis connection URL for caching"
    )

    # ==========================================
    # Security Configuration
    # ==========================================

    allowed_file_types: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "mp4", "webm", "mp3", "wav"],
        description="Allowed file extensions for downloads"
    )

    virus_scan_enabled: bool = Field(
        default=False,
        description="Enable virus scanning of downloaded files"
    )

    rate_limit_per_user: int = Field(
        default=10,
        description="Rate limit: requests per user per minute"
    )

    rate_limit_per_guild: int = Field(
        default=50,
        description="Rate limit: requests per guild per minute"
    )

    # ==========================================
    # Validation and Computed Properties
    # ==========================================

    @validator('download_dir')
    def validate_download_dir(cls, v: Path) -> Path:
        """Ensure download directory exists and is writable."""
        v = v.expanduser().resolve()
        v.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        test_file = v / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise ValueError(f"Download directory not writable: {e}")

        return v

    @validator('guild_ids', pre=True)
    def parse_guild_ids(cls, v) -> Optional[List[int]]:
        """Parse guild IDs from comma-separated string or list."""
        if v is None or v == "":
            return None

        if isinstance(v, str):
            return [int(guild_id.strip()) for guild_id in v.split(",")]

        return v

    @validator('allowed_file_types')
    def normalize_file_types(cls, v: List[str]) -> List[str]:
        """Normalize file extensions (lowercase, no dots)."""
        return [ext.lower().lstrip('.') for ext in v]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.log_level == LogLevel.DEBUG

    @property
    def total_storage_quota(self) -> int:
        """Calculate total storage quota across all users/guilds."""
        # This would be implemented based on actual usage patterns
        return self.storage_quota_per_guild * 10  # Estimate

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"  # For nested config like DISCORD__TOKEN

        # Security: Don't include sensitive values in repr
        fields = {
            'discord_token': {'repr': False},
            'database_url': {'repr': False},
            'redis_url': {'repr': False},
        }
```

## Environment Variable Configuration

### Development Environment (.env)

```bash
# .env file for development
# =========================

# ==========================================
# Discord Configuration
# ==========================================
DISCORD_TOKEN="your_bot_token_here"
COMMAND_PREFIX="$"
GUILD_IDS="123456789,987654321"  # Optional: specific guilds for development

# ==========================================
# Download Configuration
# ==========================================
DOWNLOAD_DIR="./downloads"
MAX_FILE_SIZE=100000000  # 100MB
MAX_CONCURRENT_DOWNLOADS=3
DOWNLOAD_TIMEOUT=300

# ==========================================
# Feature Flags (Experimental Features)
# ==========================================
TWITTER_USE_API_CLIENT=false
REDDIT_USE_API_CLIENT=false
INSTAGRAM_USE_API_CLIENT=false
YOUTUBE_USE_API_CLIENT=false
DOWNLOAD_API_FALLBACK_TO_CLI=true

# ==========================================
# External Tool Configuration
# ==========================================
GALLERY_DL_CONFIG_FILE="~/.gallery-dl.conf"
GALLERY_DL_COOKIES_FROM_BROWSER="firefox"
GALLERY_DL_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"

# ==========================================
# Storage and Quota
# ==========================================
STORAGE_QUOTA_PER_USER=1000000000    # 1GB
STORAGE_QUOTA_PER_GUILD=10000000000  # 10GB
CLEANUP_ENABLED=true
CLEANUP_AFTER_DAYS=30

# ==========================================
# Monitoring and Logging
# ==========================================
LOG_LEVEL="DEBUG"
LOG_FILE="./logs/boss-bot.log"
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true

# ==========================================
# Security
# ==========================================
ALLOWED_FILE_TYPES="jpg,jpeg,png,gif,mp4,webm,mp3,wav"
VIRUS_SCAN_ENABLED=false
RATE_LIMIT_PER_USER=10
RATE_LIMIT_PER_GUILD=50

# ==========================================
# Database (Future)
# ==========================================
# DATABASE_URL="postgresql://user:pass@localhost/bossbot"
# REDIS_URL="redis://localhost:6379"
```

### Production Environment

```bash
# Production environment variables
# ================================

# Security: Use secrets management system in production
DISCORD_TOKEN="${SECRET_DISCORD_TOKEN}"
DATABASE_URL="${SECRET_DATABASE_URL}"

# Production-specific settings
LOG_LEVEL="INFO"
LOG_FILE="/var/log/boss-bot/app.log"
DOWNLOAD_DIR="/var/lib/boss-bot/downloads"

# Enhanced security in production
VIRUS_SCAN_ENABLED=true
CLEANUP_ENABLED=true
CLEANUP_AFTER_DAYS=7  # Shorter retention in production

# Conservative feature flags
TWITTER_USE_API_CLIENT=false
REDDIT_USE_API_CLIENT=false
DOWNLOAD_API_FALLBACK_TO_CLI=true

# Tighter rate limits
RATE_LIMIT_PER_USER=5
RATE_LIMIT_PER_GUILD=25
MAX_CONCURRENT_DOWNLOADS=2
```

## Feature Flag System

### DownloadFeatureFlags

```python
# src/boss_bot/core/downloads/feature_flags.py
from boss_bot.core.env import BossSettings

class DownloadFeatureFlags:
    """Feature flags for download system implementations."""

    def __init__(self, settings: BossSettings):
        self.settings = settings

    @property
    def use_api_twitter(self) -> bool:
        """Use API-direct approach for Twitter downloads."""
        return self.settings.twitter_use_api_client

    @property
    def use_api_reddit(self) -> bool:
        """Use API-direct approach for Reddit downloads."""
        return self.settings.reddit_use_api_client

    @property
    def use_api_instagram(self) -> bool:
        """Use API-direct approach for Instagram downloads."""
        return self.settings.instagram_use_api_client

    @property
    def use_api_youtube(self) -> bool:
        """Use API-direct approach for YouTube downloads."""
        return self.settings.youtube_use_api_client

    @property
    def api_fallback_to_cli(self) -> bool:
        """Fallback to CLI if API fails."""
        return self.settings.download_api_fallback_to_cli

    def get_strategy_type(self, platform: str) -> str:
        """Get strategy type for platform."""
        platform_flags = {
            'twitter': self.use_api_twitter,
            'reddit': self.use_api_reddit,
            'instagram': self.use_api_instagram,
            'youtube': self.use_api_youtube,
        }

        use_api = platform_flags.get(platform.lower(), False)
        return "api" if use_api else "cli"

    def should_fallback(self, platform: str, error: Exception) -> bool:
        """Determine if API error should trigger CLI fallback."""
        if not self.api_fallback_to_cli:
            return False

        # Don't fallback for configuration errors
        if isinstance(error, (ValueError, TypeError)):
            return False

        # Fallback for network/API errors
        return True
```

### Feature Flag Configuration Patterns

```python
# Environment-based feature flag configuration
def configure_features_for_environment(env: str) -> Dict[str, bool]:
    """Configure feature flags based on environment."""

    if env == "development":
        return {
            "twitter_use_api_client": True,   # Test new features
            "reddit_use_api_client": True,
            "download_api_fallback_to_cli": True,  # Safety net
        }

    elif env == "staging":
        return {
            "twitter_use_api_client": True,   # Full testing
            "reddit_use_api_client": False,  # Gradual rollout
            "download_api_fallback_to_cli": True,
        }

    elif env == "production":
        return {
            "twitter_use_api_client": False,  # Conservative
            "reddit_use_api_client": False,
            "download_api_fallback_to_cli": True,
        }

    return {}  # All defaults (conservative)

# Usage in configuration
env = os.getenv("ENVIRONMENT", "development")
feature_overrides = configure_features_for_environment(env)

# Override environment variables programmatically if needed
for key, value in feature_overrides.items():
    os.environ[key.upper()] = str(value)
```

## External Tool Configuration

### Gallery-dl Configuration

```python
# src/boss_bot/core/downloads/clients/config/gallery_dl_config.py
from pydantic import BaseModel, Field, SecretStr, validator
from typing import Optional, List, Dict, Any
from pathlib import Path

class TwitterConfig(BaseModel):
    """Twitter extractor configuration."""
    quoted: bool = True
    replies: bool = True
    retweets: bool = True
    videos: bool = True
    cookies: Optional[str] = None
    filename: str = "{category}_{user[screen_name]}_{id}_{num}.{extension}"
    directory: List[str] = ["twitter", "{user[screen_name]}"]

class RedditConfig(BaseModel):
    """Reddit extractor configuration."""
    client_id: Optional[SecretStr] = Field(None, alias="client-id")
    user_agent: str = Field(alias="user-agent")
    comments: int = 0
    morecomments: bool = False
    videos: bool = True
    filename: str = "{category}_{subreddit}_{id}_{num}.{extension}"
    directory: List[str] = ["reddit", "{subreddit}"]

    @validator('user_agent')
    def validate_user_agent(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("User agent is required for Reddit")
        return v

class DownloaderConfig(BaseModel):
    """Downloader configuration."""
    filesize_min: Optional[int] = Field(None, alias="filesize-min")
    filesize_max: Optional[int] = Field(None, alias="filesize-max")
    rate: Optional[int] = None
    retries: int = 4
    timeout: float = 30.0
    verify: bool = True

class ExtractorConfig(BaseModel):
    """Main extractor configuration."""
    base_directory: str = Field("./downloads/", alias="base-directory")
    archive: Optional[str] = None
    cookies: Optional[str] = None
    user_agent: str = Field(alias="user-agent")
    twitter: TwitterConfig = TwitterConfig()
    reddit: RedditConfig = RedditConfig()

class GalleryDLConfig(BaseModel):
    """Root gallery-dl configuration with validation."""
    extractor: ExtractorConfig
    downloader: DownloaderConfig = DownloaderConfig()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for gallery-dl."""
        return self.dict(by_alias=True, exclude_none=True)

    @classmethod
    def from_file(cls, config_file: Path) -> "GalleryDLConfig":
        """Load configuration from JSON file."""
        import json

        if not config_file.exists():
            raise FileNotFoundError(f"Gallery-dl config not found: {config_file}")

        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)
```

### Sample Gallery-dl Configuration File

```json
{
    "extractor": {
        "base-directory": "./downloads/",
        "archive": "./downloads/.archive.sqlite3",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",

        "twitter": {
            "quoted": true,
            "replies": true,
            "retweets": true,
            "videos": true,
            "filename": "{category}_{user[screen_name]}_{id}_{num}.{extension}",
            "directory": ["twitter", "{user[screen_name]}"]
        },

        "reddit": {
            "user-agent": "gallery-dl:boss-bot:1.0 (by /u/boss_bot_dev)",
            "comments": 0,
            "morecomments": false,
            "videos": true,
            "filename": "{category}_{subreddit}_{id}_{num}.{extension}",
            "directory": ["reddit", "{subreddit}"]
        },

        "instagram": {
            "videos": true,
            "highlights": false,
            "stories": false,
            "filename": "{username}_{shortcode}_{num}.{extension}",
            "directory": ["instagram", "{username}"]
        }
    },

    "downloader": {
        "retries": 4,
        "timeout": 30.0,
        "verify": true,
        "rate": null
    },

    "output": {
        "mode": "auto",
        "progress": true,
        "log": "[{name}][{levelname}] {message}"
    }
}
```

## Configuration Validation and Security

### Security Best Practices

```python
# Security considerations in configuration
class SecureConfigMixin:
    """Mixin for secure configuration handling."""

    @validator('*', pre=True)
    def no_sql_injection(cls, v):
        """Prevent SQL injection in string fields."""
        if isinstance(v, str):
            dangerous_patterns = [';', '--', '/*', '*/', 'xp_', 'sp_']
            if any(pattern in v.lower() for pattern in dangerous_patterns):
                raise ValueError("Potentially dangerous SQL pattern detected")
        return v

    @validator('download_dir', 'log_file')
    def validate_paths(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate and sanitize file paths."""
        if v is None:
            return v

        # Resolve and normalize path
        v = Path(v).expanduser().resolve()

        # Prevent path traversal
        if ".." in str(v):
            raise ValueError("Path traversal detected")

        # Ensure path is within allowed directories
        allowed_roots = [
            Path.cwd(),
            Path.home(),
            Path("/var/log"),
            Path("/tmp")
        ]

        if not any(str(v).startswith(str(root)) for root in allowed_roots):
            raise ValueError(f"Path not allowed: {v}")

        return v

# Apply security mixin
class BossSettings(BaseSettings, SecureConfigMixin):
    # ... existing configuration ...
    pass
```

### Configuration Testing

```python
# tests/test_core/test_configuration.py
import pytest
from boss_bot.core.env import BossSettings

class TestBossSettings:
    """Test configuration validation and security."""

    def test_default_configuration(self, monkeypatch):
        """Test default configuration is valid."""
        # Set required fields
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")

        settings = BossSettings()

        assert settings.command_prefix == "$"
        assert settings.max_concurrent_downloads == 3
        assert settings.log_level.value == "INFO"

    def test_environment_override(self, monkeypatch):
        """Test environment variables override defaults."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("COMMAND_PREFIX", "!")
        monkeypatch.setenv("MAX_CONCURRENT_DOWNLOADS", "5")

        settings = BossSettings()

        assert settings.command_prefix == "!"
        assert settings.max_concurrent_downloads == 5

    def test_path_validation(self, monkeypatch, tmp_path):
        """Test path validation and creation."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))

        settings = BossSettings()

        assert settings.download_dir.exists()
        assert settings.download_dir.is_dir()

    def test_secret_repr_hidden(self, monkeypatch):
        """Test sensitive values are hidden in repr."""
        monkeypatch.setenv("DISCORD_TOKEN", "secret_token")

        settings = BossSettings()
        settings_repr = repr(settings)

        assert "secret_token" not in settings_repr
        assert "discord_token=" not in settings_repr

    def test_feature_flags_integration(self, monkeypatch):
        """Test feature flags work with settings."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("TWITTER_USE_API_CLIENT", "true")

        settings = BossSettings()
        feature_flags = DownloadFeatureFlags(settings)

        assert feature_flags.use_api_twitter is True
        assert feature_flags.use_api_reddit is False  # Default
```

## Configuration Management in Practice

### Dependency Injection Pattern

```python
# Inject configuration throughout the application
class BossBot(commands.Bot):
    """Main bot with configuration dependency injection."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        super().__init__(
            command_prefix=settings.command_prefix,
            intents=discord.Intents.default()
        )

        # Initialize subsystems with configuration
        self.queue_manager = QueueManager(settings)
        self.download_manager = DownloadManager(settings)
        self.feature_flags = DownloadFeatureFlags(settings)

# Usage
def main():
    settings = BossSettings()  # Loads from environment
    bot = BossBot(settings)
    bot.run(settings.discord_token.get_secret_value())
```

### Hot Configuration Reloading (Future)

```python
# Future: Support for configuration reloading without restart
class ConfigurationManager:
    """Manage configuration with hot reloading support."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self._watchers = []

    async def watch_config_changes(self):
        """Watch for configuration file changes."""
        # Implementation would watch .env file and config files
        # Reload and validate configuration on changes
        # Emit events for components to update their configuration
        pass

    def reload_configuration(self) -> BossSettings:
        """Reload configuration from environment."""
        return BossSettings()
```

This configuration system provides type-safe, validated configuration management with security considerations, feature flags, and proper separation of concerns across different environments.
