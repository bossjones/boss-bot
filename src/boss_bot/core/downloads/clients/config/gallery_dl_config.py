"""Pydantic configuration models for gallery-dl."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, SecretStr, field_validator

from boss_bot.core.downloads.clients.aio_gallery_dl_utils import get_default_gallery_dl_config_locations

logger = logging.getLogger(__name__)


class TwitterConfig(BaseModel):
    """Twitter extractor configuration."""

    quoted: bool = True
    replies: bool = True
    retweets: bool = True
    videos: bool = True
    cookies: str | None = None
    filename: str = "{category}_{user[screen_name]}_{id}_{num}.{extension}"
    directory: list[str] = ["twitter", "{user[screen_name]}"]

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class InstagramConfig(BaseModel):
    """Instagram extractor configuration."""

    cookies: str | dict[str, str] | list[str] | None = ["firefox"]
    sleep_request: float | str = Field(default="6.0-12.0", alias="sleep-request")

    # Advanced options
    api: str = Field(default="rest", description="API mode: rest, graphql")
    cursor: bool = Field(default=True, description="Controls from which position to start the extraction process from.")
    include: str | list[str] = Field(default="all", description="Content types to include")
    max_posts: int | None = Field(None, alias="max-posts")
    metadata: bool = Field(default=False, description="Extract additional metadata")
    order_files: str = Field(default="asc", alias="order-files", description="File ordering")
    order_posts: str = Field(default="asc", alias="order-posts", description="Post ordering")
    previews: bool = Field(default=False, description="Download preview images")
    videos: bool = Field(default=True, description="Download videos")

    filename: str = "{category}_{user[username]}_{id}_{num}.{extension}"
    directory: list[str] = ["instagram", "{user[username]}"]

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class YouTubeConfig(BaseModel):
    """YouTube extractor configuration (via ytdl)."""

    enabled: bool = Field(default=False, description="Enable ytdl extractor")
    module: str = Field(default="yt_dlp", description="ytdl module to use")
    config_file: str | None = Field(None, alias="config-file")
    cmdline_args: list[str] | None = Field(None, alias="cmdline-args")
    format: str | None = Field(None, description="Video format selection")
    raw_options: dict[str, Any] | None = Field(None, alias="raw-options")

    filename: str = "{category}_{uploader}_{title}_{id}.{extension}"
    directory: list[str] = ["youtube", "{uploader}"]

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class PixivConfig(BaseModel):
    """Pixiv extractor configuration."""

    refresh_token: SecretStr | None = Field(None, alias="refresh-token")
    cookies: str | dict[str, str] | None = None

    # Content options
    captions: bool = Field(default=False, description="Download captions")
    comments: bool = Field(default=False, description="Download comments")
    include: list[str] = Field(default_factory=lambda: ["artworks"], description="Content types")
    max_posts: int | None = Field(None, alias="max-posts")
    metadata: bool = Field(default=False, description="Extract metadata")
    metadata_bookmark: bool = Field(default=False, alias="metadata-bookmark")
    sanity: bool = Field(default=True, description="Enable sanity checks")
    tags: str = Field(default="japanese", description="Tag language")
    ugoira: bool = Field(default=True, description="Download ugoira animations")

    filename: str = "{category}_{user[name]}_{id}_{num}.{extension}"
    directory: list[str] = ["pixiv", "{user[name]}"]

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class RedditConfig(BaseModel):
    """Reddit extractor configuration."""

    client_id: SecretStr | None = Field(None, alias="client-id")
    user_agent: str = Field(default="gallery-dl:boss-bot:1.0 (by /u/boss_bot)", alias="user-agent")
    comments: int = 0
    morecomments: bool = False
    videos: bool = True
    filename: str = "{category}_{subreddit}_{id}_{num}.{extension}"
    directory: list[str] = ["reddit", "{subreddit}"]

    @field_validator("user_agent")
    @classmethod
    def validate_user_agent(cls, v: str) -> str:
        """Validate user agent is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("User agent is required for Reddit")
        return v

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class DownloaderConfig(BaseModel):
    """Downloader configuration."""

    filesize_min: int | None = Field(None, alias="filesize-min")
    filesize_max: int | None = Field(None, alias="filesize-max")
    rate: int | None = None
    retries: int = 4
    timeout: float = 30.0
    verify: bool = True

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class ExtractorConfig(BaseModel):
    """Main extractor configuration."""

    base_directory: str = Field("./downloads/", alias="base-directory")
    archive: str | None = None
    cookies: str | None = None
    user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0", alias="user-agent"
    )

    # Platform-specific configurations
    twitter: TwitterConfig = TwitterConfig()
    reddit: RedditConfig = RedditConfig()
    instagram: InstagramConfig = InstagramConfig()
    youtube: YouTubeConfig = YouTubeConfig()
    pixiv: PixivConfig = PixivConfig()

    # Additional extractor features
    sleep: float | str = Field(default=0, description="Sleep between requests")
    sleep_request: float | str = Field(default=0, alias="sleep-request", description="Sleep between requests")
    sleep_extractor: float | str = Field(default=0, alias="sleep-extractor", description="Sleep between extractors")

    # Proxy settings
    proxy: str | None = None
    source_address: str | None = Field(None, alias="source-address", description="Bind to specific IP")

    # Cookie management
    cookies_from_browser: str | None = Field(None, alias="cookies-from-browser")
    cookies_update: bool = Field(default=True, alias="cookies-update")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class OutputConfig(BaseModel):
    """Output configuration."""

    mode: str = "auto"
    progress: bool = True
    log: str = "[{name}][{levelname}] {message}"

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class GalleryDLConfig(BaseModel):
    """Root gallery-dl configuration with comprehensive options."""

    extractor: ExtractorConfig = ExtractorConfig()
    downloader: DownloaderConfig = DownloaderConfig()
    output: OutputConfig = OutputConfig()

    # Enhanced configuration sections
    postprocessor: dict[str, Any] | None = None  # For flexible postprocessor configs
    cache: CacheConfig | None = None

    # Global filters and archive
    filter: FilterConfig | None = None
    archive: ArchiveConfig | None = None
    path: PathConfig | None = None
    proxy: ProxyConfig | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> GalleryDLConfig:
        """Create configuration from dictionary."""
        return cls(**config_dict)

    @classmethod
    def from_file(cls, override_config: str | Path | None = None) -> GalleryDLConfig:
        """Create configuration from file.

        Args:
            override_config: Optional path to configuration file. If not provided,
                           searches for config in default gallery-dl locations.

        Returns:
            GalleryDLConfig instance loaded from file.

        Raises:
            FileNotFoundError: If no configuration file is found.
            ValueError: If configuration file contains invalid JSON or data.
        """
        import json

        from boss_bot.core.downloads.clients.aio_gallery_dl_utils import get_default_gallery_dl_config_locations

        config_path: Path | None = None
        config_data: dict[str, Any] = {}

        if override_config:
            # Use provided config path
            config_path = Path(override_config)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
        else:
            # Search default locations
            config_locations = get_default_gallery_dl_config_locations()
            for potential_path in config_locations:
                if potential_path.exists():
                    config_path = potential_path
                    break

            if not config_path:
                # Return default configuration if no file found
                logger.info("No gallery-dl configuration file found in default locations. Using defaults.")
                return cls()

        try:
            with open(config_path, encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning(f"Configuration file is empty: {config_path}. Using defaults.")
                return cls()

            try:
                config_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}") from e

            if not isinstance(config_data, dict):
                raise ValueError(f"Configuration must be a JSON object, got {type(config_data).__name__}")

            logger.info(f"Loaded gallery-dl configuration from: {config_path}")
            return cls.from_dict(config_data)

        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"Error reading configuration file {config_path}: {e}") from e

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def merge_with(self, other_config: dict[str, Any]) -> GalleryDLConfig:
        """Merge with another configuration dictionary."""
        current_dict = self.to_dict()
        merged_dict = self._deep_merge(current_dict, other_config)
        return self.from_dict(merged_dict)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries with override taking precedence."""
        import copy

        merged = copy.deepcopy(base)

        def merge_recursive(base_dict: dict[str, Any], override_dict: dict[str, Any]) -> dict[str, Any]:
            for key, value in override_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    base_dict[key] = merge_recursive(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict

        return merge_recursive(merged, override)

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        validate_assignment = True


# Additional configuration classes for comprehensive gallery-dl support


class PostprocessorConfig(BaseModel):
    """Postprocessor configuration for various operations."""

    # Metadata postprocessor
    metadata: dict[str, Any] | None = None

    # Archive postprocessors
    zip: dict[str, Any] | None = None
    cbz: dict[str, Any] | None = None

    # Media conversion postprocessors
    ugoira: dict[str, Any] | None = None
    ffmpeg: dict[str, Any] | None = None

    # Content postprocessors
    content: dict[str, Any] | None = None
    exec: dict[str, Any] | None = None

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class FilterConfig(BaseModel):
    """Content filtering configuration."""

    # Image filters
    image_filter: str | None = Field(None, alias="image-filter")
    image_range: str | None = Field(None, alias="image-range")
    image_unique: bool = Field(default=False, alias="image-unique")

    # Chapter filters
    chapter_filter: str | None = Field(None, alias="chapter-filter")
    chapter_range: str | None = Field(None, alias="chapter-range")
    chapter_unique: bool = Field(default=False, alias="chapter-unique")

    # Size filters
    filesize_min: int | None = Field(None, alias="filesize-min")
    filesize_max: int | None = Field(None, alias="filesize-max")

    # Date filters
    date_min: int | str | None = Field(None, alias="date-min")
    date_max: int | str | None = Field(None, alias="date-max")
    date_format: str = Field(default="%Y-%m-%dT%H:%M:%S", alias="date-format")

    # Extension filters
    extension_map: dict[str, str] = Field(default_factory=dict, alias="extension-map")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class ArchiveConfig(BaseModel):
    """Archive configuration for duplicate detection."""

    archive: str | None = Field(None, description="Archive file path")
    archive_format: str | None = Field(None, alias="archive-format", description="Archive entry format")
    archive_prefix: str | None = Field(None, alias="archive-prefix", description="Archive entry prefix")
    archive_pragma: list[str] = Field(
        default_factory=list, alias="archive-pragma", description="SQLite PRAGMA statements"
    )
    archive_event: list[str] = Field(
        default_factory=lambda: ["file"], alias="archive-event", description="Events to archive"
    )
    archive_mode: str = Field(default="file", alias="archive-mode", description="Archive mode")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class PathConfig(BaseModel):
    """Path and filename configuration."""

    # Path handling
    path_restrict: str = Field(default="auto", alias="path-restrict", description="Path character restrictions")
    path_replace: str = Field(default="_", alias="path-replace", description="Replacement for invalid characters")
    path_remove: str = Field(default="\\u0000-\\u001f\\u007f", alias="path-remove", description="Characters to remove")
    path_strip: str = Field(default="auto", alias="path-strip", description="Characters to strip")
    path_extended: bool = Field(default=True, alias="path-extended", description="Enable extended path handling")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class ProxyConfig(BaseModel):
    """Proxy configuration."""

    proxy: str | None = None
    proxy_env: bool = Field(default=True, alias="proxy-env", description="Use environment proxy settings")
    source_address: str | None = Field(None, alias="source-address", description="Bind to specific IP")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class CacheConfig(BaseModel):
    """Cache configuration."""

    file: str | None = Field(None, description="Cache file path")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
