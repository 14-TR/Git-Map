"""GitMap pull command.

Pulls latest changes from ArcGIS Portal.

Execution Context:
    CLI command - invoked via `gitmap pull`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Remote operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import find_repository

from .utils import get_portal_url

console = Console()


# ---- Pull Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--branch",
    "-b",
    default="",
    help="Branch to pull (defaults to current branch).",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (uses configured remote if not specified).",
)
@click.option(
    "--username",
    default="",
    help="Portal username (or use ARCGIS_USERNAME env var).",
)
def pull(
        branch: str,
        url: str,
        username: str,
) -> None:
    """Pull latest changes from Portal.

    Fetches the web map from Portal and updates the local staging area.
    Does not automatically commit - review changes with 'gitmap diff'.

    Examples:
        gitmap pull
        gitmap pull --branch main
        gitmap pull --url https://portal.example.com
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Determine Portal URL
        config = repo.get_config()
        if url:
            # Use provided URL
            portal_url = url
        elif config.remote and config.remote.url:
            # Use configured remote URL
            portal_url = config.remote.url
        else:
            # Get from environment variable (required)
            portal_url = get_portal_url()

        # Connect to Portal
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
        )

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # Perform pull
        target_branch = branch or repo.get_current_branch()
        console.print(f"[dim]Pulling branch '{target_branch}'...[/dim]")

        remote_ops = RemoteOperations(repo, connection)
        map_data = remote_ops.pull(target_branch)

        # Display result
        layers = map_data.get("operationalLayers", [])

        console.print()
        console.print(f"[green]Pulled '{target_branch}' from Portal[/green]")
        console.print()
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        console.print()
        console.print("[dim]Changes staged. Use 'gitmap diff' to review and 'gitmap commit' to save.[/dim]")

    except Exception as pull_error:
        msg = f"Pull failed: {pull_error}"
        raise click.ClickException(msg) from pull_error


