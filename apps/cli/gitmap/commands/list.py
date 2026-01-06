"""List web maps from Portal/AGOL.

The list command connects to ArcGIS Online/Enterprise using the
existing GitMap authentication helpers and displays all available
web maps from the portal.

Execution Context:
    CLI command - invoked via `gitmap list`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Portal connection and web map helpers

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os

import click
from rich.console import Console
from rich.table import Table

from gitmap_core.connection import get_connection
from gitmap_core.maps import list_webmaps

from .utils import get_portal_url

console = Console()


# ---- List Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--query",
    "-q",
    default="",
    help="Search query to filter web maps (e.g., 'title:MyMap').",
)
@click.option(
    "--owner",
    "-o",
    default="",
    help="Filter web maps by owner username.",
)
@click.option(
    "--tag",
    "-t",
    default="",
    help="Filter web maps by tag.",
)
@click.option(
    "--max-results",
    "-m",
    default=100,
    type=int,
    help="Maximum number of web maps to return (default: 100).",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (or use PORTAL_URL env var, which is required).",
)
@click.option(
    "--username",
    default="",
    help="Portal username (or use ARCGIS_USERNAME env var).",
)
@click.option(
    "--password",
    default="",
    help="Portal password (or use ARCGIS_PASSWORD env var).",
)
def list_maps(
        query: str,
        owner: str,
        tag: str,
        max_results: int,
        url: str,
        username: str,
        password: str,
) -> None:
    """List all available web maps from Portal/AGOL.
    
    Displays web maps in a table with ID, title, owner, and type.
    Use --query, --owner, or --tag to filter results.
    
    Examples:
        gitmap list --owner myusername
        gitmap list --tag production
        gitmap list --owner myusername --tag production
        gitmap list --query "title:MyMap"
    """
    try:
        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url if url else None)
        
        # Connect to Portal/AGOL
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
            password=password if password else None,
        )
        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        console.print("[dim]Querying available web maps...[/dim]")
        webmaps = list_webmaps(
            gis=connection.gis,
            query=query,
            owner=owner,
            tag=tag,
            max_results=max_results,
        )

        if not webmaps:
            console.print("[dim]No web maps found.[/dim]")
            return

        # Display web maps in a table
        table = Table(title="Available Web Maps")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="green")
        table.add_column("Owner", style="yellow")
        table.add_column("Type", style="blue")

        for webmap_info in webmaps:
            table.add_row(
                webmap_info.get("id", ""),
                webmap_info.get("title", ""),
                webmap_info.get("owner", ""),
                webmap_info.get("type", ""),
            )

        console.print()
        console.print(table)
    except Exception as list_error:
        msg = f"Failed to list web maps: {list_error}"
        raise click.ClickException(msg) from list_error

