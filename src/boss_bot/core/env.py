"""Environment settings for the Boss-Bot application."""

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BossSettings(BaseSettings):
    """Settings for the Boss-Bot application.

    Attributes:
        discord_token: Discord bot token
        discord_client_id: Discord client ID
        discord_server_id: Discord server ID
        discord_admin_user_id: Discord admin user ID
        discord_admin_user_invited: Whether the admin user has been invited
        enable_ai: Whether AI features are enabled
        enable_redis: Whether Redis is enabled
        enable_sentry: Whether Sentry is enabled
        sentry_dsn: Sentry DSN
        openai_api_key: OpenAI API key
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
    discord_client_id: int = Field(..., description="Discord client ID", validation_alias="DISCORD_CLIENT_ID")
    discord_server_id: int = Field(..., description="Discord server ID", validation_alias="DISCORD_SERVER_ID")
    discord_admin_user_id: int = Field(
        ..., description="Discord admin user ID", validation_alias="DISCORD_ADMIN_USER_ID"
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

    @field_validator("discord_token")
    def validate_discord_token(cls, v: SecretStr) -> SecretStr:
        """Validate Discord token format."""
        token = v.get_secret_value()
        if not token.startswith("test_token") and not token.startswith("Bot "):
            raise ValueError("Invalid Discord token format")
        return v

    @field_validator("openai_api_key")
    def validate_openai_key(cls, v: SecretStr) -> SecretStr:
        """Validate OpenAI API key format."""
        if not v.get_secret_value().startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("sentry_dsn")
    def validate_sentry_dsn(cls, v: str | None) -> str | None:
        """Convert empty string to None for sentry_dsn."""
        if not v:
            return None
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
            f"openai_api_key=SecretStr('**********'))"
        )
