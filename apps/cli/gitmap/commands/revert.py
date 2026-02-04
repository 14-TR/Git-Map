"""GitMap revert command.

Reverts a specific commit by creating an inverse commit.

Execution Context:
    CLI command - invoked via `gitmap revert <commit_hash>`

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


# ---- Revert Command -----------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "commit_hash",
    required=True,
)
@click.option(
    "--rationale",
    "-r",
    default="",
    help="Optional rationale explaining why this revert is being made.",
)
def revert(
        commit_hash: str,
        rationale: str,
) -> None:
    """Revert a specific commit.

    Creates a new commit that undoes the changes introduced by the
    specified commit. Does not remove history - adds an inverse commit.

    Examples:
        gitmap revert abc12345
        gitmap revert abc12345 -r "Reverted due to breaking changes"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Check for uncommitted changes
        if repo.has_uncommitted_changes():
            console.print("[yellow]Warning: You have uncommitted changes.[/yellow]")
            if not click.confirm("Continue with revert?", default=False):
                console.print("[dim]Revert cancelled.[/dim]")
                return

        # Get commit info for display
        commit_to_revert = repo.get_commit(commit_hash)
        if not commit_to_revert:
            raise click.ClickException(f"Commit '{commit_hash}' not found")

        # Display what we're reverting
        console.print(f"[dim]Reverting commit {commit_hash[:8]}...[/dim]")
        console.print(f"  [bold]Message:[/bold] {commit_to_revert.message}")

        # Perform the revert
        revert_commit = repo.revert(
            commit_id=commit_hash,
            rationale=rationale if rationale else None,
        )

        # Display result
        console.print()
        console.print(f"[green]Created revert commit {revert_commit.id[:8]}[/green]")
        console.print()
        console.print(f"  [bold]Message:[/bold] {revert_commit.message.split(chr(10))[0]}")
        console.print(f"  [bold]Author:[/bold] {revert_commit.author}")
        console.print(f"  [bold]Timestamp:[/bold] {revert_commit.timestamp}")

        if rationale:
            console.print(f"  [bold]Rationale:[/bold] {rationale}")

        # Show layer summary
        layers = revert_commit.map_data.get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        current_branch = repo.get_current_branch()
        if current_branch:
            console.print()
            console.print(f"[dim]Branch '{current_branch}' updated to {revert_commit.id[:8]}[/dim]")

    except Exception as revert_error:
        msg = f"Revert failed: {revert_error}"
        raise click.ClickException(msg) from revert_error
