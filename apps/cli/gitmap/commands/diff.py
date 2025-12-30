"""GitMap diff command.

Shows differences between commits, branches, or staging area.

Execution Context:
    CLI command - invoked via `gitmap diff [target]`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Diff operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from gitmap_core.diff import diff_maps
from gitmap_core.diff import format_diff_summary
from gitmap_core.repository import find_repository

console = Console()


# ---- Diff Command -------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "target",
    required=False,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed property-level changes.",
)
def diff(
        target: str | None,
        verbose: bool,
) -> None:
    """Show changes between states.

    Without arguments, shows differences between staging area (index)
    and the last commit. With a TARGET, compares staging to that
    branch or commit.

    Examples:
        gitmap diff                 # Index vs HEAD
        gitmap diff main            # Index vs main branch
        gitmap diff abc123          # Index vs specific commit
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Get current staging area
        index_data = repo.get_index()

        # Determine target commit
        if target:
            # Check if target is a branch name
            branches = repo.list_branches()
            if target in branches:
                commit_id = repo.get_branch_commit(target)
            else:
                # Assume it's a commit ID
                commit_id = target
        else:
            # Default to HEAD
            commit_id = repo.get_head_commit()

        if not commit_id:
            console.print("[yellow]No commits to compare against[/yellow]")
            return

        # Load target commit
        target_commit = repo.get_commit(commit_id)
        if not target_commit:
            raise click.ClickException(f"Commit '{commit_id}' not found")

        # Perform diff
        map_diff = diff_maps(index_data, target_commit.map_data)

        if not map_diff.has_changes:
            console.print("[green]No differences[/green]")
            return

        # Display header
        console.print(Panel(
            f"Comparing [cyan]index[/cyan] to [yellow]{commit_id[:8]}[/yellow]",
            title="GitMap Diff",
            border_style="blue",
        ))

        # Display summary
        console.print(format_diff_summary(map_diff))

        # Verbose output
        if verbose and map_diff.modified_layers:
            console.print()
            console.print("[bold]Detailed Changes:[/bold]")

            for change in map_diff.modified_layers:
                console.print()
                console.print(f"[cyan]Layer: {change.layer_title}[/cyan]")

                if change.details:
                    import json
                    details_json = json.dumps(change.details, indent=2)
                    syntax = Syntax(details_json, "json", theme="monokai")
                    console.print(syntax)

    except Exception as diff_error:
        msg = f"Diff failed: {diff_error}"
        raise click.ClickException(msg) from diff_error


