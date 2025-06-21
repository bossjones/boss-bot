"""File type detection utilities."""

from enum import Enum
from pathlib import Path
from typing import Optional, Set


class MediaType(Enum):
    """Media file types."""

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """Detects and categorizes file types for compression."""

    def __init__(self) -> None:
        """Initialize with supported file extensions."""
        self.video_extensions: set[str] = {
            "mp4",
            "avi",
            "mkv",
            "mov",
            "flv",
            "wmv",
            "webm",
            "mpeg",
            "3gp",
            "m4v",
            "mpg",
            "ogv",
        }

        self.audio_extensions: set[str] = {"mp3", "wav", "m4a", "flac", "aac", "ogg", "wma", "opus", "amr", "3ga"}

        self.image_extensions: set[str] = {
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp",
            "bmp",
            "tiff",
            "tif",
            "svg",
            "heic",
            "heif",
        }

    def get_media_type(self, file_path: Path) -> MediaType:
        """Determine the media type of a file.

        Args:
            file_path: Path to file

        Returns:
            MediaType enum value
        """
        extension = file_path.suffix.lower().lstrip(".")

        if extension in self.video_extensions:
            return MediaType.VIDEO
        elif extension in self.audio_extensions:
            return MediaType.AUDIO
        elif extension in self.image_extensions:
            return MediaType.IMAGE
        else:
            return MediaType.UNKNOWN

    def is_video_file(self, file_path: Path) -> bool:
        """Check if file is a video file.

        Args:
            file_path: Path to file

        Returns:
            True if file is a video
        """
        return self.get_media_type(file_path) == MediaType.VIDEO

    def is_audio_file(self, file_path: Path) -> bool:
        """Check if file is an audio file.

        Args:
            file_path: Path to file

        Returns:
            True if file is audio
        """
        return self.get_media_type(file_path) == MediaType.AUDIO

    def is_image_file(self, file_path: Path) -> bool:
        """Check if file is an image file.

        Args:
            file_path: Path to file

        Returns:
            True if file is an image
        """
        return self.get_media_type(file_path) == MediaType.IMAGE

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported for compression.

        Args:
            file_path: Path to file

        Returns:
            True if file type is supported
        """
        return self.get_media_type(file_path) != MediaType.UNKNOWN

    def get_supported_extensions(self, media_type: MediaType | None = None) -> set[str]:
        """Get supported file extensions.

        Args:
            media_type: Optional media type filter

        Returns:
            Set of supported extensions
        """
        if media_type == MediaType.VIDEO:
            return self.video_extensions.copy()
        elif media_type == MediaType.AUDIO:
            return self.audio_extensions.copy()
        elif media_type == MediaType.IMAGE:
            return self.image_extensions.copy()
        else:
            # Return all supported extensions
            return self.video_extensions | self.audio_extensions | self.image_extensions
