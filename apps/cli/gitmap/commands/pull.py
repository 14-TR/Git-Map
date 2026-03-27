"""GitMap pull command.

Pulls latest changes from ArcGIS Portal.

Execution Context:
    CLI command - invoked via `gitmap pull`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Remote operations

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import find_repository

from .utils import get_portal_url

console = Console()


# ---- Pull Command -------------------------------------------------------------------------------------------


@click.command(epilog="Tip: use 'gitmap diff' to review pulled changes before committing.")
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
@click.option(
    "--rationale",
    "-r",
    default="",
    help="Optional rationale explaining why this pull is being made.",
)
def pull(
        branch: str,
        url: str,
        username: str,
        rationale: str,
) -> None:
    """Pull latest changes from Portal.

    Fetches the web map from Portal and updates the local staging area.
    Does not automatically commit — review changes with 'gitmap diff'
    then save with 'gitmap commit'.

    Examples:
        gitmap pull
        gitmap pull --branch main
        gitmap pull --url https://portal.example.com
        gitmap pull -r "Syncing production changes"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException(
                "Not a GitMap repository. Run 'gitmap init' to create one."
            )

        # Determine Portal URL
        config = repo.get_config()
        if url:
            portal_url = url
        elif config.remote and config.remote.url:
            portal_url = config.remote.url
        else:
            portal_url = get_portal_url()

        target_branch = branch or repo.get_current_branch()

        map_data: dict = {}
        connection = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Connecting to {portal_url}...", total=None)

            connection = get_connection(
                url=portal_url,
                username=username if username else None,
            )

            progress.update(task, description=f"Pulling '{target_branch}' from Portal...")
            remote_ops = RemoteOperations(repo, connection)
            map_data = remote_ops.pull(target_branch)

            progress.update(task, description="Done.")

        # Display result
        layers = map_data.get("operationalLayers", [])
        auth_line = f" [dim](as {connection.username})[/dim]" if connection and connection.username else ""
        console.print(f"[green]✓ Pulled '{target_branch}' from Portal[/green]{auth_line}")
        console.print()
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        if rationale:
            console.print()
            console.print(f"  [bold]Rationale:[/bold] {rationale}")

        console.print()
        console.print(
            "[dim]Changes staged. Use 'gitmap diff' to review and 'gitmap commit' to save.[/dim]"
        )

        # Record event in context store (non-blocking)
        try:
            with repo.get_context_store() as store:
                store.record_event(
                    event_type="pull",
                    repo=str(repo.root),
                    ref=target_branch,
                    actor=connection.username if connection else None,
                    payload={
                        "layers_count": len(layers),
                        "portal_url": portal_url,
                        "branch": target_branch,
                    },
                    rationale=rationale if rationale else None,
                )

            config = repo.get_config()
            if config.auto_visualize:
                repo.regenerate_context_graph()
        except Exception:
            pass  # Don't fail pull if context recording fails

    except click.ClickException:
        raise
    except Exception as pull_error:
        err = str(pull_error)
        if "not connected" in err.lower() or "connect()" in err.lower():
            msg = (
                "Pull failed: Portal authentication error.\n"
                "  Hint: check PORTAL_URL, ARCGIS_USERNAME, and ARCGIS_PASSWORD in your .env file."
            )
        elif "not found" in err.lower() or "no item" in err.lower():
            msg = (
                "Pull failed: web map not found on Portal.\n"
                "  Hint: verify the item ID in .gitmap/config.json and that the item still exists."
            )
        else:
            msg = f"Pull failed: {pull_error}"
        raise click.ClickException(msg) from pull_error
