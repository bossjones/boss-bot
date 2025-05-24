"""Download commands for various platforms."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from boss_bot.core.downloads.handlers import TwitterHandler

# Create a sub-application for download commands
app = typer.Typer(name="download", help="Download content from various platforms", no_args_is_help=True)

console = Console()


def validate_twitter_url(url: str) -> str:
    """Validate that the URL is a Twitter/X URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL is not a valid Twitter/X URL
    """
    handler = TwitterHandler()
    if not handler.supports_url(url):
        raise typer.BadParameter(
            f"URL is not a valid Twitter/X URL: {url}\n"
            "Supported formats:\n"
            "  - https://twitter.com/username/status/123456789\n"
            "  - https://x.com/username/status/123456789\n"
            "  - https://twitter.com/username\n"
            "  - https://x.com/username"
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
    """Download Twitter/X content using gallery-dl.

    Based on the 'dlt' shell alias:
    gallery-dl --no-mtime -v --write-info-json --write-metadata <url>

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

    # Initialize handler
    handler = TwitterHandler(download_dir=download_dir)

    console.print("[blue]Twitter Download[/blue]")
    console.print(f"URL: {url}")
    console.print(f"Output Directory: {download_dir}")
    console.print(f"Mode: {'Async' if async_mode else 'Sync'}")
    console.print()

    if metadata_only:
        # Extract metadata only
        console.print("[yellow]Extracting metadata...[/yellow]")

        try:
            if async_mode:
                metadata = asyncio.run(handler.aget_metadata(url))
            else:
                metadata = handler.get_metadata(url)

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
                if async_mode:
                    result = asyncio.run(handler.adownload(url))
                else:
                    result = handler.download(url)

                progress.update(task, completed=True)

                if result.success:
                    console.print("[green]✓ Download completed successfully[/green]")

                    if result.files:
                        console.print(f"\n[bold]Downloaded {len(result.files)} files:[/bold]")
                        for file_path in result.files:
                            console.print(f"  📄 {file_path}")

                    if verbose:
                        if result.stdout:
                            console.print("\n[bold]Command Output:[/bold]")
                            console.print(result.stdout)

                        if result.metadata:
                            console.print("\n[bold]Metadata:[/bold]")
                            import json

                            console.print(json.dumps(result.metadata, indent=2))

                else:
                    console.print(f"[red]✗ Download failed: {result.error}[/red]")
                    if verbose and result.stderr:
                        console.print(f"\n[bold]Error Details:[/bold]\n{result.stderr}")
                    raise typer.Exit(1)

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

    console.print("[bold]Available Commands:[/bold]")
    console.print("  twitter  - Download Twitter/X content using gallery-dl")
    console.print()

    console.print("[bold]Examples:[/bold]")
    console.print("  bossctl download twitter https://twitter.com/username/status/123")
    console.print("  bossctl download twitter https://x.com/username --metadata-only")
    console.print("  bossctl download twitter <url> --output-dir ./downloads --async")


# Make the app available for import
if __name__ == "__main__":
    app()
