"""Test secure exception handling functionality."""

import os
import sys
import pytest
from pydantic import SecretStr

from boss_bot.monitoring.exceptions import (
    init_secure_exceptions,
    is_secure_exceptions_active,
    BossBotSecureExceptionFormatter,
    get_boss_bot_sensitive_filters,
    format_exception_secure,
)


def test_secure_exception_formatter_with_secretstr():
    """Test that SecretStr values are properly filtered."""
    # Create a formatter
    formatter = BossBotSecureExceptionFormatter(
        colored=False,  # Disable colors for testing
        theme=None,
        max_length=128
    )

    # Test with a SecretStr
    secret = SecretStr("my-super-secret-password-12345")
    result = formatter.format_value(secret)
    print(f"SecretStr filtered: {result}")
    assert result == "'my-s...***REDACTED***'"

    # Test with a short SecretStr
    short_secret = SecretStr("abc")
    result = formatter.format_value(short_secret)
    print(f"Short SecretStr filtered: {result}")
    assert result == "'***REDACTED***'"


def test_boss_bot_specific_filters():
    """Test boss-bot specific sensitive data patterns."""
    formatter = BossBotSecureExceptionFormatter(
        colored=False,
        theme=None,
        max_length=128
    )

    # Test Discord token patterns
    discord_token = "ODgzNDI2NzQ1MjI3MjUzNzky.sample.token"
    result = formatter.format_value(discord_token)
    print(f"Discord token filtered: {result}")
    assert "***DISCORD_TOKEN_REDACTED***" in result

    # Test OpenAI API key
    openai_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
    result = formatter.format_value(openai_key)
    print(f"OpenAI key filtered: {result}")
    assert "***OPENAI_KEY_REDACTED***" in result

    # Test GitHub token
    github_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz123"
    result = formatter.format_value(github_token)
    print(f"GitHub token filtered: {result}")
    assert "***GITHUB_TOKEN_REDACTED***" in result

    # Test LangChain key
    langchain_key = "lsv2_abc123def456"
    result = formatter.format_value(langchain_key)
    print(f"LangChain key filtered: {result}")
    assert "***LANGCHAIN_KEY_REDACTED***" in result


def test_normal_values_not_filtered():
    """Test that normal values are not filtered."""
    formatter = BossBotSecureExceptionFormatter(
        colored=False,
        theme=None,
        max_length=128
    )

    # Test regular string
    regular = "not-a-secret"
    result = formatter.format_value(regular)
    print(f"Regular string: {result}")
    assert result == "'not-a-secret'"

    # Test number
    number = 12345
    result = formatter.format_value(number)
    print(f"Number: {result}")
    assert "12345" in result


def test_custom_filters():
    """Test custom filter configuration."""
    custom_filters = {
        "CustomData": lambda v: "'***CUSTOM_DATA***'",
        "BusinessInfo": lambda v: "'***BUSINESS_INFO***'"
    }

    formatter = BossBotSecureExceptionFormatter(
        colored=False,
        theme=None,
        max_length=128,
        sensitive_filter_config=custom_filters
    )

    class CustomData:
        def __init__(self, value):
            self.value = value
        def __repr__(self):
            return f"CustomData('{self.value}')"

    class BusinessInfo:
        def __init__(self, info):
            self.info = info
        def __repr__(self):
            return f"BusinessInfo('{self.info}')"

    # Test custom filters (using names that won't conflict with boss-bot filters)
    data = CustomData("my-custom-data")
    result = formatter.format_value(data)
    print(f"Custom CustomData filtered: {result}")
    assert result == "'***CUSTOM_DATA***'"

    info = BusinessInfo("sensitive-business-info")
    result = formatter.format_value(info)
    print(f"Custom BusinessInfo filtered: {result}")
    assert result == "'***BUSINESS_INFO***'"


def test_get_boss_bot_sensitive_filters():
    """Test that boss-bot filters are properly defined."""
    filters = get_boss_bot_sensitive_filters()

    # Should have expected filter types
    expected_types = ["BossSettings", "DiscordToken", "APIKey", "DatabaseURL", "SentryDSN"]
    for expected_type in expected_types:
        assert expected_type in filters
        assert callable(filters[expected_type])


def test_init_secure_exceptions_without_env_var():
    """Test init_secure_exceptions when BETTER_EXCEPTIONS is not set."""
    # Make sure BETTER_EXCEPTIONS is not set
    old_value = os.environ.pop('BETTER_EXCEPTIONS', None)

    try:
        result = init_secure_exceptions()
        assert result is False  # Should return False when env var not set
    finally:
        # Restore original value if it existed
        if old_value is not None:
            os.environ['BETTER_EXCEPTIONS'] = old_value


def test_init_secure_exceptions_with_env_var():
    """Test init_secure_exceptions when BETTER_EXCEPTIONS is set."""
    # Set the environment variable
    old_value = os.environ.get('BETTER_EXCEPTIONS')
    os.environ['BETTER_EXCEPTIONS'] = '1'

    try:
        result = init_secure_exceptions()
        # Should return True if better_exceptions is available, False if not
        # We can't guarantee better_exceptions is available in all test environments
        assert isinstance(result, bool)
    finally:
        # Restore original value
        if old_value is not None:
            os.environ['BETTER_EXCEPTIONS'] = old_value
        else:
            os.environ.pop('BETTER_EXCEPTIONS', None)


def test_format_exception_secure():
    """Test the format_exception_secure function."""
    try:
        # Create a situation with sensitive data
        secret_password = SecretStr("super-secret-password-123")
        api_key = "sk-test123456789"

        # Trigger an exception
        result = 1 / 0
    except Exception:
        exc_info = sys.exc_info()

        # Format with secure filtering
        formatted_lines = format_exception_secure(*exc_info)

        # Should get a list of formatted lines
        assert isinstance(formatted_lines, list)
        assert len(formatted_lines) > 0

        # Join and check content
        formatted_text = ''.join(formatted_lines)
        print("Formatted exception output:")
        print(formatted_text)

        # Should contain the division error info
        assert "ZeroDivisionError" in formatted_text or "division" in formatted_text.lower()


def test_exception_handler_detection_in_pytest():
    """Test what exception handler is active during pytest."""
    current_hook = sys.excepthook
    original_hook = sys.__excepthook__

    print(f"\nCurrent hook: {current_hook}")
    print(f"Module: {getattr(current_hook, '__module__', 'N/A')}")
    print(f"Name: {getattr(current_hook, '__name__', 'N/A')}")

    # Check if better_exceptions is active (should be in pytest due to conftest.py)
    try:
        import better_exceptions
        is_better_exceptions = 'better_exceptions' in getattr(current_hook, '__module__', '')
        print(f"better_exceptions active: {is_better_exceptions}")

        # If better_exceptions is active, our secure handler should also be possible
        if is_better_exceptions:
            print("✅ better_exceptions is active - secure filtering should work")
        else:
            print("ℹ️ better_exceptions not active - secure filtering not applicable")

    except ImportError:
        print("better_exceptions not available")

    # Always pass - this is informational
    assert True
