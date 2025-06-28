"""Pydantic models for LangGraph assistant management.

This module provides comprehensive data models for managing LangGraph assistants,
including configuration validation, YAML serialization, and runtime management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class PlatformType(str, Enum):
    """Supported social media platforms."""

    YOUTUBE = "youtube"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    GENERIC = "generic"


class QualityLevel(str, Enum):
    """Download quality levels."""

    LOW = "low"
    GOOD = "good"
    HIGH = "high"
    BEST = "best"


class AssistantStatus(str, Enum):
    """Assistant runtime status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    INITIALIZING = "initializing"


class AIConfiguration(BaseModel):
    """AI model and behavior configuration.

    Attributes:
        enable_ai_strategy_selection: Whether to use AI for strategy selection
        enable_content_analysis: Whether to enable content analysis
        ai_model: AI model to use (e.g., "gpt-4", "claude-3")
        ai_temperature: Temperature for AI model responses (0.0-1.0)
        ai_max_tokens: Maximum tokens for AI responses
        ai_timeout_seconds: Timeout for AI requests in seconds
    """

    enable_ai_strategy_selection: bool = Field(default=True, description="Enable AI-powered strategy selection")
    enable_content_analysis: bool = Field(default=True, description="Enable AI content analysis before download")
    ai_model: str = Field(default="gpt-4", description="AI model identifier (e.g., 'gpt-4', 'claude-3')")
    ai_temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Temperature for AI model responses")
    ai_max_tokens: int = Field(default=1000, gt=0, description="Maximum tokens for AI responses")
    ai_timeout_seconds: int = Field(default=30, gt=0, description="Timeout for AI requests in seconds")

    @field_validator("ai_model")
    @classmethod
    def validate_ai_model(cls, v: str) -> str:
        """Validate AI model format."""
        if not v or not isinstance(v, str):
            raise ValueError("AI model must be a non-empty string")
        return v.strip().lower()


class DownloadConfiguration(BaseModel):
    """Download behavior configuration.

    Attributes:
        max_retries: Maximum number of download retries
        timeout_seconds: Download timeout in seconds
        download_quality: Overall download quality preference
        max_concurrent_downloads: Maximum concurrent downloads
        enable_fallback: Whether to fall back to traditional methods on AI failure
    """

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of download retries")
    timeout_seconds: int = Field(default=300, gt=0, le=3600, description="Download timeout in seconds")
    download_quality: QualityLevel = Field(default=QualityLevel.GOOD, description="Overall download quality preference")
    max_concurrent_downloads: int = Field(default=3, gt=0, le=10, description="Maximum concurrent downloads")
    enable_fallback: bool = Field(default=True, description="Fall back to traditional methods on AI failure")


class PlatformConfiguration(BaseModel):
    """Platform-specific configuration settings.

    Attributes:
        youtube_quality: YouTube video quality preference
        twitter_include_replies: Include Twitter thread replies
        instagram_include_stories: Include Instagram stories
        reddit_include_comments: Include Reddit comments
        generic_user_agent: User agent for generic downloads
    """

    youtube_quality: str = Field(default="720p", description="YouTube video quality (e.g., '720p', '1080p')")
    twitter_include_replies: bool = Field(default=False, description="Include replies when downloading Twitter threads")
    instagram_include_stories: bool = Field(
        default=True, description="Include stories when downloading Instagram content"
    )
    reddit_include_comments: bool = Field(default=False, description="Include comments when downloading Reddit posts")
    generic_user_agent: str = Field(
        default="Mozilla/5.0 (compatible; Boss-Bot/1.0)", description="User agent string for generic downloads"
    )

    @field_validator("youtube_quality")
    @classmethod
    def validate_youtube_quality(cls, v: str) -> str:
        """Validate YouTube quality format."""
        valid_qualities = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "best", "worst"]
        if v not in valid_qualities:
            raise ValueError(f"YouTube quality must be one of: {valid_qualities}")
        return v


class WorkflowConfiguration(BaseModel):
    """Workflow orchestration configuration.

    Attributes:
        enable_parallel_processing: Enable parallel agent execution
        max_workflow_duration_seconds: Maximum workflow execution time
        enable_detailed_logging: Enable detailed workflow logging
        checkpoint_interval_seconds: Interval for workflow checkpointing
    """

    enable_parallel_processing: bool = Field(
        default=True, description="Enable parallel execution of compatible workflow steps"
    )
    max_workflow_duration_seconds: int = Field(
        default=600, gt=0, le=3600, description="Maximum workflow execution time in seconds"
    )
    enable_detailed_logging: bool = Field(default=False, description="Enable detailed workflow execution logging")
    checkpoint_interval_seconds: int = Field(default=30, gt=0, description="Interval for workflow state checkpointing")


class AssistantMetadata(BaseModel):
    """Assistant metadata and statistics.

    Attributes:
        created_at: When the assistant was created
        updated_at: When the assistant was last updated
        version: Assistant configuration version
        total_requests: Total number of requests processed
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        average_response_time_seconds: Average response time
        last_used_at: When the assistant was last used
    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")
    total_requests: int = Field(default=0, ge=0)
    successful_requests: int = Field(default=0, ge=0)
    failed_requests: int = Field(default=0, ge=0)
    average_response_time_seconds: float = Field(default=0.0, ge=0.0)
    last_used_at: datetime | None = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        import re

        version_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
        if not re.match(version_pattern, v):
            raise ValueError("Version must follow semantic versioning (e.g., '1.0.0')")
        return v

    @model_validator(mode="after")
    def validate_request_counts(self) -> AssistantMetadata:
        """Validate that request counts are consistent."""
        if self.successful_requests + self.failed_requests > self.total_requests:
            raise ValueError("Sum of successful and failed requests cannot exceed total requests")
        return self


class AssistantConfig(BaseModel):
    """Complete assistant configuration model.

    This model represents the full configuration for a LangGraph assistant,
    including all settings that can be specified in YAML configuration files.

    Attributes:
        name: Human-readable assistant name
        description: Assistant description and purpose
        assistant_id: Unique identifier for the assistant
        graph_id: LangGraph workflow graph identifier
        ai: AI model and behavior configuration
        download: Download behavior configuration
        platforms: Platform-specific settings
        workflow: Workflow orchestration settings
        metadata: Assistant metadata and statistics
        tags: Optional tags for categorization
        enabled: Whether the assistant is currently enabled
    """

    name: str = Field(..., min_length=1, max_length=100, description="Human-readable assistant name")
    description: str = Field(..., min_length=1, max_length=500, description="Assistant description and purpose")
    assistant_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the assistant"
    )
    graph_id: str = Field(default="download_workflow", description="LangGraph workflow graph identifier")
    ai: AIConfiguration = Field(default_factory=AIConfiguration, description="AI model and behavior configuration")
    download: DownloadConfiguration = Field(
        default_factory=DownloadConfiguration, description="Download behavior configuration"
    )
    platforms: PlatformConfiguration = Field(
        default_factory=PlatformConfiguration, description="Platform-specific settings"
    )
    workflow: WorkflowConfiguration = Field(
        default_factory=WorkflowConfiguration, description="Workflow orchestration settings"
    )
    metadata: AssistantMetadata = Field(
        default_factory=AssistantMetadata, description="Assistant metadata and statistics"
    )
    tags: list[str] = Field(default_factory=list, description="Optional tags for categorization")
    enabled: bool = Field(default=True, description="Whether the assistant is currently enabled")

    @field_validator("assistant_id")
    @classmethod
    def validate_assistant_id(cls, v: str) -> str:
        """Validate assistant ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Assistant ID cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    def to_config_schema(self) -> dict[str, Any]:
        """Convert to ConfigSchema format for LangGraph workflow.

        Returns:
            Dictionary compatible with ConfigSchema from download_workflow.py
        """
        return {
            # AI Configuration
            "enable_ai_strategy_selection": self.ai.enable_ai_strategy_selection,
            "enable_content_analysis": self.ai.enable_content_analysis,
            "ai_model": self.ai.ai_model,
            "ai_temperature": self.ai.ai_temperature,
            # Download Configuration
            "max_retries": self.download.max_retries,
            "timeout_seconds": self.download.timeout_seconds,
            "download_quality": self.download.download_quality.value,
            # Platform Specific Settings
            "youtube_quality": self.platforms.youtube_quality,
            "twitter_include_replies": self.platforms.twitter_include_replies,
            "instagram_include_stories": self.platforms.instagram_include_stories,
            "reddit_include_comments": self.platforms.reddit_include_comments,
        }

    @classmethod
    def from_yaml_file(cls, file_path: Path | str) -> AssistantConfig:
        """Load assistant configuration from YAML file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            AssistantConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValidationError: If configuration is invalid
        """
        # Convert to Path if string
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise ValueError("Configuration file is empty")

            logger.info(f"Loaded assistant configuration from {path}")
            return cls.model_validate(data)

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            raise

    def to_yaml_file(self, file_path: Path | str, create_dirs: bool = True) -> None:
        """Save assistant configuration to YAML file.

        Args:
            file_path: Path where to save the configuration
            create_dirs: Whether to create parent directories if they don't exist

        Raises:
            OSError: If file cannot be written
        """
        # Convert to Path if string
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Update metadata before saving
            self.metadata.updated_at = datetime.utcnow()

            # Convert to dictionary and clean up for YAML
            data = self.model_dump(mode="json", exclude_none=True)

            # Convert datetime objects to ISO format strings
            if "metadata" in data:
                metadata = data["metadata"]
                for field in ["created_at", "updated_at", "last_used_at"]:
                    if metadata.get(field):
                        if isinstance(metadata[field], datetime):
                            metadata[field] = metadata[field].isoformat()

            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=False,
                    allow_unicode=True,
                )

            logger.info(f"Saved assistant configuration to {path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to {path}: {e}")
            raise

    def update_metadata(
        self,
        total_requests: int | None = None,
        successful_requests: int | None = None,
        failed_requests: int | None = None,
        response_time_seconds: float | None = None,
    ) -> None:
        """Update assistant usage metadata.

        Args:
            total_requests: New total request count
            successful_requests: New successful request count
            failed_requests: New failed request count
            response_time_seconds: Latest response time to include in average
        """
        now = datetime.utcnow()

        if total_requests is not None:
            self.metadata.total_requests = total_requests

        if successful_requests is not None:
            self.metadata.successful_requests = successful_requests

        if failed_requests is not None:
            self.metadata.failed_requests = failed_requests

        if response_time_seconds is not None:
            # Update rolling average response time
            current_avg = self.metadata.average_response_time_seconds
            total = self.metadata.total_requests

            if total > 0:
                # Calculate weighted average
                self.metadata.average_response_time_seconds = (
                    current_avg * (total - 1) + response_time_seconds
                ) / total
            else:
                self.metadata.average_response_time_seconds = response_time_seconds

        self.metadata.last_used_at = now
        self.metadata.updated_at = now


class Assistant(BaseModel):
    """Runtime assistant instance with configuration and state.

    This model represents an active assistant instance that can be used
    to execute workflows and manage runtime state.

    Attributes:
        config: Assistant configuration
        status: Current runtime status
        last_error: Last error message if status is ERROR
        created_at: When the instance was created
        session_id: Current session identifier
    """

    config: AssistantConfig = Field(..., description="Assistant configuration")
    status: AssistantStatus = Field(default=AssistantStatus.INITIALIZING, description="Current runtime status")
    last_error: str | None = Field(default=None, description="Last error message if status is ERROR")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the instance was created")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Current session identifier")

    @property
    def name(self) -> str:
        """Get assistant name."""
        return self.config.name

    @property
    def assistant_id(self) -> str:
        """Get assistant ID."""
        return self.config.assistant_id

    @property
    def is_healthy(self) -> bool:
        """Check if assistant is in a healthy state."""
        return self.status in [AssistantStatus.ACTIVE, AssistantStatus.INITIALIZING]

    @property
    def is_enabled(self) -> bool:
        """Check if assistant is enabled."""
        return self.config.enabled and self.is_healthy

    def activate(self) -> None:
        """Activate the assistant."""
        self.status = AssistantStatus.ACTIVE
        self.last_error = None
        logger.info(f"Assistant {self.name} activated")

    def deactivate(self) -> None:
        """Deactivate the assistant."""
        self.status = AssistantStatus.INACTIVE
        logger.info(f"Assistant {self.name} deactivated")

    def set_error(self, error_message: str) -> None:
        """Set assistant to error state.

        Args:
            error_message: Error description
        """
        self.status = AssistantStatus.ERROR
        self.last_error = error_message
        logger.error(f"Assistant {self.name} error: {error_message}")

    def record_request(
        self,
        success: bool,
        response_time_seconds: float,
        error_message: str | None = None,
    ) -> None:
        """Record a request execution.

        Args:
            success: Whether the request was successful
            response_time_seconds: Request execution time
            error_message: Error message if request failed
        """
        # Update metadata counters
        self.config.metadata.total_requests += 1

        if success:
            self.config.metadata.successful_requests += 1
        else:
            self.config.metadata.failed_requests += 1
            if error_message:
                self.set_error(error_message)

        # Update response time average
        self.config.update_metadata(response_time_seconds=response_time_seconds)

        logger.debug(f"Assistant {self.name} request recorded: success={success}, time={response_time_seconds:.2f}s")

    @classmethod
    def from_config_file(cls, file_path: Path) -> Assistant:
        """Create assistant instance from configuration file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            Assistant instance
        """
        config = AssistantConfig.from_yaml_file(file_path)
        assistant = cls(config=config)
        assistant.activate()
        return assistant

    def save_config(self, file_path: Path) -> None:
        """Save current configuration to file.

        Args:
            file_path: Path where to save the configuration
        """
        self.config.to_yaml_file(file_path)


# Helper functions for YAML operations


def load_assistant_configs(config_dir: Path) -> list[AssistantConfig]:
    """Load all assistant configurations from a directory.

    Args:
        config_dir: Directory containing YAML configuration files

    Returns:
        List of AssistantConfig instances
    """
    configs: list[AssistantConfig] = []

    if not config_dir.exists():
        logger.warning(f"Configuration directory does not exist: {config_dir}")
        return configs

    for yaml_file in config_dir.glob("*.yaml"):
        try:
            config = AssistantConfig.from_yaml_file(yaml_file)
            configs.append(config)
            logger.info(f"Loaded assistant config: {config.name} from {yaml_file}")
        except Exception as e:
            logger.error(f"Failed to load config from {yaml_file}: {e}")

    return configs


def save_assistant_configs(configs: list[AssistantConfig], config_dir: Path) -> None:
    """Save assistant configurations to a directory.

    Args:
        configs: List of AssistantConfig instances
        config_dir: Directory where to save configurations
    """
    config_dir.mkdir(parents=True, exist_ok=True)

    for config in configs:
        # Use assistant name as filename (sanitized)
        safe_name = "".join(c for c in config.name if c.isalnum() or c in "-_").lower()
        file_path = config_dir / f"{safe_name}.yaml"

        try:
            config.to_yaml_file(file_path)
            logger.info(f"Saved assistant config: {config.name} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save config {config.name}: {e}")


def create_default_assistant_config(
    name: str,
    description: str,
    **overrides: Any,
) -> AssistantConfig:
    """Create a default assistant configuration.

    Args:
        name: Assistant name
        description: Assistant description
        **overrides: Additional configuration overrides

    Returns:
        AssistantConfig instance with defaults
    """
    config_data = {
        "name": name,
        "description": description,
        **overrides,
    }

    return AssistantConfig.model_validate(config_data)
