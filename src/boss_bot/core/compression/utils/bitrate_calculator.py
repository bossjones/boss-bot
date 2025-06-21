"""Bitrate calculation utilities."""

from typing import Tuple


class BitrateCalculator:
    """Utility class for bitrate calculations."""

    @staticmethod
    def calculate_target_bitrate(target_size_mb: int, duration_seconds: float, buffer_mb: int = 2) -> int:
        """Calculate target bitrate based on file size and duration.

        Replicates bash script logic but with configurable target size.
        Leave buffer for container overhead (similar to bash script using 23MB for 25MB target).

        Args:
            target_size_mb: Target file size in MB
            duration_seconds: Media duration in seconds
            buffer_mb: Buffer size to subtract from target

        Returns:
            Target bitrate in kbps
        """
        # Ensure at least 1MB after buffer
        effective_size_mb = max(1, target_size_mb - buffer_mb)
        return int(effective_size_mb * 8 * 1000 / duration_seconds)

    @staticmethod
    def allocate_video_audio_bitrates(
        total_bitrate_kbps: int, video_ratio: float = 0.9, audio_ratio: float = 0.1
    ) -> tuple[int, int]:
        """Allocate total bitrate between video and audio.

        Args:
            total_bitrate_kbps: Total bitrate to allocate
            video_ratio: Ratio for video (default 90%)
            audio_ratio: Ratio for audio (default 10%)

        Returns:
            Tuple of (video_bitrate_kbps, audio_bitrate_kbps)
        """
        video_bitrate = int(total_bitrate_kbps * video_ratio)
        audio_bitrate = int(total_bitrate_kbps * audio_ratio)
        return video_bitrate, audio_bitrate

    @staticmethod
    def validate_minimum_bitrates(
        video_bitrate_kbps: int, audio_bitrate_kbps: int, min_video_kbps: int = 125, min_audio_kbps: int = 32
    ) -> tuple[bool, str]:
        """Validate that bitrates meet minimum requirements.

        Args:
            video_bitrate_kbps: Video bitrate to validate
            audio_bitrate_kbps: Audio bitrate to validate
            min_video_kbps: Minimum video bitrate
            min_audio_kbps: Minimum audio bitrate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if video_bitrate_kbps < min_video_kbps:
            return False, f"Video bitrate {video_bitrate_kbps}kbps below minimum {min_video_kbps}kbps"

        if audio_bitrate_kbps < min_audio_kbps:
            return False, f"Audio bitrate {audio_bitrate_kbps}kbps below minimum {min_audio_kbps}kbps"

        return True, ""
