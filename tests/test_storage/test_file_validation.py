"""Tests for file validation functionality."""
import pytest
from pathlib import Path

from boss_bot.storage.validation import FileValidator, FileValidationError

def test_file_type_validation_allowed():
    """Test that allowed file types pass validation."""
    validator = FileValidator()

    # Test common media types that should be allowed
    assert validator.is_valid_type("video.mp4") is True
    assert validator.is_valid_type("image.jpg") is True
    assert validator.is_valid_type("image.png") is True
    assert validator.is_valid_type("audio.mp3") is True

def test_file_type_validation_forbidden():
    """Test that forbidden file types are rejected."""
    validator = FileValidator()

    # Test potentially dangerous file types
    assert validator.is_valid_type("script.exe") is False
    assert validator.is_valid_type("danger.sh") is False
    assert validator.is_valid_type("malware.bat") is False
    assert validator.is_valid_type("hack.py") is False

def test_filename_sanitization():
    """Test that filenames are properly sanitized."""
    validator = FileValidator()

    # Test various filename scenarios
    assert validator.sanitize_filename("my video.mp4") == "my_video.mp4"
    assert validator.sanitize_filename("../hack.mp4") == "hack.mp4"
    assert validator.sanitize_filename("$pecial@chars.jpg") == "pecial_chars.jpg"
    assert validator.sanitize_filename("spaces   here.png") == "spaces_here.png"
    assert validator.sanitize_filename("UPPER_CASE.MP4") == "upper_case.mp4"

def test_filename_security_checks():
    """Test that filenames pass security checks."""
    validator = FileValidator()

    # Test security validations
    with pytest.raises(FileValidationError, match="Invalid characters"):
        validator.validate_filename("../traversal.mp4")

    with pytest.raises(FileValidationError, match="Invalid characters"):
        validator.validate_filename("c:\\windows\\hack.mp4")

    with pytest.raises(FileValidationError, match="Invalid characters"):
        validator.validate_filename("$ecret.mp4")

    # Valid filenames should pass
    validator.validate_filename("normal_video.mp4")
    validator.validate_filename("my-image.jpg")
    validator.validate_filename("audio_2024.mp3")

def test_full_file_validation():
    """Test complete file validation process."""
    validator = FileValidator()

    # Test valid file
    result = validator.validate_file("my_video.mp4", size_mb=25)
    assert result.is_valid is True
    assert result.sanitized_name == "my_video.mp4"

    # Test invalid type
    result = validator.validate_file("script.exe", size_mb=1)
    assert result.is_valid is False
    assert "file type not allowed" in result.error_message.lower()

    # Test invalid size
    result = validator.validate_file("large_video.mp4", size_mb=75)
    assert result.is_valid is False
    assert "exceeds maximum size" in result.error_message.lower()

    # Test invalid name
    result = validator.validate_file("../hack.mp4", size_mb=10)
    assert result.is_valid is False
    assert "path traversal not allowed" in result.error_message.lower()

def test_validation_with_path():
    """Test validation with Path objects."""
    validator = FileValidator()

    # Test with relative path (should be allowed)
    path = Path("downloads/my_video.mp4")
    result = validator.validate_file(path, size_mb=25)
    assert result.is_valid is True
    assert result.sanitized_name == "my_video.mp4"

    # Test with path traversal (should be rejected)
    path = Path("user/downloads/../video.mp4")
    result = validator.validate_file(path, size_mb=25)
    assert result.is_valid is False
    assert "path traversal not allowed" in result.error_message.lower()
