"""Stash management tools for GitMap MCP server.

Exposes the GitMap stash workflow — save, apply, list, drop, and clear
stash entries — as MCP-callable functions.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository and stash operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from typing import Any

from .utils import find_repo_from_path


def gitmap_stash_push(
        message: str | None = None,
        path: str | None = None,
) -> dict[str, Any]:
    """Save uncommitted changes to the stash stack.

    The working index is reset to HEAD state after the stash is created,
    leaving the working tree clean.

    Args:
        message: Optional description for the stash entry.
        path: Optional path to repository directory.

    Returns:
        Dictionary with stash entry details on success, or an error message.

        Keys on success:
        - ``success`` (bool): ``True``.
        - ``stash_id`` (str): Identifier such as ``stash@{0}``.
        - ``branch`` (str | None): Branch name at stash time.
        - ``message`` (str): Stash description.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        stash_entry = repo.stash_push(message=message)

        return {
            "success": True,
            "stash_id": stash_entry["id"],
            "branch": stash_entry.get("branch"),
            "message": stash_entry.get("message", ""),
        }

    except RuntimeError as stash_error:
        return {
            "success": False,
            "error": str(stash_error),
        }
    except Exception as stash_error:
        return {
            "success": False,
            "error": f"Stash push failed: {stash_error}",
        }


def gitmap_stash_pop(
        index: int = 0,
        path: str | None = None,
) -> dict[str, Any]:
    """Apply and remove a stash entry.

    Restores the stash entry at ``index`` to the working index and
    removes it from the stash list.

    Args:
        index: Position in the stash list (0 = most recent).
        path: Optional path to repository directory.

    Returns:
        Dictionary with applied stash details on success, or an error
        message if the stash list is empty or the index is out of range.

        Keys on success:
        - ``success`` (bool): ``True``.
        - ``stash_id`` (str): ID of the applied stash entry.
        - ``message`` (str): Stash description.
        - ``branch`` (str | None): Branch the stash was created on.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        stash_entry = repo.stash_pop(index=index)

        return {
            "success": True,
            "stash_id": stash_entry["id"],
            "message": stash_entry.get("message", ""),
            "branch": stash_entry.get("branch"),
        }

    except RuntimeError as stash_error:
        return {
            "success": False,
            "error": str(stash_error),
        }
    except Exception as stash_error:
        return {
            "success": False,
            "error": f"Stash pop failed: {stash_error}",
        }


def gitmap_stash_list(
        path: str | None = None,
) -> dict[str, Any]:
    """List all stash entries (newest first).

    Args:
        path: Optional path to repository directory.

    Returns:
        Dictionary with stash entries.

        Keys:
        - ``success`` (bool): ``True``.
        - ``entries`` (list[dict]): Each entry has ``stash_id``,
          ``message``, and ``branch``.
        - ``count`` (int): Total number of entries.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        raw = repo.stash_list()

        entries = [
            {
                "index": i,
                "stash_id": entry.get("id", f"stash@{{{i}}}"),
                "message": entry.get("message", ""),
                "branch": entry.get("branch"),
            }
            for i, entry in enumerate(raw)
        ]

        return {
            "success": True,
            "entries": entries,
            "count": len(entries),
        }

    except Exception as stash_error:
        return {
            "success": False,
            "error": f"Stash list failed: {stash_error}",
        }


def gitmap_stash_drop(
        index: int = 0,
        path: str | None = None,
) -> dict[str, Any]:
    """Drop a stash entry without applying it.

    Removes the stash entry at ``index`` from the stash list and
    deletes its stored data.

    Args:
        index: Position in the stash list (0 = most recent).
        path: Optional path to repository directory.

    Returns:
        Dictionary with dropped entry details on success, or an error
        message if the stash is empty or the index is out of range.

        Keys on success:
        - ``success`` (bool): ``True``.
        - ``stash_id`` (str): ID of the dropped stash entry.
        - ``message`` (str): Human-readable confirmation.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        dropped = repo.stash_drop(index=index)

        stash_id = dropped.get("id", f"stash@{{{index}}}")
        return {
            "success": True,
            "stash_id": stash_id,
            "message": f"Dropped stash entry {stash_id}",
        }

    except RuntimeError as stash_error:
        return {
            "success": False,
            "error": str(stash_error),
        }
    except Exception as stash_error:
        return {
            "success": False,
            "error": f"Stash drop failed: {stash_error}",
        }
