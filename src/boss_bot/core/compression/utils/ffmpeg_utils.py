"""FFmpeg wrapper utilities for media operations."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from boss_bot.core.compression.models import CompressionError, MediaInfo
from boss_bot.core.env import BossSettings


class FFmpegError(CompressionError):
    """Exception raised when FFmpeg operations fail."""

    pass


class FFmpegWrapper:
    """Wrapper for FFmpeg operations."""

    def __init__(self, settings: BossSettings):
        """Initialize FFmpeg wrapper.

        Args:
            settings: Boss-Bot settings object
        """
        self.settings = settings
        self.ffmpeg_path = "ffmpeg"  # Could be configurable via settings
        self.ffprobe_path = "ffprobe"

    async def get_media_info(self, file_path: Path) -> MediaInfo:
        """Get media file information using ffprobe.

        Args:
            file_path: Path to media file

        Returns:
            MediaInfo object with file details

        Raises:
            FFmpegError: If ffprobe fails
        """
        raw_info = await self._get_raw_media_info(file_path)
        return self._parse_media_info(file_path, raw_info)

    async def _get_raw_media_info(self, file_path: Path) -> dict[str, Any]:
        """Get raw media information using ffprobe.

        Args:
            file_path: Path to media file

        Returns:
            Raw ffprobe output as dictionary

        Raises:
            FFmpegError: If ffprobe fails
        """
        cmd = [
            self.ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {stderr.decode()}")

        try:
            return json.loads(stdout.decode())  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse ffprobe output: {e}")

    def _parse_media_info(self, file_path: Path, raw_info: dict[str, Any]) -> MediaInfo:
        """Parse raw ffprobe output into MediaInfo object.

        Args:
            file_path: Path to media file
            raw_info: Raw ffprobe output

        Returns:
            MediaInfo object
        """
        format_info = raw_info.get("format", {})
        streams = raw_info.get("streams", [])

        # Get video stream info (first video stream)
        video_stream: dict[str, Any] = next((s for s in streams if s.get("codec_type") == "video"), {})

        # Get audio stream info (first audio stream)
        audio_stream: dict[str, Any] = next((s for s in streams if s.get("codec_type") == "audio"), {})

        # Use video stream if available, otherwise audio stream
        primary_stream = video_stream or audio_stream

        duration_seconds = None
        if format_info.get("duration"):
            try:
                duration_seconds = float(format_info["duration"])
            except (ValueError, TypeError):
                pass

        bitrate_kbps = None
        if format_info.get("bit_rate"):
            try:
                bitrate_kbps = int(float(format_info["bit_rate"]) / 1000)
            except (ValueError, TypeError):
                pass

        return MediaInfo(
            file_path=file_path,
            file_size_bytes=int(format_info.get("size", file_path.stat().st_size)),
            duration_seconds=duration_seconds,
            format_name=format_info.get("format_name", "unknown"),
            codec_name=primary_stream.get("codec_name"),
            width=primary_stream.get("width"),
            height=primary_stream.get("height"),
            bitrate_kbps=bitrate_kbps,
            metadata={
                "format": format_info,
                "streams": streams,
            },
        )

    async def compress_video(
        self,
        input_path: Path,
        output_path: Path,
        video_bitrate_kbps: int,
        audio_bitrate_kbps: int,
        max_bitrate_kbps: int,
        preset: str = "slow",
    ) -> None:
        """Execute video compression using ffmpeg.

        Replicates the bash script's ffmpeg command:
        ffmpeg -hide_banner -loglevel warning -stats -threads 0 -hwaccel auto -i "$input_file"
        -preset slow -c:v libx264 -b:v ${video_bitrate}k -c:a aac -b:a ${audio_bitrate}k
        -bufsize ${bitrate}k -minrate 100k -maxrate ${bitrate}k "output.mp4"

        Args:
            input_path: Input file path
            output_path: Output file path
            video_bitrate_kbps: Video bitrate in kbps
            audio_bitrate_kbps: Audio bitrate in kbps
            max_bitrate_kbps: Maximum bitrate in kbps
            preset: FFmpeg encoding preset

        Raises:
            FFmpegError: If compression fails
        """
        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "warning",
            "-stats",
            "-threads",
            "0",
        ]

        # Add hardware acceleration if enabled
        if getattr(self.settings, "compression_hardware_acceleration", True):
            cmd.extend(["-hwaccel", "auto"])

        cmd.extend(
            [
                "-i",
                str(input_path),
                "-preset",
                preset,
                "-c:v",
                "libx264",
                "-b:v",
                f"{video_bitrate_kbps}k",
                "-c:a",
                "aac",
                "-b:a",
                f"{audio_bitrate_kbps}k",
                "-bufsize",
                f"{max_bitrate_kbps}k",
                "-minrate",
                "100k",
                "-maxrate",
                f"{max_bitrate_kbps}k",
                "-y",  # Overwrite output file
                str(output_path),
            ]
        )

        await self._execute_ffmpeg_command(cmd)

    async def compress_audio(self, input_path: Path, output_path: Path, bitrate_kbps: int) -> None:
        """Execute audio compression using ffmpeg.

        Replicates the bash script's audio compression:
        ffmpeg -y -hide_banner -loglevel warning -stats -i "$input_file"
        -preset slow -c:a libmp3lame -b:a ${bitrate}k -bufsize ${bitrate}k
        -minrate 100k -maxrate ${bitrate}k "output.mp3"

        Args:
            input_path: Input file path
            output_path: Output file path
            bitrate_kbps: Target bitrate in kbps

        Raises:
            FFmpegError: If compression fails
        """
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output file
            "-hide_banner",
            "-loglevel",
            "warning",
            "-stats",
            "-i",
            str(input_path),
            "-preset",
            "slow",
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{bitrate_kbps}k",
            "-bufsize",
            f"{bitrate_kbps}k",
            "-minrate",
            "100k",
            "-maxrate",
            f"{bitrate_kbps}k",
            str(output_path),
        ]

        await self._execute_ffmpeg_command(cmd)

    async def _execute_ffmpeg_command(self, cmd: list[str]) -> None:
        """Execute FFmpeg command.

        Args:
            cmd: Command and arguments list

        Raises:
            FFmpegError: If command fails
        """
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            raise FFmpegError(f"FFmpeg failed (code {process.returncode}): {error_msg}")

    async def check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg binaries are available.

        Returns:
            True if both ffmpeg and ffprobe are available
        """
        try:
            # Check ffmpeg
            process = await asyncio.create_subprocess_exec(
                self.ffmpeg_path, "-version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode != 0:
                return False

            # Check ffprobe
            process = await asyncio.create_subprocess_exec(
                self.ffprobe_path, "-version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0

        except FileNotFoundError:
            return False
