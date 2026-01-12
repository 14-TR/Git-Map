"""GitMap merge command.

Merges one branch into the current branch.

Execution Context:
    CLI command - invoked via `gitmap merge <branch>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Merge operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gitmap_core.merge import apply_resolution
from gitmap_core.merge import format_merge_summary
from gitmap_core.merge import merge_maps
from gitmap_core.merge import resolve_conflict
from gitmap_core.repository import find_repository

console = Console()


def _record_merge_event(
    repo,
    source_branch: str,
    target_branch: str,
    commit_id: str | None = None,
    had_conflicts: bool = False,
    conflicts_resolved: int = 0,
) -> None:
    """Record a merge event to the context store."""
    try:
        config = repo.get_config()
        actor = config.user_name if config else None
        with repo.get_context_store() as store:
            store.record_event(
                event_type="merge",
                repo=str(repo.root),
                ref=commit_id or target_branch,
                actor=actor,
                payload={
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "commit_id": commit_id,
                    "had_conflicts": had_conflicts,
                    "conflicts_resolved": conflicts_resolved,
                },
            )
    except Exception:
        pass  # Don't fail merge if context recording fails


# ---- Merge Command ------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "branch",
    required=True,
)
@click.option(
    "--no-commit",
    is_flag=True,
    help="Perform merge but don't auto-commit.",
)
@click.option(
    "--abort",
    "abort_merge",
    is_flag=True,
    help="Abort an in-progress merge.",
)
def merge(
        branch: str,
        no_commit: bool,
        abort_merge: bool,
) -> None:
    """Merge a branch into the current branch.

    Performs a layer-level merge. Conflicts are flagged when the
    same layer is modified in both branches.

    Examples:
        gitmap merge feature/new-layer
        gitmap merge main --no-commit
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        current_branch = repo.get_current_branch()
        if not current_branch:
            raise click.ClickException("Cannot merge in detached HEAD state")

        if branch == current_branch:
            raise click.ClickException("Cannot merge branch into itself")

        # Check branch exists
        if branch not in repo.list_branches():
            raise click.ClickException(f"Branch '{branch}' not found")

        # Get commit data
        our_commit_id = repo.get_branch_commit(current_branch)
        their_commit_id = repo.get_branch_commit(branch)

        if not their_commit_id:
            raise click.ClickException(f"Branch '{branch}' has no commits")

        their_commit = repo.get_commit(their_commit_id)
        if not their_commit:
            raise click.ClickException(f"Commit '{their_commit_id}' not found")

        # Get our data (from index or commit)
        our_data = repo.get_index()
        if not our_data and our_commit_id:
            our_commit = repo.get_commit(our_commit_id)
            if our_commit:
                our_data = our_commit.map_data

        # Perform merge
        console.print(f"[dim]Merging '{branch}' into '{current_branch}'...[/dim]")

        merge_result = merge_maps(
            ours=our_data,
            theirs=their_commit.map_data,
            base=None,  # TODO: Find common ancestor
        )

        # Track initial conflicts for event recording
        initial_conflict_count = len(merge_result.conflicts) if merge_result.has_conflicts else 0

        # Handle conflicts
        if merge_result.has_conflicts:
            # Separate table conflicts from layer conflicts
            # Check merged_data to see which conflicts are tables vs layers
            merged_tables = merge_result.merged_data.get("tables", [])
            merged_layers = merge_result.merged_data.get("operationalLayers", [])
            
            table_ids = {table.get("id") for table in merged_tables if table.get("id")}
            layer_ids = {layer.get("id") for layer in merged_layers if layer.get("id")}
            
            # A conflict could be in either, but check tables first (more specific)
            table_conflicts = [c for c in merge_result.conflicts if c.layer_id in table_ids]
            layer_conflicts = [c for c in merge_result.conflicts if c.layer_id not in table_ids]

            total_conflicts = len(merge_result.conflicts)
            console.print(Panel(
                f"[yellow]Merge has {total_conflicts} conflict(s)[/yellow]\n"
                f"  Layers: {len(layer_conflicts)}\n"
                f"  Tables: {len(table_conflicts)}",
                title="Merge Conflicts",
                border_style="yellow",
            ))

            # Handle table conflicts - prompt once for all
            if table_conflicts:
                console.print()
                console.print(f"[bold]Table Conflicts ({len(table_conflicts)}):[/bold]")
                console.print("  Tables will be resolved together.")
                
                table_choice = Prompt.ask(
                    "  Resolve all tables with",
                    choices=["ours", "theirs", "skip"],
                    default="theirs",
                )

                if table_choice in ("ours", "theirs"):
                    for conflict in table_conflicts:
                        resolved = resolve_conflict(conflict, table_choice)
                        merge_result = apply_resolution(merge_result, conflict.layer_id, resolved)
                    console.print(f"  [green]Resolved {len(table_conflicts)} table(s) with '{table_choice}'[/green]")

            # Handle layer conflicts - prompt individually
            if layer_conflicts:
                console.print()
                console.print(f"[bold]Layer Conflicts ({len(layer_conflicts)}):[/bold]")
                
                for conflict in layer_conflicts:
                    console.print()
                    console.print(f"[bold]Conflict in layer: {conflict.layer_title}[/bold]")
                    console.print(f"  Layer ID: {conflict.layer_id}")

                    # Prompt for resolution
                    choice = Prompt.ask(
                        "  Resolve with",
                        choices=["ours", "theirs", "skip"],
                        default="skip",
                    )

                    if choice in ("ours", "theirs"):
                        resolved = resolve_conflict(conflict, choice)
                        merge_result = apply_resolution(merge_result, conflict.layer_id, resolved)
                        console.print(f"  [green]Resolved with '{choice}'[/green]")

        # Check if conflicts remain
        if merge_result.has_conflicts:
            console.print()
            console.print("[yellow]Unresolved conflicts remain. Merge not applied.[/yellow]")
            return

        # Update index with merged data
        repo.update_index(merge_result.merged_data)

        # Display summary
        console.print()
        console.print(format_merge_summary(merge_result))

        # Auto-commit unless --no-commit
        merge_commit_id = None
        if not no_commit:
            commit_msg = f"Merge branch '{branch}' into '{current_branch}'"
            new_commit = repo.create_commit(message=commit_msg)
            merge_commit_id = new_commit.id

            console.print()
            console.print(f"[green]Merge commit: {new_commit.id[:8]}[/green]")
        else:
            console.print()
            console.print("[dim]Merge staged. Use 'gitmap commit' to finalize.[/dim]")

        # Record merge event
        _record_merge_event(
            repo,
            source_branch=branch,
            target_branch=current_branch,
            commit_id=merge_commit_id,
            had_conflicts=initial_conflict_count > 0,
            conflicts_resolved=initial_conflict_count,
        )

    except Exception as merge_error:
        msg = f"Merge failed: {merge_error}"
        raise click.ClickException(msg) from merge_error


