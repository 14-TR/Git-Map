"""GitMap lsm command.

Transfers popup settings (popupInfo) and form settings (formInfo) from
layers and tables in a source map to matching layers and tables in a target map.

Execution Context:
    CLI command - invoked via `gitmap lsm <source> <target>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository, maps, and connection management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.maps import load_map_json
from gitmap_core.models import Remote
from gitmap_core.repository import Repository
from gitmap_core.repository import find_repository
from gitmap_core.repository import init_repository

console = Console()


# ---- Helper Functions -----------------------------------------------------------------------------------------


def _is_item_id(
        identifier: str,
) -> bool:
    """Check if identifier looks like a Portal item ID.

    Args:
        identifier: String to check.

    Returns:
        True if identifier appears to be an item ID.
    """
    # Item IDs are typically alphanumeric strings, often with hyphens
    # They're usually longer than branch names and don't contain slashes
    return (
        len(identifier) > 8
        and "/" not in identifier
        and identifier.replace("-", "").replace("_", "").isalnum()
    )


def _find_repo_by_item_id(
        item_id: str,
        start_path: Path | None = None,
) -> Repository | None:
    """Find GitMap repository by matching item ID in config.

    Walks up from start_path and checks sibling directories for
    .gitmap repos with matching item_id in their remote config.

    Args:
        item_id: Portal item ID to search for.
        start_path: Directory to start searching from.

    Returns:
        Repository if found, None otherwise.
    """
    start = Path(start_path or Path.cwd()).resolve()

    # Check current directory and parent directories
    current = start
    while current != current.parent:
        # Check current directory
        repo = Repository(current)
        if repo.exists() and repo.is_valid():
            try:
                config = repo.get_config()
                if config.remote and config.remote.item_id == item_id:
                    return repo
            except Exception:
                pass

        # Check sibling directories
        if current.parent.exists():
            for sibling in current.parent.iterdir():
                if sibling.is_dir() and sibling != current:
                    repo = Repository(sibling)
                    if repo.exists() and repo.is_valid():
                        try:
                            config = repo.get_config()
                            if config.remote and config.remote.item_id == item_id:
                                return repo
                        except Exception:
                            pass

        current = current.parent

    return None


def _resolve_source_map(
        source: str,
        current_repo: Repository | None,
) -> dict[str, Any]:
    """Resolve source identifier to map JSON data.

    Handles item IDs, branch names, commit IDs, and file paths.
    If source is an item ID and no repo exists, clones it.

    Args:
        source: Source identifier (item ID, branch, commit, or file path).
        current_repo: Current repository context (for Portal connection).

    Returns:
        Map JSON dictionary.

    Raises:
        click.ClickException: If source cannot be resolved.
    """
    # Check if it's a file or directory path
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_file():
            try:
                return load_map_json(source_path)
            except Exception as load_error:
                msg = f"Failed to load source file '{source}': {load_error}"
                raise click.ClickException(msg) from load_error
        elif source_path.is_dir():
            # Check if it's a directory containing a .gitmap repo
            repo = Repository(source_path)
            if repo.exists() and repo.is_valid():
                # Get map data from current branch or index
                current_branch = repo.get_current_branch()
                if current_branch:
                    commit_id = repo.get_branch_commit(current_branch)
                    if commit_id:
                        commit = repo.get_commit(commit_id)
                        if commit:
                            return commit.map_data
                # Fall back to index
                index_data = repo.get_index()
                if index_data:
                    return index_data
                msg = f"Repository at '{source}' has no map data"
                raise click.ClickException(msg)

    # Check if it's an item ID
    if _is_item_id(source):
        # Try to find existing repo
        repo = _find_repo_by_item_id(source)
        if repo:
            # Prompt for branch selection
            branches = repo.list_branches()
            if not branches:
                msg = f"Repository found for item {source} but has no branches"
                raise click.ClickException(msg)

            if len(branches) == 1:
                selected_branch = branches[0]
                console.print(f"[dim]Using branch '{selected_branch}' from existing repository[/dim]")
            else:
                console.print(f"[bold]Found repository for item {source}[/bold]")
                console.print(f"Available branches: {', '.join(branches)}")
                selected_branch = Prompt.ask(
                    "Select branch",
                    choices=branches,
                    default=branches[0],
                )

            # Get map data from selected branch
            commit_id = repo.get_branch_commit(selected_branch)
            if not commit_id:
                msg = f"Branch '{selected_branch}' has no commits"
                raise click.ClickException(msg)

            commit = repo.get_commit(commit_id)
            if not commit:
                msg = f"Commit '{commit_id}' not found"
                raise click.ClickException(msg)

            return commit.map_data

        # No repo found - need to clone
        console.print(f"[dim]No repository found for item {source}[/dim]")
        console.print("[dim]Cloning map from Portal...[/dim]")

        # Get Portal connection from current repo or use defaults
        portal_url = "https://www.arcgis.com"
        if current_repo:
            config = current_repo.get_config()
            if config.remote:
                portal_url = config.remote.url

        connection = get_connection(url=portal_url)
        item, map_data = get_webmap_by_id(connection.gis, source)

        # Create a temporary directory for the clone
        # Use sanitized map title with item ID to ensure uniqueness
        safe_title = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in item.title
        )
        # Create in a temp location relative to current repo or current directory
        if current_repo:
            base_dir = current_repo.root.parent
        else:
            base_dir = Path.cwd()

        clone_dir = base_dir / f"{safe_title}_{source[:8]}"

        # Check if directory already exists
        if clone_dir.exists():
            # If it exists, try to use it as a repo
            existing_repo = Repository(clone_dir)
            if existing_repo.exists() and existing_repo.is_valid():
                console.print(f"[dim]Using existing repository at {clone_dir}[/dim]")
                branches = existing_repo.list_branches()
                if branches:
                    if len(branches) == 1:
                        selected_branch = branches[0]
                    else:
                        console.print(f"Available branches: {', '.join(branches)}")
                        selected_branch = Prompt.ask(
                            "Select branch",
                            choices=branches,
                            default=branches[0],
                        )
                    commit_id = existing_repo.get_branch_commit(selected_branch)
                    if commit_id:
                        commit = existing_repo.get_commit(commit_id)
                        if commit:
                            return commit.map_data
                # Repo exists but has no branches, use the map data we fetched
                return map_data
            else:
                # Directory exists but isn't a valid repo, create new one with suffix
                existing_dirs = list(base_dir.glob(f"{safe_title}_{source[:8]}*"))
                clone_dir = base_dir / f"{safe_title}_{source[:8]}_{len(existing_dirs)}"

        # Create directory and initialize repo
        clone_dir.mkdir(parents=True, exist_ok=True)
        new_repo = init_repository(
            path=clone_dir,
            project_name=item.title,
            user_name=connection.username or "",
            user_email="",
        )

        # Configure remote
        config = new_repo.get_config()
        config.remote = Remote(
            name="origin",
            url=portal_url,
            item_id=source,
        )
        new_repo.update_config(config)

        # Stage and commit the map
        new_repo.update_index(map_data)
        new_repo.create_commit(
            message=f"Clone from Portal: {item.title}",
            author=connection.username or "GitMap",
        )

        console.print(f"[green]Cloned '{item.title}' into {clone_dir}[/green]")
        console.print(f"[dim]Repository created for item {source}[/dim]")

        # Return the map data from the newly created commit
        commit = new_repo.get_commit(new_repo.get_head_commit())
        if commit:
            return commit.map_data
        return map_data

    # Assume it's a branch name or commit ID in current repo
    if not current_repo:
        msg = f"Cannot resolve '{source}' - not in a GitMap repository"
        raise click.ClickException(msg)

    # Try as branch name
    branches = current_repo.list_branches()
    if source in branches:
        commit_id = current_repo.get_branch_commit(source)
        if commit_id:
            commit = current_repo.get_commit(commit_id)
            if commit:
                return commit.map_data

    # Try as commit ID
    commit = current_repo.get_commit(source)
    if commit:
        return commit.map_data

    msg = f"Source '{source}' not found (not a branch, commit, file, or item ID)"
    raise click.ClickException(msg)


def _resolve_target_map(
        target: str | None,
        current_repo: Repository,
) -> dict[str, Any]:
    """Resolve target identifier to map JSON data.

    Args:
        target: Target identifier (item ID, branch, commit, or None for index).
        current_repo: Current repository.

    Returns:
        Map JSON dictionary.

    Raises:
        click.ClickException: If target cannot be resolved.
    """
    # Default to current index
    if not target:
        index_data = current_repo.get_index()
        if not index_data:
            msg = "No map data in index. Use 'gitmap pull' or specify a target."
            raise click.ClickException(msg)
        return index_data

    # Check if it's a file path
    target_path = Path(target)
    if target_path.exists() and target_path.is_file():
        try:
            return load_map_json(target_path)
        except Exception as load_error:
            msg = f"Failed to load target file '{target}': {load_error}"
            raise click.ClickException(msg) from load_error

    # Check if it's an item ID
    if _is_item_id(target):
        # For target, we'll fetch from Portal directly
        portal_url = "https://www.arcgis.com"
        config = current_repo.get_config()
        if config.remote:
            portal_url = config.remote.url

        connection = get_connection(url=portal_url)
        item, map_data = get_webmap_by_id(connection.gis, target)
        console.print(f"[dim]Fetched target map '{item.title}' from Portal[/dim]")
        return map_data

    # Try as branch name
    branches = current_repo.list_branches()
    if target in branches:
        commit_id = current_repo.get_branch_commit(target)
        if commit_id:
            commit = current_repo.get_commit(commit_id)
            if commit:
                return commit.map_data

    # Try as commit ID
    commit = current_repo.get_commit(target)
    if commit:
        return commit.map_data

    msg = f"Target '{target}' not found (not a branch, commit, file, or item ID)"
    raise click.ClickException(msg)


def _find_layer_by_name(
        layers: list[dict[str, Any]],
        layer_name: str,
) -> dict[str, Any] | None:
    """Find layer in list by exact name match.

    Args:
        layers: List of layer dictionaries.
        layer_name: Layer name to find.

    Returns:
        Layer dictionary if found, None otherwise.
    """
    for layer in layers:
        if layer.get("title") == layer_name or layer.get("id") == layer_name:
            return layer
    return None


def _transfer_layer_settings(
        source_layer: dict[str, Any],
        target_layer: dict[str, Any],
) -> dict[str, Any]:
    """Transfer popup and form settings from source to target layer.

    Also handles nested layers within group layers recursively.

    Args:
        source_layer: Source layer dictionary.
        target_layer: Target layer dictionary.

    Returns:
        Updated target layer dictionary.
    """
    updated_layer = target_layer.copy()

    # Transfer popupInfo if present in source (add it even if target doesn't have it)
    if "popupInfo" in source_layer:
        updated_layer["popupInfo"] = json.loads(
            json.dumps(source_layer["popupInfo"]),
        )  # Deep copy

    # Transfer formInfo if present in source (add it even if target doesn't have it)
    if "formInfo" in source_layer:
        updated_layer["formInfo"] = json.loads(
            json.dumps(source_layer["formInfo"]),
        )  # Deep copy

    # Handle nested layers (for GroupLayers)
    if "layers" in source_layer and "layers" in target_layer:
        source_nested = source_layer["layers"]
        target_nested = target_layer["layers"]
        updated_nested = []

        for target_nest_layer in target_nested:
            target_nest_name = target_nest_layer.get("title") or target_nest_layer.get("id", "Unknown")
            source_nest_layer = _find_layer_by_name(source_nested, target_nest_name)

            if source_nest_layer:
                # Recursively transfer settings (handles nested layers within nested layers)
                updated_nest_layer = _transfer_layer_settings(source_nest_layer, target_nest_layer)
                updated_nested.append(updated_nest_layer)
            else:
                updated_nested.append(target_nest_layer)

        updated_layer["layers"] = updated_nested

    return updated_layer


# ---- Layer Settings Merge Command -----------------------------------------------------------------------------


@click.command(name="lsm")
@click.argument(
    "source",
    required=True,
)
@click.argument(
    "target",
    required=False,
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying them.",
)
def layer_settings_merge(
        source: str,
        target: str | None,
        dry_run: bool,
) -> None:
    """Transfer popup and form settings between maps.

    Transfers popupInfo and formInfo from layers and tables in the source
    map to matching layers and tables (by name) in the target map. Works
    with item IDs, branches, commits, or file paths.

    If source is an item ID and a repository exists for it, prompts to
    select a branch. If no repository exists, clones the map from Portal.

    Examples:
        gitmap lsm main feature/new-layer
        gitmap lsm abc123def456
        gitmap lsm source.json target.json --dry-run
    """
    try:
        # Get current repository
        current_repo = find_repository()
        if not current_repo:
            raise click.ClickException("Not a GitMap repository")

        # Resolve source map
        console.print(f"[dim]Resolving source: {source}[/dim]")
        source_map = _resolve_source_map(source, current_repo)

        # Resolve target map
        target_display = target or "index"
        console.print(f"[dim]Resolving target: {target_display}[/dim]")
        target_map = _resolve_target_map(target, current_repo)

        # Extract layers and tables
        source_layers = source_map.get("operationalLayers", [])
        target_layers = target_map.get("operationalLayers", [])
        source_tables = source_map.get("tables", [])
        target_tables = target_map.get("tables", [])

        if not source_layers and not source_tables:
            console.print("[yellow]Source map has no operational layers or tables[/yellow]")
            return

        if not target_layers and not target_tables:
            console.print("[yellow]Target map has no operational layers or tables[/yellow]")
            return

        # Transfer settings for matching layers
        transferred_layers = []
        skipped_layers = []

        for source_layer in source_layers:
            layer_name = source_layer.get("title") or source_layer.get("id", "Unknown")
            target_layer = _find_layer_by_name(target_layers, layer_name)

            if not target_layer:
                skipped_layers.append(layer_name)
                continue

            # Transfer settings
            updated_layer = _transfer_layer_settings(source_layer, target_layer)
            # Update in target_layers list
            for i, layer in enumerate(target_layers):
                if layer.get("title") == layer_name or layer.get("id") == layer_name:
                    target_layers[i] = updated_layer
                    break

            transferred_layers.append(layer_name)

        # Transfer settings for matching tables
        transferred_tables = []
        skipped_tables = []

        for source_table in source_tables:
            table_name = source_table.get("title") or source_table.get("id", "Unknown")
            target_table = _find_layer_by_name(target_tables, table_name)

            if not target_table:
                skipped_tables.append(table_name)
                continue

            # Transfer settings
            updated_table = _transfer_layer_settings(source_table, target_table)
            # Update in target_tables list
            for i, table in enumerate(target_tables):
                if table.get("title") == table_name or table.get("id") == table_name:
                    target_tables[i] = updated_table
                    break

            transferred_tables.append(table_name)

        # Display results
        total_transferred = len(transferred_layers) + len(transferred_tables)
        total_skipped = len(skipped_layers) + len(skipped_tables)

        console.print()
        console.print(Panel(
            f"[bold]Settings Transfer Summary[/bold]\n\n"
            f"Layers - Transferred: {len(transferred_layers)}, Skipped: {len(skipped_layers)}\n"
            f"Tables - Transferred: {len(transferred_tables)}, Skipped: {len(skipped_tables)}\n\n"
            f"Total - Transferred: {total_transferred}, Skipped: {total_skipped}",
            title="Results",
            border_style="blue",
        ))

        if transferred_layers:
            console.print()
            console.print("[bold green]Transferred layer settings for:[/bold green]")
            for layer_name in transferred_layers:
                console.print(f"  • {layer_name}")

        if transferred_tables:
            console.print()
            console.print("[bold green]Transferred table settings for:[/bold green]")
            for table_name in transferred_tables:
                console.print(f"  • {table_name}")

        if skipped_layers:
            console.print()
            console.print("[yellow]Skipped layers (not found in target):[/yellow]")
            for layer_name in skipped_layers:
                console.print(f"  • {layer_name}")

        if skipped_tables:
            console.print()
            console.print("[yellow]Skipped tables (not found in target):[/yellow]")
            for table_name in skipped_tables:
                console.print(f"  • {table_name}")

        # Apply changes unless dry-run
        if not dry_run:
            # Update target map - create a new dict to avoid reference issues
            updated_map = target_map.copy()
            # Ensure we're assigning the modified lists (which are new references)
            updated_map["operationalLayers"] = list(target_layers)  # Create new list
            updated_map["tables"] = list(target_tables)  # Create new list

            # If target was None, update index; otherwise, save to file
            if not target:
                current_repo.update_index(updated_map)
                console.print()
                console.print("[green]Settings transferred to index[/green]")
                console.print("[dim]Use 'gitmap commit' to save changes[/dim]")
            else:
                # If target was a file path, save it
                target_path = Path(target)
                if target_path.exists() and target_path.is_file():
                    target_path.write_text(json.dumps(updated_map, indent=2))
                    console.print()
                    console.print(f"[green]Settings saved to {target}[/green]")
                else:
                    # Otherwise update index
                    current_repo.update_index(updated_map)
                    console.print()
                    console.print("[green]Settings transferred to index[/green]")
        else:
            console.print()
            console.print("[dim]Dry-run mode: No changes applied[/dim]")

    except Exception as merge_error:
        msg = f"Layer settings merge failed: {merge_error}"
        raise click.ClickException(msg) from merge_error

