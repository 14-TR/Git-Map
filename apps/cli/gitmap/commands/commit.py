"""GitMap commit command.

Records changes to the repository by creating a new commit snapshot.

Execution Context:
    CLI command - invoked via `gitmap commit -m "message"`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console

from gitmap_core.repository import find_repository

console = Console()


# ---- Commit Command -----------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--message",
    "-m",
    required=True,
    help="Commit message describing the changes.",
)
@click.option(
    "--author",
    "-a",
    default="",
    help="Override the commit author.",
)
def commit(
        message: str,
        author: str,
) -> None:
    """Record changes to the repository.

    Creates a new commit with the current staging area (index) content.
    A commit message is required.

    Examples:
        gitmap commit -m "Initial commit"
        gitmap commit -m "Added new layer" --author "John Doe"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Check for changes
        if not repo.has_uncommitted_changes():
            console.print("[yellow]Nothing to commit, working tree clean[/yellow]")
            return

        # Create commit
        new_commit = repo.create_commit(
            message=message,
            author=author if author else None,
        )

        # Display result
        console.print(f"[green]Created commit {new_commit.id[:8]}[/green]")
        console.print()
        console.print(f"  [bold]Message:[/bold] {new_commit.message}")
        console.print(f"  [bold]Author:[/bold] {new_commit.author}")
        console.print(f"  [bold]Timestamp:[/bold] {new_commit.timestamp}")

        if new_commit.parent:
            console.print(f"  [bold]Parent:[/bold] {new_commit.parent[:8]}")

        # Show layer summary
        layers = new_commit.map_data.get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        current_branch = repo.get_current_branch()
        if current_branch:
            console.print()
            console.print(f"[dim]Branch '{current_branch}' updated to {new_commit.id[:8]}[/dim]")

    except Exception as commit_error:
        msg = f"Commit failed: {commit_error}"
        raise click.ClickException(msg) from commit_error


