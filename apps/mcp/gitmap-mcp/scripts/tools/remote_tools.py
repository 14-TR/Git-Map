"""Remote operations tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Remote operations and connection

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from typing import Any

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import find_repository

from .utils import get_workspace_directory


def gitmap_push(
    branch: str | None = None,
    url: str | None = None,
    username: str | None = None,
    no_notify: bool = False,
) -> dict[str, Any]:
    """Push branch to ArcGIS Portal.

    Args:
        branch: Branch to push (defaults to current branch).
        url: Portal URL (uses configured remote if not specified).
        username: Portal username (optional, uses env vars if not provided).
        no_notify: Skip sending notifications.

    Returns:
        Dictionary with success status and push details.
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

        # Determine Portal URL
        config = repo.get_config()
        portal_url = url or (config.remote.url if config.remote else "https://www.arcgis.com")

        # Connect to Portal
        connection = get_connection(
            url=portal_url,
            username=username,
        )

        # Perform push
        target_branch = branch or repo.get_current_branch()
        if not target_branch:
            return {
                "success": False,
                "error": "No branch specified and not on any branch",
            }

        remote_ops = RemoteOperations(repo, connection)
        item, notification_status = remote_ops.push(target_branch, skip_notifications=no_notify)

        result: dict[str, Any] = {
            "success": True,
            "branch": target_branch,
            "item_id": item.id,
            "item_title": item.title,
            "item_url": item.homepage,
            "message": f"Pushed '{target_branch}' to Portal",
        }

        if notification_status["attempted"]:
            result["notifications"] = {
                "sent": notification_status["sent"],
                "users_notified": notification_status["users_notified"],
                "reason": notification_status.get("reason"),
            }

        return result

    except Exception as push_error:
        return {
            "success": False,
            "error": f"Push failed: {push_error}",
        }


def gitmap_pull(
    branch: str | None = None,
    url: str | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    """Pull latest changes from Portal.

    Args:
        branch: Branch to pull (defaults to current branch).
        url: Portal URL (uses configured remote if not specified).
        username: Portal username (optional, uses env vars if not provided).

    Returns:
        Dictionary with success status and pull details.
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

        # Determine Portal URL
        config = repo.get_config()
        if not config.remote:
            return {
                "success": False,
                "error": "No remote configured. Use gitmap_clone or configure a remote.",
            }

        portal_url = url or config.remote.url

        # Connect to Portal
        connection = get_connection(
            url=portal_url,
            username=username,
        )

        # Perform pull
        target_branch = branch or repo.get_current_branch()
        if not target_branch:
            return {
                "success": False,
                "error": "No branch specified and not on any branch",
            }

        remote_ops = RemoteOperations(repo, connection)
        map_data = remote_ops.pull(target_branch)

        layers = map_data.get("operationalLayers", [])
        return {
            "success": True,
            "branch": target_branch,
            "layers": len(layers),
            "message": f"Pulled '{target_branch}' from Portal. Use gitmap_diff to review changes.",
        }

    except Exception as pull_error:
        return {
            "success": False,
            "error": f"Pull failed: {pull_error}",
        }
