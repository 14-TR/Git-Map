"""Portal operations tools for GitMap MCP server.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Portal connection, maps, and communication

Metadata:
    Version: 0.1.1
    Author: GitMap Team
    Format: List format with code blocks (STRICT)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from gitmap_core.communication import get_group_member_usernames
from gitmap_core.communication import list_groups
from gitmap_core.communication import send_group_notification
from gitmap_core.connection import get_connection
from gitmap_core.maps import list_webmaps

from .utils import get_portal_url
from .utils import get_workspace_directory
from .utils import resolve_path

# Format version identifier
_FORMAT_VERSION = "0.1.1-list-with-code-blocks"


def gitmap_notify(
    group: str,
    subject: str,
    message: str | None = None,
    message_file: str | None = None,
    users: list[str] | None = None,
    url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Send a notification to group members using ArcGIS APIs.

    Args:
        group: Group ID or title to target for notifications.
        subject: Notification subject line.
        message: Notification body text (or use message_file).
        message_file: Path to file containing notification body.
        users: Specific usernames to notify (defaults to all group members).
        url: Portal URL (uses PORTAL_URL env var if not provided, which is required).
        username: Portal username (optional, uses env vars if not provided).
        password: Portal password (optional, uses env vars if not provided).

    Returns:
        Dictionary with success status and notification details.
    """
    try:
        # Load message body
        if message_file:
            # Resolve message file path relative to workspace
            workspace_dir = get_workspace_directory()
            message_path = resolve_path(message_file, base=workspace_dir)
            body = message_path.read_text(encoding="utf-8")
        elif message:
            body = message
        else:
            return {
                "success": False,
                "error": "Notification body is required (use message or message_file)",
            }

        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url)

        # Connect to Portal
        connection = get_connection(
            url=portal_url,
            username=username,
            password=password,
        )

        # Determine recipients
        if users:
            recipients = users
        else:
            recipients = get_group_member_usernames(connection.gis, group)

        if not recipients:
            return {
                "success": False,
                "error": f"No recipients found for group '{group}'",
            }

        # Send notification
        notified_users = send_group_notification(
            gis=connection.gis,
            group_id_or_title=group,
            subject=subject,
            body=body,
            users=recipients,
        )

        return {
            "success": True,
            "group": group,
            "users_notified": notified_users,
            "count": len(notified_users),
            "message": f"Notification sent to {len(notified_users)} user(s)",
        }

    except Exception as notify_error:
        return {
            "success": False,
            "error": f"Notification failed: {notify_error}",
        }


def gitmap_list_groups(
    url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """List all available groups from Portal.

    Args:
        url: Portal URL (uses PORTAL_URL env var if not provided, which is required).
        username: Portal username (optional, uses env vars if not provided).
        password: Portal password (optional, uses env vars if not provided).

    Returns:
        Dictionary with list of groups and formatted table.
    """
    try:
        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url)

        # Connect to Portal
        connection = get_connection(
            url=portal_url,
            username=username,
            password=password,
        )

        # List groups
        groups = list_groups(connection.gis)

        # Format as list with each title followed by ID in code block for easy copying
        # STRICT FORMAT: Each item must be "**Title**:\n```\nid\n```"
        # This format ensures each ID is in its own code block with a copy button
        ids_list = []
        list_items = []
        for group in groups:
            title = group.get("title", "N/A")
            owner = group.get("owner", "N/A")
            group_id = group.get("id", "N/A")
            if group_id != "N/A":
                ids_list.append(group_id)
                # Format as: Title: followed by code block with ID (STRICT FORMAT)
                list_items.append(f"**{title}**:\n```\n{group_id}\n```")
        
        # Create the formatted list
        # STRICT FORMAT: Items joined with double newline for proper spacing
        table = "\n\n".join(list_items) if list_items else "No groups found."
        
        # Create copyable IDs text (one per line for easy copying)
        ids_text = "\n".join(ids_list) if ids_list else ""

        return {
            "success": True,
            "groups": groups,
            "count": len(groups),
            "table": table,
            "ids": ids_list,
            "ids_text": ids_text,
            "message": f"Found {len(groups)} group(s)",
        }

    except Exception as list_error:
        return {
            "success": False,
            "error": f"Failed to list groups: {list_error}",
        }


def gitmap_list_maps(
    query: str | None = None,
    owner: str | None = None,
    tag: str | None = None,
    max_results: int = 100,
    url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """List all available web maps from Portal.

    Args:
        query: Search query to filter web maps.
        owner: Filter web maps by owner username.
        tag: Filter web maps by tag.
        max_results: Maximum number of web maps to return.
        url: Portal URL (uses PORTAL_URL env var if not provided, which is required).
        username: Portal username (optional, uses env vars if not provided).
        password: Portal password (optional, uses env vars if not provided).

    Returns:
        Dictionary with list of web maps and formatted table.
    """
    try:
        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url)

        # Connect to Portal
        connection = get_connection(
            url=portal_url,
            username=username,
            password=password,
        )

        # List web maps
        webmaps = list_webmaps(
            gis=connection.gis,
            query=query or "",
            owner=owner or "",
            tag=tag or "",
            max_results=max_results,
        )

        # Format as list with each title followed by ID in code block for easy copying
        # STRICT FORMAT: Each item must be "**Title**:\n```\nid\n```"
        # This format ensures each ID is in its own code block with a copy button
        ids_list = []
        list_items = []
        for webmap in webmaps:
            title = webmap.get("title", "N/A")
            owner = webmap.get("owner", "N/A")
            item_id = webmap.get("id", "N/A")
            if item_id != "N/A":
                ids_list.append(item_id)
                # Format as: Title: followed by code block with ID (STRICT FORMAT)
                list_items.append(f"**{title}**:\n```\n{item_id}\n```")
        
        # Create the formatted list
        # STRICT FORMAT: Items joined with double newline for proper spacing
        table = "\n\n".join(list_items) if list_items else "No web maps found."
        
        # Create copyable IDs text (one per line for easy copying)
        ids_text = "\n".join(ids_list) if ids_list else ""

        return {
            "success": True,
            "webmaps": webmaps,
            "count": len(webmaps),
            "table": table,
            "ids": ids_list,
            "ids_text": ids_text,
            "message": f"Found {len(webmaps)} web map(s)",
        }

    except Exception as list_error:
        return {
            "success": False,
            "error": f"Failed to list web maps: {list_error}",
        }
