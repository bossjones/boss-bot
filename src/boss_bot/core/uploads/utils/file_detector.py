"""Media file detection and categorization utilities."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import List

from loguru import logger

from boss_bot.core.uploads.models import MediaFile, MediaType


class MediaFileDetector:
    """Detects and categorizes media files."""

    def __init__(self):
        self.video_extensions = {
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".flv",
            ".wmv",
            ".webm",
            ".mpeg",
            ".3gp",
            ".m4v",
            ".ogv",
            ".ts",
        }
        self.audio_extensions = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma", ".opus", ".aiff", ".au"}
        self.image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".svg", ".ico"}

    async def find_media_files(self, directory: Path) -> list[MediaFile]:
        """Find all media files in directory recursively.

        Args:
            directory: Directory to search for media files

        Returns:
            List of MediaFile objects found in the directory
        """
        logger.debug(f"Starting media file search in directory: {directory}")
        media_files = []

        if not directory.exists() or not directory.is_dir():
            logger.debug(f"Directory does not exist or is not a directory: {directory}")
            return media_files

        logger.debug(f"Recursively searching for media files in: {directory}")
        for file_path in directory.rglob("*"):
            if file_path.is_file() and self._is_media_file(file_path):
                logger.debug(f"Found media file: {file_path}")
                media_type = self._determine_media_type(file_path)

                try:
                    file_size = file_path.stat().st_size
                    media_file = MediaFile(
                        path=file_path, filename=file_path.name, size_bytes=file_size, media_type=media_type
                    )
                    media_files.append(media_file)
                    logger.debug(f"Added media file: {file_path.name} ({media_type.value}, {file_size} bytes)")
                except OSError as e:
                    logger.warning(f"Could not access file {file_path}: {e}")
                    continue

        logger.debug(f"Found {len(media_files)} media files in {directory}")
        return media_files

    def _is_media_file(self, file_path: Path) -> bool:
        """Check if file is a media file based on extension.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file is a media file, False otherwise
        """
        suffix = file_path.suffix.lower()
        is_media = suffix in self.video_extensions or suffix in self.audio_extensions or suffix in self.image_extensions
        logger.trace(f"Checking if {file_path.name} is media file: {is_media} (extension: {suffix})")
        return is_media

    def _determine_media_type(self, file_path: Path) -> MediaType:
        """Determine the type of media file based on extension.

        Args:
            file_path: Path to the file to analyze

        Returns:
            MediaType enum value
        """
        suffix = file_path.suffix.lower()

        if suffix in self.video_extensions:
            media_type = MediaType.VIDEO
        elif suffix in self.audio_extensions:
            media_type = MediaType.AUDIO
        elif suffix in self.image_extensions:
            media_type = MediaType.IMAGE
        else:
            media_type = MediaType.UNKNOWN

        logger.trace(f"Determined media type for {file_path.name}: {media_type.value} (extension: {suffix})")
        return media_type

    def filter_by_type(self, media_files: list[MediaFile], media_type: MediaType) -> list[MediaFile]:
        """Filter media files by type.

        Args:
            media_files: List of media files to filter
            media_type: Type to filter by

        Returns:
            Filtered list containing only files of the specified type
        """
        filtered_files = [f for f in media_files if f.media_type == media_type]
        logger.debug(f"Filtered {len(media_files)} files by type {media_type.value}: {len(filtered_files)} matches")
        return filtered_files

    def get_total_size(self, media_files: list[MediaFile]) -> int:
        """Calculate total size of media files in bytes.

        Args:
            media_files: List of media files

        Returns:
            Total size in bytes
        """
        total_size = sum(f.size_bytes for f in media_files)
        logger.debug(f"Calculated total size for {len(media_files)} files: {total_size} bytes")
        return total_size
