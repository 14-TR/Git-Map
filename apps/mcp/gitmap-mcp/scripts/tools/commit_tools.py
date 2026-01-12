"""Commit management tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository and diff operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from typing import Any

from gitmap_core.diff import diff_maps
from gitmap_core.diff import format_diff_summary
from gitmap_core.repository import find_repository

from .utils import find_repo_from_path


def gitmap_commit(message: str, author: str | None = None, path: str | None = None) -> dict[str, Any]:
    """Create a new commit.

    Args:
        message: Commit message describing the changes.
        author: Override commit author (optional).
        path: Optional path to repository directory.

    Returns:
        Dictionary with success status and commit details.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        # Check for changes
        if not repo.has_uncommitted_changes():
            return {
                "success": False,
                "error": "Nothing to commit, working tree clean",
            }

        # Create commit
        new_commit = repo.create_commit(
            message=message,
            author=author,
        )

        layers = new_commit.map_data.get("operationalLayers", [])
        return {
            "success": True,
            "commit": {
                "id": new_commit.id,
                "message": new_commit.message,
                "author": new_commit.author,
                "timestamp": new_commit.timestamp,
                "parent": new_commit.parent,
                "layers": len(layers),
            },
            "message": f"Created commit {new_commit.id[:8]}",
        }

    except Exception as commit_error:
        return {
            "success": False,
            "error": f"Commit failed: {commit_error}",
        }


def gitmap_log(limit: int = 10, oneline: bool = False, path: str | None = None) -> dict[str, Any]:
    """Show commit history.

    Args:
        limit: Maximum number of commits to show.
        oneline: Show compact one-line format.
        path: Optional path to repository directory.

    Returns:
        Dictionary with commit history.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        commits = repo.get_commit_history(limit=limit)
        current_branch = repo.get_current_branch()
        head_commit = repo.get_head_commit()

        commit_list = []
        for commit in commits:
            commit_data: dict[str, Any] = {
                "id": commit.id,
                "message": commit.message,
                "author": commit.author,
                "timestamp": commit.timestamp,
                "parent": commit.parent,
                "is_head": commit.id == head_commit,
            }

            if not oneline:
                layers = commit.map_data.get("operationalLayers", [])
                commit_data["layers"] = len(layers)

            commit_list.append(commit_data)

        return {
            "success": True,
            "commits": commit_list,
            "current_branch": current_branch,
            "head_commit": head_commit,
        }

    except Exception as log_error:
        return {
            "success": False,
            "error": f"Log failed: {log_error}",
        }


def gitmap_diff(target: str | None = None, verbose: bool = False, path: str | None = None) -> dict[str, Any]:
    """Show changes between states.

    Args:
        target: Branch name or commit ID to compare with (defaults to HEAD).
        verbose: Show detailed property-level changes.
        path: Optional path to repository directory.

    Returns:
        Dictionary with diff results.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

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
            return {
                "success": True,
                "has_changes": False,
                "message": "No commits to compare against",
            }

        # Load target commit
        target_commit = repo.get_commit(commit_id)
        if not target_commit:
            return {
                "success": False,
                "error": f"Commit '{commit_id}' not found",
            }

        # Perform diff
        map_diff = diff_maps(index_data, target_commit.map_data)

        if not map_diff.has_changes:
            return {
                "success": True,
                "has_changes": False,
                "message": "No differences",
            }

        # Format summary
        summary_text = format_diff_summary(map_diff)

        result: dict[str, Any] = {
            "success": True,
            "has_changes": True,
            "target": commit_id,
            "summary": summary_text,
            "added_layers": len(map_diff.added_layers),
            "removed_layers": len(map_diff.removed_layers),
            "modified_layers": len(map_diff.modified_layers),
        }

        if verbose and map_diff.modified_layers:
            modified_details = []
            for change in map_diff.modified_layers:
                modified_details.append({
                    "layer_id": change.layer_id,
                    "layer_title": change.layer_title,
                    "details": change.details,
                })
            result["modified_details"] = modified_details

        return result

    except Exception as diff_error:
        return {
            "success": False,
            "error": f"Diff failed: {diff_error}",
        }
