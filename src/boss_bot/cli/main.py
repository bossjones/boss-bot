"""boss_bot.cli"""

# pyright: reportMissingTypeStubs=false
# pylint: disable=no-member
# pylint: disable=no-value-for-parameter
# SOURCE: https://github.com/tiangolo/typer/issues/88#issuecomment-1732469681
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import traceback
import typing
from collections.abc import Awaitable, Callable, Iterable, Sequence
from enum import Enum
from functools import partial, wraps
from importlib import import_module, metadata
from importlib.metadata import version as importlib_metadata_version
from pathlib import Path
from re import Pattern
from types import FrameType
from typing import Annotated, Any, Dict, List, NoReturn, Optional, Set, Tuple, Type, Union

import rich
import typer
from rich.console import Console

import boss_bot
from boss_bot.__version__ import __version__
from boss_bot.bot.client import BossBot
from boss_bot.cli.commands import download_app
from boss_bot.core.env import BossSettings
from boss_bot.utils.asynctyper import AsyncTyper

# Set up logging
LOGGER = logging.getLogger(__name__)

APP = AsyncTyper()
console = Console()
cprint = console.print

# Add download commands
APP.add_typer(download_app, name="download")


# Load existing subcommands
def load_commands(directory: str = "subcommands"):
    script_dir = Path(__file__).parent
    subcommands_dir = script_dir / directory

    LOGGER.info(f"Loading subcommands from {subcommands_dir}")

    for filename in os.listdir(subcommands_dir):
        if filename.endswith("_cmd.py"):
            module_name = f"{__name__.split('.')[0]}.{directory}.{filename[:-3]}"
            module = import_module(module_name)
            if hasattr(module, "app"):
                APP.add_typer(module.app, name=filename[:-7])


def version_callback(version: bool) -> None:
    """Print the version of boss_bot."""
    if version:
        rich.print(f"boss_bot version: {__version__}")
        raise typer.Exit()


@APP.command()
def version() -> None:
    """Version command"""
    rich.print(f"boss_bot version: {__version__}")


@APP.command()
def deps() -> None:
    """Deps command"""
    rich.print(f"boss_bot version: {__version__}")
    rich.print(f"langchain_version: {importlib_metadata_version('langchain')}")
    rich.print(f"langchain_community_version: {importlib_metadata_version('langchain_community')}")
    rich.print(f"langchain_core_version: {importlib_metadata_version('langchain_core')}")
    rich.print(f"langchain_openai_version: {importlib_metadata_version('langchain_openai')}")
    rich.print(f"langchain_text_splitters_version: {importlib_metadata_version('langchain_text_splitters')}")
    rich.print(f"chromadb_version: {importlib_metadata_version('chromadb')}")
    rich.print(f"langsmith_version: {importlib_metadata_version('langsmith')}")
    rich.print(f"pydantic_version: {importlib_metadata_version('pydantic')}")
    rich.print(f"pydantic_settings_version: {importlib_metadata_version('pydantic_settings')}")
    rich.print(f"ruff_version: {importlib_metadata_version('ruff')}")


@APP.command()
def about() -> None:
    """About command"""
    typer.echo("This is BossBot CLI")


@APP.command()
def show() -> None:
    """Show command"""
    cprint("\nShow boss_bot", style="yellow")


@APP.command()
def config() -> None:
    """Show BossSettings configuration and environment variables"""
    import json

    from pydantic import SecretStr

    settings = BossSettings()

    cprint("\n[bold blue]BossBot Configuration[/bold blue]", style="bold blue")
    cprint("=" * 50, style="blue")

    # Get all fields from the settings
    for field_name, field_info in settings.model_fields.items():
        value = getattr(settings, field_name)

        # Handle SecretStr fields - don't unmask them
        if isinstance(value, SecretStr):
            display_value = "[yellow]<SECRET>[/yellow]"
        elif isinstance(value, (dict, list)):
            # Pretty print complex types
            display_value = json.dumps(value, indent=2, default=str)
        else:
            display_value = str(value)

        # Get field description from docstring if available
        description = field_info.description or ""

        cprint(f"\n[bold green]{field_name}[/bold green]: {display_value}")
        if description:
            cprint(f"  [dim]{description}[/dim]")

    cprint("\n" + "=" * 50, style="blue")
    cprint("[bold blue]Environment Variables Status[/bold blue]", style="bold blue")

    # Check key environment variables
    import os

    env_vars_to_check = [
        # Core settings
        "DISCORD_TOKEN",
        "OPENAI_API_KEY",
        "LANGCHAIN_API_KEY",
        "PREFIX",
        "DEBUG",
        "LOG_LEVEL",
        "ENVIRONMENT",
        # Feature flags
        "ENABLE_AI",
        "ENABLE_REDIS",
        "ENABLE_SENTRY",
        # Download settings
        "MAX_QUEUE_SIZE",
        "MAX_CONCURRENT_DOWNLOADS",
        "STORAGE_ROOT",
        "MAX_FILE_SIZE_MB",
        # Strategy feature flags
        "TWITTER_USE_API_CLIENT",
        "REDDIT_USE_API_CLIENT",
        "INSTAGRAM_USE_API_CLIENT",
        "YOUTUBE_USE_API_CLIENT",
        "DOWNLOAD_API_FALLBACK_TO_CLI",
        # Monitoring
        "ENABLE_METRICS",
        "METRICS_PORT",
        "ENABLE_HEALTH_CHECK",
        "HEALTH_CHECK_PORT",
    ]

    for var in env_vars_to_check:
        value = os.getenv(var)
        if value is not None:
            # Mask sensitive values
            if any(keyword in var for keyword in ["TOKEN", "SECRET", "PASSWORD", "API_KEY"]):
                display_value = "[yellow]<SET>[/yellow]"
            else:
                display_value = value
            cprint(f"[green]✓[/green] {var}: {display_value}")
        else:
            cprint(f"[red]✗[/red] {var}: [dim]not set[/dim]")


def main():
    APP()
    load_commands()


def entry():
    """Required entry point to enable hydra to work as a console_script."""
    main()  # pylint: disable=no-value-for-parameter


async def run_bot():
    """Run the Discord bot."""
    settings = BossSettings()
    bot = BossBot(settings)

    try:
        # Use the modern async context manager pattern
        async with bot:
            await bot.start(settings.discord_token.get_secret_value())
    except KeyboardInterrupt:
        print("\nShutting down...")


@APP.command()
def go() -> None:
    """Main entry point for BossAI"""
    typer.echo("Starting up BossAI Bot")
    asyncio.run(run_bot())


def handle_sigterm(signo: int, frame: FrameType | None) -> NoReturn:
    """Handle SIGTERM signal by exiting with the appropriate status code.

    Args:
        signo: The signal number received
        frame: The current stack frame (may be None)

    Returns:
        Never returns, always exits
    """
    sys.exit(128 + signo)  # this will raise SystemExit and cause atexit to be called


signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    APP()
