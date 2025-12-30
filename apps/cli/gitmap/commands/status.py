"""GitMap status command.

Shows the current state of the repository including current branch,
uncommitted changes, and staging area status.

Execution Context:
    CLI command - invoked via `gitmap status`

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
from rich.panel import Panel

from gitmap_core.diff import diff_maps
from gitmap_core.diff import format_diff_summary
from gitmap_core.repository import find_repository

console = Console()


# ---- Status Command -----------------------------------------------------------------------------------------


@click.command()
def status() -> None:
    """Show the working tree status.

    Displays the current branch, whether there are uncommitted changes,
    and a summary of modifications in the staging area.

    Example:
        gitmap status
    """
    try:
        repo = find_repository()

        if not repo:
            console.print("[red]Not a GitMap repository[/red]")
            console.print("Run 'gitmap init' to create a new repository.")
            return

        # Get current branch
        current_branch = repo.get_current_branch()
        head_commit = repo.get_head_commit()

        # Display header
        branch_display = current_branch or "(detached HEAD)"
        console.print(Panel(
            f"[bold]On branch:[/bold] [cyan]{branch_display}[/cyan]",
            title="GitMap Status",
            border_style="blue",
        ))

        # Display commit info
        if head_commit:
            commit = repo.get_commit(head_commit)
            if commit:
                console.print(f"[dim]Latest commit: {commit.id[:8]} - {commit.message}[/dim]")
        else:
            console.print("[dim]No commits yet[/dim]")

        console.print()

        # Check for uncommitted changes
        if repo.has_uncommitted_changes():
            console.print("[yellow]Changes not committed:[/yellow]")

            # Get diff details
            index_data = repo.get_index()

            if head_commit:
                commit = repo.get_commit(head_commit)
                if commit:
                    map_diff = diff_maps(index_data, commit.map_data)
                    console.print(format_diff_summary(map_diff))
            else:
                # No commits yet, show what's staged
                layers = index_data.get("operationalLayers", [])
                if layers:
                    console.print(f"  Staged map with {len(layers)} layer(s)")
                else:
                    console.print("  Staged empty map")

            console.print()
            console.print('[dim]Use "gitmap commit -m <message>" to commit changes[/dim]')
        else:
            console.print("[green]Nothing to commit, working tree clean[/green]")

    except Exception as status_error:
        msg = f"Failed to get status: {status_error}"
        raise click.ClickException(msg) from status_error


