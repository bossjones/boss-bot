"""Assistant management commands for LangGraph Cloud integration."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from boss_bot.ai.assistants import (
    LangGraphAssistantClient,
    LangGraphClientConfig,
    create_assistant_client,
    export_assistants_to_directory,
    sync_assistants_from_directory,
)
from boss_bot.ai.assistants.models import AssistantConfig, create_default_assistant_config
from boss_bot.core.env import BossSettings

# Create a sub-application for assistant commands
app = typer.Typer(name="assistants", help="Manage LangGraph assistants", no_args_is_help=True)

console = Console()

# Initialize settings lazily to avoid test collection issues
_settings = None


def get_settings() -> BossSettings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = BossSettings()
    return _settings


@app.command()
def list(
    deployment_url: Annotated[str | None, typer.Option("--url", "-u", help="LangGraph Cloud deployment URL")] = None,
    api_key: Annotated[str | None, typer.Option("--key", "-k", help="API key for authentication")] = None,
    graph_id: Annotated[str | None, typer.Option("--graph", "-g", help="Filter by graph ID")] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Maximum number of assistants to show")] = 20,
) -> None:
    """List assistants from LangGraph Cloud."""

    async def _list_assistants():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Connecting to LangGraph Cloud...", total=None)

                # Create client configuration if URL provided
                client_config = None
                if deployment_url:
                    from pydantic import AnyHttpUrl, SecretStr

                    client_config = LangGraphClientConfig(
                        deployment_url=AnyHttpUrl(deployment_url),
                        api_key=SecretStr(api_key) if api_key else None,
                    )

                # Create and connect client
                async with LangGraphAssistantClient(config=client_config) as client:
                    progress.update(task, description="Fetching assistants...")
                    assistants = await client.list_assistants(limit=limit, graph_id=graph_id)

                    progress.update(task, description="Processing results...")

                    if not assistants:
                        console.print("[yellow]No assistants found.[/yellow]")
                        return

                    # Create and display table
                    table = Table(title=f"LangGraph Assistants ({len(assistants)} found)")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("Name", style="bold")
                    table.add_column("Graph ID", style="green")
                    table.add_column("Created", style="dim")
                    table.add_column("Updated", style="dim")

                    for assistant in assistants:
                        # Format dates
                        created = assistant.created_at.strftime("%Y-%m-%d %H:%M") if assistant.created_at else "N/A"
                        updated = assistant.updated_at.strftime("%Y-%m-%d %H:%M") if assistant.updated_at else "N/A"

                        table.add_row(
                            assistant.assistant_id[:8] + "...",  # Truncate ID for display
                            assistant.name,
                            assistant.graph_id,
                            created,
                            updated,
                        )

                    console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing assistants: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_list_assistants())


@app.command()
def sync_from(
    config_dir: Annotated[Path, typer.Argument(help="Directory containing YAML configuration files")],
    deployment_url: Annotated[str | None, typer.Option("--url", "-u", help="LangGraph Cloud deployment URL")] = None,
    api_key: Annotated[str | None, typer.Option("--key", "-k", help="API key for authentication")] = None,
    delete_missing: Annotated[
        bool, typer.Option("--delete-missing", help="Delete cloud assistants not found locally")
    ] = False,
) -> None:
    """Synchronize assistants from local YAML configurations to LangGraph Cloud."""

    async def _sync_from_yaml():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Starting synchronization...", total=None)

                # Validate config directory
                if not config_dir.exists():
                    console.print(f"[red]Configuration directory not found: {config_dir}[/red]")
                    raise typer.Exit(1)

                progress.update(task, description="Synchronizing assistants...")

                # Sync assistants
                result = await sync_assistants_from_directory(
                    config_dir=config_dir,
                    deployment_url=deployment_url,
                    api_key=api_key,
                    delete_missing=delete_missing,
                )

                progress.update(task, description="Sync completed!")

                # Display results
                console.print("\n[bold green]Synchronization Results:[/bold green]")
                console.print(f"  Created: {result.created}")
                console.print(f"  Updated: {result.updated}")
                console.print(f"  Deleted: {result.deleted}")

                if result.errors:
                    console.print(f"\n[bold red]Errors ({len(result.errors)}):[/bold red]")
                    for error in result.errors:
                        console.print(f"  - {error}")
                else:
                    console.print("\n[bold green]✓ All operations completed successfully![/bold green]")

        except Exception as e:
            console.print(f"[red]Error during synchronization: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_sync_from_yaml())


@app.command()
def sync_to(
    config_dir: Annotated[Path, typer.Argument(help="Directory where to save YAML configurations")],
    deployment_url: Annotated[str | None, typer.Option("--url", "-u", help="LangGraph Cloud deployment URL")] = None,
    api_key: Annotated[str | None, typer.Option("--key", "-k", help="API key for authentication")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing local files")] = False,
) -> None:
    """Export cloud assistants to local YAML configurations."""

    async def _sync_to_yaml():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Starting export...", total=None)

                progress.update(task, description="Exporting assistants...")

                # Export assistants
                result = await export_assistants_to_directory(
                    config_dir=config_dir,
                    deployment_url=deployment_url,
                    api_key=api_key,
                    overwrite_existing=overwrite,
                )

                progress.update(task, description="Export completed!")

                # Display results
                console.print("\n[bold green]Export Results:[/bold green]")
                console.print(f"  Saved: {result.created}")
                console.print(f"  Target directory: {config_dir}")

                if result.errors:
                    console.print(f"\n[bold red]Errors ({len(result.errors)}):[/bold red]")
                    for error in result.errors:
                        console.print(f"  - {error}")
                else:
                    console.print("\n[bold green]✓ Export completed successfully![/bold green]")

        except Exception as e:
            console.print(f"[red]Error during export: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_sync_to_yaml())


@app.command()
def health(
    deployment_url: Annotated[str | None, typer.Option("--url", "-u", help="LangGraph Cloud deployment URL")] = None,
    api_key: Annotated[str | None, typer.Option("--key", "-k", help="API key for authentication")] = None,
) -> None:
    """Check LangGraph Cloud connection health."""

    async def _health_check():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Checking connection health...", total=None)

                # Create client configuration if URL provided
                client_config = None
                if deployment_url:
                    from pydantic import AnyHttpUrl, SecretStr

                    client_config = LangGraphClientConfig(
                        deployment_url=AnyHttpUrl(deployment_url),
                        api_key=SecretStr(api_key) if api_key else None,
                    )

                # Create and test client
                async with LangGraphAssistantClient(config=client_config) as client:
                    is_healthy = await client.health_check(force=True)

                    if is_healthy:
                        console.print("[bold green]✓ LangGraph Cloud connection is healthy![/bold green]")
                        console.print(f"  Deployment URL: {client.config.deployment_url}")

                        # Test listing assistants
                        progress.update(task, description="Testing assistant operations...")
                        assistants = await client.list_assistants(limit=1)
                        console.print(f"  Assistant access: [green]✓ Working[/green] ({len(assistants)} accessible)")
                    else:
                        console.print("[bold red]✗ LangGraph Cloud connection failed![/bold red]")
                        raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_health_check())


@app.command()
def create_config(
    name: Annotated[str, typer.Argument(help="Assistant name")],
    description: Annotated[str, typer.Argument(help="Assistant description")],
    output_file: Annotated[Path | None, typer.Option("--output", "-o", help="Output YAML file path")] = None,
    graph_id: Annotated[str, typer.Option("--graph", "-g", help="LangGraph workflow graph ID")] = "download_workflow",
) -> None:
    """Create a default assistant configuration YAML file."""
    try:
        # Create default configuration
        config = create_default_assistant_config(
            name=name,
            description=description,
            graph_id=graph_id,
        )

        # Determine output file
        if output_file is None:
            safe_name = "".join(c for c in name if c.isalnum() or c in "-_").lower()
            output_file = Path(f"{safe_name}_config.yaml")

        # Save configuration
        config.to_yaml_file(output_file)

        console.print(f"[bold green]✓ Created assistant configuration: {output_file}[/bold green]")
        console.print(f"  Name: {config.name}")
        console.print(f"  Description: {config.description}")
        console.print(f"  Graph ID: {config.graph_id}")
        console.print(f"  Assistant ID: {config.assistant_id}")

        console.print("\n[dim]Edit the configuration file to customize settings before deploying.[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def graphs(
    deployment_url: Annotated[str | None, typer.Option("--url", "-u", help="LangGraph Cloud deployment URL")] = None,
    api_key: Annotated[str | None, typer.Option("--key", "-k", help="API key for authentication")] = None,
) -> None:
    """List available assistant graphs from LangGraph Cloud."""

    async def _list_graphs():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching available graphs...", total=None)

                # Create client configuration if URL provided
                client_config = None
                if deployment_url:
                    from pydantic import AnyHttpUrl, SecretStr

                    client_config = LangGraphClientConfig(
                        deployment_url=AnyHttpUrl(deployment_url),
                        api_key=SecretStr(api_key) if api_key else None,
                    )

                # Create and connect client
                async with LangGraphAssistantClient(config=client_config) as client:
                    graphs = await client.get_assistant_graphs()

                    if not graphs:
                        console.print("[yellow]No graphs found.[/yellow]")
                        return

                    # Create and display table
                    table = Table(title=f"Available Assistant Graphs ({len(graphs)} found)")
                    table.add_column("Graph ID", style="cyan", no_wrap=True)
                    table.add_column("Name", style="bold")
                    table.add_column("Description", style="dim")

                    for graph in graphs:
                        table.add_row(
                            graph.graph_id,
                            getattr(graph, "name", "N/A"),
                            getattr(graph, "description", "N/A"),
                        )

                    console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing graphs: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_list_graphs())
