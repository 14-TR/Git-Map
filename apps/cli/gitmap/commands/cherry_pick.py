"""GitMap cherry-pick command.

Apply changes from a specific commit to the current branch.

Execution Context:
    CLI command - invoked via `gitmap cherry-pick <commit_hash>`

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


# ---- Cherry-pick Command ------------------------------------------------------------------------------------


@click.command(name="cherry-pick")
@click.argument(
    "commit_hash",
    required=True,
)
@click.option(
    "--rationale",
    "-r",
    default="",
    help="Optional rationale explaining why this cherry-pick is being made.",
)
def cherry_pick(
        commit_hash: str,
        rationale: str,
) -> None:
    """Apply changes from a specific commit to the current branch.

    Creates a new commit with the same changes as the source commit
    but with a new commit ID. Useful for selectively applying changes
    from one branch to another.

    Examples:
        gitmap cherry-pick abc12345
        gitmap cherry-pick abc12345 -r "Backporting critical fix"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Check for uncommitted changes
        if repo.has_uncommitted_changes():
            console.print("[yellow]Warning: You have uncommitted changes.[/yellow]")
            if not click.confirm("Continue with cherry-pick?", default=False):
                console.print("[dim]Cherry-pick cancelled.[/dim]")
                return

        # Get source commit info for display
        source_commit = repo.get_commit(commit_hash)
        if not source_commit:
            raise click.ClickException(f"Commit '{commit_hash}' not found")

        # Display what we're cherry-picking
        console.print(f"[dim]Cherry-picking commit {commit_hash[:8]}...[/dim]")
        console.print(f"  [bold]Message:[/bold] {source_commit.message.split(chr(10))[0]}")
        console.print(f"  [bold]Author:[/bold] {source_commit.author}")

        # Perform the cherry-pick
        new_commit = repo.cherry_pick(
            commit_id=commit_hash,
            rationale=rationale if rationale else None,
        )

        # Display result
        console.print()
        console.print(f"[green]Created commit {new_commit.id[:8]}[/green]")
        console.print()
        console.print(f"  [bold]Message:[/bold] {new_commit.message.split(chr(10))[0]}")
        console.print(f"  [bold]Author:[/bold] {new_commit.author}")
        console.print(f"  [bold]Timestamp:[/bold] {new_commit.timestamp}")

        if rationale:
            console.print(f"  [bold]Rationale:[/bold] {rationale}")

        # Show layer summary
        layers = new_commit.map_data.get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

        current_branch = repo.get_current_branch()
        if current_branch:
            console.print()
            console.print(f"[dim]Branch '{current_branch}' updated to {new_commit.id[:8]}[/dim]")

    except Exception as cherry_pick_error:
        msg = f"Cherry-pick failed: {cherry_pick_error}"
        raise click.ClickException(msg) from cherry_pick_error
