"""GitMap checkout command.

Switches to a different branch or restores working tree files.

Execution Context:
    CLI command - invoked via `gitmap checkout <branch>`

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


# ---- Checkout Command ---------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "branch",
    required=True,
)
@click.option(
    "--create",
    "-b",
    is_flag=True,
    help="Create branch if it doesn't exist.",
)
def checkout(
        branch: str,
        create: bool,
) -> None:
    """Switch to a different branch.

    Updates HEAD to point to the specified branch and loads the
    branch's latest commit state into the working tree.

    Examples:
        gitmap checkout main
        gitmap checkout feature/new-layer
        gitmap checkout -b feature/new-layer  # Create and checkout
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Check for uncommitted changes
        if repo.has_uncommitted_changes():
            console.print("[yellow]Warning: You have uncommitted changes[/yellow]")
            if not click.confirm("Switch branches anyway?"):
                console.print("[dim]Checkout cancelled[/dim]")
                return

        # Create branch if requested and doesn't exist
        if create:
            branches = repo.list_branches()
            if branch not in branches:
                repo.create_branch(branch)
                console.print(f"[green]Created branch '{branch}'[/green]")

        # Switch to branch
        repo.checkout_branch(branch)

        console.print(f"[green]Switched to branch '{branch}'[/green]")

        # Show commit info
        commit_id = repo.get_branch_commit(branch)
        if commit_id:
            commit = repo.get_commit(commit_id)
            if commit:
                console.print(f"[dim]At commit: {commit.id[:8]} - {commit.message}[/dim]")
        else:
            console.print("[dim]Branch has no commits yet[/dim]")

    except Exception as checkout_error:
        msg = f"Checkout failed: {checkout_error}"
        raise click.ClickException(msg) from checkout_error


