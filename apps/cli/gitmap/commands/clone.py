"""GitMap clone command.

Clones a web map from Portal and creates a local repository.

Execution Context:
    CLI command - invoked via `gitmap clone <item_id>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository and connection management

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.models import Remote
from gitmap_core.repository import Repository

console = Console()


# ---- Clone Command ------------------------------------------------------------------------------------------


@click.command(epilog="Tip: run 'gitmap status' after cloning to see the initial map state.")
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

        item = None
        map_data: dict = {}
        connection = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Connecting to {portal_url}...", total=None)

            connection = get_connection(url=portal_url, username=username if username else None)

            progress.update(task, description=f"Fetching web map {item_id}...")
            item, map_data = get_webmap_by_id(connection.gis, item_id)

            progress.update(task, description="Initializing local repository...")

            # Determine target directory
            if directory:
                target_dir = Path(directory).resolve()
            else:
                safe_title = "".join(
                    c if c.isalnum() or c in "-_" else "_"
                    for c in item.title
                )
                target_dir = Path.cwd() / safe_title

            if target_dir.exists():
                raise click.ClickException(
                    f"Directory '{target_dir}' already exists.\n"
                    "  Hint: remove it or use --directory to specify a different location."
                )

            target_dir.mkdir(parents=True)
            repo = Repository(target_dir)

            repo.init(
                project_name=item.title,
                user_name=connection.username or "",
            )

            config = repo.get_config()
            config.remote = Remote(
                name="origin",
                url=portal_url,
                item_id=item_id,
            )
            repo.update_config(config)

            repo.update_index(map_data)
            repo.create_commit(
                message=f"Clone from Portal: {item.title}",
                author=connection.username or "GitMap",
            )

            progress.update(task, description="Done.")

        # Display result
        auth_line = f" [dim](as {connection.username})[/dim]" if connection and connection.username else ""
        console.print(f"[green]✓ Cloned '{item.title}'[/green]{auth_line}")
        console.print()
        console.print(f"  [bold]Item ID:[/bold] {item_id}")
        console.print(f"  [bold]Title:[/bold]   {item.title}")

        layers = map_data.get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold]  {len(layers)}")
        console.print(f"  [bold]Path:[/bold]    {target_dir}")

        console.print()
        console.print(f"[dim]cd {target_dir.name}[/dim]")
        console.print("[dim]gitmap status[/dim]")

    except click.ClickException:
        raise
    except Exception as clone_error:
        err = str(clone_error)
        if "not connected" in err.lower() or "connect()" in err.lower():
            msg = (
                "Clone failed: Portal authentication error.\n"
                "  Hint: check PORTAL_URL, ARCGIS_USERNAME, and ARCGIS_PASSWORD in your .env file."
            )
        elif "not found" in err.lower() or "404" in err or "no item" in err.lower():
            msg = (
                f"Clone failed: item '{item_id}' not found on Portal.\n"
                "  Hint: verify the item ID and that you have access to it.\n"
                "  Use 'gitmap list' to browse available web maps."
            )
        else:
            msg = f"Clone failed: {clone_error}"
        raise click.ClickException(msg) from clone_error
