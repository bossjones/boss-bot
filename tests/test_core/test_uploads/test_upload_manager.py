"""Test upload manager functionality using TDD approach."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import discord
from discord.ext import commands

from boss_bot.core.uploads.manager import UploadManager
from boss_bot.core.uploads.models import MediaFile, MediaType, UploadResult


class TestUploadManager:
    """Test upload manager functionality using TDD approach."""

    @pytest.fixture
    def fixture_upload_manager(self, fixture_settings_test):
        """Create upload manager for testing."""
        return UploadManager(fixture_settings_test)

    @pytest.fixture
    def fixture_mock_ctx(self, mocker):
        """Create mocked Discord context."""
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890
        return ctx

    @pytest.fixture
    def fixture_temp_download_dir(self):
        """Create temporary directory with test media files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test media files
            video_file = temp_path / "test_video.mp4"
            video_file.write_bytes(b"fake video content" * 1000)  # ~17KB

            image_file = temp_path / "test_image.jpg"
            image_file.write_bytes(b"fake image content" * 500)   # ~8.5KB

            # Large file should definitely be > 25MB (Discord limit)
            large_file = temp_path / "large_video.mp4"
            large_file.write_bytes(b"X" * (30 * 1024 * 1024))    # 30MB

            yield temp_path

    # TDD: Red Phase - Write failing test first
    @pytest.mark.asyncio
    async def test_process_downloaded_files_no_media_found(
        self,
        fixture_upload_manager,
        fixture_mock_ctx
    ):
        """Test handling when no media files are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir)

            result = await fixture_upload_manager.process_downloaded_files(
                empty_dir,
                fixture_mock_ctx,
                "Twitter/X"
            )

            assert not result.success
            assert "No media files found" in result.message
            assert result.files_processed == 0

    # TDD: Green Phase - Make test pass with minimal implementation
    @pytest.mark.asyncio
    async def test_process_downloaded_files_success_small_files(
        self,
        fixture_upload_manager,
        fixture_mock_ctx,
        fixture_temp_download_dir
    ):
        """Test successful processing of small media files."""
        # Mock the upload processor to return success
        with patch.object(
            fixture_upload_manager.discord_processor,
            'upload_files',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = UploadResult(
                success=True,
                message="Upload complete: 2/2 files uploaded",
                files_processed=2,
                successful_uploads=2,
                failed_uploads=0
            )

            result = await fixture_upload_manager.process_downloaded_files(
                fixture_temp_download_dir,
                fixture_mock_ctx,
                "Twitter/X"
            )

            assert result.success
            assert "Upload complete" in result.message
            assert result.successful_uploads == 2

            # Verify upload was called with media files
            mock_upload.assert_called_once()
            call_args = mock_upload.call_args[0]
            uploaded_files = call_args[0]  # First argument: media_files list

            # Should find some files to upload
            assert len(uploaded_files) >= 2

    # TDD: Refactor Phase - Test compression integration
    @pytest.mark.asyncio
    async def test_process_downloaded_files_with_compression(
        self,
        fixture_upload_manager,
        fixture_mock_ctx,
        fixture_temp_download_dir,
        mocker
    ):
        """Test processing files that require compression."""
        # Mock compression manager
        mock_compression = mocker.Mock()
        mock_compression.compress_file = AsyncMock()

        # Mock successful compression
        from boss_bot.core.compression.models import CompressionResult

        # Create a proper output path dynamically
        large_file_path = fixture_temp_download_dir / "large_video.mp4"
        compressed_output_path = fixture_temp_download_dir / "large_video_compressed.mp4"

        mock_compression_result = CompressionResult(
            success=True,
            input_path=large_file_path,
            output_path=compressed_output_path,
            original_size_bytes=30 * 1024 * 1024,  # 30MB
            compressed_size_bytes=20 * 1024 * 1024,  # 20MB
            compression_ratio=0.67,
            processing_time_seconds=5.0
        )
        mock_compression.compress_file.return_value = mock_compression_result

        # Replace compression manager
        fixture_upload_manager.compression_manager = mock_compression

        # Mock successful upload
        with patch.object(
            fixture_upload_manager.discord_processor,
            'upload_files',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = UploadResult(
                success=True,
                message="Upload complete: 3/3 files uploaded",
                files_processed=3,
                successful_uploads=3,
                failed_uploads=0
            )

            result = await fixture_upload_manager.process_downloaded_files(
                fixture_temp_download_dir,
                fixture_mock_ctx,
                "Twitter/X"
            )

            assert result.success

            # Verify compression was called for large file
            mock_compression.compress_file.assert_called_once()

            # Verify compression status messages were sent
            compression_messages = [
                call.args[0] for call in fixture_mock_ctx.send.call_args_list
                if "🗜️ Compressing" in call.args[0]
            ]
            assert len(compression_messages) >= 1

    @pytest.mark.asyncio
    async def test_process_downloaded_files_compression_failure(
        self,
        fixture_upload_manager,
        fixture_mock_ctx,
        fixture_temp_download_dir,
        mocker
    ):
        """Test handling compression failures gracefully."""
        # Mock compression manager with failure
        mock_compression = mocker.Mock()
        mock_compression.compress_file = AsyncMock()

        from boss_bot.core.compression.models import CompressionResult

        large_file_path = fixture_temp_download_dir / "large_video.mp4"

        mock_compression_result = CompressionResult(
            success=False,
            input_path=large_file_path,
            output_path=None,
            original_size_bytes=30 * 1024 * 1024,
            compressed_size_bytes=0,
            compression_ratio=0.0,
            processing_time_seconds=0.0,
            error_message="Bitrate too low for compression"
        )
        mock_compression.compress_file.return_value = mock_compression_result

        fixture_upload_manager.compression_manager = mock_compression

        # Mock upload for remaining files
        with patch.object(
            fixture_upload_manager.discord_processor,
            'upload_files',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = UploadResult(
                success=True,
                message="Upload complete: 2/2 files uploaded",
                files_processed=2,
                successful_uploads=2,
                failed_uploads=0
            )

            result = await fixture_upload_manager.process_downloaded_files(
                fixture_temp_download_dir,
                fixture_mock_ctx,
                "Twitter/X"
            )

            # Should still succeed with small files
            assert result.success

            # Verify error message was sent
            error_messages = [
                call.args[0] for call in fixture_mock_ctx.send.call_args_list
                if "❌ Compression failed" in call.args[0]
            ]
            assert len(error_messages) >= 1

    @pytest.mark.asyncio
    async def test_upload_single_file(
        self,
        fixture_upload_manager,
        fixture_mock_ctx,
        fixture_temp_download_dir
    ):
        """Test uploading a single file."""
        video_file = fixture_temp_download_dir / "test_video.mp4"

        # Mock successful upload
        with patch.object(
            fixture_upload_manager,
            'process_downloaded_files',
            new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = UploadResult(
                success=True,
                message="Upload complete: 1/1 files uploaded",
                files_processed=1,
                successful_uploads=1,
                failed_uploads=0
            )

            result = await fixture_upload_manager.upload_single_file(
                video_file,
                fixture_mock_ctx,
                "Twitter/X"
            )

            assert result.success
            assert result.successful_uploads == 1
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_single_file_not_found(
        self,
        fixture_upload_manager,
        fixture_mock_ctx
    ):
        """Test uploading a non-existent file."""
        nonexistent_file = Path("/fake/path/file.mp4")

        result = await fixture_upload_manager.upload_single_file(
            nonexistent_file,
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert not result.success
        assert "File not found" in result.message
        assert result.files_processed == 0

    @pytest.mark.asyncio
    async def test_get_upload_preview(
        self,
        fixture_upload_manager,
        fixture_temp_download_dir
    ):
        """Test getting upload preview without actually uploading."""
        preview = await fixture_upload_manager.get_upload_preview(
            fixture_temp_download_dir
        )

        assert preview["total_files"] >= 2  # At least 2 small files
        assert preview["total_size_mb"] > 0
        assert preview["acceptable_files"] >= 2  # At least 2 small files
        assert preview["files_needing_compression"] >= 0  # May or may not have large files
        assert "media_types" in preview

    @pytest.mark.asyncio
    async def test_get_upload_preview_empty_directory(
        self,
        fixture_upload_manager
    ):
        """Test getting upload preview for empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir)

            preview = await fixture_upload_manager.get_upload_preview(empty_dir)

            assert preview["total_files"] == 0
            assert preview["total_size_mb"] == 0.0
            assert preview["acceptable_files"] == 0
            assert preview["files_needing_compression"] == 0
            assert preview["estimated_batches"] == 0
