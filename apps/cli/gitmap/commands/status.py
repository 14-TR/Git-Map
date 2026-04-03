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

import json

import click
from rich.console import Console
from rich.panel import Panel

from gitmap_core.diff import diff_maps, format_diff_summary
from gitmap_core.repository import find_repository

console = Console()


# ---- Status Command -----------------------------------------------------------------------------------------


@click.command(epilog="Tip: use 'gitmap diff' to see a full breakdown of changes.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format: 'text' for human-readable, 'json' for machine-readable.",
)
def status(fmt: str) -> None:
    """Show the working tree status.

    Displays the current branch, whether there are uncommitted changes,
    and a summary of modifications in the staging area.

    Example:
        gitmap status
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository. Run 'gitmap init' to create one.")

        # Get current branch
        current_branch = repo.get_current_branch()
        head_commit = repo.get_head_commit()
        has_changes = repo.has_uncommitted_changes()

        # Build diff if there are changes
        map_diff = None
        if has_changes:
            index_data = repo.get_index()
            if head_commit:
                commit = repo.get_commit(head_commit)
                if commit:
                    map_diff = diff_maps(index_data, commit.map_data)

        # ---- JSON output ----
        if fmt == "json":
            result = {
                "branch": current_branch or None,
                "head_commit": head_commit[:8] if head_commit else None,
                "clean": not has_changes,
            }
            if head_commit:
                commit = repo.get_commit(head_commit)
                if commit:
                    result["head_message"] = commit.message
            if map_diff:
                result["diff"] = map_diff.to_dict()
            click.echo(json.dumps(result, indent=2))
            return

        # ---- Text output (original) ----
        branch_display = current_branch or "(detached HEAD)"
        console.print(
            Panel(
                f"[bold]On branch:[/bold] [cyan]{branch_display}[/cyan]",
                title="GitMap Status",
                border_style="blue",
            )
        )

        if head_commit:
            commit = repo.get_commit(head_commit)
            if commit:
                console.print(f"[dim]Latest commit: {commit.id[:8]} - {commit.message}[/dim]")
        else:
            console.print("[dim]No commits yet[/dim]")

        console.print()

        if has_changes:
            console.print("[yellow]Changes not committed:[/yellow]")

            if map_diff:
                console.print(format_diff_summary(map_diff))
            else:
                index_data = repo.get_index()
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
