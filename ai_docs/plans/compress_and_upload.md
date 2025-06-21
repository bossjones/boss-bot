# Compress and Upload Enhancement Plan

## Overview
Enhance `src/boss_bot/bot/cogs/downloads.py` to automatically compress and upload downloaded media files to Discord as attachments. This plan leverages the compression modules from `compress_media.md` and follows TDD principles with comprehensive dpytest testing.

## Current State Analysis

<quote>
The existing downloads.py cog:
- **Downloads files successfully** but only saves to `.downloads/` directory
- **Uses strategy pattern** for different platforms (Twitter, Reddit, YouTube, Instagram)
- **Shows download completion** with metadata but doesn't send files to Discord
- **Has good error handling** and platform-specific emojis
- **Missing file upload functionality** - the key gap this plan addresses
</quote>

<quote>
Inspiration from existing compress_and_upload.md shows patterns for:
- **File size checking**: `pathlib.Path(meme).stat().st_size > constants.MAX_BYTES_UPLOAD_DISCORD`
- **Discord file uploads**: `my_files.append(discord.File(f"{f}"))` and `await recipient_user.send(files=my_files)`
- **Media filtering**: `file_functions.filter_media(file_to_upload_list)`
- **Batch processing**: Handling multiple files with chunking for Discord's 10-file limit
</quote>

However, the inspiration code lacks modern patterns and compression integration that we'll implement properly.

## Enhanced Architecture Design

### 1. New Upload Manager (`src/boss_bot/core/uploads/`)
```
src/boss_bot/core/uploads/
├── __init__.py
├── manager.py              # Main upload coordination
├── processors/             # Upload-specific processors
│   ├── __init__.py
│   ├── base_processor.py   # Abstract upload processor
│   ├── discord_processor.py # Discord-specific upload logic
│   └── fallback_processor.py # Fallback storage (future: cloud)
├── models.py              # Upload data models
├── utils/                 # Upload utilities
│   ├── __init__.py
│   ├── file_detector.py   # Media file detection and filtering
│   ├── batch_processor.py # Batch upload handling
│   └── size_analyzer.py   # File size analysis
└── config/                # Upload configuration
    ├── __init__.py
    └── upload_config.py   # Upload settings and limits
```

### 2. Upload Manager Implementation

#### A. Upload Manager (`manager.py`)
```python
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import discord
from discord.ext import commands

from boss_bot.core.compression.manager import CompressionManager
from boss_bot.core.uploads.models import UploadResult, UploadBatch, MediaFile
from boss_bot.core.uploads.processors.discord_processor import DiscordUploadProcessor
from boss_bot.core.uploads.utils.file_detector import MediaFileDetector
from boss_bot.core.uploads.utils.size_analyzer import FileSizeAnalyzer

class UploadManager:
    """Manages the complete upload workflow with compression integration."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.compression_manager = CompressionManager(settings)
        self.discord_processor = DiscordUploadProcessor(settings)
        self.file_detector = MediaFileDetector()
        self.size_analyzer = FileSizeAnalyzer(settings)

    async def process_downloaded_files(
        self,
        download_dir: Path,
        ctx: commands.Context,
        platform_name: str
    ) -> UploadResult:
        """
        Main entry point: Process all files in download directory.

        1. Detect media files
        2. Analyze file sizes
        3. Compress oversized files
        4. Upload to Discord in batches
        5. Handle fallback for too-large files
        """
        try:
            # Step 1: Find all media files
            media_files = await self.file_detector.find_media_files(download_dir)

            if not media_files:
                return UploadResult(
                    success=False,
                    message="No media files found to upload",
                    files_processed=0
                )

            # Step 2: Analyze and categorize files by size
            size_analysis = await self.size_analyzer.analyze_files(media_files)

            # Step 3: Compress files that exceed Discord limits
            compressed_files = await self._compress_oversized_files(
                size_analysis.oversized_files,
                ctx,
                platform_name
            )

            # Step 4: Prepare final upload list
            upload_files = size_analysis.acceptable_files + compressed_files

            # Step 5: Upload to Discord in batches
            upload_result = await self.discord_processor.upload_files(
                upload_files,
                ctx,
                platform_name
            )

            return upload_result

        except Exception as e:
            return UploadResult(
                success=False,
                message=f"Upload processing failed: {e}",
                error=str(e),
                files_processed=0
            )

    async def _compress_oversized_files(
        self,
        oversized_files: List[MediaFile],
        ctx: commands.Context,
        platform_name: str
    ) -> List[MediaFile]:
        """Compress files that are too large for Discord."""
        compressed_files = []

        for media_file in oversized_files:
            await ctx.send(
                f"🗜️ Compressing {media_file.filename} "
                f"({media_file.size_mb:.1f}MB → {self.settings.compression_max_upload_size_mb}MB)"
            )

            try:
                compression_result = await self.compression_manager.compress_file(
                    media_file.path,
                    target_size_mb=None,  # Use default from settings
                    output_dir=media_file.path.parent
                )

                if compression_result.success:
                    # Create new MediaFile for compressed version
                    compressed_media = MediaFile(
                        path=compression_result.output_path,
                        filename=compression_result.output_path.name,
                        size_bytes=compression_result.compressed_size_bytes,
                        media_type=media_file.media_type,
                        is_compressed=True,
                        original_path=media_file.path
                    )
                    compressed_files.append(compressed_media)

                    await ctx.send(
                        f"✅ Compressed successfully! "
                        f"Ratio: {compression_result.compression_ratio:.2f}"
                    )
                else:
                    await ctx.send(
                        f"❌ Compression failed for {media_file.filename}: "
                        f"{compression_result.error_message}"
                    )
                    # Note: Could implement fallback storage here

            except Exception as e:
                await ctx.send(
                    f"❌ Compression error for {media_file.filename}: {e}"
                )

        return compressed_files
```

#### B. Discord Upload Processor (`processors/discord_processor.py`)
```python
from typing import List
import discord
from discord.ext import commands

from boss_bot.core.uploads.models import MediaFile, UploadResult, UploadBatch
from boss_bot.core.uploads.utils.batch_processor import BatchProcessor

class DiscordUploadProcessor:
    """Handles Discord-specific upload logic."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.batch_processor = BatchProcessor(settings)
        self.max_files_per_message = 10  # Discord's limit
        self.max_message_size_mb = 25    # Discord's default limit

    async def upload_files(
        self,
        media_files: List[MediaFile],
        ctx: commands.Context,
        platform_name: str
    ) -> UploadResult:
        """Upload media files to Discord in optimized batches."""

        if not media_files:
            return UploadResult(
                success=True,
                message="No files to upload",
                files_processed=0
            )

        # Create upload batches respecting Discord limits
        batches = self.batch_processor.create_batches(
            media_files,
            max_files=self.max_files_per_message,
            max_size_mb=self.max_message_size_mb
        )

        successful_uploads = 0
        failed_uploads = 0

        for i, batch in enumerate(batches):
            try:
                # Send batch info
                batch_info = f"📎 Uploading batch {i+1}/{len(batches)}"
                if len(batches) > 1:
                    file_names = [f.filename for f in batch.files[:3]]
                    if len(batch.files) > 3:
                        file_names.append(f"... and {len(batch.files)-3} more")
                    batch_info += f": {', '.join(file_names)}"

                await ctx.send(batch_info)

                # Create Discord File objects
                discord_files = []
                for media_file in batch.files:
                    try:
                        discord_file = discord.File(
                            media_file.path,
                            filename=media_file.filename
                        )
                        discord_files.append(discord_file)
                    except Exception as e:
                        await ctx.send(
                            f"⚠️ Could not prepare {media_file.filename}: {e}"
                        )
                        failed_uploads += 1
                        continue

                # Upload batch to Discord
                if discord_files:
                    upload_message = await ctx.send(
                        f"🎯 {platform_name} media files:",
                        files=discord_files
                    )
                    successful_uploads += len(discord_files)

                    # Add metadata as follow-up if available
                    if batch.metadata:
                        metadata_lines = []
                        for file_info in batch.files:
                            if file_info.is_compressed:
                                metadata_lines.append(
                                    f"🗜️ {file_info.filename} (compressed from {file_info.original_path.name})"
                                )

                        if metadata_lines:
                            await ctx.send(f"ℹ️ **Compression Info:**\n" + "\n".join(metadata_lines))

            except discord.HTTPException as e:
                if "Request entity too large" in str(e):
                    await ctx.send(
                        f"❌ Batch {i+1} too large for Discord. Consider enabling higher compression."
                    )
                else:
                    await ctx.send(f"❌ Upload failed for batch {i+1}: {e}")
                failed_uploads += len(batch.files)

            except Exception as e:
                await ctx.send(f"❌ Unexpected error uploading batch {i+1}: {e}")
                failed_uploads += len(batch.files)

        total_files = successful_uploads + failed_uploads
        success_rate = successful_uploads / total_files if total_files > 0 else 0

        return UploadResult(
            success=success_rate > 0.5,  # Success if > 50% uploaded
            message=f"Upload complete: {successful_uploads}/{total_files} files uploaded",
            files_processed=total_files,
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads
        )
```

#### C. Data Models (`models.py`)
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

class MediaType(Enum):
    """Types of media files we can handle."""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"

@dataclass
class MediaFile:
    """Represents a media file ready for upload."""
    path: Path
    filename: str
    size_bytes: int
    media_type: MediaType
    is_compressed: bool = False
    original_path: Optional[Path] = None

    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)

@dataclass
class UploadBatch:
    """A batch of files to upload together."""
    files: List[MediaFile]
    total_size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_size_mb(self) -> float:
        """Get total batch size in MB."""
        return self.total_size_bytes / (1024 * 1024)

@dataclass
class SizeAnalysis:
    """Analysis of file sizes for upload planning."""
    acceptable_files: List[MediaFile]  # Files that fit Discord limits
    oversized_files: List[MediaFile]   # Files that need compression
    total_files: int
    total_size_mb: float

@dataclass
class UploadResult:
    """Result of an upload operation."""
    success: bool
    message: str
    files_processed: int
    successful_uploads: int = 0
    failed_uploads: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 3. Enhanced Downloads Cog Integration

#### A. Modified Download Command (`downloads.py`)
```python
# Add these imports to existing downloads.py
from boss_bot.core.uploads.manager import UploadManager

class DownloadCog(commands.Cog):
    """Enhanced cog with upload functionality."""

    def __init__(self, bot: BossBot):
        # ... existing initialization ...
        # Add upload manager
        self.upload_manager = UploadManager(bot.settings)

    @commands.command(name="download")
    async def download(self, ctx: commands.Context, url: str, upload: bool = True):
        """Download content and optionally upload to Discord.

        Args:
            url: URL to download
            upload: Whether to upload files to Discord (default: True)
        """
        # Try to find a strategy that supports this URL
        strategy = self._get_strategy_for_url(url)

        if strategy:
            # Determine platform emoji and name
            platform_info = self._get_platform_info(url)
            emoji = platform_info["emoji"]
            name = platform_info["name"]

            await ctx.send(f"{emoji} Downloading {name} content: {url}")

            # Show feature flag status if API is enabled
            platform_key = strategy.__class__.__name__.lower().replace("downloadstrategy", "")
            if self.feature_flags.is_api_enabled_for_platform(platform_key):
                await ctx.send(f"🚀 Using experimental API-direct approach for {name}")

            try:
                # Create unique download directory for this request
                request_id = f"{ctx.author.id}_{ctx.message.id}"
                download_subdir = self.download_dir / request_id
                download_subdir.mkdir(exist_ok=True, parents=True)

                # Temporarily change strategy download directory
                original_dir = strategy.download_dir
                strategy.download_dir = download_subdir

                try:
                    metadata = await strategy.download(url)

                    # Check if download was successful
                    if metadata.error:
                        await ctx.send(f"❌ {name} download failed: {metadata.error}")
                        return

                    await ctx.send(f"✅ {name} download completed!")

                    # Show basic metadata if available
                    if metadata.title:
                        title_preview = metadata.title[:100] + "..." if len(metadata.title) > 100 else metadata.title
                        await ctx.send(f"📝 **Title:** {title_preview}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        await ctx.send(f"{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    # NEW: Process and upload files if requested
                    if upload:
                        await ctx.send(f"📤 Processing files for upload...")

                        upload_result = await self.upload_manager.process_downloaded_files(
                            download_subdir,
                            ctx,
                            name
                        )

                        if upload_result.success:
                            await ctx.send(f"🎉 {upload_result.message}")
                        else:
                            await ctx.send(f"⚠️ Upload issues: {upload_result.message}")
                            if upload_result.error:
                                await ctx.send(f"Error details: {upload_result.error}")
                    else:
                        await ctx.send(f"📁 Files saved to: `{download_subdir}`")

                finally:
                    # Restore original download directory
                    strategy.download_dir = original_dir

                    # Cleanup: Remove download directory after upload (optional)
                    if upload and self.settings.cleanup_after_upload:
                        try:
                            import shutil
                            shutil.rmtree(download_subdir)
                        except Exception as cleanup_error:
                            print(f"Cleanup warning: {cleanup_error}")

            except Exception as e:
                await ctx.send(f"❌ Download error: {e!s}")
            return

        # ... rest of existing fallback logic ...

    @commands.command(name="download-only")
    async def download_only(self, ctx: commands.Context, url: str):
        """Download content without uploading to Discord."""
        await self.download(ctx, url, upload=False)
```

### 4. Configuration Integration

#### A. BossSettings Updates (`core/env.py`)
```python
class BossSettings(BaseSettings):
    # ... existing settings ...

    # Upload settings
    upload_batch_size_mb: int = Field(default=20, description="Maximum batch size for Discord uploads in MB")
    upload_max_files_per_batch: int = Field(default=10, description="Maximum files per Discord message")
    upload_cleanup_after_success: bool = Field(default=True, description="Remove downloaded files after successful upload")
    upload_enable_progress_updates: bool = Field(default=True, description="Show upload progress messages")

    # Integration with compression settings
    @property
    def cleanup_after_upload(self) -> bool:
        """Alias for upload_cleanup_after_success."""
        return self.upload_cleanup_after_success
```

### 5. TDD Testing Strategy

#### A. Test Structure
```
tests/test_core/test_uploads/
├── __init__.py
├── test_upload_manager.py           # Main upload manager tests
├── test_discord_processor.py        # Discord upload processor tests
├── test_file_detector.py           # Media file detection tests
├── test_size_analyzer.py           # File size analysis tests
├── test_batch_processor.py         # Batch processing tests
└── test_models.py                  # Data model tests

tests/test_bot/test_cogs/
└── test_downloads_upload_integration.py  # Full integration tests
```

#### B. TDD Test Examples

##### Main Upload Manager Tests (`test_upload_manager.py`)
```python
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

            large_file = temp_path / "large_video.mp4"
            large_file.write_bytes(b"large content" * 2000000)    # ~26MB

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

            # Should find 2 small files (not the large one that needs compression)
            small_files = [f for f in uploaded_files if f.size_mb < 25]
            assert len(small_files) >= 2

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
        mock_compression_result = CompressionResult(
            success=True,
            input_path=fixture_temp_download_dir / "large_video.mp4",
            output_path=fixture_temp_download_dir / "large_video_compressed.mp4",
            original_size_bytes=26 * 1024 * 1024,  # 26MB
            compressed_size_bytes=20 * 1024 * 1024,  # 20MB
            compression_ratio=0.77,
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
        mock_compression_result = CompressionResult(
            success=False,
            input_path=fixture_temp_download_dir / "large_video.mp4",
            output_path=None,
            original_size_bytes=26 * 1024 * 1024,
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
```

##### Discord Processor Tests (`test_discord_processor.py`)
```python
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
```

##### Integration Tests (`test_downloads_upload_integration.py`)
```python
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import discord
from discord.ext import commands

from boss_bot.bot.cogs.downloads import DownloadCog

class TestDownloadsUploadIntegration:
    """Integration tests for downloads with upload functionality."""

    @pytest.fixture
    async def fixture_download_cog(self, fixture_mock_bot_test):
        """Create DownloadCog with mocked dependencies."""
        cog = DownloadCog(fixture_mock_bot_test)

        # Mock the upload manager
        cog.upload_manager = Mock()
        cog.upload_manager.process_downloaded_files = AsyncMock()

        return cog

    @pytest.fixture
    def fixture_mock_strategy(self, mocker):
        """Create mock download strategy."""
        strategy = mocker.Mock()
        strategy.supports_url.return_value = True
        strategy.download = AsyncMock()
        strategy.download_dir = Path("/tmp/downloads")

        # Mock successful download
        from boss_bot.core.downloads.strategies.base_strategy import DownloadMetadata
        mock_metadata = DownloadMetadata(
            url="https://twitter.com/test/status/123",
            title="Test Tweet",
            error=None,
            download_method="api"
        )
        strategy.download.return_value = mock_metadata

        return strategy

    @pytest.mark.asyncio
    async def test_download_command_with_upload_success(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command with successful upload."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock successful upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=True,
            message="Upload complete: 2/2 files uploaded",
            files_processed=2,
            successful_uploads=2,
            failed_uploads=0
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload processing was called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_called_once()

        # Verify success messages
        success_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "🎉" in call.args[0] or "✅" in call.args[0]
        ]
        assert len(success_messages) >= 2  # Download success + upload success

    @pytest.mark.asyncio
    async def test_download_command_upload_disabled(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command with upload disabled."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Execute with upload=False
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=False
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload was NOT called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_not_called()

        # Verify file location message
        location_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "📁 Files saved to" in call.args[0]
        ]
        assert len(location_messages) >= 1

    @pytest.mark.asyncio
    async def test_download_only_command_alias(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download-only command alias."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock the download method to verify it's called with upload=False
        fixture_download_cog.download = AsyncMock()

        # Execute
        await fixture_download_cog.download_only.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123"
        )

        # Verify download was called with upload=False
        fixture_download_cog.download.assert_called_once_with(
            ctx,
            "https://twitter.com/test/status/123",
            upload=False
        )
```

### 6. File Detection and Processing Utilities

#### A. Media File Detector (`utils/file_detector.py`)
```python
from pathlib import Path
from typing import List
import mimetypes

from boss_bot.core.uploads.models import MediaFile, MediaType

class MediaFileDetector:
    """Detects and categorizes media files."""

    def __init__(self):
        self.video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv',
            '.webm', '.mpeg', '.3gp', '.m4v'
        }
        self.audio_extensions = {
            '.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg',
            '.wma', '.opus'
        }
        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
            '.tiff', '.svg'
        }

    async def find_media_files(self, directory: Path) -> List[MediaFile]:
        """Find all media files in directory recursively."""
        media_files = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and self._is_media_file(file_path):
                media_type = self._determine_media_type(file_path)

                media_file = MediaFile(
                    path=file_path,
                    filename=file_path.name,
                    size_bytes=file_path.stat().st_size,
                    media_type=media_type
                )
                media_files.append(media_file)

        return media_files

    def _is_media_file(self, file_path: Path) -> bool:
        """Check if file is a media file."""
        suffix = file_path.suffix.lower()
        return (
            suffix in self.video_extensions or
            suffix in self.audio_extensions or
            suffix in self.image_extensions
        )

    def _determine_media_type(self, file_path: Path) -> MediaType:
        """Determine the type of media file."""
        suffix = file_path.suffix.lower()

        if suffix in self.video_extensions:
            return MediaType.VIDEO
        elif suffix in self.audio_extensions:
            return MediaType.AUDIO
        elif suffix in self.image_extensions:
            return MediaType.IMAGE
        else:
            return MediaType.UNKNOWN
```

### 7. Environment Configuration

#### A. Environment Variables
```bash
# Upload settings
export UPLOAD_BATCH_SIZE_MB=20                    # Max batch size
export UPLOAD_MAX_FILES_PER_BATCH=10             # Max files per message
export UPLOAD_CLEANUP_AFTER_SUCCESS=true         # Cleanup after upload
export UPLOAD_ENABLE_PROGRESS_UPDATES=true       # Show progress messages

# Compression integration (from compress_media.md)
export COMPRESSION_MAX_UPLOAD_SIZE_MB=50          # Target compression size
```

### 8. Migration Plan

#### Phase 1: Core Upload Infrastructure ✅
1. ✅ Create upload module structure
2. ✅ Implement data models
3. ✅ Create upload manager base class
4. ✅ Build file detection utilities

#### Phase 2: Discord Integration ✅
1. ✅ Implement Discord upload processor
2. ✅ Add batch processing logic
3. ✅ Create size analysis utilities
4. ✅ Build error handling

#### Phase 3: Compression Integration ✅
1. ✅ Integrate compression manager
2. ✅ Add file size analysis
3. ✅ Implement compression workflow
4. ✅ Handle compression failures gracefully

#### Phase 4: Downloads Cog Enhancement ✅
1. ✅ Modify download command to include upload
2. ✅ Add download-only command
3. ✅ Implement temporary directory management
4. ✅ Add cleanup functionality

#### Phase 5: Testing & Validation 🔄
1. ✅ Write comprehensive unit tests
2. ✅ Create integration tests with dpytest
3. 🔄 Performance testing with large files
4. 🔄 Error scenario testing

#### Phase 6: Advanced Features 🔄
1. 🔄 Progress tracking for large uploads
2. 🔄 Thumbnail generation for videos
3. 🔄 Metadata embedding in uploads
4. 🔄 Upload queue for rate limiting

### 9. Testing Commands

#### A. Manual Testing Commands
```bash
# Test with various media types
$download https://twitter.com/user/status/123    # Auto-upload enabled
$download-only https://twitter.com/user/status/123  # No upload

# Test with large files that need compression
$download https://youtube.com/watch?v=VIDEO_ID   # Should compress if > 50MB

# Test compression settings
export COMPRESSION_MAX_UPLOAD_SIZE_MB=25         # Discord limit
$download https://instagram.com/p/POST_ID        # Should compress to 25MB
```

#### B. Automated Test Execution
```bash
# Run upload-specific tests
uv run python -m pytest tests/test_core/test_uploads/ -v

# Run integration tests
uv run python -m pytest tests/test_bot/test_cogs/test_downloads_upload_integration.py -v

# Run all compression and upload tests
uv run python -m pytest -k "upload or compress" -v
```

### 10. Error Handling & Edge Cases

#### A. Common Error Scenarios
1. **No media files found**: Clear message, no upload attempt
2. **All files too large**: Compression attempt, fallback message if fails
3. **Discord upload limits exceeded**: Batch splitting, progress updates
4. **Compression failures**: Continue with uncompressed small files
5. **Network errors**: Retry logic, detailed error reporting
6. **Permission errors**: File access validation, helpful error messages

#### B. Edge Case Handling
```python
class UploadErrorHandler:
    """Handles various upload error scenarios."""

    async def handle_file_access_error(self, ctx: commands.Context, error: OSError):
        """Handle file permission/access errors."""
        await ctx.send(
            f"❌ File access error: {error}\n"
            f"💡 This might be a permission issue. Check file access rights."
        )

    async def handle_discord_rate_limit(self, ctx: commands.Context, retry_after: float):
        """Handle Discord rate limiting."""
        await ctx.send(
            f"⏳ Upload rate limited. Retrying in {retry_after:.1f} seconds..."
        )
        await asyncio.sleep(retry_after)

    async def handle_file_too_large_after_compression(self, ctx: commands.Context, filename: str):
        """Handle files that are still too large after compression."""
        await ctx.send(
            f"⚠️ {filename} is still too large after compression.\n"
            f"💡 Consider using a lower quality setting or external storage."
        )
```

## Summary

This plan provides a comprehensive TDD-driven enhancement to the downloads cog that:

1. **Integrates seamlessly** with existing strategy pattern and compression modules
2. **Follows TDD principles** with extensive dpytest testing
3. **Handles edge cases** gracefully with proper error handling
4. **Maintains performance** with batching and async processing
5. **Provides user feedback** with progress updates and clear status messages
6. **Enables flexibility** with upload/download-only options
7. **Supports all media types** with intelligent file detection and processing

<quote>
Key integration points:
- **CompressionManager integration**: `await self.compression_manager.compress_file()`
- **Strategy pattern compatibility**: Works with existing `TwitterDownloadStrategy`, `RedditDownloadStrategy`, etc.
- **Discord.py patterns**: Uses `discord.File()` objects and proper batch uploading
- **TDD testing**: Comprehensive test coverage with dpytest mocking patterns
</quote>

The modular design allows for easy testing and future enhancements while maintaining backward compatibility with existing download functionality.
