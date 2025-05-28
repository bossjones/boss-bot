"""Asynchronous wrapper utils around gallery-dl for non-blocking downloads.

This module provides an asynchronous interface to gallery-dl operations by:
- Running gallery-dl operations in a thread pool
- Preventing event loop blocking during downloads
- Managing gallery-dl configuration and execution

The wrapper ensures efficient handling of gallery downloads while maintaining
responsiveness of the async application.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def get_default_gallery_dl_config_locations() -> list[Path]:
    """Get default gallery-dl config locations."""
    return [
        Path.home() / ".config" / "gallery-dl" / "config.json",
        Path.home() / ".gallery-dl.conf",
        Path.cwd() / "gallery-dl.conf",
        Path("/etc/gallery-dl.conf"),
        Path("/etc/gallery-dl/config.json"),
    ]
