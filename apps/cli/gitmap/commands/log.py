"""GitMap log command.

Shows commit history for the repository.

Execution Context:
    CLI command - invoked via `gitmap log`

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
from rich.table import Table

from gitmap_core.repository import find_repository

console = Console()


# ---- Log Command --------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--limit",
    "-n",
    default=10,
    help="Maximum number of commits to show.",
)
@click.option(
    "--oneline",
    is_flag=True,
    help="Show compact one-line format.",
)
def log(
        limit: int,
        oneline: bool,
) -> None:
    """Show commit history.

    Displays the commit log starting from HEAD, walking back through
    parent commits.

    Examples:
        gitmap log
        gitmap log -n 5
        gitmap log --oneline
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        commits = repo.get_commit_history(limit=limit)

        if not commits:
            console.print("[dim]No commits yet[/dim]")
            return

        current_branch = repo.get_current_branch()
        head_commit = repo.get_head_commit()

        if oneline:
            # Compact format
            for commit in commits:
                marker = "[yellow]*[/yellow] " if commit.id == head_commit else "  "
                console.print(
                    f"{marker}[cyan]{commit.id[:8]}[/cyan] {commit.message}"
                )
        else:
            # Full format
            for i, commit in enumerate(commits):
                if i > 0:
                    console.print()

                # Header with commit ID
                is_head = commit.id == head_commit
                head_marker = f" [yellow](HEAD -> {current_branch})[/yellow]" if is_head else ""

                console.print(f"[bold cyan]commit {commit.id}[/bold cyan]{head_marker}")
                console.print(f"Author: {commit.author}")
                console.print(f"Date:   {commit.timestamp}")

                if commit.parent:
                    console.print(f"Parent: {commit.parent[:8]}")

                console.print()
                console.print(f"    {commit.message}")

                # Layer summary
                layers = commit.map_data.get("operationalLayers", [])
                console.print(f"    [dim]({len(layers)} layer(s))[/dim]")

    except Exception as log_error:
        msg = f"Log failed: {log_error}"
        raise click.ClickException(msg) from log_error


