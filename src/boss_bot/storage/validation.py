"""Storage validation utilities for the boss-bot application."""

import os
from pathlib import Path
from typing import List, Optional, Tuple

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
