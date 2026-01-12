"""Branch management tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from typing import Any

from gitmap_core.repository import find_repository

from .utils import find_repo_from_path


def _record_branch_event(repo, action: str, branch_name: str, commit_id: str | None = None) -> None:
    """Record a branch event to the context store."""
    try:
        config = repo.get_config()
        actor = config.user_name if config else None
        with repo.get_context_store() as store:
            store.record_event(
                event_type="branch",
                repo=str(repo.root),
                ref=branch_name,
                actor=actor,
                payload={
                    "action": action,
                    "branch_name": branch_name,
                    "commit_id": commit_id,
                },
            )
    except Exception:
        pass  # Don't fail branch operation if context recording fails


def gitmap_branch_list(path: str | None = None) -> dict[str, Any]:
    """List all branches in the repository.

    Args:
        path: Optional path to repository directory.

    Returns:
        Dictionary with list of branches and current branch.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        branches = repo.list_branches()
        current_branch = repo.get_current_branch()

        return {
            "success": True,
            "branches": branches,
            "current_branch": current_branch,
        }

    except Exception as branch_error:
        return {
            "success": False,
            "error": f"Failed to list branches: {branch_error}",
        }


def gitmap_branch_create(name: str, path: str | None = None) -> dict[str, Any]:
    """Create a new branch.

    Args:
        name: Branch name to create.
        path: Optional path to repository directory.

    Returns:
        Dictionary with success status and branch details.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        new_branch = repo.create_branch(name)
        _record_branch_event(repo, action="create", branch_name=new_branch.name, commit_id=new_branch.commit_id)

        return {
            "success": True,
            "branch_name": new_branch.name,
            "commit_id": new_branch.commit_id,
            "message": f"Created branch '{new_branch.name}'",
        }

    except Exception as branch_error:
        return {
            "success": False,
            "error": f"Failed to create branch: {branch_error}",
        }


def gitmap_branch_delete(name: str, path: str | None = None) -> dict[str, Any]:
    """Delete a branch.

    Args:
        name: Branch name to delete.
        path: Optional path to repository directory.

    Returns:
        Dictionary with success status.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        current_branch = repo.get_current_branch()
        if name == current_branch:
            return {
                "success": False,
                "error": f"Cannot delete current branch '{name}'. Switch branches first.",
            }

        repo.delete_branch(name)
        _record_branch_event(repo, action="delete", branch_name=name)

        return {
            "success": True,
            "message": f"Deleted branch '{name}'",
        }

    except Exception as branch_error:
        return {
            "success": False,
            "error": f"Failed to delete branch: {branch_error}",
        }


def gitmap_checkout(branch: str, create: bool = False, path: str | None = None) -> dict[str, Any]:
    """Switch to a different branch.

    Args:
        branch: Branch name to checkout.
        create: Create branch if it doesn't exist.
        path: Optional path to repository directory.

    Returns:
        Dictionary with success status and branch info.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        # Check for uncommitted changes
        if repo.has_uncommitted_changes():
            return {
                "success": False,
                "error": "You have uncommitted changes. Commit or discard them first.",
                "has_uncommitted_changes": True,
            }

        # Create branch if requested and doesn't exist
        if create:
            branches = repo.list_branches()
            if branch not in branches:
                repo.create_branch(branch)

        # Switch to branch
        repo.checkout_branch(branch)

        # Get commit info
        commit_id = repo.get_branch_commit(branch)
        result: dict[str, Any] = {
            "success": True,
            "branch": branch,
            "message": f"Switched to branch '{branch}'",
        }

        if commit_id:
            commit = repo.get_commit(commit_id)
            if commit:
                result["commit"] = {
                    "id": commit.id,
                    "message": commit.message,
                }

        return result

    except Exception as checkout_error:
        return {
            "success": False,
            "error": f"Checkout failed: {checkout_error}",
        }
