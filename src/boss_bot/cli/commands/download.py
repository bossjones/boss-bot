"""Download commands for various platforms."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.strategies import (
    InstagramDownloadStrategy,
    RedditDownloadStrategy,
    TwitterDownloadStrategy,
    YouTubeDownloadStrategy,
)
from boss_bot.core.env import BossSettings

# Create a sub-application for download commands
app = typer.Typer(name="download", help="Download content from various platforms", no_args_is_help=True)

console = Console()


# Initialize settings and feature flags
settings = BossSettings()
feature_flags = DownloadFeatureFlags(settings)


def get_strategy_for_platform(platform: str, download_dir: Path):
    """Get the appropriate strategy for a platform.

    Args:
        platform: Platform name (twitter, reddit, instagram, youtube)
        download_dir: Directory for downloads

    Returns:
        Strategy instance for the platform
    """
    strategies = {
        "twitter": TwitterDownloadStrategy(feature_flags=feature_flags, download_dir=download_dir),
        "reddit": RedditDownloadStrategy(feature_flags=feature_flags, download_dir=download_dir),
        "instagram": InstagramDownloadStrategy(feature_flags=feature_flags, download_dir=download_dir),
        "youtube": YouTubeDownloadStrategy(feature_flags=feature_flags, download_dir=download_dir),
    }
    return strategies.get(platform)


def validate_twitter_url(url: str) -> str:
    """Validate that the URL is a Twitter/X URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL is not a valid Twitter/X URL
    """
    strategy = get_strategy_for_platform("twitter", Path.cwd())
    if not strategy or not strategy.supports_url(url):
        raise typer.BadParameter(
            f"URL is not a valid Twitter/X URL: {url}\n"
            "Supported formats:\n"
            "  - https://twitter.com/username/status/123456789\n"
            "  - https://x.com/username/status/123456789\n"
            "  - https://twitter.com/username\n"
            "  - https://x.com/username"
        )
    return url


def validate_reddit_url(url: str) -> str:
    """Validate that the URL is a Reddit URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL is not a valid Reddit URL
    """
    strategy = get_strategy_for_platform("reddit", Path.cwd())
    if not strategy or not strategy.supports_url(url):
        raise typer.BadParameter(
            f"URL is not a valid Reddit URL: {url}\n"
            "Supported formats:\n"
            "  - https://reddit.com/r/subreddit/comments/abc123/title/\n"
            "  - https://www.reddit.com/r/subreddit/comments/abc123/title/\n"
            "  - https://old.reddit.com/r/subreddit/comments/abc123/title/"
        )
    return url


def validate_instagram_url(url: str) -> str:
    """Validate that the URL is an Instagram URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL is not a valid Instagram URL
    """
    strategy = get_strategy_for_platform("instagram", Path.cwd())
    if not strategy or not strategy.supports_url(url):
        raise typer.BadParameter(
            f"URL is not a valid Instagram URL: {url}\n"
            "Supported formats:\n"
            "  - https://instagram.com/p/ABC123/\n"
            "  - https://www.instagram.com/p/ABC123/\n"
            "  - https://instagram.com/username/\n"
            "  - https://www.instagram.com/username/"
        )
    return url


def validate_youtube_url(url: str) -> str:
    """Validate that the URL is a YouTube URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL is not a valid YouTube URL
    """
    strategy = get_strategy_for_platform("youtube", Path.cwd())
    if not strategy or not strategy.supports_url(url):
        raise typer.BadParameter(
            f"URL is not a valid YouTube URL: {url}\n"
            "Supported formats:\n"
            "  - https://youtube.com/watch?v=VIDEO_ID\n"
            "  - https://www.youtube.com/watch?v=VIDEO_ID\n"
            "  - https://youtu.be/VIDEO_ID\n"
            "  - https://youtube.com/playlist?list=PLAYLIST_ID"
        )
    return url


@app.command("twitter")
def download_twitter(
    url: Annotated[str, typer.Argument(help="Twitter/X URL to download")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="Directory to save downloads")] = None,
    async_mode: Annotated[bool, typer.Option("--async", help="Use async download mode")] = False,
    metadata_only: Annotated[
        bool, typer.Option("--metadata-only", "-m", help="Extract metadata only, don't download files")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
) -> None:
    """Download Twitter/X content using strategy pattern.

    Uses the experimental strategy pattern with feature flag support for API-direct or CLI modes.

    Examples:
        bossctl download twitter https://twitter.com/username/status/123456789
        bossctl download twitter https://x.com/username/status/123456789 --output-dir ./downloads
        bossctl download twitter https://twitter.com/username --metadata-only
    """
    # Validate URL
    url = validate_twitter_url(url)

    # Setup download directory
    download_dir = output_dir or Path.cwd() / ".downloads"
    download_dir.mkdir(exist_ok=True, parents=True)

    # Initialize strategy
    strategy = get_strategy_for_platform("twitter", download_dir)
    if not strategy:
        console.print("[red]✗ Failed to initialize Twitter strategy[/red]")
        raise typer.Exit(1)

    console.print("[blue]Twitter Download[/blue]")
    console.print(f"URL: {url}")
    console.print(f"Output Directory: {download_dir}")
    console.print(f"Mode: {'Async' if async_mode else 'Sync'}")

    # Show strategy status
    if feature_flags.is_api_enabled_for_platform("twitter"):
        console.print("🚀 Using experimental API-direct approach")
    else:
        console.print("🖥️ Using CLI-based approach")
    console.print()

    if metadata_only:
        # Extract metadata only
        console.print("[yellow]Extracting metadata...[/yellow]")

        try:
            metadata = asyncio.run(strategy.get_metadata(url))

            console.print("[green]✓ Metadata extracted successfully[/green]")
            console.print("\n[bold]Metadata:[/bold]")

            if metadata.title:
                console.print(f"Title: {metadata.title}")
            if metadata.uploader:
                console.print(f"Author: {metadata.uploader}")
            if metadata.upload_date:
                console.print(f"Date: {metadata.upload_date}")
            if metadata.like_count:
                console.print(f"Likes: {metadata.like_count}")
            if metadata.view_count:
                console.print(f"Retweets: {metadata.view_count}")
            if metadata.download_method:
                method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                console.print(f"{method_emoji} Method: {metadata.download_method.upper()}")

            if verbose and metadata.raw_metadata:
                console.print("\n[bold]Raw Metadata:[/bold]")
                import json

                console.print(json.dumps(metadata.raw_metadata, indent=2))

        except Exception as e:
            console.print(f"[red]✗ Failed to extract metadata: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Download content
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Downloading content...", total=None)

            try:
                metadata = asyncio.run(strategy.download(url))
                progress.update(task, completed=True)

                if metadata.error:
                    console.print(f"[red]✗ Download failed: {metadata.error}[/red]")
                    raise typer.Exit(1)
                else:
                    console.print("[green]✓ Download completed successfully[/green]")

                    if metadata.files:
                        console.print(f"\n[bold]Downloaded {len(metadata.files)} files:[/bold]")
                        for file_path in metadata.files:
                            console.print(f"  📄 {file_path}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        console.print(f"\n{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    if verbose and metadata.raw_metadata:
                        console.print("\n[bold]Metadata:[/bold]")
                        import json

                        console.print(json.dumps(metadata.raw_metadata, indent=2))

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Download failed: {e}[/red]")
                if verbose:
                    import traceback

                    console.print(f"\n[bold]Traceback:[/bold]\n{traceback.format_exc()}")
                raise typer.Exit(1)


@app.command("reddit")
def download_reddit(
    url: Annotated[str, typer.Argument(help="Reddit URL to download")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="Directory to save downloads")] = None,
    async_mode: Annotated[bool, typer.Option("--async", help="Use async download mode")] = False,
    metadata_only: Annotated[
        bool, typer.Option("--metadata-only", "-m", help="Extract metadata only, don't download files")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
    config_file: Annotated[Path | None, typer.Option("--config", help="Custom gallery-dl config file")] = None,
    cookies_file: Annotated[Path | None, typer.Option("--cookies", help="Browser cookies file")] = None,
) -> None:
    """Download Reddit content using strategy pattern.

    Uses the experimental strategy pattern with feature flag support for API-direct or CLI modes.
    Can use custom config files and browser cookies for authentication.

    Examples:
        bossctl download reddit https://reddit.com/r/pics/comments/abc123/title/
        bossctl download reddit <url> --output-dir ./downloads --cookies cookies.txt
        bossctl download reddit <url> --metadata-only --config reddit-config.json
    """
    # Validate URL
    url = validate_reddit_url(url)

    # Setup download directory
    download_dir = output_dir or Path.cwd() / ".downloads"
    download_dir.mkdir(exist_ok=True, parents=True)

    # Initialize strategy
    strategy = get_strategy_for_platform("reddit", download_dir)
    if not strategy:
        console.print("[red]✗ Failed to initialize Reddit strategy[/red]")
        raise typer.Exit(1)

    console.print("[blue]Reddit Download[/blue]")
    console.print(f"URL: {url}")
    console.print(f"Output Directory: {download_dir}")
    console.print(f"Mode: {'Async' if async_mode else 'Sync'}")
    if config_file:
        console.print(f"Config File: {config_file}")
    if cookies_file:
        console.print(f"Cookies File: {cookies_file}")

    # Show strategy status
    if feature_flags.is_api_enabled_for_platform("reddit"):
        console.print("🚀 Using experimental API-direct approach")
    else:
        console.print("🖥️ Using CLI-based approach")
    console.print()

    # Prepare options
    options = {}
    if config_file:
        options["config_file"] = config_file
    if cookies_file:
        options["cookies_file"] = cookies_file

    if metadata_only:
        # Extract metadata only
        console.print("[yellow]Extracting metadata...[/yellow]")

        try:
            metadata = asyncio.run(strategy.get_metadata(url, **options))

            console.print("[green]✓ Metadata extracted successfully[/green]")
            console.print("\n[bold]Metadata:[/bold]")

            if metadata.title:
                console.print(f"Title: {metadata.title}")
            if metadata.uploader:
                console.print(f"Author: {metadata.uploader}")
            if metadata.raw_metadata and metadata.raw_metadata.get("subreddit"):
                console.print(f"Subreddit: r/{metadata.raw_metadata['subreddit']}")
            if metadata.like_count:
                console.print(f"Score: {metadata.like_count}")
            if metadata.raw_metadata and metadata.raw_metadata.get("num_comments"):
                console.print(f"Comments: {metadata.raw_metadata['num_comments']}")
            if metadata.upload_date:
                console.print(f"Posted: {metadata.upload_date}")
            if metadata.download_method:
                method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                console.print(f"{method_emoji} Method: {metadata.download_method.upper()}")

            if verbose and metadata.raw_metadata:
                console.print("\n[bold]Raw Metadata:[/bold]")
                import json

                console.print(json.dumps(metadata.raw_metadata, indent=2))

        except Exception as e:
            console.print(f"[red]✗ Failed to extract metadata: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Download content
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Downloading content...", total=None)

            try:
                metadata = asyncio.run(strategy.download(url, **options))
                progress.update(task, completed=True)

                if metadata.error:
                    console.print(f"[red]✗ Download failed: {metadata.error}[/red]")
                    raise typer.Exit(1)
                else:
                    console.print("[green]✓ Download completed successfully[/green]")

                    if metadata.files:
                        console.print(f"\n[bold]Downloaded {len(metadata.files)} files:[/bold]")
                        for file_path in metadata.files:
                            console.print(f"  📄 {file_path}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        console.print(f"\n{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    if verbose and metadata.raw_metadata:
                        console.print("\n[bold]Metadata:[/bold]")
                        import json

                        console.print(json.dumps(metadata.raw_metadata, indent=2))

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Download failed: {e}[/red]")
                if verbose:
                    import traceback

                    console.print(f"\n[bold]Traceback:[/bold]\n{traceback.format_exc()}")
                raise typer.Exit(1)


@app.command("instagram")
def download_instagram(
    url: Annotated[str, typer.Argument(help="Instagram URL to download")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="Directory to save downloads")] = None,
    async_mode: Annotated[bool, typer.Option("--async", help="Use async download mode")] = False,
    metadata_only: Annotated[
        bool, typer.Option("--metadata-only", "-m", help="Extract metadata only, don't download files")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
    cookies_browser: Annotated[
        str | None, typer.Option("--cookies-browser", help="Browser to extract cookies from (default: Firefox)")
    ] = "Firefox",
    user_agent: Annotated[str | None, typer.Option("--user-agent", help="Custom user agent string")] = "Wget/1.21.1",
) -> None:
    """Download Instagram content using strategy pattern.

    Uses the experimental strategy pattern with feature flag support for API-direct or CLI modes.
    Supports downloading posts, stories, and profile content from Instagram.

    Examples:
        bossctl download instagram https://instagram.com/p/ABC123/
        bossctl download instagram https://instagram.com/username/ --output-dir ./downloads
        bossctl download instagram <url> --metadata-only --cookies-browser Chrome
        bossctl download instagram <url> --user-agent "Custom Agent 1.0"
    """
    # Validate URL
    url = validate_instagram_url(url)

    # Setup download directory
    download_dir = output_dir or Path.cwd() / ".downloads"
    download_dir.mkdir(exist_ok=True, parents=True)

    # Initialize strategy
    strategy = get_strategy_for_platform("instagram", download_dir)
    if not strategy:
        console.print("[red]✗ Failed to initialize Instagram strategy[/red]")
        raise typer.Exit(1)

    console.print("[blue]Instagram Download[/blue]")
    console.print(f"URL: {url}")
    console.print(f"Output Directory: {download_dir}")
    console.print(f"Mode: {'Async' if async_mode else 'Sync'}")
    console.print(f"Cookies Browser: {cookies_browser}")
    console.print(f"User Agent: {user_agent}")

    # Show strategy status
    if feature_flags.is_api_enabled_for_platform("instagram"):
        console.print("🚀 Using experimental API-direct approach")
    else:
        console.print("🖥️ Using CLI-based approach")
    console.print()

    # Prepare options
    options = {}
    if cookies_browser and cookies_browser != "Firefox":
        options["cookies_browser"] = cookies_browser
    if user_agent and user_agent != "Wget/1.21.1":
        options["user_agent"] = user_agent

    if metadata_only:
        # Extract metadata only
        console.print("[yellow]Extracting metadata...[/yellow]")

        try:
            metadata = asyncio.run(strategy.get_metadata(url, **options))

            console.print("[green]✓ Metadata extracted successfully[/green]")
            console.print("\n[bold]Metadata:[/bold]")

            if metadata.title:
                console.print(f"Title: {metadata.title}")
            if metadata.uploader:
                console.print(f"Author: {metadata.uploader}")
            if metadata.upload_date:
                console.print(f"Posted: {metadata.upload_date}")
            if metadata.like_count:
                console.print(f"Likes: {metadata.like_count}")
            if metadata.raw_metadata and metadata.raw_metadata.get("comment_count"):
                console.print(f"Comments: {metadata.raw_metadata['comment_count']}")
            if metadata.raw_metadata and metadata.raw_metadata.get("description"):
                console.print(f"Description: {metadata.raw_metadata['description'][:100]}...")
            if metadata.download_method:
                method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                console.print(f"{method_emoji} Method: {metadata.download_method.upper()}")

            if verbose and metadata.raw_metadata:
                console.print("\n[bold]Raw Metadata:[/bold]")
                import json

                console.print(json.dumps(metadata.raw_metadata, indent=2))

        except Exception as e:
            console.print(f"[red]✗ Failed to extract metadata: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Download content
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Downloading content...", total=None)

            try:
                metadata = asyncio.run(strategy.download(url, **options))
                progress.update(task, completed=True)

                if metadata.error:
                    console.print(f"[red]✗ Download failed: {metadata.error}[/red]")
                    raise typer.Exit(1)
                else:
                    console.print("[green]✓ Download completed successfully[/green]")

                    if metadata.files:
                        console.print(f"\n[bold]Downloaded {len(metadata.files)} files:[/bold]")
                        for file_path in metadata.files:
                            console.print(f"  📄 {file_path}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        console.print(f"\n{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    if verbose and metadata.raw_metadata:
                        console.print("\n[bold]Metadata:[/bold]")
                        import json

                        console.print(json.dumps(metadata.raw_metadata, indent=2))

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Download failed: {e}[/red]")
                if verbose:
                    import traceback

                    console.print(f"\n[bold]Traceback:[/bold]\n{traceback.format_exc()}")
                raise typer.Exit(1)


@app.command("youtube")
def download_youtube(
    url: Annotated[str, typer.Argument(help="YouTube URL to download")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="Directory to save downloads")] = None,
    async_mode: Annotated[bool, typer.Option("--async", help="Use async download mode")] = False,
    metadata_only: Annotated[
        bool, typer.Option("--metadata-only", "-m", help="Extract metadata only, don't download files")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show verbose output")] = False,
    quality: Annotated[
        str | None, typer.Option("--quality", "-q", help="Video quality (e.g., 720p, 1080p, best)")
    ] = "best",
    audio_only: Annotated[bool, typer.Option("--audio-only", "-a", help="Download audio only")] = False,
) -> None:
    """Download YouTube content using strategy pattern.

    Uses the experimental strategy pattern with feature flag support for API-direct or CLI modes.
    Supports downloading videos, playlists, and audio content from YouTube.

    Examples:
        bossctl download youtube https://youtube.com/watch?v=VIDEO_ID
        bossctl download youtube https://youtu.be/VIDEO_ID --quality 720p
        bossctl download youtube <url> --audio-only --output-dir ./downloads
        bossctl download youtube <url> --metadata-only
    """
    # Validate URL
    url = validate_youtube_url(url)

    # Setup download directory
    download_dir = output_dir or Path.cwd() / ".downloads"
    download_dir.mkdir(exist_ok=True, parents=True)

    # Initialize strategy
    strategy = get_strategy_for_platform("youtube", download_dir)
    if not strategy:
        console.print("[red]✗ Failed to initialize YouTube strategy[/red]")
        raise typer.Exit(1)

    console.print("[blue]YouTube Download[/blue]")
    console.print(f"URL: {url}")
    console.print(f"Output Directory: {download_dir}")
    console.print(f"Mode: {'Async' if async_mode else 'Sync'}")
    console.print(f"Quality: {quality}")
    console.print(f"Audio Only: {audio_only}")

    # Show strategy status
    if feature_flags.is_api_enabled_for_platform("youtube"):
        console.print("🚀 Using experimental API-direct approach")
    else:
        console.print("🖥️ Using CLI-based approach")
    console.print()

    # Prepare options
    options = {}
    if quality and quality != "best":
        options["quality"] = quality
    if audio_only:
        options["audio_only"] = True

    if metadata_only:
        # Extract metadata only
        console.print("[yellow]Extracting metadata...[/yellow]")

        try:
            metadata = asyncio.run(strategy.get_metadata(url, **options))

            console.print("[green]✓ Metadata extracted successfully[/green]")
            console.print("\n[bold]Metadata:[/bold]")

            if metadata.title:
                console.print(f"Title: {metadata.title}")
            if metadata.uploader:
                console.print(f"Channel: {metadata.uploader}")
            if metadata.upload_date:
                console.print(f"Upload Date: {metadata.upload_date}")
            if metadata.duration:
                console.print(f"Duration: {metadata.duration}")
            if metadata.view_count:
                console.print(f"Views: {metadata.view_count}")
            if metadata.like_count:
                console.print(f"Likes: {metadata.like_count}")
            if metadata.download_method:
                method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                console.print(f"{method_emoji} Method: {metadata.download_method.upper()}")

            if verbose and metadata.raw_metadata:
                console.print("\n[bold]Raw Metadata:[/bold]")
                import json

                console.print(json.dumps(metadata.raw_metadata, indent=2))

        except Exception as e:
            console.print(f"[red]✗ Failed to extract metadata: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Download content
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Downloading content...", total=None)

            try:
                metadata = asyncio.run(strategy.download(url, **options))
                progress.update(task, completed=True)

                if metadata.error:
                    console.print(f"[red]✗ Download failed: {metadata.error}[/red]")
                    raise typer.Exit(1)
                else:
                    console.print("[green]✓ Download completed successfully[/green]")

                    if metadata.files:
                        console.print(f"\n[bold]Downloaded {len(metadata.files)} files:[/bold]")
                        for file_path in metadata.files:
                            console.print(f"  📄 {file_path}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        console.print(f"\n{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    if verbose and metadata.raw_metadata:
                        console.print("\n[bold]Metadata:[/bold]")
                        import json

                        console.print(json.dumps(metadata.raw_metadata, indent=2))

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Download failed: {e}[/red]")
                if verbose:
                    import traceback

                    console.print(f"\n[bold]Traceback:[/bold]\n{traceback.format_exc()}")
                raise typer.Exit(1)


@app.command("info")
def download_info() -> None:
    """Show information about download capabilities."""
    console.print("[bold blue]BossBot Download Commands[/bold blue]")
    console.print()

    console.print("[bold]Supported Platforms:[/bold]")
    console.print("  🐦 Twitter/X (twitter.com, x.com)")
    console.print("     - Individual tweets")
    console.print("     - User profiles")
    console.print("     - Media content (images, videos)")
    console.print()
    console.print("  🤖 Reddit (reddit.com)")
    console.print("     - Individual posts")
    console.print("     - Gallery posts")
    console.print("     - Video posts")
    console.print("     - Custom config and cookie support")
    console.print()
    console.print("  📷 Instagram (instagram.com) [EXPERIMENTAL]")
    console.print("     - Individual posts")
    console.print("     - User profiles")
    console.print("     - Stories and highlights")
    console.print("     - Firefox cookies and custom user agent support")
    console.print()
    console.print("  📺 YouTube (youtube.com) [EXPERIMENTAL]")
    console.print("     - Individual videos")
    console.print("     - Playlists")
    console.print("     - Quality selection (360p-4K)")
    console.print("     - Audio-only downloads")
    console.print()

    console.print("[bold]Available Commands:[/bold]")
    console.print("  twitter    - Download Twitter/X content using gallery-dl")
    console.print("  reddit     - Download Reddit content using gallery-dl")
    console.print("  instagram  - Download Instagram content using gallery-dl [EXPERIMENTAL]")
    console.print("  youtube    - Download YouTube content using yt-dlp [EXPERIMENTAL]")
    console.print()

    console.print("[bold]Configuration Commands:[/bold]")
    console.print("  validate-config   - Validate gallery-dl config for platform (instagram)")
    console.print("  check-config      - Check config with detailed output")
    console.print("  config-summary    - Show current config values")
    console.print("  strategies        - Show strategy configuration")
    console.print()

    console.print("[bold]Strategy Features:[/bold]")
    console.print("  🚀 API-Direct Mode: Experimental direct API integration")
    console.print("  🖥️ CLI Mode: Stable subprocess-based approach (default)")
    console.print("  🔄 Auto-Fallback: API failures automatically fallback to CLI")
    console.print("  ⚙️ Feature Flags: Environment variable control (e.g., TWITTER_USE_API_CLIENT=true)")
    console.print()

    console.print("[bold]Examples:[/bold]")
    console.print("  bossctl download twitter https://twitter.com/username/status/123")
    console.print("  bossctl download twitter https://x.com/username --metadata-only")
    console.print("  bossctl download reddit https://reddit.com/r/pics/comments/abc123/title/")
    console.print("  bossctl download instagram https://instagram.com/p/ABC123/")
    console.print("  bossctl download youtube https://youtube.com/watch?v=VIDEO_ID --quality 720p")


@app.command("strategies")
def show_strategies() -> None:
    """Show current download strategy configuration."""
    info = feature_flags.get_strategy_info()

    console.print("[bold blue]Download Strategy Configuration[/bold blue]")
    console.print()

    platforms = [
        ("🐦 Twitter/X", "twitter_api"),
        ("🤖 Reddit", "reddit_api"),
        ("📺 YouTube", "youtube_api"),
        ("📷 Instagram", "instagram_api"),
    ]

    for emoji_name, key in platforms:
        status = "🚀 **API-Direct**" if info[key] else "🖥️ **CLI Mode**"
        console.print(f"{emoji_name}: {status}")

    console.print()
    console.print(f"🔄 **API Fallback**: {'✅ Enabled' if info['api_fallback'] else '❌ Disabled'}")
    console.print()
    console.print(
        "💡 *Tip: Enable experimental features with environment variables like `TWITTER_USE_API_CLIENT=true`*"
    )


@app.command("validate-config")
def validate_config(
    platform: Annotated[str, typer.Argument(help="Platform to validate config for (instagram)")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed validation information")] = False,
) -> None:
    """Validate gallery-dl configuration for specific platforms.

    Currently supports Instagram configuration validation.

    Examples:
        bossctl download validate-config instagram
        bossctl download validate-config instagram --verbose
    """
    platform = platform.lower()

    if platform == "instagram":
        download_dir = Path.cwd() / ".downloads"
        strategy = get_strategy_for_platform("instagram", download_dir)
        if not strategy:
            console.print("[red]✗ Failed to initialize Instagram strategy[/red]")
            raise typer.Exit(1)

        console.print(f"[bold blue]Validating {platform.title()} Configuration[/bold blue]")
        console.print()

        # Perform validation
        is_valid, issues = strategy.validate_config(verbose=verbose)

        if is_valid:
            console.print("[green]✅ Configuration is valid![/green]")
        else:
            console.print("[red]❌ Configuration has issues:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            raise typer.Exit(1)
    else:
        console.print(f"[red]✗ Configuration validation not yet supported for platform: {platform}[/red]")
        console.print("Supported platforms: instagram")
        raise typer.Exit(1)


@app.command("check-config")
def check_config(
    platform: Annotated[str, typer.Argument(help="Platform to check config for (instagram)")],
) -> None:
    """Check gallery-dl configuration with detailed output.

    Shows comprehensive configuration status for the specified platform.

    Examples:
        bossctl download check-config instagram
    """
    platform = platform.lower()

    if platform == "instagram":
        download_dir = Path.cwd() / ".downloads"
        strategy = get_strategy_for_platform("instagram", download_dir)
        if not strategy:
            console.print("[red]✗ Failed to initialize Instagram strategy[/red]")
            raise typer.Exit(1)

        console.print(f"[bold blue]Checking {platform.title()} Configuration[/bold blue]")
        console.print()

        # Perform detailed check with verbose output
        is_valid = strategy.check_config(verbose=True)

        if not is_valid:
            raise typer.Exit(1)
    else:
        console.print(f"[red]✗ Configuration check not yet supported for platform: {platform}[/red]")
        console.print("Supported platforms: instagram")
        raise typer.Exit(1)


@app.command("config-summary")
def config_summary(
    platform: Annotated[str, typer.Argument(help="Platform to show config summary for (instagram)")],
) -> None:
    """Show configuration summary for specific platforms.

    Displays current configuration values without validation.

    Examples:
        bossctl download config-summary instagram
    """
    platform = platform.lower()

    if platform == "instagram":
        download_dir = Path.cwd() / ".downloads"
        strategy = get_strategy_for_platform("instagram", download_dir)
        if not strategy:
            console.print("[red]✗ Failed to initialize Instagram strategy[/red]")
            raise typer.Exit(1)

        console.print(f"[bold blue]{platform.title()} Configuration Summary[/bold blue]")
        console.print()

        # Show configuration summary
        strategy.print_config_summary()
    else:
        console.print(f"[red]✗ Configuration summary not yet supported for platform: {platform}[/red]")
        console.print("Supported platforms: instagram")
        raise typer.Exit(1)


# Make the app available for import
if __name__ == "__main__":
    app()
