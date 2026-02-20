"""GitMap diff command.

Shows differences between commits, branches, or staging area.

Execution Context:
    CLI command - invoked via `gitmap diff [source] [target]`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Diff operations

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from gitmap_core.diff import diff_maps
from gitmap_core.diff import format_diff_summary
from gitmap_core.repository import find_repository
from gitmap_core.repository import Repository

console = Console()


# ---- Helpers ------------------------------------------------------------------------------------------------


def _resolve_ref(
        repo: Repository,
        ref: str,
) -> str | None:
    """Resolve a branch name or commit ID to a commit ID.

    Args:
        repo: Repository to search.
        ref: Branch name or commit ID string.

    Returns:
        Resolved commit ID, or None if not found.
    """
    branches = repo.list_branches()
    if ref in branches:
        return repo.get_branch_commit(ref)
    # Treat as raw commit ID
    return ref if repo.get_commit(ref) else None


def _print_diff(
        map_diff,
        label_a: str,
        label_b: str,
        verbose: bool,
) -> None:
    """Display a MapDiff result to the console.

    Args:
        map_diff: MapDiff object to display.
        label_a: Human-readable label for the 'from' side.
        label_b: Human-readable label for the 'to' side.
        verbose: Whether to show property-level change details.
    """
    if not map_diff.has_changes:
        console.print("[green]No differences[/green]")
        return

    console.print(Panel(
        f"Comparing [cyan]{label_a}[/cyan] → [yellow]{label_b}[/yellow]",
        title="GitMap Diff",
        border_style="blue",
    ))

    console.print(format_diff_summary(map_diff))

    if verbose and map_diff.modified_layers:
        console.print()
        console.print("[bold]Detailed Changes:[/bold]")

        for change in map_diff.modified_layers:
            console.print()
            console.print(f"[cyan]Layer: {change.layer_title}[/cyan]")

            if change.details:
                details_json = json.dumps(change.details, indent=2)
                syntax = Syntax(details_json, "json", theme="monokai")
                console.print(syntax)


# ---- Diff Command -------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "source",
    required=False,
)
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
        source: str | None,
        target: str | None,
        verbose: bool,
) -> None:
    """Show changes between states.

    With no arguments, compares the staging area (index) to HEAD.
    With one argument (SOURCE), compares the staging area to that
    branch or commit.
    With two arguments (SOURCE TARGET), compares the two branches or
    commits directly — the staging area is not involved.

    Examples:
        gitmap diff                         # Index vs HEAD
        gitmap diff main                    # Index vs main
        gitmap diff abc123                  # Index vs commit abc123
        gitmap diff main feature/new-layer  # Branch vs branch
        gitmap diff abc123 def456           # Commit vs commit
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        if source and target:
            # ---- Two-argument form: compare two refs directly ---------
            source_id = _resolve_ref(repo, source)
            if not source_id:
                raise click.ClickException(
                    f"Branch or commit not found: '{source}'"
                )

            target_id = _resolve_ref(repo, target)
            if not target_id:
                raise click.ClickException(
                    f"Branch or commit not found: '{target}'"
                )

            source_commit = repo.get_commit(source_id)
            if not source_commit:
                raise click.ClickException(
                    f"Could not load commit '{source_id}'"
                )

            target_commit = repo.get_commit(target_id)
            if not target_commit:
                raise click.ClickException(
                    f"Could not load commit '{target_id}'"
                )

            map_diff = diff_maps(source_commit.map_data, target_commit.map_data)
            label_a = f"{source} ({source_id[:8]})"
            label_b = f"{target} ({target_id[:8]})"

        else:
            # ---- One- or zero-argument form: index vs ref -------------
            index_data = repo.get_index()

            if source:
                # Resolve the single ref argument
                commit_id = _resolve_ref(repo, source)
                if not commit_id:
                    raise click.ClickException(
                        f"Branch or commit not found: '{source}'"
                    )
                label_b = f"{source} ({commit_id[:8]})"
            else:
                # Default to HEAD
                commit_id = repo.get_head_commit()
                if not commit_id:
                    console.print("[yellow]No commits to compare against[/yellow]")
                    return
                label_b = f"HEAD ({commit_id[:8]})"

            target_commit = repo.get_commit(commit_id)
            if not target_commit:
                raise click.ClickException(f"Commit '{commit_id}' not found")

            map_diff = diff_maps(index_data, target_commit.map_data)
            label_a = "index"

        _print_diff(map_diff, label_a, label_b, verbose)

    except Exception as diff_error:
        msg = f"Diff failed: {diff_error}"
        raise click.ClickException(msg) from diff_error
