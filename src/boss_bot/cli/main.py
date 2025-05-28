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


@APP.command()
def show_configs() -> None:
    """Show gallery-dl and yt-dlp configuration files"""
    import json
    from pathlib import Path

    cprint("\n[bold blue]Download Tool Configurations[/bold blue]", style="bold blue")
    cprint("=" * 60, style="blue")

    # Check for gallery-dl config
    gallery_dl_configs = [
        Path.home() / ".config" / "gallery-dl" / "config.json",
        Path.home() / ".gallery-dl.conf",
        Path.cwd() / "gallery-dl.conf",
        Path("/etc/gallery-dl.conf"),
    ]

    cprint("\n[bold green]Gallery-dl Configuration[/bold green]")
    cprint("-" * 30, style="green")

    gallery_config_found = False
    for config_path in gallery_dl_configs:
        if config_path.exists():
            gallery_config_found = True
            cprint(f"[green]✓[/green] Found config: {config_path}")
            try:
                with open(config_path) as f:
                    config_content = f.read()

                # Try to parse as JSON first
                try:
                    config_data = json.loads(config_content)
                    # Mask sensitive data
                    masked_config = _mask_sensitive_config(config_data)
                    formatted_config = json.dumps(masked_config, indent=2)
                    cprint(f"\n[dim]{formatted_config}[/dim]")
                except json.JSONDecodeError:
                    # If not JSON, show as plain text (but mask sensitive lines)
                    lines = config_content.split("\n")
                    for line in lines[:20]:  # Show first 20 lines
                        if any(keyword in line.lower() for keyword in ["password", "token", "key", "secret"]):
                            # Mask the value part
                            if "=" in line or ":" in line:
                                separator = "=" if "=" in line else ":"
                                key_part = line.split(separator)[0]
                                cprint(f"[dim]{key_part}{separator} <MASKED>[/dim]")
                            else:
                                cprint(f"[dim]{line}[/dim]")
                        else:
                            cprint(f"[dim]{line}[/dim]")
                    if len(lines) > 20:
                        cprint(f"[dim]... ({len(lines) - 20} more lines)[/dim]")
            except Exception as e:
                cprint(f"[red]Error reading config: {e}[/red]")
        else:
            cprint(f"[red]✗[/red] Not found: {config_path}")

    if not gallery_config_found:
        cprint("[yellow]ℹ️  No gallery-dl config found. Using default settings.[/yellow]")

    # Check for yt-dlp config
    cprint("\n[bold green]yt-dlp Configuration[/bold green]")
    cprint("-" * 25, style="green")

    yt_dlp_configs = [
        Path.home() / ".config" / "yt-dlp" / "config",
        Path.home() / ".config" / "yt-dlp" / "config.txt",
        Path.home() / "yt-dlp.conf",
        Path.cwd() / "yt-dlp.conf",
    ]

    yt_dlp_config_found = False
    for config_path in yt_dlp_configs:
        if config_path.exists():
            yt_dlp_config_found = True
            cprint(f"[green]✓[/green] Found config: {config_path}")
            try:
                with open(config_path) as f:
                    lines = f.readlines()
                    for line in lines[:30]:  # Show first 30 lines
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Mask sensitive options
                            if any(
                                keyword in line.lower()
                                for keyword in ["password", "token", "username", "key", "secret", "cookie"]
                            ):
                                if line.startswith("--"):
                                    option = line.split()[0] if " " in line else line
                                    cprint(f"[dim]{option} <MASKED>[/dim]")
                                else:
                                    cprint("[dim]<MASKED LINE>[/dim]")
                            else:
                                cprint(f"[dim]{line}[/dim]")
                        elif line.startswith("#"):
                            cprint(f"[dim green]{line}[/dim green]")
                    if len(lines) > 30:
                        cprint(f"[dim]... ({len(lines) - 30} more lines)[/dim]")
            except Exception as e:
                cprint(f"[red]Error reading config: {e}[/red]")
        else:
            cprint(f"[red]✗[/red] Not found: {config_path}")

    if not yt_dlp_config_found:
        cprint("[yellow]ℹ️  No yt-dlp config found. Using default settings.[/yellow]")

    # Show some common config locations info
    cprint("\n[bold blue]Configuration Help[/bold blue]")
    cprint("-" * 18, style="blue")
    cprint("[dim]Common config locations:[/dim]")
    cprint("[dim]• gallery-dl: ~/.config/gallery-dl/config.json or ~/.gallery-dl.conf[/dim]")
    cprint("[dim]• yt-dlp: ~/.config/yt-dlp/config or ~/yt-dlp.conf[/dim]")
    cprint("[dim]• Use 'gallery-dl --help' or 'yt-dlp --help' for configuration options[/dim]")


def _mask_sensitive_config(config_data: dict) -> dict:
    """Recursively mask sensitive configuration values."""
    if not isinstance(config_data, dict):
        return config_data

    masked_config = {}
    sensitive_keys = ["password", "token", "key", "secret", "username", "user", "auth", "cookie", "session"]

    for key, value in config_data.items():
        key_lower = key.lower()

        if any(sensitive in key_lower for sensitive in sensitive_keys):
            masked_config[key] = "<MASKED>"
        elif isinstance(value, dict):
            masked_config[key] = _mask_sensitive_config(value)
        elif isinstance(value, list):
            masked_config[key] = [_mask_sensitive_config(item) if isinstance(item, dict) else item for item in value]
        else:
            masked_config[key] = value

    return masked_config


@APP.command()
def fetch(
    urls: list[str] = typer.Argument(..., help="One or more URLs to download"),
    output_dir: str = typer.Option("./downloads", "--output", "-o", help="Output directory for downloads"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be downloaded without actually downloading"),
) -> None:
    """Download media from URLs using appropriate API client (gallery-dl or yt-dlp)"""
    import asyncio
    from pathlib import Path

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cprint("\n[bold blue]BossBot Media Downloader (API Mode)[/bold blue]", style="bold blue")
    cprint("=" * 60, style="blue")
    cprint(f"📁 Output directory: {output_path.absolute()}")
    cprint(f"🔗 URLs to process: {len(urls)}")

    if dry_run:
        cprint("[yellow]🏃 DRY RUN MODE - No actual downloads will occur[/yellow]")

    cprint("")

    # Run the async download process
    asyncio.run(_download_urls_async(urls, output_path, verbose, dry_run))


async def _download_urls_async(urls: list[str], output_dir: Path, verbose: bool, dry_run: bool) -> None:
    """Async function to handle URL downloads."""
    from boss_bot.core.downloads.clients.aio_gallery_dl import AsyncGalleryDL
    from boss_bot.core.downloads.clients.aio_yt_dlp import AsyncYtDlp
    from boss_bot.core.env import BossSettings

    settings = BossSettings()
    success_count = 0
    failed_count = 0

    for i, url in enumerate(urls, 1):
        cprint(f"\n[bold green]Processing URL {i}/{len(urls)}[/bold green]")
        cprint(f"🔗 {url}")

        # Determine which tool to use based on URL patterns
        tool, reason = _determine_download_tool(url)

        if dry_run:
            cprint(f"[yellow]Would use {tool}: {reason}[/yellow]")
            continue

        cprint(f"🔧 Using {tool}: {reason}")

        try:
            if tool == "yt-dlp":
                async with AsyncYtDlp(output_dir=output_dir) as yt_dlp_client:
                    success = await _download_with_ytdlp_api(yt_dlp_client, url, output_dir, verbose)
            else:  # gallery-dl
                async with AsyncGalleryDL(output_dir=output_dir) as gallery_dl_client:
                    success = await _download_with_gallery_dl_api(gallery_dl_client, url, output_dir, verbose)

            if success:
                success_count += 1
                cprint(f"[green]✅ Successfully downloaded from {url}[/green]")
            else:
                failed_count += 1
                cprint(f"[red]❌ Failed to download from {url}[/red]")

        except Exception as e:
            failed_count += 1
            cprint(f"[red]❌ Error downloading {url}: {e}[/red]")
            if verbose:
                import traceback

                cprint(f"[dim red]{traceback.format_exc()}[/dim red]")

    # Summary
    cprint("\n[bold blue]Download Summary[/bold blue]")
    cprint("-" * 20, style="blue")
    cprint(f"[green]✅ Successful: {success_count}[/green]")
    cprint(f"[red]❌ Failed: {failed_count}[/red]")
    cprint(f"📁 Files saved to: {output_dir.absolute()}")


def _determine_download_tool(url: str) -> tuple[str, str]:
    """Determine which download tool to use based on URL patterns.

    Args:
        url: The URL to analyze

    Returns:
        Tuple of (tool_name, reason)
    """
    import re

    url_lower = url.lower()

    # YouTube and video platforms - use yt-dlp
    youtube_patterns = [
        r"youtube\.com",
        r"youtu\.be",
        r"youtube-nocookie\.com",
        r"twitch\.tv",
        r"vimeo\.com",
        r"dailymotion\.com",
        r"tiktok\.com",
        r"vm\.tiktok\.com",
    ]

    for pattern in youtube_patterns:
        if re.search(pattern, url_lower):
            return "yt-dlp", f"Video platform detected ({pattern.replace(r'\.', '.')})"

    # Platforms typically better handled by gallery-dl
    gallery_dl_patterns = [
        r"twitter\.com",
        r"x\.com",
        r"instagram\.com",
        r"reddit\.com",
        r"imgur\.com",
        r"deviantart\.com",
        r"artstation\.com",
        r"pixiv\.net",
        r"danbooru\.donmai\.us",
        r"gelbooru\.com",
        r"pinterest\.com",
        r"tumblr\.com",
    ]

    for pattern in gallery_dl_patterns:
        if re.search(pattern, url_lower):
            return "gallery-dl", f"Gallery platform detected ({pattern.replace(r'\.', '.')})"

    # Default to yt-dlp for unknown URLs as it has broader support
    return "yt-dlp", "Unknown platform, defaulting to yt-dlp"


async def _download_with_ytdlp_api(client: AsyncYtDlp, url: str, output_dir: Path, verbose: bool) -> bool:
    """Download using yt-dlp API client.

    Args:
        client: AsyncYtDlp client instance
        url: URL to download
        output_dir: Output directory
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    try:
        if verbose:
            cprint(f"[dim]Using yt-dlp API client for {url}[/dim]")

        # Configure download options
        options = {
            "outtmpl": str(output_dir / "%(uploader)s - %(title)s.%(ext)s"),
            "writeinfojson": True,
            "embed_metadata": True,
        }

        # Perform download - the download method returns an AsyncIterator
        download_successful = False
        async for result in client.download(url, **options):
            if verbose:
                cprint(f"[dim]Download result: {result}[/dim]")
            download_successful = True  # If we get any result, consider it successful

        return download_successful

    except Exception as e:
        cprint(f"[red]❌ yt-dlp API error: {e}[/red]")
        if verbose:
            import traceback

            cprint(f"[dim red]{traceback.format_exc()}[/dim red]")
        return False


async def _download_with_gallery_dl_api(client: AsyncGalleryDL, url: str, output_dir: Path, verbose: bool) -> bool:
    """Download using gallery-dl API client.

    Args:
        client: AsyncGalleryDL client instance
        url: URL to download
        output_dir: Output directory
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    try:
        if verbose:
            cprint(f"[dim]Using gallery-dl API client for {url}[/dim]")

        # Configure download options as keyword arguments
        options = {
            "base_directory": str(output_dir),
        }

        # Perform download - the download method returns an AsyncIterator
        download_successful = False
        async for result in client.download(url, **options):
            if verbose:
                cprint(f"[dim]Download result: {result}[/dim]")
            download_successful = True  # If we get any result, consider it successful

        return download_successful

    except Exception as e:
        cprint(f"[red]❌ gallery-dl API error: {e}[/red]")
        if verbose:
            import traceback

            cprint(f"[dim red]{traceback.format_exc()}[/dim red]")
        return False


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
