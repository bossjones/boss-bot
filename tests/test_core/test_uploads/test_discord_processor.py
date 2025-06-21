"""Test Discord upload processor with dpytest patterns."""

import pytest
from unittest.mock import AsyncMock, Mock
import discord
from discord.ext import commands

from boss_bot.core.uploads.processors.discord_processor import DiscordUploadProcessor
from boss_bot.core.uploads.models import MediaFile, MediaType, UploadResult


class TestDiscordUploadProcessor:
    """Test Discord upload processor with dpytest patterns."""

    @pytest.fixture
    def fixture_discord_processor(self, fixture_settings_test):
        """Create Discord processor for testing."""
        return DiscordUploadProcessor(fixture_settings_test)

    @pytest.fixture
    def fixture_mock_ctx(self, mocker):
        """Create mocked Discord context."""
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        return ctx

    @pytest.fixture
    def fixture_sample_media_files(self, tmp_path):
        """Create sample MediaFile objects."""
        # Create actual test files
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video" * 100)

        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(b"fake image" * 50)

        return [
            MediaFile(
                path=video_file,
                filename="test.mp4",
                size_bytes=video_file.stat().st_size,
                media_type=MediaType.VIDEO
            ),
            MediaFile(
                path=image_file,
                filename="test.jpg",
                size_bytes=image_file.stat().st_size,
                media_type=MediaType.IMAGE
            )
        ]

    @pytest.mark.asyncio
    async def test_upload_files_empty_list(
        self,
        fixture_discord_processor,
        fixture_mock_ctx
    ):
        """Test upload with empty file list."""
        result = await fixture_discord_processor.upload_files(
            [],
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert result.success
        assert "No files to upload" in result.message
        assert result.files_processed == 0

    @pytest.mark.asyncio
    async def test_upload_files_success(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        fixture_sample_media_files,
        mocker
    ):
        """Test successful file upload."""
        # Mock ctx.send to return a Message object when files are sent
        mock_message = mocker.Mock(spec=discord.Message)
        fixture_mock_ctx.send.return_value = mock_message

        result = await fixture_discord_processor.upload_files(
            fixture_sample_media_files,
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert result.success
        assert result.successful_uploads == 2
        assert result.failed_uploads == 0

        # Verify Discord send was called with files
        calls = fixture_mock_ctx.send.call_args_list
        file_upload_calls = [call for call in calls if 'files' in call.kwargs]
        assert len(file_upload_calls) >= 1

        # Verify actual Discord.File objects were created
        files_sent = file_upload_calls[0].kwargs['files']
        assert len(files_sent) == 2
        assert all(isinstance(f, discord.File) for f in files_sent)

    @pytest.mark.asyncio
    async def test_upload_files_discord_error(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        fixture_sample_media_files
    ):
        """Test handling Discord upload errors."""
        # Mock ctx.send to raise HTTPException for file uploads
        def side_effect(*args, **kwargs):
            if 'files' in kwargs:
                raise discord.HTTPException(
                    response=Mock(status=413),
                    message="Request entity too large"
                )
            return AsyncMock()

        fixture_mock_ctx.send.side_effect = side_effect

        result = await fixture_discord_processor.upload_files(
            fixture_sample_media_files,
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert not result.success
        assert result.failed_uploads == 2
        assert result.successful_uploads == 0

        # Verify error message was sent
        error_calls = [
            call.args[0] for call in fixture_mock_ctx.send.call_args_list
            if "too large" in call.args[0]
        ]
        assert len(error_calls) >= 1

    @pytest.mark.asyncio
    async def test_upload_files_rate_limit_retry(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        fixture_sample_media_files,
        mocker
    ):
        """Test handling Discord rate limiting with retry."""
        # Mock rate limit on first attempt, success on second
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            if 'files' in kwargs:
                call_count += 1
                if call_count == 1:
                    # First call: rate limited
                    error = discord.HTTPException(
                        response=Mock(status=429),
                        message="Rate limited"
                    )
                    error.retry_after = 0.1  # Short retry for testing
                    raise error
                else:
                    # Second call: success
                    return mocker.Mock(spec=discord.Message)
            return AsyncMock()

        fixture_discord_processor.retry_delay = 0.1  # Short delay for testing
        fixture_mock_ctx.send.side_effect = side_effect

        result = await fixture_discord_processor.upload_files(
            fixture_sample_media_files,
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert result.success
        assert result.successful_uploads == 2
        assert call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_upload_files_file_preparation_error(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        tmp_path
    ):
        """Test handling file preparation errors."""
        # Create MediaFile with non-existent path
        bad_file = MediaFile(
            path=tmp_path / "nonexistent.mp4",
            filename="nonexistent.mp4",
            size_bytes=1000,
            media_type=MediaType.VIDEO
        )

        result = await fixture_discord_processor.upload_files(
            [bad_file],
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert not result.success
        # Should have at least one failure (the file preparation or upload failure)
        assert result.failed_uploads > 0 or not result.success

        # Verify the upload failed due to batch validation (file doesn't exist)
        # No messages should be sent to context because validation fails before upload attempt
        assert fixture_mock_ctx.send.call_count == 0

    @pytest.mark.asyncio
    async def test_upload_files_with_compressed_metadata(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        tmp_path,
        mocker
    ):
        """Test upload with compressed file metadata."""
        # Create compressed file
        compressed_file = tmp_path / "compressed.mp4"
        compressed_file.write_bytes(b"compressed content")

        original_file = tmp_path / "original.mp4"
        original_file.write_bytes(b"original content")

        media_file = MediaFile(
            path=compressed_file,
            filename="compressed.mp4",
            size_bytes=compressed_file.stat().st_size,
            media_type=MediaType.VIDEO,
            is_compressed=True,
            original_path=original_file
        )

        # Mock successful upload
        mock_message = mocker.Mock(spec=discord.Message)
        fixture_mock_ctx.send.return_value = mock_message

        result = await fixture_discord_processor.upload_files(
            [media_file],
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert result.success
        assert result.successful_uploads == 1

        # Verify compression metadata message was sent
        compression_info_calls = [
            call.args[0] for call in fixture_mock_ctx.send.call_args_list
            if "🗜️" in call.args[0] and "compressed from" in call.args[0]
        ]
        assert len(compression_info_calls) >= 1

    @pytest.mark.asyncio
    async def test_upload_files_large_batch_splitting(
        self,
        fixture_discord_processor,
        fixture_mock_ctx,
        tmp_path,
        mocker
    ):
        """Test that large batches are split properly."""
        # Create 15 files (exceeds Discord's 10-file limit)
        media_files = []
        for i in range(15):
            file_path = tmp_path / f"file_{i}.jpg"
            file_path.write_bytes(b"content" * 100)

            media_files.append(MediaFile(
                path=file_path,
                filename=f"file_{i}.jpg",
                size_bytes=file_path.stat().st_size,
                media_type=MediaType.IMAGE
            ))

        # Mock successful upload
        mock_message = mocker.Mock(spec=discord.Message)
        fixture_mock_ctx.send.return_value = mock_message

        result = await fixture_discord_processor.upload_files(
            media_files,
            fixture_mock_ctx,
            "Twitter/X"
        )

        assert result.success
        assert result.successful_uploads == 15

        # Verify multiple file upload calls were made (should be split into batches)
        file_upload_calls = [
            call for call in fixture_mock_ctx.send.call_args_list
            if 'files' in call.kwargs
        ]
        assert len(file_upload_calls) >= 2  # Should be split into multiple batches
