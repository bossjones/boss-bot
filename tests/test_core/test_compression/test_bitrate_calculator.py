"""Tests for bitrate calculation utilities."""

import pytest

from boss_bot.core.compression.utils.bitrate_calculator import BitrateCalculator


class TestBitrateCalculator:
    """Tests for BitrateCalculator utility class."""

    def test_calculate_target_bitrate_basic(self):
        """Test basic bitrate calculation."""
        # Test with 25MB target for 100 seconds
        # Formula: (25 - 2) * 8 * 1000 / 100 = 1840 kbps
        bitrate = BitrateCalculator.calculate_target_bitrate(25, 100.0)
        assert bitrate == 1840

    def test_calculate_target_bitrate_with_buffer(self):
        """Test bitrate calculation with custom buffer."""
        # Test with 30MB target, 5MB buffer for 120 seconds
        # Formula: (30 - 5) * 8 * 1000 / 120 = 1666 kbps
        bitrate = BitrateCalculator.calculate_target_bitrate(30, 120.0, buffer_mb=5)
        assert bitrate == 1666

    def test_calculate_target_bitrate_minimum_size(self):
        """Test bitrate calculation ensures minimum 1MB after buffer."""
        # With 2MB target and 2MB buffer, should use 1MB effective size
        # Formula: 1 * 8 * 1000 / 60 = 133 kbps
        bitrate = BitrateCalculator.calculate_target_bitrate(2, 60.0, buffer_mb=2)
        assert bitrate == 133

        # With 1MB target and 2MB buffer, should still use 1MB effective size
        bitrate_small = BitrateCalculator.calculate_target_bitrate(1, 60.0, buffer_mb=2)
        assert bitrate_small == 133

    def test_calculate_target_bitrate_fractional_duration(self):
        """Test bitrate calculation with fractional duration."""
        # Test with 25MB target for 90.5 seconds
        # Formula: (25 - 2) * 8 * 1000 / 90.5 = 2033 kbps (truncated)
        bitrate = BitrateCalculator.calculate_target_bitrate(25, 90.5)
        assert bitrate == 2033

    def test_calculate_target_bitrate_zero_buffer(self):
        """Test bitrate calculation with zero buffer."""
        # Test with 25MB target, no buffer for 100 seconds
        # Formula: 25 * 8 * 1000 / 100 = 2000 kbps
        bitrate = BitrateCalculator.calculate_target_bitrate(25, 100.0, buffer_mb=0)
        assert bitrate == 2000

    def test_allocate_video_audio_bitrates_default(self):
        """Test default video/audio bitrate allocation (90/10)."""
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(1000)

        assert video_bitrate == 900  # 90%
        assert audio_bitrate == 100  # 10%

    def test_allocate_video_audio_bitrates_custom_ratios(self):
        """Test custom video/audio bitrate allocation."""
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(
            1000, video_ratio=0.8, audio_ratio=0.2
        )

        assert video_bitrate == 800  # 80%
        assert audio_bitrate == 200  # 20%

    def test_allocate_video_audio_bitrates_small_total(self):
        """Test allocation with small total bitrate."""
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(100)

        assert video_bitrate == 90   # 90%
        assert audio_bitrate == 10   # 10%

    def test_allocate_video_audio_bitrates_large_total(self):
        """Test allocation with large total bitrate."""
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(10000)

        assert video_bitrate == 9000   # 90%
        assert audio_bitrate == 1000   # 10%

    def test_allocate_video_audio_bitrates_fractional_result(self):
        """Test allocation handles fractional results by truncating."""
        # 1001 kbps total: 90% = 900.9, 10% = 100.1
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(1001)

        assert video_bitrate == 900   # Truncated from 900.9
        assert audio_bitrate == 100   # Truncated from 100.1

    def test_validate_minimum_bitrates_success(self):
        """Test successful bitrate validation."""
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=200,
            audio_bitrate_kbps=50
        )

        assert is_valid is True
        assert error_msg == ""

    def test_validate_minimum_bitrates_video_too_low(self):
        """Test validation fails when video bitrate is too low."""
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=100,  # Below default minimum of 125
            audio_bitrate_kbps=50
        )

        assert is_valid is False
        assert "Video bitrate 100kbps below minimum 125kbps" in error_msg

    def test_validate_minimum_bitrates_audio_too_low(self):
        """Test validation fails when audio bitrate is too low."""
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=200,
            audio_bitrate_kbps=20  # Below default minimum of 32
        )

        assert is_valid is False
        assert "Audio bitrate 20kbps below minimum 32kbps" in error_msg

    def test_validate_minimum_bitrates_both_too_low(self):
        """Test validation fails when both bitrates are too low."""
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=100,  # Below minimum
            audio_bitrate_kbps=20   # Below minimum
        )

        assert is_valid is False
        # Should return the first error encountered (video)
        assert "Video bitrate 100kbps below minimum 125kbps" in error_msg

    def test_validate_minimum_bitrates_custom_minimums(self):
        """Test validation with custom minimum values."""
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=150,
            audio_bitrate_kbps=40,
            min_video_kbps=200,  # Custom higher minimum
            min_audio_kbps=50    # Custom higher minimum
        )

        assert is_valid is False
        assert "Video bitrate 150kbps below minimum 200kbps" in error_msg

    def test_validate_minimum_bitrates_edge_cases(self):
        """Test validation at exact minimum values."""
        # Exactly at minimum should be valid
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=125,  # Exactly at minimum
            audio_bitrate_kbps=32    # Exactly at minimum
        )

        assert is_valid is True
        assert error_msg == ""

        # One below minimum should fail
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(
            video_bitrate_kbps=124,  # One below minimum
            audio_bitrate_kbps=32
        )

        assert is_valid is False
        assert "Video bitrate 124kbps below minimum 125kbps" in error_msg

    def test_complete_workflow_integration(self):
        """Test complete workflow using all calculator methods together."""
        # Simulate compressing a 2-minute video to 25MB
        target_size_mb = 25
        duration_seconds = 120.0

        # Step 1: Calculate target bitrate
        total_bitrate = BitrateCalculator.calculate_target_bitrate(target_size_mb, duration_seconds)
        assert total_bitrate == 1533  # (25-2) * 8 * 1000 / 120

        # Step 2: Allocate between video and audio
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(total_bitrate)
        assert video_bitrate == 1379  # 90% of 1533 (truncated)
        assert audio_bitrate == 153   # 10% of 1533 (truncated)

        # Step 3: Validate minimums
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(video_bitrate, audio_bitrate)
        assert is_valid is True
        assert error_msg == ""

    def test_workflow_integration_fails_validation(self):
        """Test workflow where final validation fails."""
        # Simulate compressing a long video to small size
        target_size_mb = 5
        duration_seconds = 300.0  # 5 minutes

        # Step 1: Calculate target bitrate
        total_bitrate = BitrateCalculator.calculate_target_bitrate(target_size_mb, duration_seconds)
        assert total_bitrate == 80  # (5-2) * 8 * 1000 / 300

        # Step 2: Allocate between video and audio
        video_bitrate, audio_bitrate = BitrateCalculator.allocate_video_audio_bitrates(total_bitrate)
        assert video_bitrate == 72   # 90% of 80
        assert audio_bitrate == 8    # 10% of 80

        # Step 3: Validate minimums - should fail
        is_valid, error_msg = BitrateCalculator.validate_minimum_bitrates(video_bitrate, audio_bitrate)
        assert is_valid is False
        assert "Video bitrate 72kbps below minimum 125kbps" in error_msg
