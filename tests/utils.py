"""Common utilities for tests."""

from __future__ import annotations

import re


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences from text for assertion testing.

    This is useful for testing CLI output that contains color codes,
    cursor control sequences, and other terminal formatting.

    Args:
        text: The text containing ANSI escape sequences

    Returns:
        The text with all ANSI escape sequences removed
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
