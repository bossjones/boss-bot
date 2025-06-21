"""Test media file detection utilities."""

import pytest
from pathlib import Path

from boss_bot.core.uploads.utils.file_detector import MediaFileDetector
from boss_bot.core.uploads.models import MediaType


class TestMediaFileDetector:
    """Test media file detection functionality."""

    @pytest.fixture
    def detector(self):
        """Create MediaFileDetector instance."""
        return MediaFileDetector()

    @pytest.fixture
    def test_files_dir(self, tmp_path):
        """Create test directory with various file types."""
        # Video files
        (tmp_path / "video.mp4").write_bytes(b"video content")
        (tmp_path / "movie.avi").write_bytes(b"movie content")
        (tmp_path / "clip.webm").write_bytes(b"clip content")

        # Audio files
        (tmp_path / "song.mp3").write_bytes(b"song content")
        (tmp_path / "audio.wav").write_bytes(b"audio content")
        (tmp_path / "track.flac").write_bytes(b"track content")

        # Image files
        (tmp_path / "photo.jpg").write_bytes(b"photo content")
        (tmp_path / "image.png").write_bytes(b"image content")
        (tmp_path / "pic.gif").write_bytes(b"pic content")

        # Non-media files
        (tmp_path / "document.txt").write_bytes(b"text content")
        (tmp_path / "data.json").write_bytes(b"json content")
        (tmp_path / "script.py").write_bytes(b"python content")

        # Subdirectory with media files
        subdir = tmp_path / "subfolder"
        subdir.mkdir()
        (subdir / "nested_video.mkv").write_bytes(b"nested video")
        (subdir / "nested_audio.opus").write_bytes(b"nested audio")

        return tmp_path

    @pytest.mark.asyncio
    async def test_find_media_files_all_types(self, detector, test_files_dir):
        """Test finding all media files in directory."""
        media_files = await detector.find_media_files(test_files_dir)

        # Should find 11 media files (9 in root + 2 in subdirectory)
        assert len(media_files) == 11

        # Verify all files are MediaFile objects with correct attributes
        for media_file in media_files:
            assert media_file.path.exists()
            assert media_file.filename == media_file.path.name
            assert media_file.size_bytes > 0
            assert media_file.media_type != MediaType.UNKNOWN

    @pytest.mark.asyncio
    async def test_find_media_files_by_type(self, detector, test_files_dir):
        """Test filtering media files by type."""
        media_files = await detector.find_media_files(test_files_dir)

        # Count files by type
        video_files = detector.filter_by_type(media_files, MediaType.VIDEO)
        audio_files = detector.filter_by_type(media_files, MediaType.AUDIO)
        image_files = detector.filter_by_type(media_files, MediaType.IMAGE)

        # Should have 4 video files (3 in root + 1 in subdir)
        assert len(video_files) == 4
        # Should have 4 audio files (3 in root + 1 in subdir)
        assert len(audio_files) == 4
        # Should have 3 image files (all in root)
        assert len(image_files) == 3

    @pytest.mark.asyncio
    async def test_find_media_files_empty_directory(self, detector, tmp_path):
        """Test finding media files in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        media_files = await detector.find_media_files(empty_dir)
        assert len(media_files) == 0

    @pytest.mark.asyncio
    async def test_find_media_files_nonexistent_directory(self, detector, tmp_path):
        """Test finding media files in non-existent directory."""
        nonexistent_dir = tmp_path / "does_not_exist"

        media_files = await detector.find_media_files(nonexistent_dir)
        assert len(media_files) == 0

    @pytest.mark.asyncio
    async def test_find_media_files_no_media(self, detector, tmp_path):
        """Test finding media files in directory with no media files."""
        # Create only non-media files
        (tmp_path / "document.txt").write_bytes(b"text")
        (tmp_path / "data.json").write_bytes(b"json")
        (tmp_path / "README.md").write_bytes(b"readme")

        media_files = await detector.find_media_files(tmp_path)
        assert len(media_files) == 0

    def test_is_media_file_video_extensions(self, detector):
        """Test video file extension detection."""
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"]

        for ext in video_extensions:
            test_path = Path(f"test{ext}")
            assert detector._is_media_file(test_path)

        # Test case insensitivity
        assert detector._is_media_file(Path("test.MP4"))
        assert detector._is_media_file(Path("test.AVI"))

    def test_is_media_file_audio_extensions(self, detector):
        """Test audio file extension detection."""
        audio_extensions = [".mp3", ".wav", ".flac", ".aac", ".opus", ".ogg"]

        for ext in audio_extensions:
            test_path = Path(f"test{ext}")
            assert detector._is_media_file(test_path)

        # Test case insensitivity
        assert detector._is_media_file(Path("test.MP3"))
        assert detector._is_media_file(Path("test.WAV"))

    def test_is_media_file_image_extensions(self, detector):
        """Test image file extension detection."""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]

        for ext in image_extensions:
            test_path = Path(f"test{ext}")
            assert detector._is_media_file(test_path)

        # Test case insensitivity
        assert detector._is_media_file(Path("test.JPG"))
        assert detector._is_media_file(Path("test.PNG"))

    def test_is_media_file_non_media_extensions(self, detector):
        """Test non-media file extension rejection."""
        non_media_extensions = [".txt", ".json", ".py", ".html", ".css", ".js", ".md"]

        for ext in non_media_extensions:
            test_path = Path(f"test{ext}")
            assert not detector._is_media_file(test_path)

    def test_determine_media_type_video(self, detector):
        """Test video media type determination."""
        video_files = ["movie.mp4", "clip.avi", "video.mkv", "film.webm"]

        for filename in video_files:
            media_type = detector._determine_media_type(Path(filename))
            assert media_type == MediaType.VIDEO

    def test_determine_media_type_audio(self, detector):
        """Test audio media type determination."""
        audio_files = ["song.mp3", "track.wav", "music.flac", "audio.opus"]

        for filename in audio_files:
            media_type = detector._determine_media_type(Path(filename))
            assert media_type == MediaType.AUDIO

    def test_determine_media_type_image(self, detector):
        """Test image media type determination."""
        image_files = ["photo.jpg", "picture.png", "animation.gif", "image.webp"]

        for filename in image_files:
            media_type = detector._determine_media_type(Path(filename))
            assert media_type == MediaType.IMAGE

    def test_determine_media_type_unknown(self, detector):
        """Test unknown media type for non-media files."""
        non_media_files = ["document.txt", "data.json", "script.py"]

        for filename in non_media_files:
            media_type = detector._determine_media_type(Path(filename))
            assert media_type == MediaType.UNKNOWN

    @pytest.mark.asyncio
    async def test_get_total_size(self, detector, test_files_dir):
        """Test calculating total size of media files."""
        media_files = await detector.find_media_files(test_files_dir)

        total_size = detector.get_total_size(media_files)

        # Total size should be positive and equal sum of individual file sizes
        assert total_size > 0
        expected_total = sum(f.size_bytes for f in media_files)
        assert total_size == expected_total

    @pytest.mark.asyncio
    async def test_get_total_size_empty_list(self, detector):
        """Test calculating total size of empty file list."""
        total_size = detector.get_total_size([])
        assert total_size == 0

    @pytest.mark.asyncio
    async def test_find_media_files_inaccessible_file(self, detector, tmp_path):
        """Test handling files that cannot be accessed."""
        # Create a file
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"content")

        # Make the parent directory unreadable (Unix-like systems)
        import os
        import stat
        if os.name != 'nt':  # Skip on Windows
            original_mode = tmp_path.stat().st_mode
            try:
                tmp_path.chmod(0o000)  # Remove all permissions

                media_files = await detector.find_media_files(tmp_path)
                # Should handle the error gracefully and return empty list
                assert len(media_files) == 0

            finally:
                # Restore permissions
                tmp_path.chmod(original_mode)

    def test_filter_by_type_mixed_list(self, detector, tmp_path):
        """Test filtering mixed media file types."""
        # Create MediaFile objects of different types
        from boss_bot.core.uploads.models import MediaFile

        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"video")

        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"audio")

        image_file = tmp_path / "image.jpg"
        image_file.write_bytes(b"image")

        media_files = [
            MediaFile(
                path=video_file,
                filename="video.mp4",
                size_bytes=5,
                media_type=MediaType.VIDEO
            ),
            MediaFile(
                path=audio_file,
                filename="audio.mp3",
                size_bytes=5,
                media_type=MediaType.AUDIO
            ),
            MediaFile(
                path=image_file,
                filename="image.jpg",
                size_bytes=5,
                media_type=MediaType.IMAGE
            )
        ]

        # Test filtering each type
        videos = detector.filter_by_type(media_files, MediaType.VIDEO)
        audios = detector.filter_by_type(media_files, MediaType.AUDIO)
        images = detector.filter_by_type(media_files, MediaType.IMAGE)

        assert len(videos) == 1
        assert len(audios) == 1
        assert len(images) == 1
        assert videos[0].media_type == MediaType.VIDEO
        assert audios[0].media_type == MediaType.AUDIO
        assert images[0].media_type == MediaType.IMAGE
