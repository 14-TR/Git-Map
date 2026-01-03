"""Layer settings management tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository, maps, and connection management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.maps import get_webmap_json
from gitmap_core.maps import load_map_json
from gitmap_core.repository import Repository
from gitmap_core.repository import find_repository

from .utils import get_workspace_directory
from .utils import resolve_path


def _is_item_id(identifier: str) -> bool:
    """Check if identifier looks like a Portal item ID."""
    return (
        len(identifier) > 8
        and "/" not in identifier
        and identifier.replace("-", "").replace("_", "").isalnum()
    )


def _resolve_source_map(
    source: str,
    current_repo: Repository | None,
) -> dict[str, Any]:
    """Resolve source identifier to map JSON data.

    Handles item IDs, branch names, commit IDs, and file paths.

    Args:
        source: Source identifier (item ID, branch, commit, or file path).
        current_repo: Current repository context (for Portal connection).

    Returns:
        Map JSON dictionary.
    """
    # Check if it's a file or directory path
    # Resolve relative to workspace directory
    workspace_dir = get_workspace_directory()
    source_path = resolve_path(source, base=workspace_dir)
    if source_path.exists():
        if source_path.is_file():
            return load_map_json(source_path)
        elif source_path.is_dir():
            repo = Repository(source_path)
            if repo.exists() and repo.is_valid():
                current_branch = repo.get_current_branch()
                if current_branch:
                    commit_id = repo.get_branch_commit(current_branch)
                    if commit_id:
                        commit = repo.get_commit(commit_id)
                        if commit:
                            return commit.map_data
                index_data = repo.get_index()
                if index_data:
                    return index_data
                raise ValueError(f"Repository at '{source}' has no map data")

    # Check if it's a branch name or commit ID in current repo
    if current_repo:
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

    # Check if it's an item ID
    if _is_item_id(source):
        # Get Portal connection from current repo or use defaults
        portal_url = "https://www.arcgis.com"
        if current_repo:
            config = current_repo.get_config()
            if config.remote:
                portal_url = config.remote.url

        connection = get_connection(url=portal_url)
        _, map_data = get_webmap_by_id(connection.gis, source)
        return map_data

    raise ValueError(f"Cannot resolve source '{source}'")


def _transfer_layer_settings(
    source_layer: dict[str, Any],
    target_layer: dict[str, Any],
) -> dict[str, Any]:
    """Transfer popupInfo and formInfo from source to target layer.

    Args:
        source_layer: Source layer with settings to copy.
        target_layer: Target layer to update.

    Returns:
        Updated target layer.
    """
    updated_layer = target_layer.copy()

    # Transfer popupInfo
    if "popupInfo" in source_layer:
        updated_layer["popupInfo"] = source_layer["popupInfo"]

    # Transfer formInfo
    if "formInfo" in source_layer:
        updated_layer["formInfo"] = source_layer["formInfo"]

    return updated_layer


def gitmap_layer_settings_merge(
    source: str,
    target: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Transfer popup and form settings between maps.

    Transfers popupInfo and formInfo from layers and tables in a source map
    to matching layers and tables in a target map.

    Args:
        source: Source map (item ID, branch name, commit ID, or file path).
        target: Target map (optional, defaults to current index).
        dry_run: Preview changes without applying them.

    Returns:
        Dictionary with success status and transfer details.
    """
    try:
        # Start search from workspace directory
        workspace_dir = get_workspace_directory()
        current_repo = find_repository(start_path=workspace_dir)

        # Resolve source map
        source_map = _resolve_source_map(source, current_repo)

        # Resolve target map
        if target:
            target_map = _resolve_source_map(target, current_repo)
        else:
            if not current_repo:
                return {
                    "success": False,
                    "error": "No target specified and not in a GitMap repository",
                }
            target_map = current_repo.get_index()
            if not target_map:
                return {
                    "success": False,
                    "error": "No target specified and no staged changes",
                }

        # Build lookup maps by layer ID
        source_layers = {
            layer.get("id"): layer
            for layer in source_map.get("operationalLayers", [])
            if layer.get("id")
        }
        source_tables = {
            table.get("id"): table
            for table in source_map.get("tables", [])
            if table.get("id")
        }

        target_layers = target_map.get("operationalLayers", [])
        target_tables = target_map.get("tables", [])

        transferred = []
        not_found = []

        # Transfer layer settings
        for i, target_layer in enumerate(target_layers):
            layer_id = target_layer.get("id")
            if layer_id and layer_id in source_layers:
                if not dry_run:
                    target_layers[i] = _transfer_layer_settings(
                        source_layers[layer_id],
                        target_layer,
                    )
                transferred.append({
                    "type": "layer",
                    "id": layer_id,
                    "title": target_layer.get("title", layer_id),
                })

        # Transfer table settings
        for i, target_table in enumerate(target_tables):
            table_id = target_table.get("id")
            if table_id and table_id in source_tables:
                if not dry_run:
                    target_tables[i] = _transfer_layer_settings(
                        source_tables[table_id],
                        target_table,
                    )
                transferred.append({
                    "type": "table",
                    "id": table_id,
                    "title": target_table.get("title", table_id),
                })

        # Update target map
        if not dry_run and current_repo:
            target_map["operationalLayers"] = target_layers
            target_map["tables"] = target_tables
            current_repo.update_index(target_map)

        return {
            "success": True,
            "dry_run": dry_run,
            "transferred": transferred,
            "count": len(transferred),
            "message": f"{'Would transfer' if dry_run else 'Transferred'} settings for {len(transferred)} item(s)",
        }

    except Exception as lsm_error:
        return {
            "success": False,
            "error": f"Layer settings merge failed: {lsm_error}",
        }
