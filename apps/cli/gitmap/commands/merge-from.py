"""GitMap cross-repository merge command.

Merges a branch from one GitMap repository into the current branch
of another repository.

Execution Context:
    CLI command - invoked via `gitmap merge-from <source_repo> <source_branch>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository and merge operations

Metadata:
    Version: 1.0.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from gitmap_core.merge import apply_resolution
from gitmap_core.merge import format_merge_summary
from gitmap_core.merge import merge_maps
from gitmap_core.merge import resolve_conflict
from gitmap_core.repository import Repository
from gitmap_core.repository import find_repository

console = Console()


# ---- Helper Functions ---------------------------------------------------------------------------


def get_branch_map_data(repo: Repository, branch: str) -> dict[str, any]:
    """Get map data from a specific branch in a repository.

    Args:
        repo: Repository instance.
        branch: Branch name.

    Returns:
        Map data dictionary.

    Raises:
        click.ClickException: If branch doesn't exist or has no commits.
    """
    if branch not in repo.list_branches():
        msg = f"Branch '{branch}' not found in source repository"
        raise click.ClickException(msg)

    commit_id = repo.get_branch_commit(branch)
    if not commit_id:
        msg = f"Branch '{branch}' has no commits"
        raise click.ClickException(msg)

    commit = repo.get_commit(commit_id)
    if not commit:
        msg = f"Commit '{commit_id}' not found"
        raise click.ClickException(msg)

    return commit.map_data


# ---- Merge From Command -------------------------------------------------------------------------


@click.command()
@click.argument(
    "source_repo",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "source_branch",
    required=True,
)
@click.option(
    "--no-commit",
    is_flag=True,
    help="Perform merge but don't auto-commit.",
)
def merge_from(
    source_repo: Path,
    source_branch: str,
    no_commit: bool,
) -> None:
    """Merge a branch from another repository into the current branch.

    Merges map data from a branch in a different GitMap repository
    into the current branch of the current repository.

    Examples:
        gitmap merge-from /path/to/master-repo 2.1
        gitmap merge-from ../other-repo feature/new-layer --no-commit
    """
    try:
        # Find current repository
        target_repo = find_repository()
        if not target_repo:
            raise click.ClickException("Not a GitMap repository. Run this command from within a GitMap repository.")

        current_branch = target_repo.get_current_branch()
        if not current_branch:
            raise click.ClickException("Cannot merge in detached HEAD state")

        # Load source repository
        source_repo_obj = Repository(source_repo)
        if not source_repo_obj.is_valid():
            msg = f"Source repository is not valid: {source_repo}"
            raise click.ClickException(msg)

        console.print(f"[dim]Source repository: {source_repo}[/dim]")
        console.print(f"[dim]Source branch: {source_branch}[/dim]")
        console.print(f"[dim]Target branch: {current_branch}[/dim]")

        # Get map data from both branches
        console.print(f"\n[dim]Getting map data from source repository...[/dim]")
        theirs_data = get_branch_map_data(source_repo_obj, source_branch)

        console.print(f"[dim]Getting map data from current branch...[/dim]")
        # Get our data (from index or commit)
        our_data = target_repo.get_index()
        our_commit_id = target_repo.get_branch_commit(current_branch)
        if not our_data and our_commit_id:
            our_commit = target_repo.get_commit(our_commit_id)
            if our_commit:
                our_data = our_commit.map_data

        if not our_data:
            msg = f"Current branch '{current_branch}' has no map data"
            raise click.ClickException(msg)

        # Perform merge
        console.print(f"\n[dim]Merging '{source_branch}' from source repo into '{current_branch}'...[/dim]")

        merge_result = merge_maps(
            ours=our_data,
            theirs=theirs_data,
            base=None,  # No common ancestor for cross-repo merges
        )

        # Track initial conflicts for event recording
        initial_conflict_count = len(merge_result.conflicts) if merge_result.has_conflicts else 0

        # Handle conflicts
        if merge_result.has_conflicts:
            # Separate table conflicts from layer conflicts
            merged_tables = merge_result.merged_data.get("tables", [])
            merged_layers = merge_result.merged_data.get("operationalLayers", [])

            table_ids = {table.get("id") for table in merged_tables if table.get("id")}
            layer_ids = {layer.get("id") for layer in merged_layers if layer.get("id")}

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

                from rich.prompt import Prompt
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

                from rich.prompt import Prompt
                for conflict in layer_conflicts:
                    console.print()
                    console.print(f"[bold]Conflict in layer: {conflict.layer_title}[/bold]")
                    console.print(f"  Layer ID: {conflict.layer_id}")

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
        target_repo.update_index(merge_result.merged_data)

        # Display summary
        console.print()
        console.print(format_merge_summary(merge_result))

        # Auto-commit unless --no-commit
        merge_commit_id = None
        if not no_commit:
            commit_msg = f"Merge '{source_branch}' from {source_repo.name} into '{current_branch}'"
            new_commit = target_repo.create_commit(message=commit_msg)
            merge_commit_id = new_commit.id

            console.print()
            console.print(f"[green]Merge commit: {new_commit.id[:8]}[/green]")
        else:
            console.print()
            console.print("[dim]Merge staged. Use 'gitmap commit' to finalize.[/dim]")

        # Record merge event (non-blocking)
        try:
            config = target_repo.get_config()
            actor = config.user_name if config else None
            with target_repo.get_context_store() as store:
                store.record_event(
                    event_type="merge-from",
                    repo=str(target_repo.root),
                    ref=merge_commit_id or current_branch,
                    actor=actor,
                    payload={
                        "source_repo": str(source_repo),
                        "source_branch": source_branch,
                        "target_branch": current_branch,
                        "commit_id": merge_commit_id,
                        "had_conflicts": initial_conflict_count > 0,
                        "conflicts_resolved": initial_conflict_count,
                    },
                )
        except Exception:
            pass  # Don't fail merge if context recording fails

        # Auto-regenerate context graph if enabled
        try:
            config = target_repo.get_config()
            if config.auto_visualize:
                target_repo.regenerate_context_graph()
        except Exception:
            pass  # Don't fail merge if visualization fails

    except Exception as merge_error:
        msg = f"Cross-repo merge failed: {merge_error}"
        raise click.ClickException(msg) from merge_error
