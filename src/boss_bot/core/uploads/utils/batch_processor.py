"""Batch processing utilities for Discord upload limits."""

from __future__ import annotations

from typing import List

from boss_bot.core.env import BossSettings
from boss_bot.core.uploads.models import MediaFile, UploadBatch


class BatchProcessor:
    """Processes media files into batches respecting Discord limits."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        # Discord's hard limits
        self.max_files_per_message = 10
        self.max_message_size_mb = 25.0

        # Configurable limits from settings
        self.preferred_batch_size_mb = getattr(settings, "upload_batch_size_mb", 20.0)
        self.preferred_max_files = min(getattr(settings, "upload_max_files_per_batch", 10), self.max_files_per_message)

    def create_batches(
        self, media_files: list[MediaFile], max_files: int = None, max_size_mb: float = None
    ) -> list[UploadBatch]:
        """Create upload batches respecting Discord limits.

        Args:
            media_files: List of media files to batch
            max_files: Maximum files per batch (uses default if None)
            max_size_mb: Maximum batch size in MB (uses default if None)

        Returns:
            List of UploadBatch objects ready for upload
        """
        if max_files is None:
            max_files = self.preferred_max_files
        if max_size_mb is None:
            max_size_mb = self.preferred_batch_size_mb

        # Ensure we don't exceed Discord's hard limits
        max_files = min(max_files, self.max_files_per_message)
        max_size_mb = min(max_size_mb, self.max_message_size_mb)

        batches = []
        current_batch_files = []
        current_batch_size = 0.0

        for media_file in media_files:
            file_size_mb = media_file.size_mb

            # Check if adding this file would exceed limits
            would_exceed_count = len(current_batch_files) >= max_files
            would_exceed_size = (current_batch_size + file_size_mb) > max_size_mb

            # If file is too large for any batch, create single-file batch
            if file_size_mb > max_size_mb:
                # Finish current batch if it has files
                if current_batch_files:
                    batches.append(self._create_upload_batch(current_batch_files, current_batch_size))
                    current_batch_files = []
                    current_batch_size = 0.0

                # Create single-file batch for oversized file
                batches.append(self._create_upload_batch([media_file], file_size_mb, metadata={"oversized": True}))
                continue

            # Start new batch if current would exceed limits
            if (would_exceed_count or would_exceed_size) and current_batch_files:
                batches.append(self._create_upload_batch(current_batch_files, current_batch_size))
                current_batch_files = []
                current_batch_size = 0.0

            # Add file to current batch
            current_batch_files.append(media_file)
            current_batch_size += file_size_mb

        # Add final batch if there are remaining files
        if current_batch_files:
            batches.append(self._create_upload_batch(current_batch_files, current_batch_size))

        return batches

    def _create_upload_batch(self, files: list[MediaFile], total_size_mb: float, metadata: dict = None) -> UploadBatch:
        """Create an UploadBatch object.

        Args:
            files: List of media files for the batch
            total_size_mb: Total size in MB
            metadata: Optional metadata for the batch

        Returns:
            UploadBatch object
        """
        total_size_bytes = int(total_size_mb * 1024 * 1024)

        batch_metadata = {
            "file_count": len(files),
            "has_compressed_files": any(f.is_compressed for f in files),
            "media_types": list({f.media_type.value for f in files}),
        }

        if metadata:
            batch_metadata.update(metadata)

        return UploadBatch(files=files, total_size_bytes=total_size_bytes, metadata=batch_metadata)

    def optimize_batches(self, media_files: list[MediaFile]) -> list[UploadBatch]:
        """Create optimized batches for better upload efficiency.

        Args:
            media_files: List of media files to optimize

        Returns:
            Optimized list of upload batches
        """
        # Sort files by size (smaller first) for better packing
        sorted_files = sorted(media_files, key=lambda f: f.size_mb)

        return self.create_batches(sorted_files)

    def validate_batch(self, batch: UploadBatch) -> bool:
        """Validate that a batch meets Discord requirements.

        Args:
            batch: Upload batch to validate

        Returns:
            True if batch is valid for Discord upload
        """
        # Check file count limit
        if len(batch.files) > self.max_files_per_message:
            return False

        # Check size limit (with small buffer for metadata)
        if batch.total_size_mb > (self.max_message_size_mb * 0.95):
            return False

        # Check that all files exist and are readable
        for media_file in batch.files:
            if not media_file.path.exists() or not media_file.path.is_file():
                return False

        return True

    def get_batch_summary(self, batch: UploadBatch) -> str:
        """Get a human-readable summary of a batch.

        Args:
            batch: Upload batch to summarize

        Returns:
            String summary of the batch
        """
        file_count = len(batch.files)
        size_mb = batch.total_size_mb

        if file_count == 1:
            return f"1 file ({size_mb:.1f}MB)"
        else:
            return f"{file_count} files ({size_mb:.1f}MB)"
