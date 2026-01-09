"""GitMap setup-repos command.

Automates bulk cloning of web maps from Portal into a repositories directory.
Each map is cloned into its own directory with a .gitmap folder.

Execution Context:
    CLI command - invoked via `gitmap setup-repos`

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
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id, list_webmaps
from gitmap_core.models import Remote
from gitmap_core.repository import Repository

from .utils import get_portal_url

console = Console()


# ---- Setup Repos Command ------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--directory",
    "-d",
    default="repositories",
    help="Directory to clone repositories into (defaults to 'repositories').",
)
@click.option(
    "--owner",
    "-o",
    default="",
    help="Filter web maps by owner username.",
)
@click.option(
    "--query",
    "-q",
    default="",
    help="Search query to filter web maps (e.g., 'title:MyMap').",
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
    help="Maximum number of web maps to clone (default: 100).",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (or use PORTAL_URL env var).",
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
@click.option(
    "--skip-existing",
    is_flag=True,
    default=False,
    help="Skip maps that already have directories (instead of failing).",
)
def setup_repos(
        directory: str,
        owner: str,
        query: str,
        tag: str,
        max_results: int,
        url: str,
        username: str,
        password: str,
        skip_existing: bool,
) -> None:
    """Bulk clone web maps into a repositories directory.

    Creates a repositories directory and clones each web map into its own
    subdirectory with a .gitmap folder. Useful for setting up local copies
    of multiple maps at once.

    Examples:
        gitmap setup-repos --owner myusername
        gitmap setup-repos --owner myusername --directory my-repos
        gitmap setup-repos --tag production --skip-existing
        gitmap setup-repos --query "title:Project*" --owner myusername
    """
    try:
        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url if url else None)

        # Create base repositories directory
        base_dir = Path(directory).resolve()
        if not base_dir.exists():
            base_dir.mkdir(parents=True)
            console.print(f"[green]Created directory: {base_dir}[/green]")
        else:
            console.print(f"[dim]Using existing directory: {base_dir}[/dim]")

        # Connect to Portal
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
            password=password if password else None,
        )

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # List web maps
        console.print("[dim]Querying available web maps...[/dim]")
        webmaps = list_webmaps(
            gis=connection.gis,
            query=query,
            owner=owner,
            tag=tag,
            max_results=max_results,
        )

        if not webmaps:
            console.print("[yellow]No web maps found matching the filters.[/yellow]")
            return

        console.print(f"\n[bold]Found {len(webmaps)} web map(s) to clone[/bold]")

        # Display filter info
        filters = []
        if owner:
            filters.append(f"owner={owner}")
        if tag:
            filters.append(f"tag={tag}")
        if query:
            filters.append(f"query={query}")
        if filters:
            console.print(f"[dim]Filters: {', '.join(filters)}[/dim]")

        console.print()

        # Clone each web map
        success_count = 0
        skipped_count = 0
        failed_maps = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for idx, webmap_info in enumerate(webmaps, 1):
                item_id = webmap_info.get("id", "")
                title = webmap_info.get("title", "Unknown")
                map_owner = webmap_info.get("owner", "")

                task = progress.add_task(
                    f"[{idx}/{len(webmaps)}] Cloning '{title}'...",
                    total=None
                )

                try:
                    # Fetch web map data
                    item, map_data = get_webmap_by_id(connection.gis, item_id)

                    # Create sanitized directory name
                    safe_title = "".join(
                        c if c.isalnum() or c in "-_" else "_"
                        for c in title
                    )
                    target_dir = base_dir / safe_title

                    # Check if directory exists
                    if target_dir.exists():
                        if skip_existing:
                            progress.update(task, description=f"[{idx}/{len(webmaps)}] Skipped '{title}' (exists)")
                            skipped_count += 1
                            continue
                        else:
                            raise click.ClickException(f"Directory '{target_dir.name}' already exists")

                    # Create directory and initialize repo
                    target_dir.mkdir(parents=True)
                    repo = Repository(target_dir)

                    repo.init(
                        project_name=title,
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
                        message=f"Clone from Portal: {title}",
                        author=connection.username or "GitMap",
                    )

                    progress.update(task, description=f"[{idx}/{len(webmaps)}] ✓ Cloned '{title}'")
                    success_count += 1

                except Exception as clone_error:
                    progress.update(task, description=f"[{idx}/{len(webmaps)}] ✗ Failed '{title}'")
                    failed_maps.append({
                        "title": title,
                        "id": item_id,
                        "error": str(clone_error),
                    })

        # Display summary
        console.print()
        console.print("[bold]═" * 60 + "[/bold]")
        console.print("[bold]Summary[/bold]")
        console.print("[bold]═" * 60 + "[/bold]")
        console.print(f"  [green]✓ Successfully cloned:[/green] {success_count}")

        if skipped_count > 0:
            console.print(f"  [yellow]⊘ Skipped (existing):[/yellow] {skipped_count}")

        if failed_maps:
            console.print(f"  [red]✗ Failed:[/red] {len(failed_maps)}")
            console.print()
            console.print("[bold red]Failed Maps:[/bold red]")
            for failed in failed_maps:
                console.print(f"  • {failed['title']} ({failed['id']})")
                console.print(f"    [dim]{failed['error']}[/dim]")

        console.print()
        console.print(f"[dim]All repositories cloned into: {base_dir}[/dim]")

        if success_count > 0:
            console.print()
            console.print("[dim]Example commands:[/dim]")
            console.print(f"[dim]  cd {base_dir}/<map-directory>[/dim]")
            console.print("[dim]  gitmap status[/dim]")

    except Exception as setup_error:
        msg = f"Setup repositories failed: {setup_error}"
        raise click.ClickException(msg) from setup_error
