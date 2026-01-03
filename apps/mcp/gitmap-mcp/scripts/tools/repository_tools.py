"""Repository management tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository and connection management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from gitmap_core.connection import get_connection
from gitmap_core.maps import get_webmap_by_id
from gitmap_core.models import Remote
from gitmap_core.repository import Repository
from gitmap_core.repository import find_repository

from .utils import get_workspace_directory
from .utils import resolve_path


def gitmap_init(
    path: str = ".",
    project_name: str | None = None,
    user_name: str | None = None,
    user_email: str | None = None,
) -> dict[str, Any]:
    """Initialize a new GitMap repository.

    Creates a .gitmap directory structure in the specified path.

    Args:
        path: Directory path to initialize (defaults to workspace directory).
        project_name: Project name (defaults to directory name).
        user_name: Default author name for commits.
        user_email: Default author email for commits.

    Returns:
        Dictionary with success status and repository path.
    """
    try:
        # If path is "." (default), use workspace directory
        if path == ".":
            repo_path = get_workspace_directory()
        else:
            repo_path = resolve_path(path)
        repo = Repository(repo_path)

        if repo.exists():
            return {
                "success": False,
                "error": f"GitMap repository already exists at {repo.gitmap_dir}",
            }

        repo.init(
            project_name=project_name or "",
            user_name=user_name or "",
            user_email=user_email or "",
        )

        return {
            "success": True,
            "repository_path": str(repo_path),
            "gitmap_dir": str(repo.gitmap_dir),
            "message": f"Initialized empty GitMap repository in {repo.gitmap_dir}",
        }

    except Exception as init_error:
        return {
            "success": False,
            "error": f"Failed to initialize repository: {init_error}",
        }


def gitmap_clone(
    item_id: str,
    directory: str | None = None,
    url: str = "https://www.arcgis.com",
    username: str | None = None,
) -> dict[str, Any]:
    """Clone a web map from Portal.

    Creates a new GitMap repository containing the specified web map.

    Args:
        item_id: Portal item ID to clone.
        directory: Directory to clone into (defaults to map title).
        url: Portal URL (defaults to ArcGIS Online).
        username: Portal username (optional, uses env vars if not provided).

    Returns:
        Dictionary with success status and clone details.
    """
    try:
        # Connect to Portal
        connection = get_connection(url=url, username=username)

        # Fetch web map
        item, map_data = get_webmap_by_id(connection.gis, item_id)

        # Determine target directory
        if directory:
            target_dir = resolve_path(directory)
        else:
            # Use sanitized map title
            safe_title = "".join(
                c if c.isalnum() or c in "-_" else "_"
                for c in item.title
            )
            # Use workspace directory as base instead of current working directory
            workspace_dir = get_workspace_directory()
            target_dir = workspace_dir / safe_title

        # Check if directory exists
        if target_dir.exists():
            return {
                "success": False,
                "error": f"Directory '{target_dir}' already exists",
            }

        # Create directory and initialize repo
        target_dir.mkdir(parents=True)
        repo = Repository(target_dir)

        repo.init(
            project_name=item.title,
            user_name=connection.username or "",
        )

        # Configure remote
        config = repo.get_config()
        config.remote = Remote(
            name="origin",
            url=url,
            item_id=item_id,
        )
        repo.update_config(config)

        # Stage and commit the map
        repo.update_index(map_data)
        commit = repo.create_commit(
            message=f"Clone from Portal: {item.title}",
            author=connection.username or "GitMap",
        )

        layers = map_data.get("operationalLayers", [])
        return {
            "success": True,
            "repository_path": str(target_dir),
            "item_id": item_id,
            "title": item.title,
            "layers": len(layers),
            "commit_id": commit.id,
            "message": f"Cloned '{item.title}' into {target_dir}",
        }

    except Exception as clone_error:
        return {
            "success": False,
            "error": f"Clone failed: {clone_error}",
        }


def gitmap_status() -> dict[str, Any]:
    """Show the working tree status.

    Returns:
        Dictionary with current branch, commit info, and change status.
    """
    try:
        # Start search from workspace directory
        workspace_dir = get_workspace_directory()
        repo = find_repository(start_path=workspace_dir)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        # Get current branch
        current_branch = repo.get_current_branch()
        head_commit = repo.get_head_commit()

        # Check for uncommitted changes
        has_changes = repo.has_uncommitted_changes()

        result: dict[str, Any] = {
            "success": True,
            "current_branch": current_branch or "(detached HEAD)",
            "has_uncommitted_changes": has_changes,
        }

        if head_commit:
            commit = repo.get_commit(head_commit)
            if commit:
                result["latest_commit"] = {
                    "id": commit.id,
                    "message": commit.message,
                    "author": commit.author,
                    "timestamp": commit.timestamp,
                }

        if has_changes:
            index_data = repo.get_index()
            layers = index_data.get("operationalLayers", [])
            result["staged_layers"] = len(layers)

        return result

    except Exception as status_error:
        return {
            "success": False,
            "error": f"Failed to get status: {status_error}",
        }
