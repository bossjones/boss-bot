"""boss_bot.cli"""

# pyright: reportMissingTypeStubs=false
# pylint: disable=no-member
# pylint: disable=no-value-for-parameter
# pylint: disable=no-name-in-module
# SOURCE: https://github.com/tiangolo/typer/issues/88#issuecomment-1732469681
from __future__ import annotations

# main.py or boss-bot application entry point
from boss_bot.monitoring.logging import early_init

# 🔥 STEP 1: Call early_init() FIRST - before ANY other imports
early_init()

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
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, NoReturn, Optional, Set, Tuple, Type, Union

import bpdb
import pysnooper
import rich
import typer
from rich.console import Console

import boss_bot
from boss_bot.__version__ import __version__
from boss_bot.bot.client import BossBot
from boss_bot.cli.commands import download_app
from boss_bot.core.env import BossSettings
from boss_bot.utils.asynctyper import AsyncTyper

if TYPE_CHECKING:
    from boss_bot.core.downloads.clients.aio_gallery_dl import AsyncGalleryDL
    from boss_bot.core.downloads.clients.aio_yt_dlp import AsyncYtDlp

# 🔥 STEP 3: Configure full logging features after imports
from boss_bot.core.env import BossSettings
from boss_bot.monitoring.logging import setup_boss_bot_logging

# Initialize boss-bot settings
settings = BossSettings()

# Configure logging with boss-bot integration
LOGGER = setup_boss_bot_logging(settings)


# Set up logging
# LOGGER = logging.getLogger(__name__)

APP = AsyncTyper()
console = Console()
cprint = console.print

# Add download commands
APP.add_typer(download_app, name="download")


# Load existing subcommands
def load_commands(directory: str = "subcommands"):
    script_dir = Path(__file__).parent
    subcommands_dir = script_dir / directory

    # Check if subcommands directory exists
    if not subcommands_dir.exists():
        LOGGER.debug(f"Subcommands directory {subcommands_dir} does not exist, skipping")
        return

    LOGGER.info(f"Loading subcommands from {subcommands_dir}")

    try:
        for filename in os.listdir(subcommands_dir):
            if filename.endswith("_cmd.py"):
                module_name = f"{__name__.split('.')[0]}.{directory}.{filename[:-3]}"
                module = import_module(module_name)
                if hasattr(module, "app"):
                    APP.add_typer(module.app, name=filename[:-7])
    except Exception as e:
        LOGGER.error(f"Error loading subcommands: {e}")


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
def show_configs(
    dump: bool = typer.Option(False, "--dump", help="Dump GalleryDLConfig as pretty-printed dictionary"),
) -> None:
    """Show gallery-dl and yt-dlp configuration files"""
    import json
    from pathlib import Path

    cprint("\n[bold blue]Download Tool Configurations[/bold blue]", style="bold blue")
    cprint("=" * 60, style="blue")
    from boss_bot.core.downloads.clients.aio_gallery_dl import get_default_gallery_dl_config_locations

    # Check for gallery-dl config
    gallery_dl_configs = get_default_gallery_dl_config_locations()

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

    # Handle --dump flag to show GalleryDLConfig dictionary
    if dump:
        cprint("\n[bold blue]GalleryDLConfig Dictionary Dump[/bold blue]")
        cprint("=" * 40, style="blue")

        try:
            from boss_bot.core.downloads.clients.config.gallery_dl_config import GalleryDLConfig

            # Create a default GalleryDLConfig instance
            config = GalleryDLConfig()
            config_dict = config.to_dict()

            # Pretty print the configuration dictionary
            formatted_config = json.dumps(config_dict, indent=2, default=str)
            cprint(formatted_config)

        except Exception as e:
            cprint(f"[red]❌ Error dumping GalleryDLConfig: {e}[/red]")


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

    settings = BossSettings()

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

    try:
        # Run the async download process
        asyncio.run(_download_urls_async(urls, output_path, verbose, dry_run))
    except Exception as e:
        print(f"{e}")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f"Error Class: {e.__class__}")
        output = f"[UNEXPECTED] {type(e).__name__}: {e}"
        print(output)
        print(f"exc_type: {exc_type}")
        print(f"exc_value: {exc_value}")
        traceback.print_tb(exc_traceback)

        # Only launch debugger if in dev mode and not in test mode
        if settings.debug:
            bpdb.pm()

        LOGGER.error("Error in gallery-dl download")
        # cprint(f"[red]❌ Error: {e}[/red]")
        # raise typer.Exit(1)


# @pysnooper.snoop(thread_info=True, max_variable_length=None, depth=10)
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

        if verbose:
            # Show equivalent command-line in verbose mode
            equivalent_cmd = _generate_ytdlp_command_equivalent(options, url, output_dir)
            cprint(f"[dim cyan]Equivalent command: {equivalent_cmd}[/dim cyan]")

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

            # Show equivalent command-line in verbose mode
            equivalent_cmd = await _generate_gallery_dl_command_equivalent(client, url, output_dir)
            cprint(f"[dim cyan]Equivalent command: {equivalent_cmd}[/dim cyan]")

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


async def _generate_gallery_dl_command_equivalent(client: AsyncGalleryDL, url: str, output_dir: Path) -> str:
    """Generate equivalent gallery-dl command line from client configuration.

    Args:
        client: AsyncGalleryDL client instance
        url: URL being processed
        output_dir: Output directory

    Returns:
        String representation of equivalent command
    """
    cmd_parts = ["gallery-dl"]

    # Get the effective configuration
    config = client.config_dict

    # Extract extractor config if available
    extractor_config = config.get("extractor", {})

    # Determine which platform/extractor is being used
    platform = _detect_platform_from_url(url)
    platform_config = extractor_config.get(platform, {}) if platform else {}

    # Add common global options
    if extractor_config.get("cookies-from-browser"):
        cmd_parts.append(f"--cookies-from-browser {extractor_config['cookies-from-browser']}")
    elif extractor_config.get("cookies"):
        cmd_parts.append(f"--cookies {extractor_config['cookies']}")

    if extractor_config.get("user-agent") or platform_config.get("user-agent"):
        user_agent = platform_config.get("user-agent") or extractor_config.get("user-agent")
        cmd_parts.append(f"--user-agent '{user_agent}'")

    # Add write options
    if extractor_config.get("writeinfojson", True):
        cmd_parts.append("--write-info-json")

    if extractor_config.get("write-metadata", True):
        cmd_parts.append("--write-metadata")

    # Add output directory
    if extractor_config.get("base-directory") or str(output_dir) != "./downloads":
        base_dir = extractor_config.get("base-directory", str(output_dir))
        cmd_parts.append(f"--dest '{base_dir}'")

    # Add filename template if specified for the platform
    if platform_config.get("filename"):
        filename_template = platform_config["filename"]
        cmd_parts.append(f"--filename '{filename_template}'")

    # Add directory structure if specified for the platform
    if platform_config.get("directory"):
        directory_template = platform_config["directory"]
        if isinstance(directory_template, list):
            directory_template = "/".join(directory_template)
        cmd_parts.append(f"--directory '{directory_template}'")

    # Add platform-specific options
    if platform == "instagram":
        if platform_config.get("videos", True):
            cmd_parts.append("--filter 'video or image'")
        if not platform_config.get("highlights", True):
            cmd_parts.append("--filter 'not highlight'")
        if not platform_config.get("stories", True):
            cmd_parts.append("--filter 'not story'")

    elif platform == "twitter":
        if platform_config.get("videos", True):
            cmd_parts.append("--filter 'video or image'")
        if platform_config.get("retweets", False):
            cmd_parts.append("--filter 'retweet'")

    elif platform == "reddit":
        if platform_config.get("comments", False):
            cmd_parts.append("--comments")
        if platform_config.get("morecomments", False):
            cmd_parts.append("--more-comments")

    # Add verbose flag (always on since we're in verbose mode)
    cmd_parts.append("-v")

    # Add the URL
    cmd_parts.append(f"'{url}'")

    return " ".join(cmd_parts)


def _generate_ytdlp_command_equivalent(options: dict, url: str, output_dir: Path) -> str:
    """Generate equivalent yt-dlp command line from options.

    Args:
        options: yt-dlp options dictionary
        url: URL being processed
        output_dir: Output directory

    Returns:
        String representation of equivalent command
    """
    cmd_parts = ["yt-dlp"]

    # Add output template
    if options.get("outtmpl"):
        cmd_parts.append(f"--output '{options['outtmpl']}'")

    # Add info json option
    if options.get("writeinfojson"):
        cmd_parts.append("--write-info-json")

    # Add metadata embedding
    if options.get("embed_metadata"):
        cmd_parts.append("--embed-metadata")

    # Add other common options that might be in the options dict
    if options.get("format"):
        cmd_parts.append(f"--format '{options['format']}'")

    if options.get("quality"):
        cmd_parts.append(f"--format 'best[height<={options['quality']}]'")

    if options.get("extract_flat"):
        cmd_parts.append("--flat-playlist")

    if options.get("no_playlist"):
        cmd_parts.append("--no-playlist")

    if options.get("verbose"):
        cmd_parts.append("--verbose")
    else:
        # Always add verbose since we're in verbose mode
        cmd_parts.append("-v")

    # Add cookies if specified
    if options.get("cookiefile"):
        cmd_parts.append(f"--cookies '{options['cookiefile']}'")

    # Add user agent if specified
    if options.get("user_agent"):
        cmd_parts.append(f"--user-agent '{options['user_agent']}'")

    # Add the URL
    cmd_parts.append(f"'{url}'")

    return " ".join(cmd_parts)


def _detect_platform_from_url(url: str) -> str | None:
    """Detect platform name from URL for configuration lookup.

    Args:
        url: URL to analyze

    Returns:
        Platform name or None if not detected
    """
    import re

    url_lower = url.lower()

    platform_patterns = {
        "twitter": [r"twitter\.com", r"x\.com"],
        "instagram": [r"instagram\.com"],
        "reddit": [r"reddit\.com"],
        "youtube": [r"youtube\.com", r"youtu\.be"],
        "tiktok": [r"tiktok\.com", r"vm\.tiktok\.com"],
        "imgur": [r"imgur\.com"],
        "tumblr": [r"tumblr\.com"],
        "pinterest": [r"pinterest\.com"],
        "deviantart": [r"deviantart\.com"],
        "pixiv": [r"pixiv\.net"],
    }

    for platform, patterns in platform_patterns.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return platform

    return None


def main():
    load_commands()
    APP()


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
def check_config() -> None:
    """Check and validate gallery-dl configuration using gallery-dl's config.load and GalleryDLConfig validation"""
    import json
    from pathlib import Path

    try:
        import gallery_dl.config
    except ImportError:
        cprint("[red]❌ gallery-dl is not installed or not available[/red]")
        cprint("[yellow]Install gallery-dl with: pip install gallery-dl[/yellow]")
        raise typer.Exit(1)

    try:
        from boss_bot.core.downloads.clients.config.gallery_dl_config import GalleryDLConfig
    except ImportError as e:
        cprint(f"[red]❌ Error importing GalleryDLConfig: {e}[/red]")
        raise typer.Exit(1)

    cprint("\n[bold blue]🔧 Gallery-dl Configuration Check[/bold blue]", style="bold blue")
    cprint("=" * 60, style="blue")

    # Step 1: Use gallery-dl's config.load to load configuration
    cprint("\n[bold green]1. Loading Configuration with gallery-dl[/bold green]")
    cprint("-" * 45, style="green")

    # Clear any existing config first
    gallery_dl.config.clear()

    try:
        # Use gallery-dl's config.load function (same as what gallery-dl uses internally)
        gallery_dl.config.load()
        raw_config = gallery_dl.config._config

        if not raw_config:
            cprint("[yellow]⚠️  No configuration loaded. Using defaults.[/yellow]")
            cprint("[dim]This means no config files were found in standard locations[/dim]")
            config_found = False
        else:
            cprint("[green]✅ Configuration loaded successfully[/green]")
            config_found = True

            # Show some basic info about loaded config
            config_sections = list(raw_config.keys())
            if config_sections:
                cprint(f"[dim green]📂 Found sections: {', '.join(config_sections)}[/dim green]")

    except Exception as e:
        cprint(f"[red]❌ Error loading configuration: {e}[/red]")
        raw_config = {}
        config_found = False

    # Step 2: Validate with GalleryDLConfig
    cprint("\n[bold green]2. Validating with GalleryDLConfig[/bold green]")
    cprint("-" * 40, style="green")

    try:
        if raw_config:
            # Try to create GalleryDLConfig from loaded config
            validated_config = GalleryDLConfig.from_dict(raw_config)
            cprint("[green]✅ Configuration is valid according to GalleryDLConfig schema[/green]")
            validation_success = True
        else:
            # Create default config for validation
            validated_config = GalleryDLConfig()
            cprint("[yellow]⚠️  Using default GalleryDLConfig (no custom config found)[/yellow]")
            validation_success = True

    except Exception as e:
        cprint(f"[red]❌ Configuration validation failed: {e}[/red]")
        validated_config = GalleryDLConfig()  # Use defaults
        validation_success = False

    # Step 3: Display configuration by sections (with sensitive data masked)
    if config_found and raw_config:
        cprint("\n[bold green]3. Configuration Overview[/bold green]")
        cprint("-" * 30, style="green")

        # Display each section
        _display_config_section("Extractor", raw_config.get("extractor", {}))
        _display_config_section("Downloader", raw_config.get("downloader", {}))
        _display_config_section("Output", raw_config.get("output", {}))
        _display_config_section("Postprocessor", raw_config.get("postprocessor", {}))

        # Show any additional sections
        standard_sections = {"extractor", "downloader", "output", "postprocessor"}
        additional_sections = set(raw_config.keys()) - standard_sections
        if additional_sections:
            for section in sorted(additional_sections):
                _display_config_section(f"Custom: {section}", raw_config[section])

    # Step 4: Show configuration file locations
    cprint("\n[bold green]4. Configuration File Status[/bold green]")
    cprint("-" * 35, style="green")

    # Check standard gallery-dl config locations
    from boss_bot.core.downloads.clients.aio_gallery_dl import get_default_gallery_dl_config_locations

    config_paths = get_default_gallery_dl_config_locations()

    found_configs = []
    for config_path in config_paths:
        if config_path.exists():
            found_configs.append(config_path)
            cprint(f"[green]✓[/green] Found: {config_path}")

            # Show file size and last modified
            try:
                stat = config_path.stat()
                size_kb = stat.st_size / 1024
                import datetime

                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                cprint(f"[dim]  Size: {size_kb:.1f} KB, Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            except Exception:
                pass
        else:
            cprint(f"[dim]✗ Not found: {config_path}[/dim]")

    if not found_configs:
        cprint("[yellow]⚠️  No configuration files found in standard locations[/yellow]")
        cprint("[dim]Consider creating a config file with: gallery-dl --help[/dim]")

    # Step 5: Summary
    cprint("\n[bold blue]📋 Summary[/bold blue]")
    cprint("=" * 15, style="blue")

    if config_found and validation_success:
        cprint("[green]🎉 Configuration is valid and loaded successfully![/green]")
        cprint(f"[green]📂 Found {len(found_configs)} config file(s)[/green]")
    elif config_found and not validation_success:
        cprint("[yellow]⚠️  Configuration loaded but has validation issues[/yellow]")
        cprint("[yellow]The config may still work, but consider reviewing the errors above[/yellow]")
    elif validation_success and not config_found:
        cprint("[cyan]ℹ️  No custom configuration found, using defaults[/cyan]")
        cprint("[cyan]This is normal for new installations[/cyan]")
    else:
        cprint("[red]❌ Configuration has issues that need attention[/red]")
        raise typer.Exit(1)


def _display_config_section(section_name: str, section_data: dict) -> None:
    """Display a configuration section with masked sensitive data."""
    if not section_data:
        return

    cprint(f"\n[bold cyan]{section_name}[/bold cyan]")

    # Mask sensitive data
    masked_data = _mask_sensitive_config(section_data)

    # Display in a compact format
    if isinstance(masked_data, dict):
        for key, value in masked_data.items():
            if isinstance(value, dict):
                cprint(f"  [yellow]{key}[/yellow]: {{...}} [dim]({len(value)} items)[/dim]")
            elif isinstance(value, list):
                cprint(f"  [yellow]{key}[/yellow]: [...] [dim]({len(value)} items)[/dim]")
            elif isinstance(value, str) and len(value) > 50:
                cprint(f"  [yellow]{key}[/yellow]: [dim]{value[:47]}...[/dim]")
            else:
                cprint(f"  [yellow]{key}[/yellow]: {value}")
    else:
        cprint(f"  {masked_data}")


@APP.command()
def doctor() -> None:
    """Run health checks to verify repository requirements"""
    cprint("\n[bold blue]🏥 BossBot Doctor - Health Check[/bold blue]", style="bold blue")
    cprint("=" * 50, style="blue")

    overall_status = True
    checks_passed = 0
    total_checks = 0

    # Check 1: Gallery-dl configuration validation
    total_checks += 1
    cprint("\n[bold green]1. Gallery-dl Configuration Validation[/bold green]")
    cprint("-" * 40, style="green")

    gallery_config_status = _check_gallery_dl_config()
    if gallery_config_status:
        checks_passed += 1
        cprint("[green]✅ Gallery-dl configuration is valid[/green]")
    else:
        overall_status = False
        cprint("[red]❌ Gallery-dl configuration issues detected[/red]")

    # Summary
    cprint("\n[bold blue]Health Check Summary[/bold blue]")
    cprint("=" * 25, style="blue")
    cprint(f"Checks passed: {checks_passed}/{total_checks}")

    if overall_status:
        cprint("[green]🎉 All health checks passed![/green]")
        cprint("[green]Your repository is ready to work properly.[/green]")
    else:
        cprint("[red]⚠️  Some health checks failed.[/red]")
        cprint("[yellow]Please address the issues above before proceeding.[/yellow]")
        raise typer.Exit(1)


def _check_gallery_dl_config() -> bool:
    """Check if gallery-dl configuration is valid.

    Returns:
        True if configuration is valid, False otherwise
    """
    import json
    from pathlib import Path

    # Define possible config locations in order of precedence
    gallery_dl_configs = [
        Path.cwd() / "gallery-dl.conf",
        Path.home() / ".gallery-dl.conf",
        Path.home() / ".config" / "gallery-dl" / "config.json",
        Path("/etc/gallery-dl.conf"),
    ]

    config_found = False
    config_valid = False

    for config_path in gallery_dl_configs:
        if config_path.exists():
            config_found = True
            cprint(f"[cyan]📁 Found config: {config_path}[/cyan]")

            try:
                with open(config_path, encoding="utf-8") as f:
                    config_content = f.read().strip()

                if not config_content:
                    cprint(f"[yellow]⚠️  Config file is empty: {config_path}[/yellow]")
                    continue

                # Try to parse as JSON
                try:
                    config_data = json.loads(config_content)

                    # Basic validation checks
                    if not isinstance(config_data, dict):
                        cprint(f"[red]❌ Config must be a JSON object: {config_path}[/red]")
                        continue

                    # Check for common configuration sections
                    valid_sections = ["extractor", "output", "downloader", "cache", "cookies"]
                    has_valid_sections = any(section in config_data for section in valid_sections)

                    if not has_valid_sections:
                        cprint(
                            f"[yellow]⚠️  Config lacks common sections (extractor, output, etc.): {config_path}[/yellow]"
                        )
                        cprint("[dim]This might still be valid but could be misconfigured[/dim]")

                    # Check extractor configuration if present
                    if "extractor" in config_data:
                        extractor_config = config_data["extractor"]
                        if isinstance(extractor_config, dict):
                            # Count configured extractors
                            configured_extractors = [
                                key
                                for key in extractor_config.keys()
                                if key not in ["base-directory", "user-agent", "cookies", "cookies-from-browser"]
                            ]
                            if configured_extractors:
                                cprint(
                                    f"[dim green]✓ Configured extractors: {', '.join(configured_extractors)}[/dim green]"
                                )

                    config_valid = True
                    cprint(f"[green]✅ Valid JSON configuration: {config_path}[/green]")
                    break  # Use first valid config found

                except json.JSONDecodeError as e:
                    cprint(f"[red]❌ Invalid JSON in {config_path}: {e}[/red]")
                    # Try to give helpful error context
                    lines = config_content.split("\n")
                    if hasattr(e, "lineno") and e.lineno <= len(lines):
                        error_line = lines[e.lineno - 1] if e.lineno > 0 else "N/A"
                        cprint(f"[dim red]Error near line {e.lineno}: {error_line}[/dim red]")
                    continue

            except Exception as e:
                cprint(f"[red]❌ Error reading {config_path}: {e}[/red]")
                continue

    if not config_found:
        cprint("[yellow]⚠️  No gallery-dl configuration file found[/yellow]")
        cprint("[dim]Searched locations:[/dim]")
        for config_path in gallery_dl_configs:
            cprint(f"[dim]  - {config_path}[/dim]")
        cprint("[dim]This will use gallery-dl defaults, which may not be optimal[/dim]")
        cprint("[dim]Consider creating a config file with: gallery-dl --help[/dim]")
        return False

    return config_valid


@APP.command()
def setup_config(
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt and create config file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without making modifications"),
) -> None:
    """Create a dummy gallery-dl configuration file at ~/.gallery-dl.conf"""
    import difflib
    import json
    import shutil
    from datetime import datetime
    from pathlib import Path

    config_path = Path.home() / ".gallery-dl.conf"

    # Define the dummy config content
    dummy_config = {
        "extractor": {
            "base-directory": "./gallery-dl/",
            "postprocessors": None,
            "archive": None,
            "cookies": None,
            "cookies-update": True,
            "proxy": None,
            "skip": True,
            "sleep": 0,
            "sleep-request": 0,
            "sleep-extractor": 0,
            "path-restrict": "auto",
            "path-replace": "_",
            "path-remove": "\\u0000-\\u001f\\u007f",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "path-strip": "auto",
            "path-extended": True,
            "extension-map": {"jpeg": "jpg", "jpe": "jpg", "jfif": "jpg", "jif": "jpg", "jfi": "jpg"},
            "artstation": {"external": False, "pro-first": True},
            "aryion": {"username": None, "password": None},
            "blogger": {"videos": True},
            "danbooru": {"username": None, "password": None, "ugoira": False},
            "deviantart": {
                "extra": False,
                "flat": True,
                "folders": False,
                "journals": "html",
                "mature": True,
                "metadata": False,
                "original": True,
                "quality": 100,
                "wait-min": 0,
            },
            "exhentai": {
                "username": None,
                "password": None,
                "domain": "auto",
                "limits": True,
                "original": True,
                "wait-min": 3.0,
                "wait-max": 6.0,
            },
            "flickr": {"videos": True, "size-max": None},
            "gelbooru": {"api": True},
            "gfycat": {"format": "mp4"},
            "hitomi": {"metadata": True},
            "idolcomplex": {"username": None, "password": None, "wait-min": 3.0, "wait-max": 6.0},
            "imgur": {"mp4": True},
            "instagram": {
                "highlights": False,
                "videos": True,
                "include": "all",
                "directory": ["Instagram", "{username}", "Posts", "({date}) ({post_shortcode}) - {description[0:150]}"],
                "stories": {"directory": ["Instagram", "{username}", "Stories", "({expires}) {post_id}"]},
                "channel": {"directory": ["Instagram", "{username}", "IGTV", "{post_id}"]},
                "tagged": {"directory": ["Instagram", "{tagged_username}", "Tagged", "{username}"]},
                "reels": {"directory": ["Instagram", "{username}", "Reels", "{post_shortcode}"]},
                "filename": "({date})_{username}_{num}.{extension}",
                "date-format": "%Y-%m-%dT%H:%M:%S",
                "cookies": "<CHANGEME>",
                "username": "<CHANGEME>",
                "password": "<CHANGEME>",
                "sleep-request": 8.0,
            },
            "nijie": {"username": None, "password": None},
            "oauth": {"browser": "true", "cache": True, "host": "localhost", "port": 6414},
            "pinterest": {"domain": "auto", "sections": True, "videos": True},
            "pixiv": {"username": None, "password": None, "avatar": False, "ugoira": True},
            "reactor": {"wait-min": 3.0, "wait-max": 6.0},
            "reddit": {
                "client-id": "<REDACT>",
                "user-agent": "Python:gdl:v1.0 (by /u/bossjones)",
                "browser": "firefox:macos",
                "refresh-token": None,
                "comments": 0,
                "morecomments": False,
                "date-min": 0,
                "date-max": 253402210800,
                "date-format": "%Y-%m-%dT%H:%M:%S",
                "id-min": None,
                "id-max": None,
                "recursion": 0,
                "videos": True,
                "parent-directory": True,
                "directory": ["reddit", "_u_{author}", "{subreddit}"],
                "filename": "{subreddit}_{author}_{title}_{id}_{num}_{filename}_{date}.{extension}",
            },
            "redgifs": {"format": ["hd", "sd", "gif"], "username": "<CHANGEME>", "password": "<CHANGEME>"},
            "seiga": {"username": None, "password": None},
            "tumblr": {"avatar": False, "external": False, "inline": True, "posts": "all", "reblogs": True},
            "twitter": {
                "quoted": True,
                "replies": True,
                "retweets": True,
                "twitpic": False,
                "videos": True,
                "cookies": "<CHANGEME>",
                "filename": "{author[name]}-{tweet_id}-({date:%Y%m%d_%H%M%S})-img{num}.{extension}",
            },
            "vsco": {"videos": True},
            "wallhaven": {"api-key": None},
            "weibo": {"retweets": True, "videos": True},
            "booru": {"tags": False},
        },
        "downloader": {
            "filesize-min": None,
            "filesize-max": None,
            "part": True,
            "part-directory": None,
            "http": {
                "adjust-extensions": True,
                "mtime": True,
                "rate": None,
                "retries": 4,
                "timeout": 30.0,
                "verify": True,
            },
            "ytdl": {
                "format": None,
                "forward-cookies": False,
                "logging": True,
                "mtime": True,
                "outtmpl": None,
                "rate": None,
                "retries": 4,
                "timeout": 30.0,
                "verify": True,
            },
        },
        "output": {
            "mode": "auto",
            "progress": True,
            "shorten": True,
            "log": "[{name}][{levelname}][{extractor.url}] {message}",
            "logfile": None,
            "unsupportedfile": None,
        },
        "netrc": False,
    }

    if dry_run:
        cprint("\n[bold yellow]🔍 DRY RUN MODE - No files will be modified[/bold yellow]", style="bold yellow")
        cprint("=" * 50, style="yellow")
    else:
        cprint("\n[bold blue]🔧 Gallery-dl Configuration Setup[/bold blue]", style="bold blue")
        cprint("=" * 50, style="blue")

    # Check if config file already exists
    config_exists = config_path.exists()
    backup_path = None

    # Generate new config content as JSON string for comparison
    new_config_json = json.dumps(dummy_config, indent=4, ensure_ascii=False)

    if config_exists:
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".conf.backup_{timestamp}")

        # Read existing config for comparison
        try:
            with open(config_path, encoding="utf-8") as f:
                existing_config = f.read()
        except Exception as e:
            existing_config = f"# Error reading file: {e}\n"

        if dry_run:
            cprint(f"[cyan]📁 Found existing config: {config_path}[/cyan]")
            cprint(f"[dim]Backup would be created at: {backup_path}[/dim]")

            # Show diff
            _show_config_diff(existing_config, new_config_json, config_path)
            return
        else:
            cprint(f"[yellow]⚠️  Existing config found at: {config_path}[/yellow]")
            cprint(f"[cyan]📁 Backup will be created at: {backup_path}[/cyan]")

            if not force:
                cprint("\n[bold yellow]Do you want to replace the existing configuration?[/bold yellow]")
                cprint("[dim]The existing file will be backed up before replacement.[/dim]")

                confirm = typer.confirm("Continue with setup?")
                if not confirm:
                    cprint("[yellow]Setup cancelled by user.[/yellow]")
                    raise typer.Exit(0)
    else:
        if dry_run:
            cprint(f"[green]📝 Would create new config at: {config_path}[/green]")

            # Show what would be created
            _show_new_config_preview(new_config_json, config_path)
            return
        else:
            cprint(f"[green]✅ No existing config found. Creating new config at: {config_path}[/green]")

            if not force:
                confirm = typer.confirm("Create the configuration file?")
                if not confirm:
                    cprint("[yellow]Setup cancelled by user.[/yellow]")
                    raise typer.Exit(0)

    try:
        # Create backup if file exists
        if config_exists and backup_path:
            cprint(f"\n[cyan]📋 Creating backup: {backup_path}[/cyan]")
            shutil.copy2(config_path, backup_path)
            cprint("[green]✅ Backup created successfully[/green]")

        # Write the new config file
        cprint(f"\n[blue]✍️  Writing configuration to: {config_path}[/blue]")

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(dummy_config, f, indent=4, ensure_ascii=False)

        cprint("[green]✅ Configuration file created successfully![/green]")

        # Show next steps
        cprint("\n[bold green]🎉 Setup Complete![/bold green]")
        cprint("-" * 20, style="green")
        cprint(f"[green]📁 Config file: {config_path}[/green]")
        if backup_path:
            cprint(f"[cyan]💾 Backup file: {backup_path}[/cyan]")

        cprint("\n[bold blue]Next Steps:[/bold blue]")
        cprint("[dim]1. Edit the config file to add your credentials:[/dim]")
        cprint("[dim]   - Replace <CHANGEME> values with actual credentials[/dim]")
        cprint("[dim]   - Update paths and preferences as needed[/dim]")
        cprint("[dim]2. Test the configuration with:[/dim]")
        cprint("[dim]   bossctl check-config[/dim]")
        cprint("[dim]3. View the configuration with:[/dim]")
        cprint("[dim]   bossctl show-configs[/dim]")

    except Exception as e:
        cprint(f"[red]❌ Error creating configuration: {e}[/red]")

        # Clean up backup if we created one but failed to write config
        if backup_path and backup_path.exists() and not config_path.exists():
            try:
                backup_path.unlink()
                cprint(f"[yellow]🧹 Cleaned up failed backup: {backup_path}[/yellow]")
            except Exception:
                pass

        raise typer.Exit(1)


def _show_config_diff(existing_config: str, new_config: str, config_path: Path) -> None:
    """Show a diff between existing and new configuration."""
    import difflib

    cprint(f"\n[bold blue]📋 Configuration Diff for {config_path}[/bold blue]")
    cprint("=" * 60, style="blue")

    # Split into lines for difflib
    existing_lines = existing_config.splitlines(keepends=True)
    new_lines = new_config.splitlines(keepends=True)

    # Generate unified diff
    diff = list(
        difflib.unified_diff(
            existing_lines,
            new_lines,
            fromfile=f"current {config_path.name}",
            tofile=f"new {config_path.name}",
            lineterm="",
        )
    )

    if not diff:
        cprint("[green]✅ No changes needed - files are identical[/green]")
        return

    # Display diff with color coding
    cprint("\n[bold yellow]Changes that would be made:[/bold yellow]")
    cprint("-" * 40, style="yellow")

    max_lines = 50  # Limit output for readability

    for line_count, line in enumerate(diff):
        if line_count >= max_lines:
            remaining = len(diff) - line_count
            cprint(f"[dim]... and {remaining} more lines[/dim]")
            break

        line = line.rstrip()
        if line.startswith("+++") or line.startswith("---"):
            cprint(f"[bold blue]{line}[/bold blue]")
        elif line.startswith("@@"):
            cprint(f"[bold cyan]{line}[/bold cyan]")
        elif line.startswith("+"):
            cprint(f"[green]{line}[/green]")
        elif line.startswith("-"):
            cprint(f"[red]{line}[/red]")
        elif line.startswith(" "):
            cprint(f"[dim]{line}[/dim]")
        else:
            cprint(line)

    # Summary
    added_lines = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed_lines = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    cprint("\n[bold blue]Summary:[/bold blue]")
    cprint(f"[green]+ {added_lines} lines would be added[/green]")
    cprint(f"[red]- {removed_lines} lines would be removed[/red]")

    cprint("\n[dim]Run without --dry-run to apply these changes[/dim]")


def _show_new_config_preview(new_config: str, config_path: Path) -> None:
    """Show a preview of the new configuration that would be created."""
    cprint(f"\n[bold blue]📝 New Configuration Preview for {config_path}[/bold blue]")
    cprint("=" * 60, style="blue")

    lines = new_config.splitlines()
    total_lines = len(lines)

    # Show first 30 lines as preview
    preview_lines = 30

    cprint(f"[dim]Preview (first {min(preview_lines, total_lines)} of {total_lines} lines):[/dim]")
    cprint("-" * 50, style="dim")

    for i, line in enumerate(lines[:preview_lines], 1):
        # Add line numbers and syntax highlighting for JSON
        if (line.strip().startswith('"') and line.strip().endswith('":')) or line.strip().endswith('": {'):
            # JSON keys
            cprint(f"[dim]{i:3d}[/dim] [bold blue]{line}[/bold blue]")
        elif line.strip() in ["{", "}", "[", "]"]:
            # JSON structure
            cprint(f"[dim]{i:3d}[/dim] [bold]{line}[/bold]")
        elif "<CHANGEME>" in line or "<REDACT>" in line:
            # Placeholder values
            cprint(f"[dim]{i:3d}[/dim] [yellow]{line}[/yellow]")
        elif line.strip().startswith('"') and line.strip().endswith(","):
            # JSON string values
            cprint(f"[dim]{i:3d}[/dim] [green]{line}[/green]")
        elif (
            any(keyword in line for keyword in ["true", "false", "null"])
            or line.strip().replace(",", "").replace(".", "").isdigit()
        ):
            # JSON literals and numbers
            cprint(f"[dim]{i:3d}[/dim] [cyan]{line}[/cyan]")
        else:
            # Default
            cprint(f"[dim]{i:3d}[/dim] {line}")

    if total_lines > preview_lines:
        cprint(f"[dim]... and {total_lines - preview_lines} more lines[/dim]")

    # Show file info
    estimated_size = len(new_config.encode("utf-8"))
    cprint("\n[bold blue]File Information:[/bold blue]")
    cprint(f"[dim]• Total lines: {total_lines}[/dim]")
    cprint(f"[dim]• Estimated size: {estimated_size:,} bytes ({estimated_size / 1024:.1f} KB)[/dim]")
    cprint(f"[dim]• Path: {config_path}[/dim]")

    # Show key configuration sections
    try:
        import json

        config_data = json.loads(new_config)

        cprint("\n[bold blue]Configuration Sections:[/bold blue]")
        if "extractor" in config_data:
            extractor_platforms = [
                k
                for k in config_data["extractor"].keys()
                if k
                not in [
                    "base-directory",
                    "user-agent",
                    "cookies",
                    "cookies-update",
                    "proxy",
                    "skip",
                    "sleep",
                    "sleep-request",
                    "sleep-extractor",
                    "path-restrict",
                    "path-replace",
                    "path-remove",
                    "path-strip",
                    "path-extended",
                    "extension-map",
                ]
            ]
            if extractor_platforms:
                cprint(
                    f"[dim]• Extractor platforms: {', '.join(extractor_platforms[:10])}{'...' if len(extractor_platforms) > 10 else ''}[/dim]"
                )

        if "downloader" in config_data:
            cprint("[dim]• Downloader configuration included[/dim]")
        if "output" in config_data:
            cprint("[dim]• Output configuration included[/dim]")
    except Exception:
        pass

    cprint("\n[dim]Run without --dry-run to create this configuration file[/dim]")


@APP.command()
def logtree() -> None:
    """Display the current logging hierarchy using logging_tree"""
    try:
        from logging_tree import printout

        cprint("\n[bold blue]📊 Logging Tree Hierarchy[/bold blue]", style="bold blue")
        cprint("=" * 50, style="blue")
        cprint("")
        printout()
        cprint("")
        cprint("[dim]This shows the current logger hierarchy and configuration[/dim]")
    except ImportError:
        cprint("[red]❌ logging_tree is not installed[/red]")
        cprint("[yellow]Install with: pip install logging-tree[/yellow]")
        raise typer.Exit(1)


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
