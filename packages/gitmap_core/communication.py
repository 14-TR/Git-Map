"""Communication helpers for Portal/AGOL users and groups.

Provides utilities to gather group members and send notifications using the
ArcGIS API for Python `Group.notify` method (no SMTP wiring required).

Execution Context:
    Library module - imported by CLI notification commands

Dependencies:
    - arcgis: Portal/AGOL interaction

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

from collections.abc import Sequence

try:
    from arcgis.gis import GIS  # type: ignore
except Exception:  # pragma: no cover - handled at runtime
    GIS = None  # type: ignore


def _ensure_gis(gis: GIS) -> None:
    """Ensure a GIS connection object is available.

    Args:
        gis: GIS connection object.

    Raises:
        RuntimeError: If GIS is not available.
    """
    if GIS is None:
        msg = "ArcGIS API for Python is not installed."
        raise RuntimeError(msg)
    if gis is None:
        msg = "A valid GIS connection is required."
        raise RuntimeError(msg)


def _resolve_group(gis: GIS, group_id_or_title: str):
    """Resolve a group by ID or title.

    Args:
        gis: Authenticated GIS connection.
        group_id_or_title: Group ID or title to resolve.

    Returns:
        Group object if found, otherwise None.
    """
    _ensure_gis(gis)
    group = gis.groups.get(group_id_or_title)
    if group:
        return group

    matches = gis.groups.search(f'title:"{group_id_or_title}"')
    return matches[0] if matches else None


def get_group_member_usernames(
        gis: GIS,
        group_id_or_title: str,
) -> list[str]:
    """Collect usernames for all members of a group.

    Args:
        gis: Authenticated GIS connection.
        group_id_or_title: Group ID or title.

    Returns:
        List of unique usernames (owner, admins, users, and invited users).

    Raises:
        RuntimeError: If group cannot be found or no members are available.
    """
    _ensure_gis(gis)
    group = _resolve_group(gis, group_id_or_title)
    if group is None:
        msg = f"Group '{group_id_or_title}' not found."
        raise RuntimeError(msg)

    members = group.get_members()
    usernames: set[str] = set()

    owner = members.get("owner")
    if owner:
        usernames.add(owner)

    for key in ("admins", "users", "admins_invited", "users_invited"):
        for username in members.get(key, []) or []:
            if username:
                usernames.add(username)

    if not usernames:
        msg = f"No members found for group '{group_id_or_title}'."
        raise RuntimeError(msg)

    return sorted(usernames)


def list_groups(
        gis: GIS,
        query: str = "",
        max_results: int = 100,
) -> list[dict[str, str]]:
    """List available groups from the Portal.

    Args:
        gis: Authenticated GIS connection.
        query: Optional search query string to filter groups (e.g., "title:MyGroup").
            Defaults to empty string to list all groups.
        max_results: Maximum number of groups to return (default: 100).

    Returns:
        List of dictionaries containing group information (id, title, owner).

    Raises:
        RuntimeError: If group search fails.
    """
    _ensure_gis(gis)
    try:
        # groups.search() only accepts query string as positional argument
        groups = gis.groups.search(query)
        result = []
        for group in groups[:max_results]:
            result.append({
                "id": getattr(group, "id", ""),
                "title": getattr(group, "title", ""),
                "owner": getattr(group, "owner", ""),
            })
        return result
    except Exception as search_error:
        msg = f"Failed to search groups: {search_error}"
        raise RuntimeError(msg) from search_error


def send_group_notification(
        gis: GIS,
        group_id_or_title: str,
        subject: str,
        body: str,
        users: Sequence[str] | None = None,
) -> Sequence[str]:
    """Send a notification to group members using ArcGIS `Group.notify`.

    Args:
        gis: Authenticated GIS connection.
        group_id_or_title: Group ID or title to resolve.
        subject: Notification subject.
        body: Notification message body (plain text or HTML supported by ArcGIS).
        users: Optional iterable of usernames; when omitted, the entire group is notified.

    Returns:
        Sequence of usernames passed to the notification call.

    Raises:
        RuntimeError: If notification fails or no users can be determined.
    """
    _ensure_gis(gis)
    group = _resolve_group(gis, group_id_or_title)
    if group is None:
        msg = f"Group '{group_id_or_title}' not found."
        raise RuntimeError(msg)

    target_users = list(users) if users else get_group_member_usernames(gis, group_id_or_title)
    if not target_users:
        msg = f"No target users resolved for group '{group_id_or_title}'."
        raise RuntimeError(msg)

    try:
        group.notify(users=target_users, subject=subject, message=body)
    except Exception as notify_error:  # pragma: no cover - depends on ArcGIS service
        msg = f"Failed to send notification: {notify_error}"
        raise RuntimeError(msg) from notify_error

    return target_users


def get_item_group_users(
        gis: GIS,
        item,
) -> list[str]:
    """Collect all users from groups that have access to a Portal item.

    Gets all groups that the item is shared with and collects unique usernames
    from all those groups. De-duplicates users across groups.

    Args:
        gis: Authenticated GIS connection.
        item: Portal Item object.

    Returns:
        List of unique usernames from all groups sharing the item.

    Raises:
        RuntimeError: If item sharing information cannot be retrieved.
    """
    _ensure_gis(gis)
    try:
        # Get item sharing information
        # item.sharing is a SharingManager object, not a dict
        # Check if item is private (not shared)
        if item.access == "private":
            return []

        # Get groups the item is shared with
        # Try to get from item properties or by querying user's groups
        groups = []
        try:
            # Method 1: Try to get from item's properties
            if hasattr(item, "properties") and item.properties:
                sharing_data = item.properties.get("sharing", {})
                if isinstance(sharing_data, dict):
                    groups = sharing_data.get("groups", [])

            # Method 2: If not found, query user's groups to find which have access
            if not groups:
                user = gis.users.me
                if user:
                    user_groups = user.groups
                    for group in user_groups:
                        try:
                            # Check if this group has access to the item
                            # by checking if the item appears in the group's content
                            group_items = group.content()
                            if any(g_item.id == item.id for g_item in group_items):
                                groups.append(group.id)
                        except Exception:
                            continue
        except Exception:
            groups = []

        if not groups:
            return []

        # Collect all unique usernames from all groups
        all_users: set[str] = set()
        for group_id in groups:
            try:
                group_users = get_group_member_usernames(gis, group_id)
                all_users.update(group_users)
            except Exception:
                # Skip groups that can't be accessed
                continue

        return sorted(all_users)

    except Exception as sharing_error:
        msg = f"Failed to get item group users: {sharing_error}"
        raise RuntimeError(msg) from sharing_error


def notify_item_group_users(
        gis: GIS,
        item,
        subject: str,
        body: str,
) -> list[str]:
    """Send notifications to all users from groups that have access to an item.

    Gets all groups that the item is shared with, collects unique usernames
    from all those groups, and sends notifications. The ArcGIS API handles
    deduplication of notifications.

    Args:
        gis: Authenticated GIS connection.
        item: Portal Item object.
        subject: Notification subject.
        body: Notification message body.

    Returns:
        List of unique usernames from all groups (may receive notifications
        through multiple groups, but ArcGIS handles deduplication).

    Raises:
        RuntimeError: If notification fails.
    """
    _ensure_gis(gis)
    try:
        # Get item sharing information
        # item.sharing is a SharingManager object, not a dict
        # Check if item is private (not shared)
        if item.access == "private":
            return []

        # Get groups the item is shared with
        # Try to get from item properties or by querying user's groups
        groups = []
        try:
            # Method 1: Try to get from item's properties
            if hasattr(item, "properties") and item.properties:
                sharing_data = item.properties.get("sharing", {})
                if isinstance(sharing_data, dict):
                    groups = sharing_data.get("groups", [])

            # Method 2: If not found, query user's groups to find which have access
            if not groups:
                user = gis.users.me
                if user:
                    user_groups = user.groups
                    for group in user_groups:
                        try:
                            # Check if this group has access to the item
                            # by checking if the item appears in the group's content
                            group_items = group.content()
                            if any(g_item.id == item.id for g_item in group_items):
                                groups.append(group.id)
                        except Exception:
                            continue
        except Exception:
            groups = []

        if not groups:
            return []

        # Collect all unique usernames from all groups
        all_users: set[str] = set()

        for group_id in groups:
            try:
                group_users = get_group_member_usernames(gis, group_id)
                all_users.update(group_users)

                # Send notification to each group
                # ArcGIS API handles deduplication of notifications
                try:
                    group = _resolve_group(gis, group_id)
                    if group:
                        group.notify(users=group_users, subject=subject, message=body)
                except Exception:
                    # Skip groups that fail to notify, but keep their users in the list
                    continue

            except Exception:
                # Skip groups that can't be accessed
                continue

        return sorted(all_users)

    except Exception as notify_error:
        msg = f"Failed to notify item group users: {notify_error}"
        raise RuntimeError(msg) from notify_error


