"""Media compression processors for different file types."""

from .audio_processor import AudioProcessor
from .base_processor import BaseProcessor
from .image_processor import ImageProcessor
from .video_processor import VideoProcessor

__all__ = [
    "BaseProcessor",
    "VideoProcessor",
    "AudioProcessor",
    "ImageProcessor",
]
