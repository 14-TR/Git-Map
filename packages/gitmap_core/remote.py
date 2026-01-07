"""Remote operations module for GitMap.

Handles push and pull operations between local repository and
ArcGIS Portal/AGOL remotes.

Execution Context:
    Library module - imported by CLI push/pull commands

Dependencies:
    - arcgis: Portal interaction
    - gitmap_core.connection: Portal authentication
    - gitmap_core.models: Data models

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from gitmap_core.communication import notify_item_group_users
from gitmap_core.connection import PortalConnection
from gitmap_core.models import Remote
from gitmap_core.models import RepoConfig

if TYPE_CHECKING:
    from arcgis.gis import GIS
    from arcgis.gis import Item

    from gitmap_core.repository import Repository


# ---- Constants ----------------------------------------------------------------------------------------------


GITMAP_META_TITLE = ".gitmap_meta"
GITMAP_FOLDER_SUFFIX = "_GitMap"


# ---- Remote Operations Class --------------------------------------------------------------------------------


class RemoteOperations:
    """Handles remote repository operations.

    Provides methods for pushing branches to Portal and pulling
    updates from Portal.

    Attributes:
        repo: Local Repository instance.
        connection: Portal connection.
        config: Repository configuration.
    """

    def __init__(
            self,
            repo: Repository,
            connection: PortalConnection,
    ) -> None:
        """Initialize remote operations.

        Args:
            repo: Local repository.
            connection: Authenticated Portal connection.
        """
        self.repo = repo
        self.connection = connection
        self.config = repo.get_config()

    @property
    def gis(
            self,
    ) -> GIS:
        """Get GIS connection."""
        return self.connection.gis

    @property
    def remote(
            self,
    ) -> Remote | None:
        """Get configured remote."""
        return self.config.remote

    # ---- Folder Management ----------------------------------------------------------------------------------

    def get_or_create_folder(
            self,
    ) -> str:
        """Get or create the GitMap folder in Portal.

        Returns:
            Folder ID.

        Raises:
            RuntimeError: If folder creation fails.
        """
        folder_name = self.config.project_name

        # Check if folder_id is already stored in config (from previous push)
        if self.remote and self.remote.folder_id:
            return self.remote.folder_id

        try:
            # Check existing folders first
            user = self.gis.users.me
            folders = user.folders

            # Search for existing folder
            for folder in folders:
                # Folder objects have 'title' and 'id' as attributes
                folder_title = getattr(folder, "title", None)
                if folder_title == folder_name:
                    folder_id = getattr(folder, "id", None)
                    if folder_id:
                        return folder_id

            # Try to get folder by searching user's content
            # Sometimes folders aren't in user.folders but exist
            try:
                user_content = user.items()
                for item in user_content:
                    # Check if item is in a folder with matching name
                    item_folder = getattr(item, "ownerFolder", None)
                    if item_folder:
                        # Get folder info
                        folder_info = self.gis.content.get_folder(item_folder, user.username)
                        if folder_info:
                            folder_title = getattr(folder_info, "title", None) or (folder_info.get("title") if isinstance(folder_info, dict) else None)
                            if folder_title == folder_name:
                                folder_id = getattr(folder_info, "id", None) or (folder_info.get("id") if isinstance(folder_info, dict) else None)
                                if folder_id:
                                    return folder_id
            except Exception:
                # If folder search fails, continue to creation
                pass

            # Create new folder using new API
            try:
                result = self.gis.content.folders.create(folder_name)
                if result:
                    # Result might be dict or object with 'id' attribute
                    if isinstance(result, dict):
                        return result.get("id", "")
                    else:
                        return getattr(result, "id", None) or ""
            except Exception as create_error:
                # If creation fails because folder exists, search one more time
                error_msg = str(create_error).lower()
                if "not available" in error_msg or "already exists" in error_msg or "unable to create" in error_msg:
                    # Folder exists but we didn't find it - search all folders again
                    try:
                        folders = user.folders
                        for folder in folders:
                            folder_title = getattr(folder, "title", None)
                            if folder_title == folder_name:
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
                                    folder_obj = self.gis.content.get_folder(item_folder, user.username)
                                    if folder_obj:
                                        folder_title = getattr(folder_obj, "title", None)
                                        if folder_title == folder_name:
                                            folder_id = getattr(folder_obj, "id", None)
                                            if folder_id:
                                                return folder_id
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    
                    # If still not found, the folder exists but we can't locate it
                    msg = f"Folder '{folder_name}' exists in Portal but could not be located automatically. Please check Portal and update config manually if needed."
                    raise RuntimeError(msg) from create_error
                else:
                    # Different error - re-raise
                    msg = f"Failed to create folder '{folder_name}': {create_error}"
                    raise RuntimeError(msg) from create_error

        except Exception as folder_error:
            msg = f"Folder operation failed: {folder_error}"
            raise RuntimeError(msg) from folder_error

    # ---- Push Operations ------------------------------------------------------------------------------------

    def push(
            self,
            branch: str | None = None,
            skip_notifications: bool = False,
    ) -> tuple[Item, dict[str, Any]]:
        """Push branch to Portal.

        Creates or updates a web map item in the GitMap folder
        representing the specified branch.

        Args:
            branch: Branch name (defaults to current branch).
            skip_notifications: If True, skip sending notifications even for production branch.

        Returns:
            Tuple of (created/updated Portal Item, notification status dict).

        Raises:
            RuntimeError: If push fails.
        """
        try:
            branch = branch or self.repo.get_current_branch()
            if not branch:
                msg = "No branch to push (detached HEAD)"
                raise RuntimeError(msg)

            commit_id = self.repo.get_branch_commit(branch)
            if not commit_id:
                msg = f"Branch '{branch}' has no commits"
                raise RuntimeError(msg)

            commit = self.repo.get_commit(commit_id)
            if not commit:
                msg = f"Commit '{commit_id}' not found"
                raise RuntimeError(msg)

            # For main branch, if we have the original item_id, update it directly
            if branch == "main" and self.remote and self.remote.item_id:
                try:
                    original_item = self.gis.content.get(self.remote.item_id)
                    if original_item and original_item.type == "Web Map":
                        updated_item = self._update_webmap_item(original_item, commit.map_data, commit)
                        
                        # Check if this is the production branch and send notifications
                        notification_status = {
                            "attempted": False,
                            "sent": False,
                            "reason": "",
                            "users_notified": [],
                        }
                        
                        if not skip_notifications and self.remote.production_branch and branch == self.remote.production_branch:
                            notification_status["attempted"] = True
                            try:
                                # Check if item is shared with groups
                                # item.sharing is a SharingManager object, not a dict
                                if updated_item.access == "private":
                                    notification_status["reason"] = "Item is private (not shared)"
                                else:
                                    # Try to get groups from item properties
                                    groups = []
                                    try:
                                        if hasattr(updated_item, "properties") and updated_item.properties:
                                            sharing_data = updated_item.properties.get("sharing", {})
                                            if isinstance(sharing_data, dict):
                                                groups = sharing_data.get("groups", [])
                                        
                                        # If not found, query user's groups
                                        if not groups:
                                            user = self.gis.users.me
                                            if user:
                                                user_groups = user.groups
                                                for group in user_groups:
                                                    try:
                                                        group_items = group.content()
                                                        if any(g_item.id == updated_item.id for g_item in group_items):
                                                            groups.append(group.id)
                                                    except Exception:
                                                        continue
                                    except Exception:
                                        groups = []
                                    
                                    if not groups:
                                        notification_status["reason"] = "Item is not shared with any groups"
                                    else:
                                        # Attempt to send notifications
                                        notified_users = notify_item_group_users(
                                            gis=self.gis,
                                            item=updated_item,
                                            subject=f"Production Map Updated: {updated_item.title}",
                                            body=f"The production map '{updated_item.title}' has been updated.\n\n"
                                                 f"Branch: {branch}\n"
                                                 f"Commit: {commit.id[:8]}\n"
                                                 f"Message: {commit.message}\n\n"
                                                 f"View the map: {updated_item.homepage}",
                                        )
                                        if notified_users:
                                            notification_status["sent"] = True
                                            notification_status["users_notified"] = notified_users
                                        else:
                                            notification_status["reason"] = "No users found in groups that have access to the map"
                            except Exception as notify_error:
                                # Don't fail the push if notifications fail
                                notification_status["reason"] = f"Notification error: {notify_error}"
                        
                        return updated_item, notification_status
                except Exception:
                    # Original item not found - fall through to folder-based logic
                    pass

            # Get or create folder (for feature branches or if main item not found)
            folder_id = self.get_or_create_folder()

            # Update config with folder info
            if self.config.remote:
                self.config.remote.folder_id = folder_id
            else:
                self.config.remote = Remote(
                    name="origin",
                    url=self.connection.url,
                    folder_id=folder_id,
                )
            self.repo.update_config(self.config)

            # Check for existing branch item in folder
            existing_item = self._find_branch_item(branch, folder_id)

            if existing_item:
                # Update existing item
                updated_item = self._update_webmap_item(existing_item, commit.map_data, commit)
            else:
                # Create new item
                updated_item = self._create_webmap_item(branch, commit.map_data, commit, folder_id)

            # Check if this is the production branch and send notifications
            notification_status = {
                "attempted": False,
                "sent": False,
                "reason": "",
                "users_notified": [],
            }
            
            if not skip_notifications and self.remote and self.remote.production_branch and branch == self.remote.production_branch:
                notification_status["attempted"] = True
                try:
                    # Check if item is shared with groups
                    # item.sharing is a SharingManager object, not a dict
                    if updated_item.access == "private":
                        notification_status["reason"] = "Item is private (not shared)"
                    else:
                        # Try to get groups from item properties
                        groups = []
                        try:
                            if hasattr(updated_item, "properties") and updated_item.properties:
                                sharing_data = updated_item.properties.get("sharing", {})
                                if isinstance(sharing_data, dict):
                                    groups = sharing_data.get("groups", [])
                            
                            # If not found, query user's groups
                            if not groups:
                                user = self.gis.users.me
                                if user:
                                    user_groups = user.groups
                                    for group in user_groups:
                                        try:
                                            group_items = group.content()
                                            if any(g_item.id == updated_item.id for g_item in group_items):
                                                groups.append(group.id)
                                        except Exception:
                                            continue
                        except Exception:
                            groups = []
                        
                        if not groups:
                            notification_status["reason"] = "Item is not shared with any groups"
                        else:
                            # Attempt to send notifications
                            notified_users = notify_item_group_users(
                                gis=self.gis,
                                item=updated_item,
                                subject=f"Production Map Updated: {updated_item.title}",
                                body=f"The production map '{updated_item.title}' has been updated.\n\n"
                                     f"Branch: {branch}\n"
                                     f"Commit: {commit.id[:8]}\n"
                                     f"Message: {commit.message}\n\n"
                                     f"View the map: {updated_item.homepage}",
                            )
                            if notified_users:
                                notification_status["sent"] = True
                                notification_status["users_notified"] = notified_users
                            else:
                                notification_status["reason"] = "No users found in groups that have access to the map"
                except Exception as notify_error:
                    # Don't fail the push if notifications fail
                    notification_status["reason"] = f"Notification error: {notify_error}"

            return updated_item, notification_status

        except Exception as push_error:
            msg = f"Push failed: {push_error}"
            raise RuntimeError(msg) from push_error

    def _find_branch_item(
            self,
            branch: str,
            folder_id: str,
    ) -> Item | None:
        """Find existing web map item for branch.

        Args:
            branch: Branch name.
            folder_id: Portal folder ID.

        Returns:
            Item if found, None otherwise.
        """
        try:
            user = self.gis.users.me
            items = user.items(folder=folder_id)

            item_title = self._branch_to_item_title(branch)
            for item in items:
                if item.title == item_title and item.type == "Web Map":
                    return item

            return None

        except Exception:
            return None

    def _branch_to_item_title(
            self,
            branch: str,
    ) -> str:
        """Convert branch name to Portal item title.

        Args:
            branch: Branch name.

        Returns:
            Sanitized item title.
        """
        # Replace slashes with underscores for Portal compatibility
        return branch.replace("/", "_")

    def _create_webmap_item(
            self,
            branch: str,
            map_data: dict[str, Any],
            commit: Any,
            folder_id: str,
    ) -> Item:
        """Create new web map item in Portal.

        Args:
            branch: Branch name.
            map_data: Web map JSON.
            commit: Commit object.
            folder_id: Target folder ID.

        Returns:
            Created Item.
        """
        item_title = self._branch_to_item_title(branch)

        item_properties = {
            "title": item_title,
            "type": "Web Map",
            "tags": ["GitMap", f"branch:{branch}", f"commit:{commit.id[:8]}"],
            "description": f"GitMap branch: {branch}\nCommit: {commit.id}\n{commit.message}",
        }

        item = self.gis.content.add(
            item_properties=item_properties,
            data=json.dumps(map_data),
            folder=folder_id,
        )

        return item

    def _update_webmap_item(
            self,
            item: Item,
            map_data: dict[str, Any],
            commit: Any,
    ) -> Item:
        """Update existing web map item.

        Args:
            item: Existing Portal item.
            map_data: New web map JSON.
            commit: Commit object.

        Returns:
            Updated Item.
        """
        # Update item properties
        item.update(
            item_properties={
                "tags": item.tags + [f"commit:{commit.id[:8]}"],
                "description": f"GitMap commit: {commit.id}\n{commit.message}",
            },
            data=json.dumps(map_data),
        )

        return item

    # ---- Pull Operations ------------------------------------------------------------------------------------

    def pull(
            self,
            branch: str | None = None,
    ) -> dict[str, Any]:
        """Pull latest from Portal.

        Fetches the web map JSON from Portal for the specified branch
        and updates the local staging area.

        Args:
            branch: Branch name (defaults to current branch).

        Returns:
            Pulled map data.

        Raises:
            RuntimeError: If pull fails.
        """
        try:
            branch = branch or self.repo.get_current_branch()
            if not branch:
                msg = "No branch to pull (detached HEAD)"
                raise RuntimeError(msg)

            if not self.remote:
                msg = "No remote configured"
                raise RuntimeError(msg)

            # For main branch, if we have the original item_id, pull from it directly
            if branch == "main" and self.remote.item_id:
                try:
                    original_item = self.gis.content.get(self.remote.item_id)
                    if original_item and original_item.type == "Web Map":
                        map_data = original_item.get_data()
                        if not map_data:
                            msg = "Failed to get data from remote item"
                            raise RuntimeError(msg)

                        # Update local index
                        self.repo.update_index(map_data)

                        # Update remote tracking ref
                        self._update_remote_ref(branch, self.repo.get_head_commit() or "")

                        return map_data
                except Exception:
                    # Original item not found - fall through to folder-based logic
                    pass

            folder_id = self.remote.folder_id
            if not folder_id:
                msg = "Remote folder not configured"
                raise RuntimeError(msg)

            # Find branch item
            item = self._find_branch_item(branch, folder_id)
            if not item:
                msg = f"Branch '{branch}' not found in remote"
                raise RuntimeError(msg)

            # Get map data
            map_data = item.get_data()
            if not map_data:
                msg = f"Failed to get data from remote item"
                raise RuntimeError(msg)

            # Update local index
            self.repo.update_index(map_data)

            # Update remote tracking ref
            self._update_remote_ref(branch, self.repo.get_head_commit() or "")

            return map_data

        except Exception as pull_error:
            msg = f"Pull failed: {pull_error}"
            raise RuntimeError(msg) from pull_error

    def _update_remote_ref(
            self,
            branch: str,
            commit_id: str,
    ) -> None:
        """Update remote tracking reference.

        Args:
            branch: Branch name.
            commit_id: Commit ID.
        """
        remote_ref_dir = self.repo.remotes_dir / "origin"
        remote_ref_dir.mkdir(parents=True, exist_ok=True)

        ref_path = remote_ref_dir / branch.replace("/", "_")
        ref_path.write_text(commit_id)

    # ---- Metadata Operations --------------------------------------------------------------------------------

    def push_metadata(
            self,
    ) -> Item:
        """Push repository metadata to Portal.

        Creates/updates the .gitmap_meta item containing branch
        and commit information.

        Returns:
            Metadata Item.
        """
        folder_id = self.get_or_create_folder()

        metadata = {
            "version": "1.0",
            "project_name": self.config.project_name,
            "branches": {},
        }

        # Collect branch info
        for branch in self.repo.list_branches():
            commit_id = self.repo.get_branch_commit(branch)
            metadata["branches"][branch] = {
                "commit_id": commit_id,
            }

        # Find or create metadata item
        existing = self._find_metadata_item(folder_id)

        if existing:
            existing.update(data=json.dumps(metadata))
            return existing
        else:
            item_properties = {
                "title": GITMAP_META_TITLE,
                "type": "Code Attachment",
                "tags": ["GitMap", "metadata"],
            }
            return self.gis.content.add(
                item_properties=item_properties,
                data=json.dumps(metadata),
                folder=folder_id,
            )

    def _find_metadata_item(
            self,
            folder_id: str,
    ) -> Item | None:
        """Find metadata item in folder."""
        try:
            user = self.gis.users.me
            items = user.items(folder=folder_id)

            for item in items:
                if item.title == GITMAP_META_TITLE:
                    return item

            return None
        except Exception:
            return None


