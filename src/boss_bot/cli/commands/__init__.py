"""CLI commands for boss-bot."""

from .assistants import app as assistants_app
from .download import app as download_app

__all__ = ["download_app", "assistants_app"]
