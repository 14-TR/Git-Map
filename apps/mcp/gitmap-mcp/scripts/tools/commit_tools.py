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


def gitmap_merge(
        branch: str,
        strategy: str | None = None,
        no_commit: bool = False,
        path: str | None = None,
) -> dict[str, Any]:
    """Merge a branch into the current branch.

    Performs a layer-level merge.  When conflicts arise they are
    returned as structured data so the calling agent can decide how to
    resolve them.  Pass ``strategy`` to auto-resolve all conflicts
    without manual intervention.

    Args:
        branch: Name of the branch to merge into the current branch.
        strategy: Auto-resolution strategy for conflicts.
            ``"ours"`` keeps the current branch's version of every
            conflicting layer; ``"theirs"`` takes the incoming branch's
            version.  Omit (or pass ``None``) to surface conflicts as
            structured data instead of resolving them automatically.
        no_commit: When ``True`` the merge is staged but not committed,
            leaving it for a subsequent ``gitmap_commit`` call.
        path: Optional path to the repository directory.

    Returns:
        Dictionary with merge results, including any conflicts as
        structured data.  Keys:

        - ``success`` (bool): ``True`` when the merge completed
          (possibly with auto-resolved conflicts).
        - ``merged`` (bool): ``True`` when the merge was applied.
        - ``committed`` (bool): ``True`` when a merge commit was
          created automatically.
        - ``commit`` (dict | None): Commit details when committed.
        - ``conflicts`` (list[dict]): Unresolved conflicts, each with
          ``layer_id``, ``layer_title``, and optional ``base`` flag.
        - ``added_layers`` (int): Layers added from the source branch.
        - ``modified_layers`` (int): Layers cleanly modified.
        - ``message`` (str): Human-readable result summary.
        - ``error`` (str): Present only on failure.

    Raises:
        Nothing — all errors are captured and returned in ``error``.
    """
    from gitmap_core.merge import apply_resolution
    from gitmap_core.merge import merge_maps
    from gitmap_core.merge import resolve_conflict

    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        current_branch = repo.get_current_branch()
        if not current_branch:
            return {
                "success": False,
                "error": "Cannot merge in detached HEAD state.",
            }

        if branch == current_branch:
            return {
                "success": False,
                "error": f"Cannot merge branch '{branch}' into itself.",
            }

        available = repo.list_branches()
        if branch not in available:
            return {
                "success": False,
                "error": f"Branch '{branch}' not found. "
                         f"Available: {', '.join(available)}",
            }

        # Resolve commits
        our_commit_id = repo.get_branch_commit(current_branch)
        their_commit_id = repo.get_branch_commit(branch)

        if not their_commit_id:
            return {
                "success": False,
                "error": f"Branch '{branch}' has no commits.",
            }

        their_commit = repo.get_commit(their_commit_id)
        if not their_commit:
            return {
                "success": False,
                "error": f"Could not load commit '{their_commit_id}'.",
            }

        # Current state from index or HEAD commit
        our_data = repo.get_index()
        if not our_data and our_commit_id:
            our_commit = repo.get_commit(our_commit_id)
            if our_commit:
                our_data = our_commit.map_data

        # Attempt three-way merge via common ancestor (requires find_common_ancestor)
        base_data: dict[str, Any] | None = None
        ancestor_id: str | None = None
        if our_commit_id and their_commit_id and hasattr(repo, "find_common_ancestor"):
            ancestor_id = repo.find_common_ancestor(our_commit_id, their_commit_id)
            if ancestor_id:
                ancestor_commit = repo.get_commit(ancestor_id)
                if ancestor_commit:
                    base_data = ancestor_commit.map_data

        merge_result = merge_maps(
            ours=our_data,
            theirs=their_commit.map_data,
            base=base_data,
        )

        # Auto-resolve conflicts when a strategy was supplied
        if merge_result.has_conflicts and strategy in ("ours", "theirs"):
            for conflict in list(merge_result.conflicts):
                resolved = resolve_conflict(conflict, strategy)
                merge_result = apply_resolution(merge_result, conflict.layer_id, resolved)

        # Surface unresolved conflicts without applying the merge
        if merge_result.has_conflicts:
            conflict_list = [
                {
                    "layer_id": c.layer_id,
                    "layer_title": c.layer_title,
                    "has_base": c.base is not None,
                }
                for c in merge_result.conflicts
            ]
            return {
                "success": False,
                "merged": False,
                "committed": False,
                "conflicts": conflict_list,
                "message": (
                    f"{len(conflict_list)} conflict(s) must be resolved. "
                    f"Re-call with strategy='ours' or strategy='theirs' to "
                    f"auto-resolve."
                ),
            }

        # Apply the merge to the index
        repo.update_index(merge_result.merged_data)

        commit_info: dict[str, Any] | None = None
        committed = False

        if not no_commit:
            commit_msg = f"Merge branch '{branch}' into '{current_branch}'"
            new_commit = repo.create_commit(message=commit_msg)
            committed = True
            layers = new_commit.map_data.get("operationalLayers", [])
            commit_info = {
                "id": new_commit.id,
                "message": new_commit.message,
                "author": new_commit.author,
                "timestamp": new_commit.timestamp,
                "layers": len(layers),
            }

        return {
            "success": True,
            "merged": True,
            "committed": committed,
            "commit": commit_info,
            "conflicts": [],
            "added_layers": len(merge_result.added_layers),
            "modified_layers": len(merge_result.modified_layers),
            "ancestor_commit": ancestor_id,
            "message": (
                f"Merged '{branch}' into '{current_branch}' "
                + (f"— commit {commit_info['id'][:8]}" if commit_info else "(staged, not committed)")
            ),
        }

    except Exception as merge_error:
        return {
            "success": False,
            "error": f"Merge failed: {merge_error}",
        }
