"""GitMap branch command.

Lists existing branches or creates a new branch.

Execution Context:
    CLI command - invoked via `gitmap branch [name]`

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


def _record_branch_event(repo, action: str, branch_name: str, commit_id: str | None = None) -> None:
    """Record a branch event to the context store."""
    try:
        config = repo.get_config()
        actor = config.user_name if config else None
        with repo.get_context_store() as store:
            store.record_event(
                event_type="branch",
                repo=str(repo.root),
                ref=branch_name,
                actor=actor,
                payload={
                    "action": action,
                    "branch_name": branch_name,
                    "commit_id": commit_id,
                },
            )
    except Exception:
        pass  # Don't fail branch operation if context recording fails


# ---- Branch Command -----------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "name",
    required=False,
)
@click.option(
    "--delete",
    "-d",
    is_flag=True,
    help="Delete the specified branch.",
)
@click.option(
    "--list",
    "-l",
    "list_branches",
    is_flag=True,
    help="List all branches.",
)
def branch(
        name: str | None,
        delete: bool,
        list_branches: bool,
) -> None:
    """List or create branches.

    Without arguments, lists all local branches. With a NAME argument,
    creates a new branch pointing to HEAD.

    Examples:
        gitmap branch              # List branches
        gitmap branch feature/x    # Create branch 'feature/x'
        gitmap branch -d feature/x # Delete branch 'feature/x'
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        current_branch = repo.get_current_branch()

        # List branches
        if list_branches or (not name and not delete):
            branches = repo.list_branches()

            if not branches:
                console.print("[dim]No branches yet[/dim]")
                return

            for branch_name in branches:
                if branch_name == current_branch:
                    console.print(f"[green]* {branch_name}[/green]")
                else:
                    console.print(f"  {branch_name}")
            return

        if not name:
            raise click.ClickException("Branch name required")

        # Delete branch
        if delete:
            repo.delete_branch(name)
            _record_branch_event(repo, action="delete", branch_name=name)
            console.print(f"[green]Deleted branch '{name}'[/green]")
            return

        # Create branch
        new_branch = repo.create_branch(name)
        _record_branch_event(repo, action="create", branch_name=new_branch.name, commit_id=new_branch.commit_id)
        console.print(f"[green]Created branch '{new_branch.name}'[/green]")

        if new_branch.commit_id:
            console.print(f"[dim]Points to commit {new_branch.commit_id[:8]}[/dim]")
        else:
            console.print("[dim]Branch created (no commits yet)[/dim]")

    except Exception as branch_error:
        msg = f"Branch operation failed: {branch_error}"
        raise click.ClickException(msg) from branch_error


