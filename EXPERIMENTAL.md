# EXPERIMENTAL.md

This document outlines experimental features and architectures being considered for boss-bot. These features are not yet implemented but represent potential future enhancements.

## Table of Contents
- [API-Direct Download Clients](#api-direct-download-clients)
- [Architecture Overview](#architecture-overview)
- [Implementation Strategy](#implementation-strategy)
- [Feature Flag Configuration](#feature-flag-configuration)
- [Testing Strategy](#testing-strategy)
- [Migration Path](#migration-path)

## API-Direct Download Clients

### Overview
Currently, boss-bot uses subprocess calls to external tools (gallery-dl, yt-dlp) for downloading media content. While this approach is stable and well-tested, it has limitations:

- **Subprocess Overhead**: Each download spawns a new process
- **Limited Error Handling**: Difficult to capture detailed error information
- **Testing Challenges**: Hard to mock and test subprocess interactions
- **Performance**: Cannot leverage async/await patterns effectively

### Proposed Solution: Hybrid Strategy Pattern

The experimental approach introduces **API-direct clients** that interact with gallery-dl and yt-dlp as Python modules rather than subprocesses, while maintaining backward compatibility with the existing CLI-based approach.

Key principles:
- ✅ **Zero Disruption**: Existing CLI handlers remain unchanged
- ✅ **Feature Flag Control**: Choose implementation per platform
- ✅ **Sync/Async Compatibility**: Handle both synchronous and asynchronous contexts
- ✅ **Fallback Strategy**: API failures can fallback to CLI approach
- ✅ **Testing**: Enable pytest-recording for API interactions

## Architecture Overview

### Current State (Preserved)
```
BossBot → DownloadCog → TwitterHandler (subprocess) ✅ KEEP AS-IS
BossBot → CLI Commands → TwitterHandler (subprocess) ✅ KEEP AS-IS
```

### New Parallel Path (Feature Flagged)
```
BossBot → DownloadCog → DownloadStrategy → [TwitterHandler OR TwitterAPIClient]
BossBot → CLI Commands → DownloadStrategy → [TwitterHandler OR TwitterAPIClient]
```

### Directory Structure

```
src/boss_bot/core/downloads/
├── __init__.py
├── manager.py                     # ✅ Unchanged
├── handlers/                      # ✅ Unchanged - existing CLI handlers
│   ├── __init__.py
│   ├── base_handler.py           # ✅ Keep existing
│   ├── twitter_handler.py        # ✅ Keep existing
│   └── reddit_handler.py         # ✅ Keep existing
├── strategies/                    # 🆕 NEW: Strategy pattern for choosing approach
│   ├── __init__.py
│   ├── base_strategy.py          # Strategy interface
│   ├── twitter_strategy.py       # Twitter: CLI vs API choice
│   └── reddit_strategy.py        # Reddit: CLI vs API choice
├── clients/                       # 🆕 NEW: API-direct implementations
│   ├── __init__.py
│   ├── base_client.py            # Async base client
│   ├── aio_gallery_dl.py         # Async gallery-dl wrapper
│   ├── aio_yt_dlp.py             # Async yt-dlp wrapper (future)
│   ├── sync_adapters.py          # Sync wrappers for API clients
│   └── config/                   # Client configuration models
│       ├── __init__.py
│       ├── gallery_dl_config.py  # Pydantic models for gallery-dl
│       └── yt_dlp_config.py      # Pydantic models for yt-dlp
└── feature_flags.py               # 🆕 NEW: Feature flag configuration
```

## Configuration Management

### Configuration Sources and Hierarchy

The API-direct approach leverages multiple configuration sources in order of precedence:

1. **Environment Variables** (Highest Priority) - Used for feature flags and basic settings
2. **Gallery-dl Config File** - Platform-specific configurations (`~/.gallery-dl.conf`)
3. **Default Configuration** - Fallback settings built into the application

### Environment Variables (Primary Configuration)

Boss-bot uses environment variables for most configuration, validated through Pydantic settings:

```python
# core/env.py additions
class BossSettings(BaseSettings):
    # ... existing settings ...

    # Feature flags for download strategies
    twitter_use_api_client: bool = Field(default=False)
    reddit_use_api_client: bool = Field(default=False)
    youtube_use_api_client: bool = Field(default=False)
    download_api_fallback_to_cli: bool = Field(default=True)

    # API client configuration
    gallery_dl_config_file: Path = Field(default=Path("~/.gallery-dl.conf"))
    gallery_dl_cookies_file: Path | None = Field(default=None)
    gallery_dl_cookies_from_browser: str | None = Field(default=None)  # firefox, chrome, etc.
```

### Gallery-dl Configuration File

The API clients load additional configuration from gallery-dl config files. Based on the [official documentation](https://gdl-org.github.io/docs/configuration.html) and [default config](https://github.com/mikf/gallery-dl/blob/master/docs/gallery-dl.conf), here's an example configuration:

```json
{
    "extractor": {
        "base-directory": "./downloads/",
        "archive": "./downloads/.archive.sqlite3",
        "cookies": null,
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
            "comments": 0,
            "morecomments": false,
            "date-min": 0,
            "date-max": 253402210800,
            "recursion": 0,
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
        "filesize-min": null,
        "filesize-max": null,
        "rate": null,
        "retries": 4,
        "timeout": 30.0,
        "verify": true
    },

    "output": {
        "mode": "auto",
        "progress": true,
        "log": "[{name}][{levelname}] {message}"
    }
}
```

### Cookie and Authentication Handling

The system supports multiple authentication methods:

#### 1. Cookie Files (Netscape Format)
```python
# Environment configuration
GALLERY_DL_COOKIES_FILE="/path/to/cookies.txt"

# Usage in client
async with AsyncGalleryDL(cookies_file=settings.gallery_dl_cookies_file) as client:
    async for item in client.download(url):
        yield item
```

#### 2. Browser Cookie Import
```python
# Environment configuration
GALLERY_DL_COOKIES_FROM_BROWSER="firefox"  # or "chrome", "safari", etc.

# Usage in client
async with AsyncGalleryDL(cookies_from_browser="firefox") as client:
    async for item in client.download(url):
        yield item
```

#### 3. Platform-Specific Authentication
```json
{
    "extractor": {
        "instagram": {
            "username": "your_username",
            "password": "your_password"
        },
        "reddit": {
            "client-id": "your_client_id",
            "user-agent": "gallery-dl:your_app_name:1.0 (by /u/your_username)"
        }
    }
}
```

### Configuration Validation with Pydantic

Configuration models ensure type safety and validation:

```python
# clients/config/gallery_dl_config.py
from pydantic import BaseModel, Field, SecretStr, validator
from typing import Optional, List, Dict, Any

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
    """Root gallery-dl configuration."""
    extractor: ExtractorConfig
    downloader: DownloaderConfig = DownloaderConfig()
```

### Configuration Loading and Merging

```python
# clients/aio_gallery_dl.py
class AsyncGalleryDL:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_file: Optional[Path] = None,
        cookies_file: Optional[Path] = None,
        cookies_from_browser: Optional[str] = None,
    ):
        self.config = config or {}
        self.config_file = config_file or Path("~/.gallery-dl.conf").expanduser()

        # Apply cookie settings
        if cookies_file:
            self.config.setdefault("extractor", {})["cookies"] = str(cookies_file)
        elif cookies_from_browser:
            self.config.setdefault("extractor", {})["cookies-from-browser"] = cookies_from_browser

    async def __aenter__(self) -> "AsyncGalleryDL":
        """Load and merge configuration on context entry."""
        # Load configuration file if it exists
        if self.config_file.exists():
            try:
                async with aiofiles.open(self.config_file, encoding="utf-8") as f:
                    file_config = json.loads(await f.read())

                # Validate configuration
                validated_config = GalleryDLConfig(**file_config)

                # Merge with instance config (instance config takes precedence)
                merged_config = self._merge_configs(validated_config.dict(), self.config)
                self.config = merged_config

                logger.debug(f"Loaded gallery-dl config from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading gallery-dl config: {e}")
                # Continue with instance config only

        return self

    def _merge_configs(self, file_config: Dict, instance_config: Dict) -> Dict:
        """Merge configuration dictionaries with instance config taking precedence."""
        import copy
        merged = copy.deepcopy(file_config)

        def deep_merge(base: Dict, override: Dict) -> Dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        return deep_merge(merged, instance_config)
```

## Implementation Strategy

### 1. Feature Flag Configuration

```python
# core/downloads/feature_flags.py
from boss_bot.core.env import BossSettings

class DownloadFeatureFlags:
    """Feature flags for download implementations."""

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
    def api_fallback_to_cli(self) -> bool:
        """Fallback to CLI if API fails."""
        return self.settings.download_api_fallback_to_cli
```

### 2. Strategy Pattern Implementation

```python
# strategies/base_strategy.py
from abc import ABC, abstractmethod
from typing import Union
from boss_bot.schemas.discord import MediaMetadata

class BaseDownloadStrategy(ABC):
    """Strategy interface for choosing download implementation."""

    @abstractmethod
    async def download(self, url: str, **kwargs) -> MediaMetadata:
        """Download using chosen strategy (CLI or API)."""
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        """Check if strategy supports URL."""
        pass

# strategies/twitter_strategy.py
class TwitterDownloadStrategy(BaseDownloadStrategy):
    """Strategy for Twitter downloads with CLI/API choice."""

    def __init__(self, feature_flags: DownloadFeatureFlags, download_dir: Path):
        self.feature_flags = feature_flags
        self.download_dir = download_dir

        # ✅ Keep existing handler (no changes)
        self.cli_handler = TwitterHandler(download_dir=download_dir)

        # 🆕 New API client (lazy loaded)
        self._api_client = None

    @property
    def api_client(self):
        """Lazy load API client only when needed."""
        if self._api_client is None:
            from boss_bot.core.downloads.clients import AsyncGalleryDL
            self._api_client = AsyncGalleryDL()
        return self._api_client

    async def download(self, url: str, **kwargs) -> MediaMetadata:
        """Download using feature-flagged approach."""

        # Feature flag: choose implementation
        if self.feature_flags.use_api_twitter:
            try:
                return await self._download_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"API download failed, falling back to CLI: {e}")
                    return await self._download_via_cli(url, **kwargs)
                raise
        else:
            return await self._download_via_cli(url, **kwargs)

    async def _download_via_cli(self, url: str, **kwargs) -> MediaMetadata:
        """Use existing CLI handler (unchanged)."""
        # ✅ Call existing handler in executor to maintain async interface
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.cli_handler.download,
            url,
            **kwargs
        )

    async def _download_via_api(self, url: str, **kwargs) -> MediaMetadata:
        """Use new API client."""
        async with self.api_client as client:
            # Convert API response to MediaMetadata
            async for item in client.download(url, **kwargs):
                return self._convert_api_response(item)
```

### 3. API Client Implementation

Based on the [democracy-exe AsyncGalleryDL implementation](https://github.com/bossjones/democracy-exe/blob/3b486e50016858b479f46376c789034ab70d3a64/democracy_exe/clients/aio_gallery_dl.py), the API client would provide:

```python
# clients/aio_gallery_dl.py
class AsyncGalleryDL:
    """Asynchronous wrapper around gallery-dl.

    This class provides an async interface to gallery-dl operations,
    running them in a thread pool to avoid blocking the event loop.
    """

    def __init__(self, config: dict[str, Any] | None = None, **kwargs):
        self.config = config or {}
        # Configuration setup...

    async def extract_metadata(self, url: str) -> AsyncIterator[dict[str, Any]]:
        """Extract metadata from a URL asynchronously."""
        # Implementation using gallery_dl.extractor.find()

    async def download(self, url: str, **options) -> AsyncIterator[dict[str, Any]]:
        """Download content from URL asynchronously."""
        # Implementation using gallery_dl.job.DownloadJob()

    async def __aenter__(self) -> AsyncGalleryDL:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        pass
```

### 4. Sync/Async Compatibility Layer

```python
# clients/sync_adapters.py
import asyncio
from typing import Any, Dict
from boss_bot.schemas.discord import MediaMetadata

class SyncAsyncBridge:
    """Bridge between sync and async download implementations."""

    @staticmethod
    def run_async_download(strategy, url: str, **kwargs) -> MediaMetadata:
        """Run async download strategy in sync context."""
        try:
            loop = asyncio.get_running_loop()
            # We're already in an async context, just await
            raise RuntimeError("Should not call sync bridge from async context")
        except RuntimeError:
            # No running loop, create new one
            return asyncio.run(strategy.download(url, **kwargs))

    @staticmethod
    async def run_sync_download(handler, url: str, **kwargs) -> MediaMetadata:
        """Run sync handler in async context (existing pattern)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler.download, url, **kwargs)
```

## Feature Flag Configuration

### Environment Variables

Add to `BossSettings` in `core/env.py`:

```python
class BossSettings(BaseSettings):
    # ... existing settings ...

    # 🆕 NEW: Download strategy feature flags
    twitter_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for Twitter downloads"
    )
    reddit_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for Reddit downloads"
    )
    youtube_use_api_client: bool = Field(
        default=False,
        description="Use API-direct client for YouTube downloads"
    )
    download_api_fallback_to_cli: bool = Field(
        default=True,
        description="Fallback to CLI if API client fails"
    )
```

### Configuration Examples

```bash
# Enable API-direct for Twitter only
export TWITTER_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=true

# Enable API-direct for all platforms
export TWITTER_USE_API_CLIENT=true
export REDDIT_USE_API_CLIENT=true
export YOUTUBE_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=false
```

## Testing Strategy

### VCR/Pytest-Recording Integration

The API-direct approach enables [pytest-recording](https://github.com/kiwicom/pytest-recording) for capturing real API interactions:

```python
# tests/test_clients/test_aio_gallery_dl.py
import pytest
from boss_bot.core.downloads.clients import AsyncGalleryDL

@pytest.mark.asyncio
@pytest.mark.vcr  # Records real API calls to cassettes
async def test_twitter_api_download():
    """Test API-direct Twitter download with VCR."""
    async with AsyncGalleryDL() as client:
        items = []
        async for item in client.download("https://twitter.com/example/status/123"):
            items.append(item)

        assert len(items) > 0
        assert items[0]["extractor"] == "twitter"

# tests/test_strategies/test_twitter_strategy.py
@pytest.mark.asyncio
async def test_twitter_strategy_cli_mode(mock_settings):
    """Test strategy in CLI mode (existing behavior)."""
    mock_settings.twitter_use_api_client = False

    feature_flags = DownloadFeatureFlags(mock_settings)
    strategy = TwitterDownloadStrategy(feature_flags, Path("/tmp"))

    # Should use CLI handler (existing code path)
    with patch.object(strategy.cli_handler, 'download') as mock_download:
        await strategy.download("https://twitter.com/test")
        mock_download.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.vcr  # 🆕 NEW: VCR for API testing
async def test_twitter_strategy_api_mode(mock_settings):
    """Test strategy in API mode (new behavior)."""
    mock_settings.twitter_use_api_client = True

    feature_flags = DownloadFeatureFlags(mock_settings)
    strategy = TwitterDownloadStrategy(feature_flags, Path("/tmp"))

    # Should use API client (new code path)
    result = await strategy.download("https://twitter.com/test")
    assert result.platform == "twitter"
```

### Test Structure

```
tests/test_core/test_downloads/
├── test_handlers/           # ✅ Existing CLI handler tests (unchanged)
├── test_clients/            # 🆕 NEW: API client tests with VCR
│   ├── test_aio_gallery_dl.py
│   ├── test_aio_yt_dlp.py
│   └── cassettes/          # VCR cassettes for pytest-recording
│       ├── test_twitter_api_download.yaml
│       └── test_reddit_api_download.yaml
├── test_strategies/         # 🆕 NEW: Strategy integration tests
│   ├── test_twitter_strategy.py
│   └── test_reddit_strategy.py
└── test_feature_flags/      # 🆕 NEW: Feature flag tests
    └── test_download_feature_flags.py
```

## Migration Path

### Phase 1: Infrastructure Setup
- [ ] Implement base strategy pattern
- [ ] Add feature flag configuration
- [ ] Create base client interfaces
- [ ] Update environment configuration

### Phase 2: Twitter API Implementation
- [ ] Implement `AsyncGalleryDL` client
- [ ] Create `TwitterDownloadStrategy`
- [ ] Add comprehensive test coverage with VCR
- [ ] Test with feature flags disabled (validate no regression)

### Phase 3: Reddit API Implementation
- [ ] Extend `AsyncGalleryDL` for Reddit
- [ ] Create `RedditDownloadStrategy`
- [ ] Add Reddit-specific test coverage
- [ ] Test strategy switching logic

### Phase 4: YouTube API Implementation
- [ ] Implement `AsyncYtDlp` client
- [ ] Create `YouTubeDownloadStrategy`
- [ ] Add yt-dlp specific configuration models
- [ ] Test video download scenarios

### Phase 5: Integration & Rollout
- [ ] Update Discord cog to use strategies
- [ ] Update CLI commands to use strategies
- [ ] Document configuration options
- [ ] Gradual rollout per platform via environment variables

### Phase 6: Advanced Features
- [ ] Implement caching layer for API responses
- [ ] Add metrics and monitoring for API vs CLI usage
- [ ] Performance benchmarking and optimization
- [ ] Advanced error handling and retry logic

## Benefits

### For Developers
- **Better Testing**: pytest-recording enables realistic test scenarios
- **Improved Debugging**: Direct Python stack traces instead of subprocess parsing
- **Performance**: Reduced subprocess overhead for high-volume downloads
- **Flexibility**: Choose optimal approach per platform

### For Users
- **Reliability**: Fallback mechanisms ensure downloads continue working
- **Performance**: Faster downloads through reduced overhead
- **Features**: Access to more detailed metadata and progress information
- **Stability**: Existing functionality remains unchanged

### For Operations
- **Monitoring**: Better observability into download operations
- **Configuration**: Fine-grained control over download strategies
- **Rollback**: Easy rollback via feature flags if issues arise
- **Scaling**: Better resource utilization in high-throughput scenarios

## Error Handling & Operational Considerations

### Error Handling Patterns

The API-direct approach implements robust error handling with automatic fallback:

```python
# strategies/base_strategy.py
async def download(self, url: str, **kwargs) -> MediaMetadata:
    """Download with error handling and fallback."""
    if self.feature_flags.use_api_client:
        try:
            return await self._download_via_api(url, **kwargs)
        except gallery_dl.exception.ExtractionError as e:
            logger.warning(f"Gallery-dl extraction failed: {e}")
            if self.feature_flags.api_fallback_to_cli:
                return await self._download_via_cli(url, **kwargs)
            raise
        except asyncio.TimeoutError as e:
            logger.error(f"API download timeout: {e}")
            if self.feature_flags.api_fallback_to_cli:
                return await self._download_via_cli(url, **kwargs)
            raise
        except Exception as e:
            logger.error(f"Unexpected API error: {e}")
            if self.feature_flags.api_fallback_to_cli:
                return await self._download_via_cli(url, **kwargs)
            raise
    else:
        return await self._download_via_cli(url, **kwargs)
```

### Security Considerations

- **Cookie Security**: Netscape format cookies are read-only and not exposed in logs
- **Secret Management**: API keys and passwords use Pydantic SecretStr for safe handling
- **Rate Limiting**: Configurable delays between requests to avoid platform bans
- **User Agent Rotation**: Configurable user agents to appear as legitimate browser traffic

### Performance Monitoring

Environment variables for performance tuning:

```python
# Performance-related settings
GALLERY_DL_RATE_LIMIT: int = 0          # Delay between requests (seconds)
GALLERY_DL_TIMEOUT: float = 30.0        # Request timeout
GALLERY_DL_RETRIES: int = 4             # Number of retries
GALLERY_DL_CONCURRENT_DOWNLOADS: int = 3 # Max concurrent downloads
```

## Risk Mitigation

1. **Feature Flags**: All new functionality is feature-flagged and disabled by default
2. **Fallback Strategy**: API failures automatically fallback to CLI approach
3. **Backward Compatibility**: Existing handlers remain unchanged and functional
4. **Incremental Rollout**: Enable per platform gradually
5. **Comprehensive Testing**: Both CLI and API paths are thoroughly tested
6. **Configuration Validation**: Pydantic ensures configuration correctness
7. **Graceful Degradation**: System continues working even if API clients fail

## Future Considerations

- **Caching Layer**: API responses could be cached for performance
- **Rate Limiting**: API clients can implement more sophisticated rate limiting
- **Batch Operations**: API approach enables batch processing of multiple URLs
- **Advanced Features**: Access to platform-specific APIs for enhanced metadata
- **Real-time Updates**: Potential for real-time download progress updates

---

**Note**: This document describes experimental features that are not yet implemented. The current production system continues to use the stable CLI-based approach described in the main documentation.
