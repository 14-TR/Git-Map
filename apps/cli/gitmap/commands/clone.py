"""GitMap clone command.

Clones a web map from Portal and creates a local repository.

Execution Context:
    CLI command - invoked via `gitmap clone <item_id>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository and connection management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from pathlib import Path

import click
from rich.console import Console

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.models import Remote
from gitmap_core.repository import Repository

console = Console()


# ---- Clone Command ------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "item_id",
    required=True,
)
@click.option(
    "--directory",
    "-d",
    default="",
    help="Directory to clone into (defaults to map title).",
)
@click.option(
    "--url",
    "-u",
    default="https://www.arcgis.com",
    help="Portal URL (defaults to ArcGIS Online).",
)
@click.option(
    "--username",
    default="",
    help="Portal username (or use ARCGIS_USERNAME env var).",
)
def clone(
        item_id: str,
        directory: str,
        url: str,
        username: str,
) -> None:
    """Clone a web map from Portal.

    Creates a new GitMap repository containing the specified web map.
    The map JSON is fetched from Portal and stored as the initial commit.

    Examples:
        gitmap clone abc123def456
        gitmap clone abc123def456 --directory my-project
        gitmap clone abc123def456 --url https://portal.example.com
    """
    try:
        # Use PORTAL_URL from env if set, otherwise use provided URL (or click default)
        portal_url = os.environ.get("PORTAL_URL") or url
        
        # Connect to Portal
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(url=portal_url, username=username if username else None)

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # Fetch web map
        console.print(f"[dim]Fetching web map {item_id}...[/dim]")
        item, map_data = get_webmap_by_id(connection.gis, item_id)

        # Determine target directory
        if directory:
            target_dir = Path(directory).resolve()
        else:
            # Use sanitized map title
            safe_title = "".join(
                c if c.isalnum() or c in "-_" else "_"
                for c in item.title
            )
            target_dir = Path.cwd() / safe_title

        # Check if directory exists
        if target_dir.exists():
            raise click.ClickException(f"Directory '{target_dir}' already exists")

        # Create directory and initialize repo
        target_dir.mkdir(parents=True)
        repo = Repository(target_dir)

        repo.init(
            project_name=item.title,
            user_name=connection.username or "",
        )

        # Configure remote
        config = repo.get_config()
        config.remote = Remote(
            name="origin",
            url=portal_url,
            item_id=item_id,
        )
        repo.update_config(config)

        # Stage and commit the map
        repo.update_index(map_data)
        repo.create_commit(
            message=f"Clone from Portal: {item.title}",
            author=connection.username or "GitMap",
        )

        # Display result
        console.print()
        console.print(f"[green]Cloned '{item.title}' into {target_dir}[/green]")
        console.print()
        console.print(f"  [bold]Item ID:[/bold] {item_id}")
        console.print(f"  [bold]Title:[/bold] {item.title}")

        layers = map_data.get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        console.print()
        console.print(f"[dim]cd {target_dir.name} && gitmap status[/dim]")

    except Exception as clone_error:
        msg = f"Clone failed: {clone_error}"
        raise click.ClickException(msg) from clone_error


