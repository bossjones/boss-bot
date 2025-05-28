"""Pydantic configuration models for gallery-dl."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, SecretStr, field_validator


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
    twitter: TwitterConfig = TwitterConfig()
    reddit: RedditConfig = RedditConfig()

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
    """Root gallery-dl configuration."""

    extractor: ExtractorConfig = ExtractorConfig()
    downloader: DownloaderConfig = DownloaderConfig()
    output: OutputConfig = OutputConfig()

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> GalleryDLConfig:
        """Create configuration from dictionary."""
        return cls(**config_dict)

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
