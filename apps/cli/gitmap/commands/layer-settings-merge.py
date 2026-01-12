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
import os
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.maps import get_webmap_json
from gitmap_core.maps import load_map_json
from gitmap_core.models import Remote
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import Repository
from gitmap_core.repository import find_repository
from gitmap_core.repository import init_repository

console = Console()


def _record_lsm_event(
    repo: Repository,
    source: str,
    target: str | None,
    transferred_count: int,
    skipped_count: int,
) -> None:
    """Record a layer settings merge event to the context store."""
    try:
        config = repo.get_config()
        actor = config.user_name if config else None
        current_branch = repo.get_current_branch()
        with repo.get_context_store() as store:
            store.record_event(
                event_type="lsm",
                repo=str(repo.root),
                ref=target or "index",
                actor=actor,
                payload={
                    "source": source,
                    "target": target or "index",
                    "transferred_count": transferred_count,
                    "skipped_count": skipped_count,
                    "branch": current_branch,  # Track which branch the LSM was done on
                },
            )
    except Exception:
        pass  # Don't fail LSM if context recording fails


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

    Searches from current directory and optionally from start_path, checking
    the directory tree (including subdirectories) for .gitmap repos with
    matching item_id in their remote config.

    Args:
        item_id: Portal item ID to search for.
        start_path: Optional additional directory to search from.

    Returns:
        Repository if found, None otherwise.
    """
    def check_repo_at_path(path: Path) -> Repository | None:
        """Check if a path is a repo with matching item_id.
        
        First checks if .gitmap/config.json exists (fast file check),
        then validates and checks the item_id.
        """
        # Quick check: does .gitmap/config.json exist?
        gitmap_config = path / ".gitmap" / "config.json"
        if not gitmap_config.exists():
            return None
        
        # Now create repo object and check item_id
        repo = Repository(path)
        if repo.exists() and repo.is_valid():
            try:
                config = repo.get_config()
                if config.remote and config.remote.item_id == item_id:
                    return repo
            except Exception:
                pass
        return None
    
    # Skip directory search to avoid hangs - the clone logic will check
    # if the expected directory already exists and validate it
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
        portal_url = os.environ.get("PORTAL_URL", "https://www.arcgis.com")
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
                # Use a simple counter instead of glob to avoid hangs
                counter = 1
                while True:
                    clone_dir = base_dir / f"{safe_title}_{source[:8]}_{counter}"
                    if not clone_dir.exists():
                        break
                    counter += 1
                    if counter > 100:  # Safety limit
                        clone_dir = base_dir / f"{safe_title}_{source[:8]}_{counter}"
                        break

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
        portal_url = os.environ.get("PORTAL_URL", "https://www.arcgis.com")
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
@click.option(
    "--local-folder",
    "-lf",
    help="Local folder path containing gitmap repositories to update.",
)
@click.option(
    "--remote-folder",
    "-rf",
    help="Portal folder ID or folder name containing target web maps.",
)
@click.option(
    "--folder-owner",
    help="Portal username that owns the remote folder (defaults to authenticated user).",
)
def layer_settings_merge(
        source: str,
        target: str | None,
        dry_run: bool,
        local_folder: str | None,
        remote_folder: str | None,
        folder_owner: str | None,
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
        if (local_folder or remote_folder) and target:
            raise click.ClickException("Specify either a target map or a folder option (--local-folder/--remote-folder), not both")
        
        if local_folder and remote_folder:
            raise click.ClickException("Specify either --local-folder or --remote-folder, not both")

        # Get current repository (optional for folder operations)
        current_repo = find_repository()
        
        # Only require repository if not using folder options
        if not local_folder and not remote_folder:
            if not current_repo:
                raise click.ClickException("Not a GitMap repository")

        # Resolve source map
        console.print(f"[dim]Resolving source: {source}[/dim]")
        source_map = _resolve_source_map(source, current_repo)

        source_layers = source_map.get("operationalLayers", [])
        source_tables = source_map.get("tables", [])
        if not source_layers and not source_tables:
            console.print("[yellow]Source map has no operational layers or tables[/yellow]")
            return

        if local_folder:
            _transfer_to_local_folder(
                source_map=source_map,
                current_repo=current_repo,  # May be None
                local_folder_path=local_folder,
                dry_run=dry_run,
            )
            return
        
        if remote_folder:
            _transfer_to_remote_folder(
                source_map=source_map,
                current_repo=current_repo,  # May be None
                folder_id=remote_folder,
                folder_owner=folder_owner,
                dry_run=dry_run,
            )
            return

        # Resolve target map
        target_display = target or "index"
        console.print(f"[dim]Resolving target: {target_display}[/dim]")
        target_map = _resolve_target_map(target, current_repo)

        target_layers = target_map.get("operationalLayers", [])
        target_tables = target_map.get("tables", [])

        if not target_layers and not target_tables:
            console.print("[yellow]Target map has no operational layers or tables[/yellow]")
            return

        updated_map, summary = _transfer_settings_between_maps(
            source_map=source_map,
            target_map=target_map,
        )

        _render_summary(summary)

        # Apply changes unless dry-run
        if not dry_run:
            transferred_count = len(summary.get("transferred_layers", [])) + len(summary.get("transferred_tables", []))
            skipped_count = len(summary.get("skipped_layers", [])) + len(summary.get("skipped_tables", []))

            if not target:
                current_repo.update_index(updated_map)
                _record_lsm_event(current_repo, source, target, transferred_count, skipped_count)
                console.print()
                console.print("[green]Settings transferred to index[/green]")
                console.print("[dim]Use 'gitmap commit' to save changes[/dim]")
            else:
                target_path = Path(target)
                if target_path.exists() and target_path.is_file():
                    target_path.write_text(json.dumps(updated_map, indent=2))
                    _record_lsm_event(current_repo, source, target, transferred_count, skipped_count)
                    console.print()
                    console.print(f"[green]Settings saved to {target}[/green]")
                else:
                    current_repo.update_index(updated_map)
                    _record_lsm_event(current_repo, source, target, transferred_count, skipped_count)
                    console.print()
                    console.print("[green]Settings transferred to index[/green]")
        else:
            console.print()
            console.print("[dim]Dry-run mode: No changes applied[/dim]")

    except Exception as merge_error:
        msg = f"Layer settings merge failed: {merge_error}"
        raise click.ClickException(msg) from merge_error


def _transfer_settings_between_maps(
        source_map: dict[str, Any],
        target_map: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Transfer popup and form settings between maps.

    Args:
        source_map: Source map JSON.
        target_map: Target map JSON.

    Returns:
        Tuple of (updated_target_map, summary dictionary).
    """
    source_layers = source_map.get("operationalLayers", [])
    source_tables = source_map.get("tables", [])

    target_layers = json.loads(json.dumps(target_map.get("operationalLayers", [])))
    target_tables = json.loads(json.dumps(target_map.get("tables", [])))

    transferred_layers: list[str] = []
    skipped_layers: list[str] = []

    for source_layer in source_layers:
        layer_name = source_layer.get("title") or source_layer.get("id", "Unknown")
        target_layer = _find_layer_by_name(target_layers, layer_name)

        if not target_layer:
            skipped_layers.append(layer_name)
            continue

        updated_layer = _transfer_layer_settings(source_layer, target_layer)
        for i, layer in enumerate(target_layers):
            if layer.get("title") == layer_name or layer.get("id") == layer_name:
                target_layers[i] = updated_layer
                break

        transferred_layers.append(layer_name)

    transferred_tables: list[str] = []
    skipped_tables: list[str] = []

    for source_table in source_tables:
        table_name = source_table.get("title") or source_table.get("id", "Unknown")
        target_table = _find_layer_by_name(target_tables, table_name)

        if not target_table:
            skipped_tables.append(table_name)
            continue

        updated_table = _transfer_layer_settings(source_table, target_table)
        for i, table in enumerate(target_tables):
            if table.get("title") == table_name or table.get("id") == table_name:
                target_tables[i] = updated_table
                break

        transferred_tables.append(table_name)

    updated_map = target_map.copy()
    updated_map["operationalLayers"] = target_layers
    updated_map["tables"] = target_tables

    summary = {
        "transferred_layers": transferred_layers,
        "skipped_layers": skipped_layers,
        "transferred_tables": transferred_tables,
        "skipped_tables": skipped_tables,
    }

    return updated_map, summary


def _render_summary(
        summary: dict[str, list[str]],
) -> None:
    """Render transfer summary to console."""
    transferred_layers = summary.get("transferred_layers", [])
    skipped_layers = summary.get("skipped_layers", [])
    transferred_tables = summary.get("transferred_tables", [])
    skipped_tables = summary.get("skipped_tables", [])

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


def _get_portal_url(
        current_repo: Repository | None,
) -> str:
    """Get Portal URL from repo config or default."""
    portal_url = os.environ.get("PORTAL_URL", "https://www.arcgis.com")
    if current_repo:
        config = current_repo.get_config()
        if config.remote and config.remote.url:
            portal_url = config.remote.url
    return portal_url


def _get_or_clone_repo_for_item(
        item_id: str,
        item_title: str,
        portal_url: str,
        connection: Any,
        start_path: Path | None = None,
) -> Repository:
    """Get existing repo or clone a new one for the given item ID.
    
    Args:
        item_id: Portal item ID.
        item_title: Item title (used for cloning).
        portal_url: Portal URL.
        connection: Portal connection object.
        start_path: Starting path for repository search.
        
    Returns:
        Repository instance (existing or newly cloned).
    """
    # Check if expected clone directory already exists and has matching item_id
    # This avoids directory searching which can hang
    safe_title = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in item_title
    )
    
    # Determine base directory
    if start_path:
        base_dir = Path(start_path).resolve().parent
    else:
        base_dir = Path.cwd()
    
    # Check common directory name patterns (without searching all directories)
    patterns_to_check = [
        base_dir / safe_title,  # Base name
        base_dir / f"{safe_title}_{item_id[:8]}",  # With item_id suffix
    ]
    
    for clone_dir in patterns_to_check:
        if clone_dir.exists():
            existing_repo = Repository(clone_dir)
            if existing_repo.exists() and existing_repo.is_valid():
                try:
                    config = existing_repo.get_config()
                    if config.remote and config.remote.item_id == item_id:
                        console.print(f"[dim]Found existing repository for item {item_id}[/dim]")
                        return existing_repo
                except Exception:
                    pass
    
    # Clone if not found
    console.print(f"[dim]No repository found for item {item_id}, cloning...[/dim]")
    
    # Use the first pattern that doesn't exist
    clone_dir = patterns_to_check[0]
    if clone_dir.exists():
        # If base exists, use item_id suffix version
        clone_dir = patterns_to_check[1]
        # If that also exists, add counter
        if clone_dir.exists():
            counter = 1
            while True:
                clone_dir = base_dir / f"{safe_title}_{item_id[:8]}_{counter}"
                if not clone_dir.exists():
                    break
                counter += 1
                if counter > 100:  # Safety limit
                    break
    
    # Create directory and initialize repo
    clone_dir.mkdir(parents=True, exist_ok=True)
    new_repo = init_repository(
        path=clone_dir,
        project_name=item_title,
        user_name=connection.username or "",
        user_email="",
    )
    
    # Configure remote
    config = new_repo.get_config()
    config.remote = Remote(
        name="origin",
        url=portal_url,
        item_id=item_id,
    )
    new_repo.update_config(config)
    
    # Fetch map data and create initial commit
    item, map_data = get_webmap_by_id(connection.gis, item_id)
    new_repo.update_index(map_data)
    new_repo.create_commit(
        message=f"Clone from Portal: {item_title}",
        author=connection.username or "GitMap",
    )
    
    console.print(f"[green]Cloned '{item_title}' into {clone_dir}[/green]")
    return new_repo


def _resolve_folder_id(
        folder_identifier: str,
        connection: Any,
        folder_owner: str | None,
) -> str:
    """Resolve folder identifier (ID or name) to folder ID.
    
    Args:
        folder_identifier: Folder ID or folder name.
        connection: Portal connection object.
        folder_owner: Portal username that owns the folder.
        
    Returns:
        Folder ID.
        
    Raises:
        click.ClickException: If folder not found.
    """
    user = connection.gis.users.get(folder_owner) if folder_owner else connection.gis.users.me
    if not user:
        msg = "Unable to resolve Portal user for folder access"
        raise click.ClickException(msg)
    
    # Check if it's already a folder ID (typically long alphanumeric string)
    # Folder IDs are usually longer than 8 characters and don't contain spaces
    if len(folder_identifier) > 8 and " " not in folder_identifier:
        # Try using it as a folder ID first
        try:
            items = user.items(folder=folder_identifier)
            # If this works, it's a valid folder ID
            return folder_identifier
        except Exception:
            # Not a valid folder ID, try as name
            pass
    
    # Try to find folder by name
    try:
        folders = user.folders
        for folder in folders:
            folder_title = getattr(folder, "title", None)
            if folder_title == folder_identifier:
                folder_id = getattr(folder, "id", None)
                if folder_id:
                    return folder_id
    except Exception:
        pass
    
    # Try searching through user's items to find the folder
    try:
        user_items = user.items()
        seen_folders = set()
        for item in user_items:
            item_folder = getattr(item, "ownerFolder", None)
            if item_folder and item_folder not in seen_folders:
                seen_folders.add(item_folder)
                try:
                    folder_obj = connection.gis.content.get_folder(item_folder, user.username)
                    if folder_obj:
                        folder_title = getattr(folder_obj, "title", None)
                        if folder_title == folder_identifier:
                            folder_id = getattr(folder_obj, "id", None)
                            if folder_id:
                                return folder_id
                except Exception:
                    continue
    except Exception:
        pass
    
    msg = f"Folder '{folder_identifier}' not found (tried as both ID and name)"
    raise click.ClickException(msg)


def _transfer_to_local_folder(
        source_map: dict[str, Any],
        current_repo: Repository | None,
        local_folder_path: str,
        dry_run: bool,
) -> None:
    """Transfer settings from a source map to all gitmap repositories in a local folder.
    
    For each gitmap repository found in the local folder, creates an 'lsm' branch
    with the changes, then prompts to merge and push.
    
    Args:
        source_map: Source map JSON data.
        current_repo: Current repository context.
        local_folder_path: Path to local folder containing gitmap repositories.
        dry_run: If True, preview changes without applying.
    """
    folder_path = Path(local_folder_path).resolve()
    
    if not folder_path.exists():
        msg = f"Local folder '{local_folder_path}' does not exist"
        raise click.ClickException(msg)
    
    if not folder_path.is_dir():
        msg = f"'{local_folder_path}' is not a directory"
        raise click.ClickException(msg)
    
    # Find all gitmap repositories in the folder
    repos: list[Repository] = []
    
    # Check if the folder itself is a gitmap repo
    repo = Repository(folder_path)
    if repo.exists() and repo.is_valid():
        repos.append(repo)
    
    # Search subdirectories for gitmap repos
    for item in folder_path.iterdir():
        if item.is_dir():
            sub_repo = Repository(item)
            if sub_repo.exists() and sub_repo.is_valid():
                repos.append(sub_repo)
    
    if not repos:
        console.print(f"[yellow]No gitmap repositories found in '{local_folder_path}'[/yellow]")
        return
    
    console.print(
        f"[dim]Processing {len(repos)} gitmap repositories in '{local_folder_path}'[/dim]",
    )
    console.print()
    
    # Track repos that were successfully updated
    updated_repos: list[tuple[Repository, str]] = []  # (repo, repo_name)
    
    for repo in repos:
        repo_name = repo.root.name
        console.print(f"[bold]{repo_name}[/bold]")
        
        try:
            # Get current map state from repo
            current_branch = repo.get_current_branch()
            if current_branch:
                commit_id = repo.get_branch_commit(current_branch)
                if commit_id:
                    commit = repo.get_commit(commit_id)
                    if commit:
                        target_map = commit.map_data
                    else:
                        # Fall back to index
                        target_map = repo.get_index()
                        if not target_map:
                            console.print("[yellow]  Repository has no map data[/yellow]")
                            console.print()
                            continue
                else:
                    target_map = repo.get_index()
                    if not target_map:
                        console.print("[yellow]  Repository has no map data[/yellow]")
                        console.print()
                        continue
            else:
                target_map = repo.get_index()
                if not target_map:
                    console.print("[yellow]  Repository has no map data[/yellow]")
                    console.print()
                    continue
            
            target_layers = target_map.get("operationalLayers", [])
            target_tables = target_map.get("tables", [])
            
            if not target_layers and not target_tables:
                console.print("[yellow]  Repository map has no operational layers or tables[/yellow]")
                console.print()
                continue
            
            # Apply settings transfer
            updated_map, summary = _transfer_settings_between_maps(
                source_map=source_map,
                target_map=target_map,
            )
            
            # Show summary (compact version)
            transferred_count = len(summary.get("transferred_layers", [])) + len(summary.get("transferred_tables", []))
            skipped_count = len(summary.get("skipped_layers", [])) + len(summary.get("skipped_tables", []))
            console.print(f"  [dim]Transferred: {transferred_count}, Skipped: {skipped_count}[/dim]")
            
            if dry_run:
                console.print("[dim]  Dry-run mode: No changes applied[/dim]")
                console.print()
                continue
            
            # Ensure main branch exists
            branches = repo.list_branches()
            if "main" not in branches:
                # Create main branch from current HEAD or initial commit
                head_commit = repo.get_head_commit()
                if head_commit:
                    repo.create_branch("main", head_commit)
                else:
                    # No commits yet, commit current state to main
                    repo.update_index(target_map)
                    repo.create_commit(
                        message=f"Initial commit: {repo_name}",
                        author="GitMap",
                    )
                    repo.create_branch("main")
            
            # Checkout main (ensure we're on main branch)
            current_branch = repo.get_current_branch()
            if current_branch != "main":
                repo.checkout_branch("main")
            
            # Get the latest main commit ID
            main_commit_id = repo.get_branch_commit("main")
            if not main_commit_id:
                # Should not happen, but handle gracefully
                main_commit_id = repo.get_head_commit()
                if main_commit_id:
                    repo.update_branch("main", main_commit_id)
            
            # Create or checkout lsm branch from latest main
            lsm_branch = "lsm"
            branches = repo.list_branches()  # Refresh branch list
            if lsm_branch in branches:
                repo.checkout_branch(lsm_branch)
                # Reset to main to ensure clean state
                if main_commit_id:
                    repo.update_branch(lsm_branch, main_commit_id)
                    main_commit = repo.get_commit(main_commit_id)
                    if main_commit:
                        repo.update_index(main_commit.map_data)
            else:
                if main_commit_id:
                    repo.create_branch(lsm_branch, main_commit_id)
                    repo.checkout_branch(lsm_branch)
                else:
                    # Fallback: create branch from current HEAD
                    repo.create_branch(lsm_branch)
                    repo.checkout_branch(lsm_branch)
            
            # Apply changes to index
            repo.update_index(updated_map)
            
            # Commit changes
            commit = repo.create_commit(
                message=f"Layer settings merge: {repo_name}",
                author="GitMap",
            )
            
            console.print(f"  [green]Created commit {commit.id[:8]} in branch 'lsm'[/green]")
            updated_repos.append((repo, repo_name))
            
        except Exception as process_error:
            console.print(f"  [red]Failed to process '{repo_name}': {process_error}[/red]")
        
        console.print()
    
    # Prompt to merge and push
    if not dry_run and updated_repos:
        console.print()
        console.print(f"[bold]Successfully updated {len(updated_repos)} repositories[/bold]")
        console.print()
        
        if Prompt.ask(
            "Merge all 'lsm' branches to 'main'?",
            choices=["yes", "no"],
            default="yes",
        ) == "yes":
            console.print()
            for repo, repo_name in updated_repos:
                try:
                    console.print(f"[dim]Merging 'lsm' to 'main' in {repo_name}...[/dim]")
                    
                    # Checkout main
                    repo.checkout_branch("main")
                    
                    # Merge lsm into main
                    lsm_commit_id = repo.get_branch_commit("lsm")
                    if not lsm_commit_id:
                        console.print(f"  [yellow]  No commits in 'lsm' branch, skipping[/yellow]")
                        continue
                    
                    lsm_commit = repo.get_commit(lsm_commit_id)
                    if not lsm_commit:
                        console.print(f"  [yellow]  Commit not found, skipping[/yellow]")
                        continue
                    
                    # Apply lsm changes to main (use lsm's data directly)
                    repo.update_index(lsm_commit.map_data)
                    merge_commit = repo.create_commit(
                        message=f"Merge 'lsm' into 'main': {repo_name}",
                        author="GitMap",
                    )
                    console.print(f"  [green]  Merged (commit {merge_commit.id[:8]})[/green]")
                    
                except Exception as merge_error:
                    console.print(f"  [red]  Failed to merge: {merge_error}[/red]")
            
            console.print()
            # For local folders, we might not have Portal connection, so check if repos have remotes
            repos_with_remotes = [
                (repo, repo_name) for repo, repo_name in updated_repos
                if repo.get_config().remote and repo.get_config().remote.item_id
            ]
            
            if repos_with_remotes and Prompt.ask(
                "Push all changes to Portal?",
                choices=["yes", "no"],
                default="yes",
            ) == "yes":
                console.print()
                # Get portal URL from first repo with remote, or use default
                portal_url = os.environ.get("PORTAL_URL", "https://www.arcgis.com")
                for repo, _ in repos_with_remotes:
                    config = repo.get_config()
                    if config.remote and config.remote.url:
                        portal_url = config.remote.url
                        break
                connection = get_connection(url=portal_url)
                
                for repo, repo_name in repos_with_remotes:
                    try:
                        console.print(f"[dim]Pushing 'main' for {repo_name}...[/dim]")
                        remote_ops = RemoteOperations(repo, connection)
                        item, _ = remote_ops.push("main")
                        console.print(f"  [green]  Pushed (Item ID: {item.id})[/green]")
                    except Exception as push_error:
                        console.print(f"  [red]  Failed to push: {push_error}[/red]")


def _transfer_to_remote_folder(
        source_map: dict[str, Any],
        current_repo: Repository | None,
        folder_id: str,
        folder_owner: str | None,
        dry_run: bool,
) -> None:
    """Transfer settings from a source map to all web maps in a Portal folder.
    
    For each target map, finds or clones the local gitmap repository, creates
    an 'lsm' branch with the changes, then prompts to merge and push.
    
    Args:
        source_map: Source map JSON data.
        current_repo: Current repository context.
        folder_id: Folder ID or folder name.
        folder_owner: Portal username that owns the folder.
        dry_run: If True, preview changes without applying.
    """
    portal_url = _get_portal_url(current_repo)
    connection = get_connection(url=portal_url)

    # Resolve folder identifier (ID or name) to folder ID
    resolved_folder_id = _resolve_folder_id(folder_id, connection, folder_owner)

    user = connection.gis.users.get(folder_owner) if folder_owner else connection.gis.users.me
    if not user:
        msg = "Unable to resolve Portal user for folder access"
        raise click.ClickException(msg)

    try:
        console.print(f"[dim]Fetching items from folder '{folder_id}'...[/dim]")
        items = user.items(folder=resolved_folder_id)
        console.print(f"[dim]Found {len(items)} items[/dim]")
    except Exception as folder_error:
        msg = f"Failed to fetch items from folder {folder_id}: {folder_error}"
        raise click.ClickException(msg) from folder_error

    webmaps = [item for item in items if getattr(item, "type", "") == "Web Map"]
    console.print(f"[dim]Found {len(webmaps)} web maps[/dim]")

    if not webmaps:
        console.print(f"[yellow]No web maps found in folder '{folder_id}'[/yellow]")
        return

    console.print(
        f"[dim]Processing {len(webmaps)} web maps in folder '{folder_id}'[/dim]",
    )
    console.print()

    # Track repos that were successfully updated
    updated_repos: list[tuple[Repository, str, str]] = []  # (repo, item_title, item_id)

    for item in webmaps:
        console.print(f"[bold]{item.title}[/bold] ({item.id})")
        
        try:
            # Get or clone repository for this item
            console.print(f"  [dim]Getting/cloning repository...[/dim]")
            start_path = current_repo.root if current_repo else None
            repo = _get_or_clone_repo_for_item(
                item_id=item.id,
                item_title=item.title,
                portal_url=portal_url,
                connection=connection,
                start_path=start_path,
            )
            
            # Get current map state from Portal
            console.print(f"  [dim]Fetching map from Portal...[/dim]")
            target_map = get_webmap_json(item)
            
            target_layers = target_map.get("operationalLayers", [])
            target_tables = target_map.get("tables", [])
            
            if not target_layers and not target_tables:
                console.print("[yellow]  Target map has no operational layers or tables[/yellow]")
                console.print()
                continue
            
            # Apply settings transfer
            updated_map, summary = _transfer_settings_between_maps(
                source_map=source_map,
                target_map=target_map,
            )
            
            # Show summary (compact version)
            transferred_count = len(summary.get("transferred_layers", [])) + len(summary.get("transferred_tables", []))
            skipped_count = len(summary.get("skipped_layers", [])) + len(summary.get("skipped_tables", []))
            console.print(f"  [dim]Transferred: {transferred_count}, Skipped: {skipped_count}[/dim]")
            
            if dry_run:
                console.print("[dim]  Dry-run mode: No changes applied[/dim]")
                console.print()
                continue
            
            # Ensure main branch exists
            branches = repo.list_branches()
            if "main" not in branches:
                # Create main branch from current HEAD or initial commit
                head_commit = repo.get_head_commit()
                if head_commit:
                    repo.create_branch("main", head_commit)
                else:
                    # No commits yet, commit current Portal state to main
                    repo.update_index(target_map)
                    repo.create_commit(
                        message=f"Initial commit from Portal: {item.title}",
                        author=connection.username or "GitMap",
                    )
                    repo.create_branch("main")
            
            # Checkout main (ensure we're on main branch)
            current_branch = repo.get_current_branch()
            if current_branch != "main":
                repo.checkout_branch("main")
            
            # Pull latest from Portal to ensure main is up to date
            try:
                remote_ops = RemoteOperations(repo, connection)
                portal_map_data = remote_ops.pull("main")
                # If index changed, commit to main
                if repo.has_uncommitted_changes():
                    repo.create_commit(
                        message=f"Update from Portal: {item.title}",
                        author=connection.username or "GitMap",
                    )
            except Exception as pull_error:
                # If pull fails (e.g., no remote item for branch), use current Portal state
                console.print(f"  [dim]Using current Portal state[/dim]")
                repo.update_index(target_map)
                if repo.has_uncommitted_changes():
                    repo.create_commit(
                        message=f"Update from Portal: {item.title}",
                        author=connection.username or "GitMap",
                    )
            
            # Get the latest main commit ID (after potential updates)
            main_commit_id = repo.get_branch_commit("main")
            if not main_commit_id:
                # Should not happen, but handle gracefully
                main_commit_id = repo.get_head_commit()
                if main_commit_id:
                    repo.update_branch("main", main_commit_id)
            
            # Create or checkout lsm branch from latest main
            lsm_branch = "lsm"
            branches = repo.list_branches()  # Refresh branch list
            if lsm_branch in branches:
                repo.checkout_branch(lsm_branch)
                # Reset to main to ensure clean state
                if main_commit_id:
                    repo.update_branch(lsm_branch, main_commit_id)
                    main_commit = repo.get_commit(main_commit_id)
                    if main_commit:
                        repo.update_index(main_commit.map_data)
            else:
                if main_commit_id:
                    repo.create_branch(lsm_branch, main_commit_id)
                    repo.checkout_branch(lsm_branch)
                else:
                    # Fallback: create branch from current HEAD
                    repo.create_branch(lsm_branch)
                    repo.checkout_branch(lsm_branch)
            
            # Apply changes to index
            repo.update_index(updated_map)
            
            # Commit changes
            commit = repo.create_commit(
                message=f"Layer settings merge: {item.title}",
                author=connection.username or "GitMap",
            )
            
            console.print(f"  [green]Created commit {commit.id[:8]} in branch 'lsm'[/green]")
            updated_repos.append((repo, item.title, item.id))
            
        except Exception as process_error:
            console.print(f"  [red]Failed to process '{item.title}': {process_error}[/red]")
        
        console.print()
    
    # Prompt to merge and push
    if not dry_run and updated_repos:
        console.print()
        console.print(f"[bold]Successfully updated {len(updated_repos)} repositories[/bold]")
        console.print()
        
        if Prompt.ask(
            "Merge all 'lsm' branches to 'main'?",
            choices=["yes", "no"],
            default="yes",
        ) == "yes":
            console.print()
            for repo, item_title, item_id in updated_repos:
                try:
                    console.print(f"[dim]Merging 'lsm' to 'main' in {item_title}...[/dim]")
                    
                    # Checkout main
                    repo.checkout_branch("main")
                    
                    # Merge lsm into main
                    # Get the lsm commit
                    lsm_commit_id = repo.get_branch_commit("lsm")
                    if not lsm_commit_id:
                        console.print(f"  [yellow]  No commits in 'lsm' branch, skipping[/yellow]")
                        continue
                    
                    lsm_commit = repo.get_commit(lsm_commit_id)
                    if not lsm_commit:
                        console.print(f"  [yellow]  Commit not found, skipping[/yellow]")
                        continue
                    
                    # Get main data
                    main_commit_id = repo.get_branch_commit("main")
                    main_data = repo.get_index()
                    if not main_data and main_commit_id:
                        main_commit = repo.get_commit(main_commit_id)
                        if main_commit:
                            main_data = main_commit.map_data
                    
                    if not main_data:
                        console.print(f"  [yellow]  No data in main branch, skipping[/yellow]")
                        continue
                    
                    # Apply lsm changes to main (use lsm's data directly)
                    repo.update_index(lsm_commit.map_data)
                    merge_commit = repo.create_commit(
                        message=f"Merge 'lsm' into 'main': {item_title}",
                        author=connection.username or "GitMap",
                    )
                    console.print(f"  [green]  Merged (commit {merge_commit.id[:8]})[/green]")
                    
                except Exception as merge_error:
                    console.print(f"  [red]  Failed to merge: {merge_error}[/red]")
            
            console.print()
            if Prompt.ask(
                "Push all changes to Portal?",
                choices=["yes", "no"],
                default="yes",
            ) == "yes":
                console.print()
                for repo, item_title, item_id in updated_repos:
                    try:
                        console.print(f"[dim]Pushing 'main' for {item_title}...[/dim]")
                        remote_ops = RemoteOperations(repo, connection)
                        item, _ = remote_ops.push("main")
                        console.print(f"  [green]  Pushed (Item ID: {item.id})[/green]")
                    except Exception as push_error:
                        console.print(f"  [red]  Failed to push: {push_error}[/red]")

