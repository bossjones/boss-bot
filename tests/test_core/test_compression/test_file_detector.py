"""Tests for file type detection utilities."""

import pytest
from pathlib import Path

from boss_bot.core.compression.utils.file_detector import FileTypeDetector, MediaType


class TestMediaType:
    """Tests for MediaType enum."""

    def test_media_type_values(self):
        """Test MediaType enum values."""
        assert MediaType.VIDEO.value == "video"
        assert MediaType.AUDIO.value == "audio"
        assert MediaType.IMAGE.value == "image"
        assert MediaType.UNKNOWN.value == "unknown"


class TestFileTypeDetector:
    """Tests for FileTypeDetector class."""

    def test_detector_initialization(self, fixture_file_detector_test):
        """Test detector initializes with correct extensions."""
        detector = fixture_file_detector_test

        # Check video extensions
        assert 'mp4' in detector.video_extensions
        assert 'avi' in detector.video_extensions
        assert 'mkv' in detector.video_extensions
        assert 'mov' in detector.video_extensions

        # Check audio extensions
        assert 'mp3' in detector.audio_extensions
        assert 'wav' in detector.audio_extensions
        assert 'm4a' in detector.audio_extensions
        assert 'flac' in detector.audio_extensions

        # Check image extensions
        assert 'jpg' in detector.image_extensions
        assert 'jpeg' in detector.image_extensions
        assert 'png' in detector.image_extensions
        assert 'gif' in detector.image_extensions

    def test_get_media_type_video(self, fixture_file_detector_test):
        """Test detecting video file types."""
        detector = fixture_file_detector_test

        video_files = [
            Path("test.mp4"),
            Path("test.avi"),
            Path("test.mkv"),
            Path("test.mov"),
            Path("test.flv"),
            Path("test.wmv"),
            Path("test.webm"),
            Path("test.mpeg"),
            Path("test.3gp"),
            Path("test.m4v")
        ]

        for video_file in video_files:
            assert detector.get_media_type(video_file) == MediaType.VIDEO

    def test_get_media_type_audio(self, fixture_file_detector_test):
        """Test detecting audio file types."""
        detector = fixture_file_detector_test

        audio_files = [
            Path("test.mp3"),
            Path("test.wav"),
            Path("test.m4a"),
            Path("test.flac"),
            Path("test.aac"),
            Path("test.ogg"),
            Path("test.wma")
        ]

        for audio_file in audio_files:
            assert detector.get_media_type(audio_file) == MediaType.AUDIO

    def test_get_media_type_image(self, fixture_file_detector_test):
        """Test detecting image file types."""
        detector = fixture_file_detector_test

        image_files = [
            Path("test.jpg"),
            Path("test.jpeg"),
            Path("test.png"),
            Path("test.gif"),
            Path("test.webp"),
            Path("test.bmp"),
            Path("test.tiff")
        ]

        for image_file in image_files:
            assert detector.get_media_type(image_file) == MediaType.IMAGE

    def test_get_media_type_unknown(self, fixture_file_detector_test):
        """Test detecting unknown file types."""
        detector = fixture_file_detector_test

        unknown_files = [
            Path("test.txt"),
            Path("test.doc"),
            Path("test.pdf"),
            Path("test.exe"),
            Path("test.unknown"),
            Path("test")  # No extension
        ]

        for unknown_file in unknown_files:
            assert detector.get_media_type(unknown_file) == MediaType.UNKNOWN

    def test_get_media_type_case_insensitive(self, fixture_file_detector_test):
        """Test that file type detection is case insensitive."""
        detector = fixture_file_detector_test

        # Test uppercase extensions
        assert detector.get_media_type(Path("test.MP4")) == MediaType.VIDEO
        assert detector.get_media_type(Path("test.MP3")) == MediaType.AUDIO
        assert detector.get_media_type(Path("test.JPG")) == MediaType.IMAGE

        # Test mixed case extensions
        assert detector.get_media_type(Path("test.Mp4")) == MediaType.VIDEO
        assert detector.get_media_type(Path("test.Mp3")) == MediaType.AUDIO
        assert detector.get_media_type(Path("test.JpG")) == MediaType.IMAGE

    def test_is_video_file(self, fixture_file_detector_test):
        """Test is_video_file method."""
        detector = fixture_file_detector_test

        assert detector.is_video_file(Path("test.mp4")) is True
        assert detector.is_video_file(Path("test.avi")) is True
        assert detector.is_video_file(Path("test.mp3")) is False
        assert detector.is_video_file(Path("test.jpg")) is False
        assert detector.is_video_file(Path("test.txt")) is False

    def test_is_audio_file(self, fixture_file_detector_test):
        """Test is_audio_file method."""
        detector = fixture_file_detector_test

        assert detector.is_audio_file(Path("test.mp3")) is True
        assert detector.is_audio_file(Path("test.wav")) is True
        assert detector.is_audio_file(Path("test.mp4")) is False
        assert detector.is_audio_file(Path("test.jpg")) is False
        assert detector.is_audio_file(Path("test.txt")) is False

    def test_is_image_file(self, fixture_file_detector_test):
        """Test is_image_file method."""
        detector = fixture_file_detector_test

        assert detector.is_image_file(Path("test.jpg")) is True
        assert detector.is_image_file(Path("test.png")) is True
        assert detector.is_image_file(Path("test.mp4")) is False
        assert detector.is_image_file(Path("test.mp3")) is False
        assert detector.is_image_file(Path("test.txt")) is False

    def test_is_supported_file(self, fixture_file_detector_test):
        """Test is_supported_file method."""
        detector = fixture_file_detector_test

        # Supported files
        assert detector.is_supported_file(Path("test.mp4")) is True
        assert detector.is_supported_file(Path("test.mp3")) is True
        assert detector.is_supported_file(Path("test.jpg")) is True

        # Unsupported files
        assert detector.is_supported_file(Path("test.txt")) is False
        assert detector.is_supported_file(Path("test.doc")) is False
        assert detector.is_supported_file(Path("test.pdf")) is False

    def test_get_supported_extensions_all(self, fixture_file_detector_test):
        """Test getting all supported extensions."""
        detector = fixture_file_detector_test

        all_extensions = detector.get_supported_extensions()

        # Check that it includes extensions from all media types
        assert 'mp4' in all_extensions  # video
        assert 'mp3' in all_extensions  # audio
        assert 'jpg' in all_extensions  # image

        # Check total count is reasonable (video + audio + image)
        assert len(all_extensions) > 15

    def test_get_supported_extensions_video(self, fixture_file_detector_test):
        """Test getting video extensions only."""
        detector = fixture_file_detector_test

        video_extensions = detector.get_supported_extensions(MediaType.VIDEO)

        assert 'mp4' in video_extensions
        assert 'avi' in video_extensions
        assert 'mkv' in video_extensions

        # Should not include audio or image extensions
        assert 'mp3' not in video_extensions
        assert 'jpg' not in video_extensions

    def test_get_supported_extensions_audio(self, fixture_file_detector_test):
        """Test getting audio extensions only."""
        detector = fixture_file_detector_test

        audio_extensions = detector.get_supported_extensions(MediaType.AUDIO)

        assert 'mp3' in audio_extensions
        assert 'wav' in audio_extensions
        assert 'flac' in audio_extensions

        # Should not include video or image extensions
        assert 'mp4' not in audio_extensions
        assert 'jpg' not in audio_extensions

    def test_get_supported_extensions_image(self, fixture_file_detector_test):
        """Test getting image extensions only."""
        detector = fixture_file_detector_test

        image_extensions = detector.get_supported_extensions(MediaType.IMAGE)

        assert 'jpg' in image_extensions
        assert 'png' in image_extensions
        assert 'gif' in image_extensions

        # Should not include video or audio extensions
        assert 'mp4' not in image_extensions
        assert 'mp3' not in image_extensions

    def test_get_supported_extensions_unknown(self, fixture_file_detector_test):
        """Test getting extensions for unknown media type returns all."""
        detector = fixture_file_detector_test

        # Passing UNKNOWN should return all extensions
        all_extensions = detector.get_supported_extensions(MediaType.UNKNOWN)

        assert 'mp4' in all_extensions  # video
        assert 'mp3' in all_extensions  # audio
        assert 'jpg' in all_extensions  # image

    def test_get_supported_extensions_returns_copy(self, fixture_file_detector_test):
        """Test that get_supported_extensions returns a copy, not the original set."""
        detector = fixture_file_detector_test

        video_extensions = detector.get_supported_extensions(MediaType.VIDEO)
        original_size = len(video_extensions)

        # Modify the returned set
        video_extensions.add('fake_extension')

        # Original detector should be unchanged
        video_extensions_new = detector.get_supported_extensions(MediaType.VIDEO)
        assert len(video_extensions_new) == original_size
        assert 'fake_extension' not in video_extensions_new
