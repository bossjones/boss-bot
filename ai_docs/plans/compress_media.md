# Media Compression Module Plan

## Overview
Convert `scripts/compress-discord.sh` into a Python module system for compressing video, audio, and image files. The goal is to integrate configurable file size limit compression into the bot's download workflow, with Discord's default limits in mind but supporting other platforms with different limits.

## Current Bash Script Analysis

<quote>
The existing bash script (`scripts/compress-discord.sh`) implements:
- **Video compression**: Uses ffprobe to get duration, calculates bitrate for 25MB target, allocates 90% video/10% audio
- **Audio compression**: Similar duration-based bitrate calculation, uses libmp3lame encoder
- **Safety thresholds**: Minimum bitrates (video: 125kbps, audio: 32kbps) to prevent over-compression
- **File extension detection**: Supports common video formats (mp4, avi, mkv, etc.) and audio formats (mp3, wav, etc.)
- **FFmpeg integration**: Direct subprocess calls with specific encoding parameters
- **Fixed target size**: Hard-coded 25MB limit (Discord's limit)
</quote>

Key functions to replicate:
```bash
# Video bitrate calculation (23MB to leave buffer for container overhead)
bitrate=$(python -c "duration=${duration}; print(int(23 * 8 * 1000 / duration))")
video_bitrate=$(python -c "bitrate=${bitrate}; print(int(bitrate * 90 / 100))")
audio_bitrate=$(python -c "bitrate=${bitrate}; print(int(bitrate * 10 / 100))")

# FFmpeg compression commands (output filename shows 25MB target)
ffmpeg -hide_banner -loglevel warning -stats -threads 0 -hwaccel auto -i "$input_file" \
  -preset slow -c:v libx264 -b:v ${video_bitrate}k -c:a aac -b:a ${audio_bitrate}k \
  -bufsize ${bitrate}k -minrate 100k -maxrate ${bitrate}k "25MB_${input_file_name}.mp4"
```

## Proposed Python Module Architecture

### 1. Core Module Structure
```
src/boss_bot/core/compression/
   __init__.py
   manager.py              # Main compression manager
   models.py              # Data models for compression settings
   processors/            # Media-specific processors
      __init__.py
      base_processor.py  # Abstract base class
      video_processor.py # Video compression logic
      audio_processor.py # Audio compression logic
      image_processor.py # Image compression logic (new)
   utils/                 # Utility functions
      __init__.py
      ffmpeg_utils.py    # FFmpeg wrapper utilities
      bitrate_calculator.py # Bitrate calculation logic
      file_detector.py   # File type detection
   config/               # Configuration management
       __init__.py
       compression_config.py # Compression settings
```

### 2. Key Components Design

#### A. Compression Manager (`manager.py`)
```python
from pathlib import Path
from typing import Union, Optional
from pydantic import BaseModel

class CompressionManager:
    """Main entry point for media compression operations."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.video_processor = VideoProcessor(settings)
        self.audio_processor = AudioProcessor(settings)
        self.image_processor = ImageProcessor(settings)

    async def compress_file(
        self,
        input_path: Path,
        target_size_mb: Optional[int] = None,
        output_dir: Optional[Path] = None
    ) -> CompressionResult:
        """Compress media file to target size. Uses settings default if not specified."""
        if target_size_mb is None:
            target_size_mb = self.settings.compression_max_upload_size_mb

    async def get_compression_info(self, input_path: Path) -> MediaInfo:
        """Get file information without compressing."""
```

#### B. Base Processor (`processors/base_processor.py`)
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

class BaseProcessor(ABC):
    """Abstract base class for media processors."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.supported_extensions: List[str] = []
        self.min_bitrate_kbps: int = 32

    @abstractmethod
    async def compress(
        self,
        input_path: Path,
        target_size_mb: int,
        output_path: Path
    ) -> CompressionResult:
        """Compress media file."""

    @abstractmethod
    async def get_media_info(self, input_path: Path) -> MediaInfo:
        """Get media file information."""

    def supports_file(self, file_path: Path) -> bool:
        """Check if processor supports this file type."""
        return file_path.suffix.lower().lstrip('.') in self.supported_extensions
```

#### C. Video Processor (`processors/video_processor.py`)
```python
class VideoProcessor(BaseProcessor):
    """Handles video file compression."""

    def __init__(self, settings: BossSettings):
        super().__init__(settings)
        self.supported_extensions = [
            'mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv',
            'webm', 'mpeg', '3gp'
        ]
        self.min_video_bitrate_kbps = 125
        self.min_audio_bitrate_kbps = 32
        self.video_bitrate_ratio = 0.9  # 90% for video
        self.audio_bitrate_ratio = 0.1  # 10% for audio

    async def compress(
        self,
        input_path: Path,
        target_size_mb: int,
        output_path: Path
    ) -> CompressionResult:
        """
        Compress video file using the same logic as bash script:
        1. Get duration using ffprobe
        2. Calculate target bitrate: (target_size_mb * 8 * 1000) / duration
        3. Allocate 90% to video, 10% to audio
        4. Apply minimum bitrate thresholds
        5. Execute ffmpeg compression
        """

        # Get media info
        media_info = await self.get_media_info(input_path)

        # Calculate bitrates (replicating bash script logic)
        target_bitrate = self._calculate_target_bitrate(
            target_size_mb, media_info.duration_seconds
        )

        video_bitrate = int(target_bitrate * self.video_bitrate_ratio)
        audio_bitrate = int(target_bitrate * self.audio_bitrate_ratio)

        # Apply minimum thresholds
        if video_bitrate < self.min_video_bitrate_kbps:
            raise CompressionError(
                f"Target video bitrate {video_bitrate}kbps is below minimum {self.min_video_bitrate_kbps}kbps"
            )

        if audio_bitrate < self.min_audio_bitrate_kbps:
            raise CompressionError(
                f"Target audio bitrate {audio_bitrate}kbps is below minimum {self.min_audio_bitrate_kbps}kbps"
            )

        # Execute ffmpeg compression
        return await self._execute_ffmpeg_compression(
            input_path, output_path, video_bitrate, audio_bitrate, target_bitrate
        )

    def _calculate_target_bitrate(self, target_size_mb: int, duration_seconds: float) -> int:
        """Calculate target bitrate based on file size and duration."""
        # Replicate bash script logic but with configurable target size
        # Leave 2MB buffer for container overhead (similar to bash script using 23MB for 25MB target)
        effective_size_mb = max(1, target_size_mb - 2)  # Ensure at least 1MB
        return int(effective_size_mb * 8 * 1000 / duration_seconds)
```

#### D. Audio Processor (`processors/audio_processor.py`)
```python
class AudioProcessor(BaseProcessor):
    """Handles audio file compression."""

    def __init__(self, settings: BossSettings):
        super().__init__(settings)
        self.supported_extensions = [
            'mp3', 'wav', 'm4a', 'flac', 'aac', 'ogg', 'wma'
        ]
        self.min_bitrate_kbps = 32

    async def compress(
        self,
        input_path: Path,
        target_size_mb: int,
        output_path: Path
    ) -> CompressionResult:
        """
        Compress audio file using the same logic as bash script:
        1. Get duration using ffprobe
        2. Calculate target bitrate: (target_size_mb * 8 * 1000) / duration
        3. Apply minimum bitrate threshold
        4. Execute ffmpeg compression with libmp3lame
        """

        media_info = await self.get_media_info(input_path)

        # Calculate target bitrate
        target_bitrate = self._calculate_target_bitrate(
            target_size_mb, media_info.duration_seconds
        )

        if target_bitrate < self.min_bitrate_kbps:
            raise CompressionError(
                f"Target bitrate {target_bitrate}kbps is below minimum {self.min_bitrate_kbps}kbps"
            )

        # Execute ffmpeg compression
        return await self._execute_ffmpeg_compression(
            input_path, output_path, target_bitrate
        )
```

#### E. Image Processor (`processors/image_processor.py`) - **NEW**
```python
class ImageProcessor(BaseProcessor):
    """Handles image file compression."""

    def __init__(self, settings: BossSettings):
        super().__init__(settings)
        self.supported_extensions = [
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff'
        ]
        self.min_quality = 10  # Minimum quality percentage

    async def compress(
        self,
        input_path: Path,
        target_size_mb: int,
        output_path: Path
    ) -> CompressionResult:
        """
        Compress image file using PIL/Pillow or ffmpeg:
        1. For static images: Use PIL with quality adjustment
        2. For animated images (GIF): Use ffmpeg
        3. Progressive quality reduction until target size is reached
        """

        if input_path.suffix.lower() == '.gif':
            return await self._compress_animated_image(input_path, output_path, target_size_mb)
        else:
            return await self._compress_static_image(input_path, output_path, target_size_mb)
```

### 3. Data Models (`models.py`)
```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class MediaInfo(BaseModel):
    """Information about a media file."""
    file_path: Path
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    format_name: str
    codec_name: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CompressionSettings(BaseModel):
    """Settings for compression operation."""
    target_size_mb: int = 50  # Default changed to 50MB, configurable via BossSettings
    video_bitrate_ratio: float = 0.9
    audio_bitrate_ratio: float = 0.1
    min_video_bitrate_kbps: int = 125
    min_audio_bitrate_kbps: int = 32
    min_image_quality: int = 10
    ffmpeg_preset: str = "slow"
    hardware_acceleration: bool = True

class CompressionResult(BaseModel):
    """Result of a compression operation."""
    success: bool
    input_path: Path
    output_path: Optional[Path] = None
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    processing_time_seconds: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 4. FFmpeg Utilities (`utils/ffmpeg_utils.py`)
```python
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List

class FFmpegWrapper:
    """Wrapper for FFmpeg operations."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.ffmpeg_path = "ffmpeg"  # Could be configurable
        self.ffprobe_path = "ffprobe"

    async def get_media_info(self, file_path: Path) -> Dict[str, Any]:
        """Get media file information using ffprobe."""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {stderr.decode()}")

        return json.loads(stdout.decode())

    async def compress_video(
        self,
        input_path: Path,
        output_path: Path,
        video_bitrate_kbps: int,
        audio_bitrate_kbps: int,
        max_bitrate_kbps: int,
        preset: str = "slow"
    ) -> None:
        """Execute video compression using ffmpeg."""
        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "warning",
            "-stats",
            "-threads", "0",
            "-hwaccel", "auto",
            "-i", str(input_path),
            "-preset", preset,
            "-c:v", "libx264",
            "-b:v", f"{video_bitrate_kbps}k",
            "-c:a", "aac",
            "-b:a", f"{audio_bitrate_kbps}k",
            "-bufsize", f"{max_bitrate_kbps}k",
            "-minrate", "100k",
            "-maxrate", f"{max_bitrate_kbps}k",
            "-y",  # Overwrite output file
            str(output_path)
        ]

        await self._execute_ffmpeg_command(cmd)
```

### 5. Integration Points

#### A. Discord Bot Integration
Add compression commands to the existing downloads cog:
```python
# In src/boss_bot/bot/cogs/downloads.py

@commands.command(name="compress")
async def compress_media(self, ctx: commands.Context, attachment_url: str = None):
    """Compress a media file for Discord's 25MB limit."""

    # Get file (from attachment or URL)
    if attachment_url:
        file_path = await self._download_file(attachment_url)
    elif ctx.message.attachments:
        file_path = await self._download_attachment(ctx.message.attachments[0])
    else:
        await ctx.send("Please provide a file attachment or URL to compress.")
        return

    # Compress using the new compression manager
    compression_manager = CompressionManager(self.bot.settings)

    try:
        result = await compression_manager.compress_file(
            file_path,
            target_size_mb=None,  # Use default from settings
            output_dir=self.bot.settings.download_dir
        )

        if result.success:
            # Send the compressed file
            await ctx.send(
                f"Compressed from {result.original_size_bytes // (1024*1024)}MB "
                f"to {result.compressed_size_bytes // (1024*1024)}MB "
                f"(ratio: {result.compression_ratio:.2f})",
                file=discord.File(result.output_path)
            )
        else:
            await ctx.send(f"Compression failed: {result.error_message}")

    except CompressionError as e:
        await ctx.send(f"Cannot compress: {e}")
```

#### B. CLI Integration
Add compression commands to the CLI:
```python
# In src/boss_bot/cli/commands/compression.py

@app.command()
def compress(
    input_file: Path = typer.Argument(..., help="Input media file"),
    target_size: Optional[int] = typer.Option(None, help="Target size in MB (uses config default if not specified)"),
    output_dir: Optional[Path] = typer.Option(None, help="Output directory")
):
    """Compress media file to target size."""

    settings = BossSettings()
    manager = CompressionManager(settings)

    result = asyncio.run(manager.compress_file(
        input_file,
        target_size_mb=target_size,  # Will use settings default if None
        output_dir=output_dir
    ))

    if result.success:
        console.print(f" Compressed successfully: {result.output_path}")
        console.print(f"Original: {result.original_size_bytes // (1024*1024)}MB")
        console.print(f"Compressed: {result.compressed_size_bytes // (1024*1024)}MB")
        console.print(f"Ratio: {result.compression_ratio:.2f}")
    else:
        console.print(f"L Compression failed: {result.error_message}")
        raise typer.Exit(1)
```

### 6. Configuration Integration

#### A. Environment Variables
Add to `src/boss_bot/core/env.py`:
```python
class BossSettings(BaseSettings):
    # ... existing settings ...

    # Compression settings
    compression_max_upload_size_mb: int = Field(default=50, description="Maximum upload size for compression target in MB")
    compression_video_bitrate_ratio: float = Field(default=0.9, description="Video bitrate allocation ratio")
    compression_audio_bitrate_ratio: float = Field(default=0.1, description="Audio bitrate allocation ratio")
    compression_min_video_bitrate: int = Field(default=125, description="Minimum video bitrate in kbps")
    compression_min_audio_bitrate: int = Field(default=32, description="Minimum audio bitrate in kbps")
    compression_ffmpeg_preset: str = Field(default="slow", description="FFmpeg encoding preset")
    compression_hardware_acceleration: bool = Field(default=True, description="Enable hardware acceleration")
```

#### B. Environment Variable Examples
```bash
# Set custom compression target (default: 50MB)
export COMPRESSION_MAX_UPLOAD_SIZE_MB=25  # Discord limit
export COMPRESSION_MAX_UPLOAD_SIZE_MB=100 # Larger limit for other platforms

# Adjust compression quality settings
export COMPRESSION_VIDEO_BITRATE_RATIO=0.85  # Give more to audio
export COMPRESSION_AUDIO_BITRATE_RATIO=0.15
export COMPRESSION_MIN_VIDEO_BITRATE=200     # Higher quality minimums
export COMPRESSION_MIN_AUDIO_BITRATE=64

# Performance settings
export COMPRESSION_FFMPEG_PRESET=fast       # Faster encoding
export COMPRESSION_HARDWARE_ACCELERATION=false  # Disable HW accel
```

### 7. Testing Strategy

#### A. Unit Tests
```python
# tests/test_core/test_compression/test_video_processor.py

class TestVideoProcessor:
    @pytest.mark.asyncio
    async def test_compress_video_success(self, fixture_settings_test, tmp_path):
        """Test successful video compression."""

        processor = VideoProcessor(fixture_settings_test)

        # Create test video file (or use fixture)
        input_file = tmp_path / "test_video.mp4"
        output_file = tmp_path / "compressed_video.mp4"

        result = await processor.compress(input_file, 25, output_file)

        assert result.success
        assert result.output_path.exists()
        assert result.compressed_size_bytes < result.original_size_bytes

    @pytest.mark.asyncio
    async def test_compress_video_bitrate_too_low(self, fixture_settings_test, tmp_path):
        """Test compression failure when target bitrate is too low."""

        processor = VideoProcessor(fixture_settings_test)

        # Create very long video that would result in low bitrate
        input_file = tmp_path / "long_video.mp4"
        output_file = tmp_path / "compressed_video.mp4"

        with pytest.raises(CompressionError, match="Target.*bitrate.*below minimum"):
            await processor.compress(input_file, 25, output_file)
```

#### B. Integration Tests
```python
# tests/test_bot/test_cogs/test_compression.py

class TestCompressionCog:
    @pytest.mark.asyncio
    async def test_compress_command_success(self, fixture_mock_bot_test, mocker):
        """Test compression command with successful compression."""

        # Mock the compression manager
        mock_manager = mocker.Mock()
        mock_result = CompressionResult(
            success=True,
            input_path=Path("test.mp4"),
            output_path=Path("compressed.mp4"),
            original_size_bytes=50 * 1024 * 1024,  # 50MB
            compressed_size_bytes=24 * 1024 * 1024,  # 24MB
            compression_ratio=0.48,
            processing_time_seconds=30.0
        )
        mock_manager.compress_file.return_value = mock_result

        # Test the command
        cog = CompressionCog(fixture_mock_bot_test)
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()

        await cog.compress_media.callback(cog, ctx, "http://example.com/video.mp4")

        # Verify the response
        ctx.send.assert_called_once()
        assert "Compressed from 50MB to 24MB" in ctx.send.call_args[0][0]
```

### 8. Migration Path

#### Phase 1: Core Infrastructure
1.  Create base module structure
2.  Implement data models and configuration
3.  Create FFmpeg wrapper utilities
4.  Implement base processor class

#### Phase 2: Media Processors
1.  Implement video processor (direct bash script port)
2.  Implement audio processor (direct bash script port)
3.  Implement image processor (new functionality)
4.  Add comprehensive error handling

#### Phase 3: Integration
1.  Add Discord bot commands
2.  Add CLI commands
3.  Update configuration system
4.  Add monitoring and logging

#### Phase 4: Testing & Validation
1.  Unit tests for all processors
2.  Integration tests with bot
3.  Performance testing
4.  Validate output quality

#### Phase 5: Advanced Features
1. = Batch compression
2. = Progress tracking for large files
3. = Quality presets (fast/balanced/high-quality)
4. = Custom output formats

### 9. Dependencies

#### New Dependencies to Add
```toml
# In pyproject.toml
[project.dependencies]
# ... existing dependencies ...
"pillow>=10.0.0",  # For image processing
"ffmpeg-python>=0.2.0",  # Alternative FFmpeg wrapper (optional)
```

#### System Dependencies
- FFmpeg (must be installed on system)
- FFprobe (usually comes with FFmpeg)

### 10. Error Handling & Edge Cases

#### A. Common Error Scenarios
1. **File not found**: Clear error message with file path
2. **Unsupported format**: List supported formats in error
3. **Insufficient compression**: Suggest alternative approaches
4. **FFmpeg not available**: Guide user to install FFmpeg
5. **Disk space issues**: Check available space before compression
6. **Corrupted files**: Validate input files before processing

#### B. Validation Rules
```python
class CompressionValidator:
    """Validates compression operations."""

    def validate_input_file(self, file_path: Path) -> None:
        """Validate input file exists and is readable."""
        if not file_path.exists():
            raise CompressionError(f"Input file not found: {file_path}")

        if not file_path.is_file():
            raise CompressionError(f"Input path is not a file: {file_path}")

        if file_path.stat().st_size == 0:
            raise CompressionError(f"Input file is empty: {file_path}")

    def validate_target_size(self, target_size_mb: int) -> None:
        """Validate target size is reasonable."""
        if target_size_mb < 1:
            raise CompressionError("Target size must be at least 1MB")

        if target_size_mb > 1000:  # 1GB
            raise CompressionError("Target size cannot exceed 1GB")
```

### 11. Performance Considerations

#### A. Async Processing
- All compression operations use async/await
- Non-blocking I/O for file operations
- Concurrent processing for batch operations

#### B. Resource Management
- Temporary file cleanup
- Memory usage monitoring
- CPU usage throttling options

#### C. Caching
- Cache media info for recently processed files
- Reuse compression settings for similar files

### 12. Future Enhancements

#### A. Advanced Compression
- Multi-pass encoding for better quality
- Adaptive bitrate based on content analysis
- HDR and high-resolution support

#### B. Cloud Integration
- Upload compressed files to cloud storage
- Streaming compression for large files
- Distributed processing

#### C. AI Integration
- Content-aware compression (preserve important scenes)
- Quality assessment using computer vision
- Automatic parameter tuning

## Summary

This plan provides a comprehensive migration path from the bash script to a robust Python module system that:

1. **Preserves existing functionality** - Direct port of bash script logic with configurable target sizes
2. **Follows project patterns** - Uses existing architecture and conventions
3. **Extends capabilities** - Adds image compression and advanced features
4. **Integrates seamlessly** - Works with Discord bot and CLI
5. **Maintains reliability** - Comprehensive testing and error handling
6. **Enables future growth** - Modular design for easy extension
7. **Configurable limits** - Default 50MB target with environment variable control for different platforms

The modular design allows each media type to be developed and tested independently while providing a unified interface for compression operations. The configurable upload size makes it suitable for Discord (25MB), Slack (1GB), Teams (250MB), and other platforms with different file size limits.
