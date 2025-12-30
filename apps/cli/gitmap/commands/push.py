"""GitMap push command.

Pushes local branch to ArcGIS Portal.

Execution Context:
    CLI command - invoked via `gitmap push`

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

console = Console()


# ---- Push Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--branch",
    "-b",
    default="",
    help="Branch to push (defaults to current branch).",
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
def push(
        branch: str,
        url: str,
        username: str,
) -> None:
    """Push branch to ArcGIS Portal.

    Uploads the current branch as a web map item in Portal. Creates
    a GitMap folder to organize branch items.

    Examples:
        gitmap push
        gitmap push --branch feature/new-layer
        gitmap push --url https://portal.example.com
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Determine Portal URL
        config = repo.get_config()
        portal_url = url or (config.remote.url if config.remote else "https://www.arcgis.com")

        # Connect to Portal
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
        )

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # Perform push
        target_branch = branch or repo.get_current_branch()
        console.print(f"[dim]Pushing branch '{target_branch}'...[/dim]")

        remote_ops = RemoteOperations(repo, connection)
        item = remote_ops.push(target_branch)

        # Display result
        console.print()
        console.print(f"[green]Pushed '{target_branch}' to Portal[/green]")
        console.print()
        console.print(f"  [bold]Item ID:[/bold] {item.id}")
        console.print(f"  [bold]Title:[/bold] {item.title}")
        console.print(f"  [bold]URL:[/bold] {item.homepage}")

    except Exception as push_error:
        msg = f"Push failed: {push_error}"
        raise click.ClickException(msg) from push_error


