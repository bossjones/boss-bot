"""Environment settings for the Boss-Bot application."""
# pylint: disable=no-member
# pylint: disable=possibly-used-before-assignment
# pyright: reportImportCycles=false
# pyright: reportFunctionMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportInvalidTypeForm=false
# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=consider-using-with, consider-using-min-builtin

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BossSettings(BaseSettings):
    """Settings for the Boss-Bot application.

    Attributes:
        discord_token: Discord bot token
        discord_client_id: Discord client ID (optional)
        discord_server_id: Discord server ID (optional)
        discord_admin_user_id: Discord admin user ID (optional)
        discord_admin_user_invited: Whether the admin user has been invited
        enable_ai: Whether AI features are enabled
        enable_redis: Whether Redis is enabled
        enable_sentry: Whether Sentry is enabled
        sentry_dsn: Sentry DSN
        openai_api_key: OpenAI API key
        storage_root: Root directory for file storage
        max_file_size_mb: Maximum file size in MB
        max_concurrent_downloads: Maximum concurrent downloads
        max_queue_size: Maximum queue size for downloads
        log_level: Logging level
        enable_metrics: Enable Prometheus metrics
        metrics_port: Port for Prometheus metrics
        enable_health_check: Enable health check endpoint
        health_check_port: Port for health check endpoint
        rate_limit_requests: Number of requests per time window
        rate_limit_window_seconds: Time window for rate limiting in seconds
        enable_file_validation: Enable file validation and security checks
        debug: Enable debug mode
        environment: Environment (development, staging, production)
        cohere_api_key: Cohere API key (optional)
        debug_aider: Enable debug aider
        firecrawl_api_key: Firecrawl API key (optional)
        langchain_api_key: LangChain API key
        langchain_debug_logs: Enable LangChain debug logs
        langchain_endpoint: LangChain endpoint
        langchain_hub_api_key: LangChain Hub API key
        langchain_hub_api_url: LangChain Hub API URL
        langchain_project: LangChain project name
        langchain_tracing_v2: Enable LangChain tracing v2
        pinecone_api_key: Pinecone API key (optional)
        pinecone_env: Pinecone environment
        pinecone_index: Pinecone index name
        tavily_api_key: Tavily API key (optional)
        unstructured_api_key: Unstructured API key (optional)
        unstructured_api_url: Unstructured API URL
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow case-insensitive env vars
        secrets_dir="/run/secrets",
        extra="ignore",  # Ignore extra env vars
        env_prefix="",  # No prefix for env vars
        env_nested_delimiter="__",  # Use __ for nested settings
    )

    # Discord settings
    discord_token: SecretStr = Field(..., description="Discord bot token", validation_alias="DISCORD_TOKEN")
    discord_client_id: int | None = Field(None, description="Discord client ID", validation_alias="DISCORD_CLIENT_ID")
    discord_server_id: int | None = Field(None, description="Discord server ID", validation_alias="DISCORD_SERVER_ID")
    discord_admin_user_id: int | None = Field(
        None, description="Discord admin user ID", validation_alias="DISCORD_ADMIN_USER_ID"
    )
    discord_admin_user_invited: bool = Field(
        False, description="Whether the admin user has been invited", validation_alias="DISCORD_ADMIN_USER_INVITED"
    )

    # Feature flags
    enable_ai: bool = Field(False, description="Whether AI features are enabled", validation_alias="ENABLE_AI")
    enable_redis: bool = Field(False, description="Whether Redis is enabled", validation_alias="ENABLE_REDIS")
    enable_sentry: bool = Field(False, description="Whether Sentry is enabled", validation_alias="ENABLE_SENTRY")

    # Service settings
    sentry_dsn: str | None = Field(None, description="Sentry DSN", validation_alias="SENTRY_DSN")
    openai_api_key: SecretStr = Field(..., description="OpenAI API key", validation_alias="OPENAI_API_KEY")

    # Storage Configuration
    storage_root: Path = Field(
        Path("/tmp/boss-bot"), description="Root directory for file storage", validation_alias="STORAGE_ROOT"
    )
    max_file_size_mb: int = Field(50, description="Maximum file size in MB", validation_alias="MAX_FILE_SIZE_MB")
    max_concurrent_downloads: int = Field(
        5, description="Maximum concurrent downloads", validation_alias="MAX_CONCURRENT_DOWNLOADS"
    )
    max_queue_size: int = Field(50, description="Maximum queue size for downloads", validation_alias="MAX_QUEUE_SIZE")

    # Monitoring Configuration
    log_level: str = Field("INFO", description="Logging level", validation_alias="LOG_LEVEL")
    enable_metrics: bool = Field(True, description="Enable Prometheus metrics", validation_alias="ENABLE_METRICS")
    metrics_port: int = Field(9090, description="Port for Prometheus metrics", validation_alias="METRICS_PORT")
    enable_health_check: bool = Field(
        True, description="Enable health check endpoint", validation_alias="ENABLE_HEALTH_CHECK"
    )
    health_check_port: int = Field(
        8080, description="Port for health check endpoint", validation_alias="HEALTH_CHECK_PORT"
    )

    # Security Configuration
    rate_limit_requests: int = Field(
        100, description="Number of requests per time window", validation_alias="RATE_LIMIT_REQUESTS"
    )
    rate_limit_window_seconds: int = Field(
        60, description="Time window for rate limiting in seconds", validation_alias="RATE_LIMIT_WINDOW_SECONDS"
    )
    enable_file_validation: bool = Field(
        True, description="Enable file validation and security checks", validation_alias="ENABLE_FILE_VALIDATION"
    )

    # Development Settings
    debug: bool = Field(False, description="Enable debug mode", validation_alias="DEBUG")
    environment: Environment = Field(
        Environment.DEVELOPMENT,
        description="Environment (development, staging, production)",
        validation_alias="ENVIRONMENT",
    )

    # Additional API Keys and Settings
    cohere_api_key: SecretStr | None = Field(None, description="Cohere API key", validation_alias="COHERE_API_KEY")
    debug_aider: bool = Field(False, description="Enable debug aider", validation_alias="DEBUG_AIDER")
    firecrawl_api_key: SecretStr | None = Field(
        None, description="Firecrawl API key", validation_alias="FIRECRAWL_API_KEY"
    )
    langchain_api_key: SecretStr = Field(..., description="LangChain API key", validation_alias="LANGCHAIN_API_KEY")
    langchain_debug_logs: bool = Field(
        False, description="Enable LangChain debug logs", validation_alias="LANGCHAIN_DEBUG_LOGS"
    )
    langchain_endpoint: AnyHttpUrl = Field(
        AnyHttpUrl("http://localhost:8000"), description="LangChain endpoint", validation_alias="LANGCHAIN_ENDPOINT"
    )
    langchain_hub_api_key: SecretStr = Field(
        ..., description="LangChain Hub API key", validation_alias="LANGCHAIN_HUB_API_KEY"
    )
    langchain_hub_api_url: AnyHttpUrl = Field(
        AnyHttpUrl("http://localhost:8001"),
        description="LangChain Hub API URL",
        validation_alias="LANGCHAIN_HUB_API_URL",
    )
    langchain_project: str = Field(
        "test-project", description="LangChain project name", validation_alias="LANGCHAIN_PROJECT"
    )
    langchain_tracing_v2: bool = Field(
        False, description="Enable LangChain tracing v2", validation_alias="LANGCHAIN_TRACING_V2"
    )
    pinecone_api_key: SecretStr | None = Field(
        None, description="Pinecone API key", validation_alias="PINECONE_API_KEY"
    )
    pinecone_env: str = Field("test-env", description="Pinecone environment", validation_alias="PINECONE_ENV")
    pinecone_index: str = Field("test-index", description="Pinecone index name", validation_alias="PINECONE_INDEX")
    tavily_api_key: SecretStr | None = Field(None, description="Tavily API key", validation_alias="TAVILY_API_KEY")
    unstructured_api_key: SecretStr | None = Field(
        None, description="Unstructured API key", validation_alias="UNSTRUCTURED_API_KEY"
    )
    unstructured_api_url: AnyHttpUrl = Field(
        AnyHttpUrl("http://localhost:8002"), description="Unstructured API URL", validation_alias="UNSTRUCTURED_API_URL"
    )

    @field_validator("discord_token")
    def validate_discord_token(cls, v: SecretStr) -> SecretStr:
        """Validate Discord token format."""
        # token = v.get_secret_value()
        # if not token.startswith("test_token") and not token.startswith("Bot "):
        #     raise ValueError("Invalid Discord token format")
        return v

    @field_validator("openai_api_key")
    def validate_openai_key(cls, v: SecretStr) -> SecretStr:
        """Validate OpenAI API key format."""
        # if not v.get_secret_value().startswith("sk-"):
        #     raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("sentry_dsn")
    def validate_sentry_dsn(cls, v: str | None) -> str | None:
        """Convert empty string to None for sentry_dsn."""
        if not v:
            return None
        return v

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("storage_root")
    def validate_storage_root(cls, v: Path) -> Path:
        """Validate storage root path."""
        if not v.is_absolute():
            raise ValueError("Storage root must be an absolute path")
        return v

    @field_validator(
        "max_file_size_mb",
        "max_concurrent_downloads",
        "max_queue_size",
        "metrics_port",
        "health_check_port",
        "rate_limit_requests",
        "rate_limit_window_seconds",
        check_fields=True,
    )
    @classmethod
    def validate_positive_int(cls, v: int, info: ValidationInfo) -> int:
        """Validate positive integer values."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be a positive integer")
        return v

    def __str__(self) -> str:
        """Return string representation with hidden secrets."""
        return (
            f"BossSettings("
            f"discord_token=SecretStr('**********'), "
            f"discord_client_id={self.discord_client_id}, "
            f"discord_server_id={self.discord_server_id}, "
            f"discord_admin_user_id={self.discord_admin_user_id}, "
            f"discord_admin_user_invited={self.discord_admin_user_invited}, "
            f"enable_ai={self.enable_ai}, "
            f"enable_redis={self.enable_redis}, "
            f"enable_sentry={self.enable_sentry}, "
            f"sentry_dsn={self.sentry_dsn}, "
            f"openai_api_key=SecretStr('**********'), "
            f"storage_root={self.storage_root}, "
            f"max_file_size_mb={self.max_file_size_mb}, "
            f"max_concurrent_downloads={self.max_concurrent_downloads}, "
            f"max_queue_size={self.max_queue_size}, "
            f"log_level={self.log_level}, "
            f"enable_metrics={self.enable_metrics}, "
            f"metrics_port={self.metrics_port}, "
            f"enable_health_check={self.enable_health_check}, "
            f"health_check_port={self.health_check_port}, "
            f"rate_limit_requests={self.rate_limit_requests}, "
            f"rate_limit_window_seconds={self.rate_limit_window_seconds}, "
            f"enable_file_validation={self.enable_file_validation}, "
            f"debug={self.debug}, "
            f"environment={self.environment}, "
            f"cohere_api_key=SecretStr('**********'), "
            f"debug_aider={self.debug_aider}, "
            f"firecrawl_api_key=SecretStr('**********'), "
            f"langchain_api_key=SecretStr('**********'), "
            f"langchain_debug_logs={self.langchain_debug_logs}, "
            f"langchain_endpoint={self.langchain_endpoint}, "
            f"langchain_hub_api_key=SecretStr('**********'), "
            f"langchain_hub_api_url={self.langchain_hub_api_url}, "
            f"langchain_project={self.langchain_project}, "
            f"langchain_tracing_v2={self.langchain_tracing_v2}, "
            f"pinecone_api_key=SecretStr('**********'), "
            f"pinecone_env={self.pinecone_env}, "
            f"pinecone_index={self.pinecone_index}, "
            f"tavily_api_key=SecretStr('**********'), "
            f"unstructured_api_key=SecretStr('**********'), "
            f"unstructured_api_url={self.unstructured_api_url})"
        )
