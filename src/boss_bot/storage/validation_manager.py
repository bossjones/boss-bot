"""Storage validation utilities for the boss-bot application."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from pydantic import BaseModel


class FileValidationConfig(BaseModel):
    """File validation configuration."""

    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list[str] = [
        # Video formats
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webm",
        # Image formats
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        # Audio formats
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
    ]
    blocked_extensions: list[str] = [
        # Executable formats
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        # Script formats
        ".sh",
        ".bat",
        ".cmd",
        ".ps1",
        # Archive formats that might contain executables
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
    ]


class StorageValidator:
    """Storage validation utilities."""

    def __init__(self, config: FileValidationConfig | None = None) -> None:
        """Initialize storage validator."""
        self.config = config or FileValidationConfig()

    def validate_file_size(self, file_path: Path) -> tuple[bool, str]:
        """Validate file size."""
        try:
            size = os.path.getsize(file_path)
            if size > self.config.max_file_size:
                return (
                    False,
                    f"File size {size} bytes exceeds maximum allowed size of {self.config.max_file_size} bytes",
                )
            return True, ""
        except Exception as e:
            return False, f"Error checking file size: {e!s}"

    def validate_file_extension(self, file_path: Path) -> tuple[bool, str]:
        """Validate file extension."""
        extension = file_path.suffix.lower()

        if extension in self.config.blocked_extensions:
            return False, f"File extension {extension} is blocked"

        if extension not in self.config.allowed_extensions:
            return False, f"File extension {extension} is not allowed"

        return True, ""

    def validate_file_path(self, file_path: Path) -> tuple[bool, str]:
        """Validate file path."""
        try:
            # Check if path contains directory traversal attempts
            if ".." in str(file_path):
                return False, "Directory traversal detected in file path"

            # Check if path is absolute
            if file_path.is_absolute():
                return False, "Absolute paths are not allowed"

            return True, ""
        except Exception as e:
            return False, f"Error validating file path: {e!s}"

    def validate_file(self, file_path: Path) -> tuple[bool, list[str]]:
        """Validate file against all checks."""
        errors = []

        # Validate path
        path_valid, path_error = self.validate_file_path(file_path)
        if not path_valid:
            errors.append(path_error)

        # If file exists, validate size and extension
        if file_path.exists():
            size_valid, size_error = self.validate_file_size(file_path)
            if not size_valid:
                errors.append(size_error)

            ext_valid, ext_error = self.validate_file_extension(file_path)
            if not ext_valid:
                errors.append(ext_error)

        return len(errors) == 0, errors


# Create global storage validator
storage_validator = StorageValidator()


@dataclass
class ValidationResult:
    """Result of a file validation check."""

    is_valid: bool
    sanitized_name: str
    error_message: str = ""


class FileValidationError(Exception):
    """Raised when file validation fails."""

    pass


class FileValidator:
    """Validates and sanitizes files for storage."""

    # Allowed file extensions for media files
    ALLOWED_EXTENSIONS: set[str] = {
        # Video formats
        "mp4",
        "webm",
        "mkv",
        "avi",
        "mov",
        # Image formats
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        # Audio formats
        "mp3",
        "wav",
        "ogg",
        "flac",
    }

    # Characters not allowed in filenames
    FORBIDDEN_CHARS = r'[<>:"/\\|?*\$@]'  # Added @ to forbidden chars

    def __init__(self):
        """Initialize the file validator."""
        pass

    def is_valid_type(self, filename: str | Path) -> bool:
        """Check if the file type is allowed.

        Args:
            filename: Name or path of the file to check

        Returns:
            True if file type is allowed, False otherwise
        """
        ext = str(filename).split(".")[-1].lower()
        return ext in self.ALLOWED_EXTENSIONS

    def sanitize_filename(self, filename: str | Path) -> str:
        """Sanitize a filename to make it safe for storage.

        Args:
            filename: Name or path of the file to sanitize

        Returns:
            Sanitized filename
        """
        # Get just the filename if a path is provided
        filename = Path(filename).name

        # Convert to lowercase
        filename = filename.lower()

        # Replace forbidden characters with underscore
        filename = re.sub(self.FORBIDDEN_CHARS, "_", filename)

        # Replace spaces and multiple underscores with single underscore
        filename = re.sub(r"\s+", "_", filename)
        filename = re.sub(r"_+", "_", filename)

        # Remove leading/trailing underscores
        filename = filename.strip("_")

        return filename

    def has_path_traversal(self, filepath: str | Path) -> bool:
        """Check if a filepath contains path traversal attempts.

        Args:
            filepath: Path to check

        Returns:
            True if path traversal is detected, False otherwise
        """
        # Convert to Path and get parts
        path = Path(filepath)

        # Check for path traversal in parts
        return ".." in path.parts

    def validate_filename(self, filename: str | Path) -> None:
        """Validate a filename for security.

        Args:
            filename: Name or path of the file to validate

        Raises:
            FileValidationError: If the filename is invalid
        """
        path = Path(filename)

        # Check for path traversal
        if self.has_path_traversal(path):
            raise FileValidationError("Invalid characters in filename: path traversal not allowed")

        # Check for forbidden characters in the filename part
        if re.search(self.FORBIDDEN_CHARS, path.name):
            raise FileValidationError("Invalid characters in filename")

    def validate_file(self, filename: str | Path, size_mb: float) -> ValidationResult:
        """Validate a file for storage.

        Args:
            filename: Name or path of the file to validate
            size_mb: Size of the file in megabytes

        Returns:
            ValidationResult with validation status and sanitized name
        """
        try:
            # Check for path traversal first
            if self.has_path_traversal(filename):
                return ValidationResult(
                    is_valid=False,
                    sanitized_name="",
                    error_message="Invalid characters in filename: path traversal not allowed",
                )

            # Check file type
            if not self.is_valid_type(filename):
                return ValidationResult(is_valid=False, sanitized_name="", error_message="File type not allowed")

            # Check file size (50MB limit from story constraints)
            if size_mb > 50:
                return ValidationResult(
                    is_valid=False,
                    sanitized_name="",
                    error_message=f"File size {size_mb}MB exceeds maximum size of 50MB",
                )

            # Validate the original filename
            self.validate_filename(filename)

            # If validation passes, sanitize the filename
            sanitized = self.sanitize_filename(filename)

            return ValidationResult(is_valid=True, sanitized_name=sanitized)

        except FileValidationError as e:
            return ValidationResult(is_valid=False, sanitized_name="", error_message=str(e))
