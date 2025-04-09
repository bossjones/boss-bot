"""Storage quota management for the boss-bot application."""

import os
from pathlib import Path
from typing import Dict, Tuple

from pydantic import BaseModel


class QuotaConfig(BaseModel):
    """Quota configuration."""

    max_total_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    max_user_size: int = 1 * 1024 * 1024 * 1024  # 1GB
    max_files_per_user: int = 1000


class QuotaManager:
    """Storage quota management."""

    def __init__(self, storage_root: Path, config: QuotaConfig | None = None) -> None:
        """Initialize quota manager."""
        self.storage_root = storage_root
        self.config = config or QuotaConfig()
        self.user_quotas: dict[str, dict[str, int]] = {}

    def get_directory_size(self, directory: Path) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        try:
            for entry in directory.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total

    def get_user_storage_info(self, user_id: str) -> dict[str, int | float]:
        """Get storage information for a user."""
        user_dir = self.storage_root / user_id

        if not user_dir.exists():
            return {"total_size": 0, "file_count": 0, "quota_used": 0.0}

        total_size = self.get_directory_size(user_dir)
        file_count = sum(1 for _ in user_dir.rglob("*") if _.is_file())

        return {
            "total_size": total_size,
            "file_count": file_count,
            "quota_used": total_size / self.config.max_user_size,
        }

    def check_user_quota(self, user_id: str, file_size: int) -> tuple[bool, str]:
        """Check if a file can be stored within user's quota."""
        info = self.get_user_storage_info(user_id)

        if info["file_count"] >= self.config.max_files_per_user:
            return False, f"User has reached maximum file count of {self.config.max_files_per_user}"

        if info["total_size"] + file_size > self.config.max_user_size:
            return False, "User quota would be exceeded"

        return True, ""

    def check_total_quota(self, file_size: int) -> tuple[bool, str]:
        """Check if a file can be stored within total quota."""
        total_size = self.get_directory_size(self.storage_root)

        if total_size + file_size > self.config.max_total_size:
            return False, "Total storage quota would be exceeded"

        return True, ""

    def get_quota_status(self) -> dict[str, int | float]:
        """Get overall quota status."""
        total_size = self.get_directory_size(self.storage_root)

        return {
            "total_size": total_size,
            "max_size": self.config.max_total_size,
            "usage_percent": (total_size / self.config.max_total_size) * 100,
        }


# Create global quota manager
quota_manager = QuotaManager(Path("storage"))
