"""Tests for verifying project structure."""
from pathlib import Path
import pytest


def test_project_structure():
    """Test that the project structure exists as defined in the story."""
    # Core project directories
    root = Path(__file__).parent.parent.parent
    assert (root / "src" / "boss_bot").is_dir()
    assert (root / "tests").is_dir()
    assert (root / "docs").is_dir()
    assert (root / "scripts").is_dir()
    # assert (root / ".vscode").is_dir()
    assert (root / ".github" / "workflows").is_dir()

    # Source code directories
    src_dirs = [
        "bot",
        "commands",
        "core",
        "downloaders",
        "schemas",
        "monitoring",
        "storage",
        "utils",
    ]
    for dir_name in src_dirs:
        assert (root / "src" / "boss_bot" / dir_name).is_dir()

    # Test directories
    test_dirs = [
        "test_bot",
        "test_commands",
        "test_downloaders",
        "test_storage",
        "cassettes",
    ]
    for dir_name in test_dirs:
        assert (root / "tests" / dir_name).is_dir()

    # Documentation directories
    assert (root / "docs" / "development").is_dir()
