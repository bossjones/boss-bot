"""Tests for the logging configuration module."""
import sys
from pathlib import Path
import pytest
from loguru import logger
from boss_bot.monitoring.logging import LogConfig

def test_log_config_initialization():
    """Test that LogConfig initializes with default values."""
    config = LogConfig()
    assert config.LOGGER_NAME == "boss_bot"
    assert "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>" in config.LOG_FORMAT
    assert config.LOG_LEVEL == "INFO"
    assert isinstance(config.LOG_FILE_PATH, Path)

def test_log_config_custom_values(tmp_path):
    """Test that LogConfig accepts custom values."""
    config = LogConfig(
        LOGGER_NAME="test",
        LOG_FORMAT="simple",
        LOG_LEVEL="DEBUG",
        LOG_FILE_PATH=tmp_path / "test.log"
    )
    assert config.LOGGER_NAME == "test"
    assert config.LOG_FORMAT == "simple"
    assert config.LOG_LEVEL == "DEBUG"
    assert config.LOG_FILE_PATH == tmp_path / "test.log"

def test_log_config_setup_creates_directory(tmp_path):
    """Test that setup_logging creates log directory if it doesn't exist."""
    log_path = tmp_path / "logs" / "test.log"
    config = LogConfig(LOG_FILE_PATH=log_path)
    config.setup_logging()
    assert log_path.parent.exists()

def test_log_config_setup_configures_handlers(tmp_path):
    """Test that setup_logging configures the correct handlers."""
    # Remove all handlers before test
    logger.remove()

    log_path = tmp_path / "logs" / "test.log"
    config = LogConfig(LOG_FILE_PATH=log_path)
    config.setup_logging()

    # Get all handlers IDs
    handler_ids = logger._core.handlers.keys()
    assert len(handler_ids) >= 2  # At least file and stderr handlers

def test_log_config_setup_file_handler_config(tmp_path):
    """Test that file handler is configured correctly."""
    logger.remove()

    log_path = tmp_path / "logs" / "test.log"
    config = LogConfig(LOG_FILE_PATH=log_path)
    config.setup_logging()

    # Write a test message
    test_message = "Test log message"
    logger.info(test_message)

    # Verify message was written to file
    assert log_path.exists()
    log_content = log_path.read_text()
    assert test_message in log_content

def test_log_config_setup_stderr_handler_config(capsys):
    """Test that stderr handler is configured correctly."""
    logger.remove()

    config = LogConfig()
    config.setup_logging()

    # Write a test message
    test_message = "Test log message"
    logger.info(test_message)

    # Check that message was written to stderr
    captured = capsys.readouterr()
    assert test_message in captured.err

def test_log_config_setup_removes_default_handler():
    """Test that setup_logging removes the default handler."""
    logger.remove()

    # Add a default handler
    default_id = logger.add(sys.stderr)

    config = LogConfig()
    config.setup_logging()

    # Check that default handler was removed
    assert default_id not in logger._core.handlers

@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_log_config_different_levels(tmp_path, log_level):
    """Test that log level is properly set for all handlers."""
    logger.remove()

    log_path = tmp_path / "logs" / "test.log"
    config = LogConfig(LOG_LEVEL=log_level, LOG_FILE_PATH=log_path)
    config.setup_logging()

    # Check all handlers have correct level
    for handler_id, handler_info in logger._core.handlers.items():
        assert handler_info._levelno == logger.level(log_level).no
