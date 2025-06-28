"""Secure exception handling configuration for boss-bot.

This module provides secure exception formatting that automatically filters
sensitive data like Pydantic SecretStr values and boss-bot specific secrets.
It extends better_exceptions with custom filtering while preserving all
original functionality.

Usage:
    from boss_bot.monitoring.exceptions import init_secure_exceptions
    init_secure_exceptions()  # Call after imports to configure filtering
"""

import os
import sys
from collections.abc import Callable
from typing import Any, Dict

try:
    from better_exceptions import CAP_CHAR, PIPE_CHAR, STREAM, SUPPORTS_COLOR, THEME, ExceptionFormatter, write_stream

    _BETTER_EXCEPTIONS_AVAILABLE = True
except ImportError:
    _BETTER_EXCEPTIONS_AVAILABLE = False


class BossBotSecureExceptionFormatter(ExceptionFormatter):
    """Custom formatter that filters sensitive data from boss-bot exceptions.

    This formatter automatically detects and filters:
    - Pydantic SecretStr values (shows first 4 chars + ...***REDACTED***)
    - Boss-bot specific sensitive types (Discord tokens, API keys, etc.)
    - Custom configured sensitive data types

    All other better_exceptions functionality is preserved.
    """

    def __init__(self, *args, **kwargs):
        """Initialize with optional sensitive filter configuration."""
        # Extract our custom config
        self.sensitive_filter_config = kwargs.pop("sensitive_filter_config", {})
        super().__init__(*args, **kwargs)

    def format_value(self, v: Any) -> str:
        """Override to filter sensitive values while preserving normal formatting."""
        # Get type information
        type_name = type(v).__name__
        module = getattr(type(v), "__module__", "")

        # Filter Pydantic SecretStr automatically
        if "pydantic" in module and "Secret" in type_name:
            return self._format_secret_str(v, type_name)

        # Check boss-bot specific filters
        boss_bot_filter = self._check_boss_bot_filters(v, type_name, module)
        if boss_bot_filter:
            return boss_bot_filter

        # Check custom filters from config
        custom_filter = self._check_custom_filters(v, type_name, module)
        if custom_filter:
            return custom_filter

        # Default formatting for non-sensitive values
        return super().format_value(v)

    def _format_secret_str(self, v: Any, type_name: str) -> str:
        """Format Pydantic SecretStr values securely."""
        try:
            # Get the secret value
            str_val = str(v.get_secret_value() if hasattr(v, "get_secret_value") else v)
            if len(str_val) > 4:
                return f"'{str_val[:4]}...***REDACTED***'"
            return "'***REDACTED***'"
        except Exception:
            return f"<{type_name} ***REDACTED***>"

    def _check_boss_bot_filters(self, v: Any, type_name: str, module: str) -> str | None:
        """Check for boss-bot specific sensitive data patterns."""
        str_val = str(v)

        # Discord token pattern
        if "discord" in str_val.lower() or str_val.startswith(("Bot ", "ODg", "MTA", "MTI")):
            if len(str_val) > 8:
                return f"'Bot {str_val[:4]}...***DISCORD_TOKEN_REDACTED***'"
            return "'***DISCORD_TOKEN_REDACTED***'"

        # OpenAI API key pattern
        if str_val.startswith("sk-"):
            return f"'{str_val[:7]}...***OPENAI_KEY_REDACTED***'"

        # Generic API key patterns
        if any(keyword in str_val.lower() for keyword in ["api_key", "api-key", "apikey"]):
            if len(str_val) > 8:
                return f"'{str_val[:4]}...***API_KEY_REDACTED***'"
            return "'***API_KEY_REDACTED***'"

        # LangChain patterns
        if any(pattern in str_val for pattern in ["lsv2_", "ls__"]):
            return f"'{str_val[:8]}...***LANGCHAIN_KEY_REDACTED***'"

        # GitHub token patterns
        if str_val.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_")):
            return f"'{str_val[:8]}...***GITHUB_TOKEN_REDACTED***'"

        # Generic secret patterns in variable names or string content
        if any(keyword in type_name.lower() for keyword in ["secret", "token", "key", "password"]):
            if len(str_val) > 6:
                return f"'{str_val[:3]}...***SECRET_REDACTED***'"
            return "'***SECRET_REDACTED***'"

        return None

    def _check_custom_filters(self, v: Any, type_name: str, module: str) -> str | None:
        """Check custom filters from configuration."""
        for filter_type, filter_func in self.sensitive_filter_config.items():
            if filter_type in type_name or filter_type in module:
                try:
                    return filter_func(v)
                except Exception:
                    return f"<{type_name} ***FILTERED***>"
        return None


def get_boss_bot_sensitive_filters() -> dict[str, Callable[[Any], str]]:
    """Get default sensitive data filters for boss-bot specific types.

    Returns:
        Dictionary mapping type names to filter functions
    """
    return {
        # Boss-bot specific custom types (can be extended)
        "BossSettings": lambda v: "'***BOSS_SETTINGS_REDACTED***'",
        "DiscordToken": lambda v: "'***DISCORD_TOKEN***'",
        "APIKey": lambda v: f"'{str(v)[:6]}...***API_KEY***'" if len(str(v)) > 6 else "'***API_KEY***'",
        "DatabaseURL": lambda v: "'***DATABASE_URL***'",
        "SentryDSN": lambda v: "'***SENTRY_DSN***'",
    }


def format_exception_secure(exc, value, tb, sensitive_filter_config=None):
    """Format exception with sensitive data filtering.

    Args:
        exc: Exception type
        value: Exception value
        tb: Traceback object
        sensitive_filter_config: Optional custom filter configuration

    Returns:
        List of formatted exception lines with sensitive data filtered
    """
    if not _BETTER_EXCEPTIONS_AVAILABLE:
        # Fallback to standard traceback if better_exceptions not available
        import traceback

        return traceback.format_exception(exc, value, tb)

    # Combine boss-bot filters with custom ones
    combined_filters = get_boss_bot_sensitive_filters()
    if sensitive_filter_config:
        combined_filters.update(sensitive_filter_config)

    formatter = BossBotSecureExceptionFormatter(
        colored=SUPPORTS_COLOR,
        theme=THEME,
        max_length=128,
        pipe_char=PIPE_CHAR,
        cap_char=CAP_CHAR,
        sensitive_filter_config=combined_filters,
    )
    return list(formatter.format_exception(exc, value, tb))


def _secure_excepthook(exc, value, tb):
    """Exception hook that filters sensitive data."""
    formatted = "".join(format_exception_secure(exc, value, tb))
    write_stream(formatted, STREAM)


def init_secure_exceptions(custom_filters: dict[str, Callable[[Any], str]] | None = None) -> bool:
    """Initialize secure exception handling if better_exceptions is enabled.

    This function:
    1. Checks if BETTER_EXCEPTIONS environment variable is set
    2. Verifies better_exceptions is available
    3. Installs secure exception hook with filtering
    4. Preserves all better_exceptions functionality

    Args:
        custom_filters: Optional additional filters beyond boss-bot defaults

    Returns:
        True if secure exceptions were configured, False otherwise
    """
    # Only configure if BETTER_EXCEPTIONS is enabled
    if "BETTER_EXCEPTIONS" not in os.environ:
        return False

    if not _BETTER_EXCEPTIONS_AVAILABLE:
        # better_exceptions not available, can't configure
        return False

    # Combine default boss-bot filters with any custom ones
    combined_filters = get_boss_bot_sensitive_filters()
    if custom_filters:
        combined_filters.update(custom_filters)

    # Create closure with the filters
    def _secure_excepthook_with_config(exc, value, tb):
        formatted = "".join(format_exception_secure(exc, value, tb, combined_filters))
        write_stream(formatted, STREAM)

    # Install our secure exception hook
    sys.excepthook = _secure_excepthook_with_config

    return True


def is_secure_exceptions_active() -> bool:
    """Check if secure exception handling is currently active.

    Returns:
        True if secure exceptions are configured and active
    """
    if not _BETTER_EXCEPTIONS_AVAILABLE:
        return False

    # Check if our custom hook is installed
    current_hook = sys.excepthook
    return (hasattr(current_hook, "__name__") and "_secure_excepthook" in current_hook.__name__) or (
        hasattr(current_hook, "__closure__") and current_hook.__closure__ is not None
    )
