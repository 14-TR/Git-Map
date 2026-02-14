"""Tests for remote operations module.

Tests RemoteOperations class including push, pull, folder management,
and metadata operations. Uses mocks to avoid actual Portal/ArcGIS API calls.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - unittest.mock: Mocking Portal/Repository objects
    - gitmap_core.remote: Module under test
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from unittest.mock import patch

import pytest

from gitmap_core.models import Commit
from gitmap_core.models import Remote
from gitmap_core.models import RepoConfig
from gitmap_core.remote import (
    GITMAP_FOLDER_SUFFIX,
    GITMAP_META_TITLE,
    RemoteOperations,
)


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def sample_map_data() -> dict[str, Any]:
    """Sample web map data."""
    return {
        "operationalLayers": [
            {"id": "layer-1", "title": "Roads"},
        ],
        "baseMap": {"baseMapLayers": []},
        "spatialReference": {"wkid": 102100},
    }


@pytest.fixture
def sample_commit(sample_map_data: dict[str, Any]) -> Commit:
    """Sample commit object."""
    return Commit(
        id="abc123def456",
        message="Test commit message",
        author="test_user",
        timestamp="2024-01-15T10:30:00",
        parent="parent123",
        map_data=sample_map_data,
    )


@pytest.fixture
def mock_repo_config() -> RepoConfig:
    """Mock repository configuration."""
    return RepoConfig(
        project_name="TestProject",
        user_name="test_user",
        user_email="test@example.com",
        remote=Remote(
            name="origin",
            url="https://portal.example.com/arcgis",
            folder_id="folder-123",
            item_id="original-item-id",
        ),
    )


@pytest.fixture
def mock_repo_config_no_remote() -> RepoConfig:
    """Mock repository configuration without remote."""
    return RepoConfig(
        project_name="TestProject",
        user_name="test_user",
        user_email="test@example.com",
        remote=None,
    )


@pytest.fixture
def mock_repository(
    mock_repo_config: RepoConfig, sample_commit: Commit
) -> MagicMock:
    """Create mock Repository."""
    repo = MagicMock()
    repo.get_config.return_value = mock_repo_config
    repo.get_current_branch.return_value = "main"
    repo.get_branch_commit.return_value = sample_commit.id
    repo.get_commit.return_value = sample_commit
    repo.get_head_commit.return_value = sample_commit.id
    repo.list_branches.return_value = ["main", "feature/test"]
    repo.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
    repo.remotes_dir.mkdir(parents=True)
    return repo


@pytest.fixture
def mock_connection() -> MagicMock:
    """Create mock PortalConnection."""
    conn = MagicMock()
    conn.url = "https://portal.example.com/arcgis"

    # Mock GIS object
    gis = MagicMock()
    conn.gis = gis

    # Mock user
    user = MagicMock()
    user.username = "test_user"
    user.folders = []
    user.items.return_value = []
    user.groups = []
    gis.users.me = user

    # Mock content
    content = MagicMock()
    gis.content = content

    return conn


@pytest.fixture
def mock_portal_item(sample_map_data: dict[str, Any]) -> MagicMock:
    """Create mock Portal Item."""
    item = MagicMock()
    item.id = "item-123"
    item.title = "Test Map"
    item.type = "Web Map"
    item.tags = ["GitMap"]
    item.access = "public"
    item.homepage = "https://portal.example.com/home/item.html?id=item-123"
    item.get_data.return_value = sample_map_data
    item.update.return_value = True
    return item


@pytest.fixture
def remote_ops(
    mock_repository: MagicMock, mock_connection: MagicMock
) -> RemoteOperations:
    """Create RemoteOperations instance."""
    return RemoteOperations(mock_repository, mock_connection)


# ---- RemoteOperations Init Tests ----------------------------------------------------------------------------


class TestRemoteOperationsInit:
    """Tests for RemoteOperations initialization."""

    def test_init_with_repo_and_connection(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test initializing RemoteOperations."""
        ops = RemoteOperations(mock_repository, mock_connection)

        assert ops.repo == mock_repository
        assert ops.connection == mock_connection
        mock_repository.get_config.assert_called_once()

    def test_gis_property(self, remote_ops: RemoteOperations) -> None:
        """Test gis property returns GIS connection."""
        gis = remote_ops.gis

        assert gis == remote_ops.connection.gis

    def test_remote_property(
        self, remote_ops: RemoteOperations, mock_repo_config: RepoConfig
    ) -> None:
        """Test remote property returns configured remote."""
        remote = remote_ops.remote

        assert remote == mock_repo_config.remote
        assert remote.name == "origin"


# ---- Folder Management Tests --------------------------------------------------------------------------------


class TestFolderManagement:
    """Tests for folder management operations."""

    def test_get_or_create_folder_uses_existing_folder_id(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test that existing folder_id is reused."""
        result = remote_ops.get_or_create_folder()

        assert result == "folder-123"

    def test_get_or_create_folder_finds_existing_folder(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test finding existing folder by name."""
        # Set up config without folder_id
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # Mock folder exists
        folder = MagicMock()
        folder.title = "TestProject"
        folder.id = "found-folder-id"
        mock_connection.gis.users.me.folders = [folder]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "found-folder-id"

    def test_get_or_create_folder_creates_new(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test creating new folder when none exists."""
        # Set up config without folder_id
        config = RepoConfig(
            project_name="NewProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # No existing folders
        mock_connection.gis.users.me.folders = []

        # Mock folder creation
        mock_connection.gis.content.folders.create.return_value = {"id": "new-folder-id"}

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "new-folder-id"
        mock_connection.gis.content.folders.create.assert_called_once_with("NewProject")

    def test_get_or_create_folder_handles_creation_with_object_response(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation when API returns object instead of dict."""
        config = RepoConfig(
            project_name="NewProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # Return object with id attribute
        folder_obj = MagicMock()
        folder_obj.id = "obj-folder-id"
        mock_connection.gis.content.folders.create.return_value = folder_obj

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "obj-folder-id"

    def test_get_or_create_folder_handles_empty_creation_result(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test fallback search when folder creation returns result without ID."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # No folders initially
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.return_value = []

        # Creation returns object with no ID
        empty_result = MagicMock()
        empty_result.id = None
        mock_connection.gis.content.folders.create.return_value = empty_result

        # After fallback, folder is found
        found_folder = MagicMock()
        found_folder.title = "TestProject"
        found_folder.id = "fallback-folder-id"
        mock_connection.gis.users.me.folders = [found_folder]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "fallback-folder-id"

    def test_get_or_create_folder_finds_folder_through_user_content(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test finding folder by searching through user content when not in folders list."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # No folders in direct list
        mock_connection.gis.users.me.folders = []

        # Item in folder with matching name
        item_in_folder = MagicMock()
        item_in_folder.ownerFolder = "hidden-folder-id"
        mock_connection.gis.users.me.items.return_value = [item_in_folder]

        # Folder info returns matching folder
        folder_info = MagicMock()
        folder_info.title = "TestProject"
        folder_info.id = "hidden-folder-id"
        mock_connection.gis.content.get_folder.return_value = folder_info

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "hidden-folder-id"

    def test_get_or_create_folder_handles_folder_exists_error_and_finds_it(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test recovery when folder creation fails because folder exists."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # Initially no folders found
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.return_value = []

        # Creation fails with "already exists" error
        mock_connection.gis.content.folders.create.side_effect = Exception(
            "Folder name is not available"
        )

        # On retry, folder is found
        found_folder = MagicMock()
        found_folder.title = "TestProject"
        found_folder.id = "retry-found-folder-id"

        # Use a counter to return empty first, then the folder
        call_count = [0]
        def folders_side_effect():
            call_count[0] += 1
            if call_count[0] > 1:
                return [found_folder]
            return []

        type(mock_connection.gis.users.me).folders = PropertyMock(side_effect=folders_side_effect)

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "retry-found-folder-id"

    def test_get_or_create_folder_raises_when_folder_exists_but_not_locatable(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test error when folder exists but cannot be found after creation fails."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # No folders found ever
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.return_value = []

        # Creation fails with "already exists" error
        mock_connection.gis.content.folders.create.side_effect = Exception(
            "unable to create folder"
        )

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.get_or_create_folder()

        assert "exists in Portal but could not be located" in str(exc_info.value)

    def test_get_or_create_folder_raises_on_creation_error(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test error propagation when folder creation fails with non-exists error."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.return_value = []

        # Creation fails with unexpected error
        mock_connection.gis.content.folders.create.side_effect = Exception(
            "Network error: connection refused"
        )

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.get_or_create_folder()

        assert "Failed to create folder" in str(exc_info.value)

    def test_get_or_create_folder_handles_dict_folder_info(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test finding folder when get_folder returns dict instead of object."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # No folders in direct list
        mock_connection.gis.users.me.folders = []

        # Item in folder
        item_in_folder = MagicMock()
        item_in_folder.ownerFolder = "dict-folder-id"
        mock_connection.gis.users.me.items.return_value = [item_in_folder]

        # Folder info returns dict (not object)
        mock_connection.gis.content.get_folder.return_value = {
            "title": "TestProject",
            "id": "dict-folder-id"
        }

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "dict-folder-id"


# ---- Push Tests ---------------------------------------------------------------------------------------------


class TestPushOperations:
    """Tests for push operations."""

    def test_push_to_existing_original_item(
        self,
        remote_ops: RemoteOperations,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test pushing to original item when on main branch."""
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        item, notification_status = remote_ops.push()

        assert item == mock_portal_item
        mock_portal_item.update.assert_called_once()

    def test_push_creates_new_item(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
        sample_map_data: dict,
    ) -> None:
        """Test push creates new item when none exists."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/new"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        # No existing item in root content
        mock_connection.gis.users.me.items.return_value = []

        # Mock item creation in root content (no folder)
        new_item = MagicMock()
        new_item.id = "new-item-id"
        new_item.access = "private"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        item, notification_status = ops.push()

        assert item == new_item
        mock_connection.gis.content.add.assert_called_once()

    def test_push_updates_existing_branch_item(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
        mock_portal_item: MagicMock,
    ) -> None:
        """Test push updates existing item for branch."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/update"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        # Existing item in folder
        mock_portal_item.title = "feature_update"  # Branch name sanitized
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        item, _ = ops.push()

        assert item == mock_portal_item
        mock_portal_item.update.assert_called_once()

    def test_push_uses_current_branch_by_default(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test push uses current branch when none specified."""
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        remote_ops.push()

        remote_ops.repo.get_current_branch.assert_called()

    def test_push_uses_specified_branch(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
        mock_portal_item: MagicMock,
    ) -> None:
        """Test push uses specified branch."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]
        mock_portal_item.title = "specific_branch"

        ops = RemoteOperations(mock_repository, mock_connection)
        ops.push(branch="specific/branch")

        mock_repository.get_branch_commit.assert_called_with("specific/branch")

    def test_push_raises_for_detached_head(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test push raises error for detached HEAD."""
        remote_ops.repo.get_current_branch.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            remote_ops.push()

        assert "No branch to push" in str(exc_info.value)

    def test_push_raises_for_branch_without_commits(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test push raises error when branch has no commits."""
        remote_ops.repo.get_branch_commit.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            remote_ops.push()

        assert "has no commits" in str(exc_info.value)

    def test_push_raises_when_commit_not_found(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test push raises error when commit not found."""
        remote_ops.repo.get_commit.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            remote_ops.push()

        assert "not found" in str(exc_info.value)

    def test_push_notification_status_not_attempted_by_default(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test push notification not attempted when not production branch."""
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        _, notification_status = remote_ops.push()

        assert notification_status["attempted"] is False

    def test_push_skip_notifications_flag(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test skip_notifications parameter."""
        # Set up as production branch
        remote_ops.config.remote.production_branch = "main"
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        _, notification_status = remote_ops.push(skip_notifications=True)

        assert notification_status["attempted"] is False

    def test_push_notification_attempted_for_production_branch(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test notification is attempted when pushing to production branch."""
        # Set up as production branch
        remote_ops.config.remote.production_branch = "main"
        mock_portal_item.access = "private"  # Private item, no groups
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        _, notification_status = remote_ops.push()

        assert notification_status["attempted"] is True
        assert notification_status["sent"] is False
        assert "private" in notification_status["reason"].lower()

    def test_push_notification_no_groups_shared(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test notification reports no groups when item not shared with any."""
        remote_ops.config.remote.production_branch = "main"
        mock_portal_item.access = "org"
        mock_portal_item.properties = None
        remote_ops.connection.gis.users.me.groups = []
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        _, notification_status = remote_ops.push()

        assert notification_status["attempted"] is True
        assert notification_status["sent"] is False
        assert "not shared with any groups" in notification_status["reason"]

    def test_push_notification_sends_to_group_users(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification sends to users in shared groups."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        mock_portal_item.properties = {"sharing": {"groups": ["group-123"]}}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock notify_item_group_users
        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1", "user2"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True
            assert notification_status["users_notified"] == ["user1", "user2"]

    def test_push_notification_handles_notify_error(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push succeeds even if notification fails."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.properties = {"sharing": {"groups": ["group-123"]}}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock notify to raise exception
        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.side_effect = Exception("Notification service unavailable")

            ops = RemoteOperations(mock_repository, mock_connection)
            item, notification_status = ops.push()

            # Push should succeed
            assert item is not None
            assert notification_status["attempted"] is True
            assert notification_status["sent"] is False
            assert "Notification error" in notification_status["reason"]

    def test_push_notification_queries_user_groups_when_no_properties(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification queries user groups when item.properties lacks sharing data."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # No properties or sharing data in properties
        mock_portal_item.properties = None
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock user and groups
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-456"
        mock_group_item = MagicMock()
        mock_group_item.id = "original-item-id"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        # Mock notify_item_group_users
        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user3", "user4"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True
            assert notification_status["users_notified"] == ["user3", "user4"]
            # Verify notify was called
            mock_notify.assert_called_once()

    def test_push_falls_through_when_original_item_not_found(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push falls through to folder logic when original item fails."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="missing-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item not found
        mock_connection.gis.content.get.side_effect = Exception("Item not found")

        # No existing items in root content
        mock_connection.gis.users.me.items.return_value = []

        # Create new item in root content (no folder)
        new_item = MagicMock()
        new_item.id = "new-item-id"
        new_item.access = "private"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        item, _ = ops.push()

        assert item == new_item
        mock_connection.gis.content.add.assert_called_once()

    def test_push_feature_branch_with_production_config(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test feature branch push doesn't trigger notifications even with production config."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                production_branch="main",  # Production is main, but we're on feature
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        new_item.id = "feature-item-id"
        new_item.access = "private"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        assert notification_status["attempted"] is False


# ---- Pull Tests ---------------------------------------------------------------------------------------------


class TestPullOperations:
    """Tests for pull operations."""

    def test_pull_from_original_item(
        self,
        remote_ops: RemoteOperations,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pulling from original item on main branch."""
        remote_ops.connection.gis.content.get.return_value = mock_portal_item

        result = remote_ops.pull()

        assert result == sample_map_data
        remote_ops.repo.update_index.assert_called_once_with(sample_map_data)

    def test_pull_from_branch_item(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pulling from branch-specific item."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.get_head_commit.return_value = "commit-123"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_portal_item.title = "feature_test"
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.pull()

        assert result == sample_map_data
        mock_repository.update_index.assert_called_once_with(sample_map_data)

    def test_pull_raises_for_detached_head(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test pull raises error for detached HEAD."""
        remote_ops.repo.get_current_branch.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            remote_ops.pull()

        assert "No branch to pull" in str(exc_info.value)

    def test_pull_raises_without_remote(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test pull raises error when no remote configured."""
        config = RepoConfig(project_name="Test", remote=None)
        mock_repository.get_config.return_value = config

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "No remote configured" in str(exc_info.value)

    def test_pull_raises_when_branch_not_found(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test pull raises error when branch not found in remote."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "nonexistent"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # No matching items
        mock_connection.gis.users.me.items.return_value = []

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "not found in remote" in str(exc_info.value)

    def test_pull_raises_when_data_empty(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
    ) -> None:
        """Test pull raises error when item data is empty."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_portal_item.title = "feature_test"
        mock_portal_item.get_data.return_value = None
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "Failed to get data" in str(exc_info.value)

    def test_pull_updates_remote_ref(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull updates remote tracking reference."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="item-123",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_head_commit.return_value = "commit-456"

        temp_dir = Path(tempfile.mkdtemp())
        mock_repository.remotes_dir = temp_dir / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_connection.gis.content.get.return_value = mock_portal_item

        ops = RemoteOperations(mock_repository, mock_connection)
        ops.pull()

        # Check remote ref was created
        ref_path = mock_repository.remotes_dir / "origin" / "main"
        assert ref_path.exists()
        assert ref_path.read_text() == "commit-456"

    def test_pull_from_main_original_item_empty_data_falls_through(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull falls through to folder logic when original item returns empty data."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_head_commit.return_value = "commit-123"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item returns empty data
        original_item = MagicMock()
        original_item.type = "Web Map"
        original_item.get_data.return_value = None
        mock_connection.gis.content.get.return_value = original_item

        # Fallback to folder item with valid data
        folder_item = MagicMock()
        folder_item.title = "main"
        folder_item.type = "Web Map"
        folder_item.get_data.return_value = sample_map_data
        mock_connection.gis.users.me.items.return_value = [folder_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.pull()

        # Should successfully pull from folder fallback
        assert result == sample_map_data
        mock_repository.update_index.assert_called_once_with(sample_map_data)

    def test_pull_from_main_falls_through_on_item_error(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull falls through to folder logic when original item fails."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_head_commit.return_value = "commit-123"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item access fails
        mock_connection.gis.content.get.side_effect = Exception("Item access denied")

        # Fallback to folder-based search
        mock_portal_item.title = "main"
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]
        mock_connection.gis.content.get.side_effect = None  # Reset for folder item
        mock_portal_item.get_data.return_value = sample_map_data

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.pull()

        assert result == sample_map_data
        mock_repository.update_index.assert_called_once_with(sample_map_data)

    def test_pull_raises_without_folder_when_not_main(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test pull raises error for feature branch without folder_id."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id=None,  # No folder configured
                item_id=None,
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "Remote folder not configured" in str(exc_info.value)

    def test_pull_branch_with_slash_updates_ref_correctly(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull correctly names remote ref for branch with slashes."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/add/layers"
        mock_repository.get_head_commit.return_value = "commit-789"

        temp_dir = Path(tempfile.mkdtemp())
        mock_repository.remotes_dir = temp_dir / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_portal_item.title = "feature_add_layers"
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        ops.pull()

        # Check remote ref uses sanitized name
        ref_path = mock_repository.remotes_dir / "origin" / "feature_add_layers"
        assert ref_path.exists()
        assert ref_path.read_text() == "commit-789"


# ---- Branch to Item Title Tests -----------------------------------------------------------------------------


class TestBranchToItemTitle:
    """Tests for branch name to item title conversion."""

    def test_simple_branch_name(self, remote_ops: RemoteOperations) -> None:
        """Test simple branch name conversion."""
        result = remote_ops._branch_to_item_title("main")
        assert result == "main"

    def test_branch_with_slashes(self, remote_ops: RemoteOperations) -> None:
        """Test branch with slashes is sanitized."""
        result = remote_ops._branch_to_item_title("feature/add-layer")
        assert result == "feature_add-layer"

    def test_nested_branch(self, remote_ops: RemoteOperations) -> None:
        """Test deeply nested branch name."""
        result = remote_ops._branch_to_item_title("jig/test/context-coverage")
        assert result == "jig_test_context-coverage"


# ---- Metadata Operations Tests ------------------------------------------------------------------------------


class TestMetadataOperations:
    """Tests for metadata push operations."""

    def test_push_metadata_creates_new(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test pushing metadata creates new item."""
        remote_ops.connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        remote_ops.connection.gis.content.add.return_value = new_item

        result = remote_ops.push_metadata()

        assert result == new_item
        remote_ops.connection.gis.content.add.assert_called_once()
        call_kwargs = remote_ops.connection.gis.content.add.call_args
        assert call_kwargs.kwargs["item_properties"]["title"] == GITMAP_META_TITLE

    def test_push_metadata_updates_existing(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test pushing metadata updates existing item."""
        existing_item = MagicMock()
        existing_item.title = GITMAP_META_TITLE
        remote_ops.connection.gis.users.me.items.return_value = [existing_item]

        result = remote_ops.push_metadata()

        assert result == existing_item
        existing_item.update.assert_called_once()

    def test_push_metadata_includes_branch_info(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test metadata includes branch information."""
        remote_ops.connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        remote_ops.connection.gis.content.add.return_value = new_item

        remote_ops.push_metadata()

        call_kwargs = remote_ops.connection.gis.content.add.call_args
        data = json.loads(call_kwargs.kwargs["data"])
        assert "branches" in data
        assert "main" in data["branches"]


# ---- Item Creation/Update Tests -----------------------------------------------------------------------------


class TestItemCreationUpdate:
    """Tests for internal item creation and update methods."""

    def test_create_webmap_item(
        self,
        remote_ops: RemoteOperations,
        sample_map_data: dict,
        sample_commit: Commit,
    ) -> None:
        """Test creating new web map item."""
        new_item = MagicMock()
        # Mock the new folder-based API
        mock_folder = MagicMock()
        mock_folder.add.return_value = new_item
        remote_ops.connection.gis.content.folders.get.return_value = mock_folder

        result = remote_ops._create_webmap_item(
            branch="feature/test",
            map_data=sample_map_data,
            commit=sample_commit,
            folder_id="folder-123",
        )

        assert result == new_item
        remote_ops.connection.gis.content.folders.get.assert_called_once_with("folder-123")
        mock_folder.add.assert_called_once()
        call_kwargs = mock_folder.add.call_args
        props = call_kwargs.kwargs["item_properties"]
        assert props["title"] == "feature_test"
        assert props["type"] == "Web Map"
        assert "GitMap" in props["tags"]

    def test_update_webmap_item(
        self,
        remote_ops: RemoteOperations,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
        sample_commit: Commit,
    ) -> None:
        """Test updating existing web map item."""
        result = remote_ops._update_webmap_item(
            item=mock_portal_item,
            map_data=sample_map_data,
            commit=sample_commit,
        )

        assert result == mock_portal_item
        mock_portal_item.update.assert_called_once()


# ---- Find Branch Item Tests ---------------------------------------------------------------------------------


class TestFindBranchItem:
    """Tests for finding branch items in folders."""

    def test_find_existing_branch_item(
        self, remote_ops: RemoteOperations, mock_portal_item: MagicMock
    ) -> None:
        """Test finding existing branch item."""
        mock_portal_item.title = "feature_test"
        remote_ops.connection.gis.users.me.items.return_value = [mock_portal_item]

        result = remote_ops._find_branch_item("feature/test", "folder-123")

        assert result == mock_portal_item

    def test_find_branch_item_not_found(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test returns None when branch item not found."""
        remote_ops.connection.gis.users.me.items.return_value = []

        result = remote_ops._find_branch_item("nonexistent", "folder-123")

        assert result is None

    def test_find_branch_item_skips_non_webmap(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test skips non-Web Map items."""
        item = MagicMock()
        item.title = "feature_test"
        item.type = "Feature Service"
        remote_ops.connection.gis.users.me.items.return_value = [item]

        result = remote_ops._find_branch_item("feature/test", "folder-123")

        assert result is None

    def test_find_branch_item_handles_exception(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test returns None on exception."""
        remote_ops.connection.gis.users.me.items.side_effect = Exception("Error")

        result = remote_ops._find_branch_item("feature/test", "folder-123")

        assert result is None


# ---- Find Metadata Item Tests -------------------------------------------------------------------------------


class TestFindMetadataItem:
    """Tests for finding metadata items."""

    def test_find_existing_metadata_item(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test finding existing metadata item."""
        meta_item = MagicMock()
        meta_item.title = GITMAP_META_TITLE
        remote_ops.connection.gis.users.me.items.return_value = [meta_item]

        result = remote_ops._find_metadata_item("folder-123")

        assert result == meta_item

    def test_find_metadata_item_not_found(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test returns None when metadata item not found."""
        remote_ops.connection.gis.users.me.items.return_value = []

        result = remote_ops._find_metadata_item("folder-123")

        assert result is None

    def test_find_metadata_item_handles_exception(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test returns None on exception."""
        remote_ops.connection.gis.users.me.items.side_effect = Exception("Error")

        result = remote_ops._find_metadata_item("folder-123")

        assert result is None


# ---- Constants Tests ----------------------------------------------------------------------------------------


class TestConstants:
    """Tests for module constants."""

    def test_gitmap_meta_title(self) -> None:
        """Test metadata item title constant."""
        assert GITMAP_META_TITLE == ".gitmap_meta"

    def test_gitmap_folder_suffix(self) -> None:
        """Test folder suffix constant."""
        assert GITMAP_FOLDER_SUFFIX == "_GitMap"


# ---- Network Failure Tests ------------------------------------------------------------------------------------


class TestNetworkFailures:
    """Tests for network failure scenarios."""

    def test_get_or_create_folder_handles_network_error_during_search(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation when network error occurs during folder search."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # First call returns folders, second call fails
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.side_effect = Exception("Network timeout")

        # Creation succeeds
        mock_connection.gis.content.folders.create.return_value = {"id": "new-folder-id"}

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "new-folder-id"

    def test_get_or_create_folder_handles_user_content_search_error(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation when user content search fails."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.side_effect = Exception("API error")
        mock_connection.gis.content.folders.create.return_value = {"id": "created-folder-id"}

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "created-folder-id"

    def test_push_handles_content_get_error(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push handles content.get error gracefully."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # content.get fails
        mock_connection.gis.content.get.side_effect = Exception("Connection refused")

        # Falls through to root content, no items found
        mock_connection.gis.users.me.items.return_value = []

        # Create new item
        new_item = MagicMock()
        new_item.id = "new-item-id"
        new_item.access = "private"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        item, _ = ops.push()

        assert item == new_item

    def test_pull_handles_content_get_error(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull falls through when original item content.get fails."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_head_commit.return_value = "commit-123"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item fails
        mock_connection.gis.content.get.side_effect = Exception("Item not accessible")

        # Fallback to folder search
        mock_portal_item.title = "main"
        mock_connection.gis.users.me.items.return_value = [mock_portal_item]
        mock_portal_item.get_data.return_value = sample_map_data

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.pull()

        assert result == sample_map_data


# ---- Edge Cases in Push Notifications ------------------------------------------------------------------------


class TestPushNotificationEdgeCases:
    """Edge case tests for push notifications."""

    def test_push_notification_with_empty_groups_list(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification with explicitly empty groups list."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        mock_portal_item.properties = {"sharing": {"groups": []}}
        mock_connection.gis.content.get.return_value = mock_portal_item

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        assert notification_status["attempted"] is True
        assert notification_status["sent"] is False

    def test_push_notification_no_users_in_groups(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification when no users are found in groups."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        mock_portal_item.properties = {"sharing": {"groups": ["group-123"]}}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock notify returns empty list (no users)
        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = []

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            assert notification_status["attempted"] is True
            assert notification_status["sent"] is False
            assert "No users found" in notification_status["reason"]

    def test_push_notification_with_group_query_exception(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification handles exception when querying groups."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        mock_portal_item.properties = None
        mock_connection.gis.content.get.return_value = mock_portal_item

        # User groups query fails
        mock_user = MagicMock()
        mock_user.groups = Exception("Group query failed")
        mock_connection.gis.users.me = mock_user

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        # Should handle gracefully
        assert notification_status["attempted"] is True


# ---- Root Content Operations Tests ---------------------------------------------------------------------------


class TestRootContentOperations:
    """Tests for root content (no folder) item operations."""

    def test_find_branch_item_in_root_finds_with_prefix(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test finding branch item in root content with project prefix."""
        config = RepoConfig(
            project_name="MyProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        # Item with prefix
        item = MagicMock()
        item.type = "Web Map"
        item.title = "MyProject_feature_test"
        item.tags = ["GitMap"]
        mock_connection.gis.users.me.items.return_value = [item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._find_branch_item_in_root("feature/test")

        assert result == item

    def test_find_branch_item_in_root_no_gitmap_tag(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test finding branch item ignores items without GitMap tag."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        # Item without GitMap tag
        item = MagicMock()
        item.type = "Web Map"
        item.title = "feature_test"
        item.tags = ["SomeOtherTag"]
        mock_connection.gis.users.me.items.return_value = [item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._find_branch_item_in_root("feature/test")

        assert result is None

    def test_find_branch_item_in_root_handles_exception(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test finding branch item handles exceptions gracefully."""
        mock_connection.gis.users.me.items.side_effect = Exception("API Error")

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._find_branch_item_in_root("feature/test")

        assert result is None

    def test_create_webmap_item_in_root(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
        sample_map_data: dict,
    ) -> None:
        """Test creating web map item in root content."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        new_item = MagicMock()
        new_item.id = "root-item-id"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._create_webmap_item_in_root(
            branch="feature/new",
            map_data=sample_map_data,
            commit=sample_commit,
        )

        assert result == new_item
        mock_connection.gis.content.add.assert_called_once()
        call_kwargs = mock_connection.gis.content.add.call_args
        assert call_kwargs.kwargs["item_properties"]["title"] == "TestProject_feature_new"
        assert "GitMap" in call_kwargs.kwargs["item_properties"]["tags"]

    def test_create_webmap_item_in_root_handles_empty_response(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
        sample_map_data: dict,
    ) -> None:
        """Test creating web map item handles API returning unexpected type."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        # API returns string instead of item
        mock_connection.gis.content.add.return_value = "unexpected-string"

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._create_webmap_item_in_root(
            branch="feature/new",
            map_data=sample_map_data,
            commit=sample_commit,
        )

        assert result == "unexpected-string"


# ---- Pull Edge Cases -----------------------------------------------------------------------------------------


class TestPullEdgeCases:
    """Edge case tests for pull operations."""

    def test_pull_updates_index_with_empty_dict(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test pull handles empty dict from get_data - raises because falsy."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.get_head_commit.return_value = "commit-123"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_item = MagicMock()
        mock_item.title = "feature_test"
        mock_item.type = "Web Map"
        mock_item.get_data.return_value = {}  # Empty dict - treated as falsy
        mock_connection.gis.users.me.items.return_value = [mock_item]

        ops = RemoteOperations(mock_repository, mock_connection)

        # Empty dict is falsy so should raise
        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "Failed to get data" in str(exc_info.value)

    def test_pull_handles_get_data_exception(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test pull raises when get_data throws exception."""
        config = RepoConfig(
            project_name="Test",
            remote=Remote(name="origin", url="https://test.com", folder_id="folder-123"),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_item = MagicMock()
        mock_item.title = "feature_test"
        mock_item.type = "Web Map"
        mock_item.get_data.side_effect = Exception("Failed to get data")
        mock_connection.gis.users.me.items.return_value = [mock_item]

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.pull()

        assert "Pull failed" in str(exc_info.value)


# ---- Update Remote Ref Tests ---------------------------------------------------------------------------------


class TestUpdateRemoteRef:
    """Tests for remote ref update functionality."""

    def test_update_remote_ref_creates_directory(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test update remote ref creates directory if not exists."""
        # Use non-existent path
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "new/remotes/path"

        ops = RemoteOperations(mock_repository, mock_connection)
        ops._update_remote_ref("feature/test", "abc123")

        ref_path = mock_repository.remotes_dir / "origin" / "feature_test"
        assert ref_path.exists()
        assert ref_path.read_text() == "abc123"

    def test_update_remote_ref_handles_slash_in_branch(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test remote ref update handles slashes in branch names."""
        temp_dir = Path(tempfile.mkdtemp())
        mock_repository.remotes_dir = temp_dir / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        ops = RemoteOperations(mock_repository, mock_connection)
        ops._update_remote_ref("feature/nested/path", "def456")

        ref_path = mock_repository.remotes_dir / "origin" / "feature_nested_path"
        assert ref_path.exists()
        assert ref_path.read_text() == "def456"


# ---- Folder Management Additional Edge Cases ---------------------------------------------------------------


class TestFolderManagementEdgeCases:
    """Additional edge case tests for folder management."""

    def test_get_or_create_folder_handles_folder_object_without_id(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation when folder object has no ID falls through."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # Create returns folder object without id
        folder_without_id = MagicMock()
        folder_without_id.id = None
        mock_connection.gis.content.folders.create.return_value = folder_without_id

        # On fallback search, find the folder this time
        found_folder = MagicMock()
        found_folder.title = "TestProject"
        found_folder.id = "found-via-fallback"
        mock_connection.gis.users.me.folders = [found_folder]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "found-via-fallback"

    def test_get_or_create_folder_case_insensitive_match(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder search is case insensitive."""
        config = RepoConfig(
            project_name="testproject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # Folder with different case
        folder = MagicMock()
        folder.title = "TestProject"
        folder.id = "case-insensitive-id"
        mock_connection.gis.users.me.folders = [folder]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "case-insensitive-id"

    def test_get_or_create_folder_handles_get_folder_exception(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation handles get_folder exception during search."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # Item in folder but get_folder fails
        item_in_folder = MagicMock()
        item_in_folder.ownerFolder = "hidden-folder-id"
        mock_connection.gis.users.me.items.return_value = [item_in_folder]
        mock_connection.gis.content.get_folder.side_effect = Exception("Folder API error")

        # Creation succeeds
        mock_connection.gis.content.folders.create.return_value = {"id": "new-folder-id"}

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "new-folder-id"


# ---- Production Branch Edge Cases ----------------------------------------------------------------------------


class TestProductionBranchEdgeCases:
    """Edge cases for production branch notification logic."""

    def test_push_notification_on_non_production_branch_no_remote(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push to non-main branch when remote has no production_branch."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                production_branch=None,  # No production branch configured
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        new_item.id = "item-id"
        new_item.access = "public"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        # No notification attempted since no production branch configured
        assert notification_status["attempted"] is False

    def test_push_notification_item_properties_no_sharing(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification when item properties exist but lack sharing key."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # Properties exist but no sharing key
        mock_portal_item.properties = {"someOtherKey": "value"}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock user groups that have access
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-123"
        mock_group_item = MagicMock()
        mock_group_item.id = "original-item-id"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            # Should query user groups as fallback
            assert notification_status["attempted"] is True


# ---- Commit Not Found Edge Cases ------------------------------------------------------------------------------


class TestCommitNotFoundEdgeCases:
    """Edge cases for commit-related errors."""

    def test_push_with_invalid_commit_id_format(
        self, mock_repository: MagicMock, mock_connection: MagicMock, sample_map_data: dict
    ) -> None:
        """Test push handles unusual but valid commit ID formats."""
        # Create commit with unusual ID (shorter)
        commit = Commit(
            id="a1b2c3d4e5f6",  # 12 char hex (shorter than 16)
            message="Test",
            author="user",
            timestamp="2024-01-01T00:00:00",
            parent=None,
            map_data=sample_map_data,
        )

        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = commit.id
        mock_repository.get_commit.return_value = commit

        # Return existing item
        mock_item = MagicMock()
        mock_item.id = "item-123"
        mock_item.type = "Web Map"
        mock_item.access = "private"
        mock_connection.gis.content.get.return_value = mock_item

        ops = RemoteOperations(mock_repository, mock_connection)
        item, _ = ops.push()

        assert item == mock_item
        # Verify update was called - it will try [:8] on 12-char ID
        mock_item.update.assert_called_once()


# ---- Metadata Edge Cases -------------------------------------------------------------------------------------


class TestMetadataEdgeCases:
    """Edge cases for metadata operations."""

    def test_push_metadata_handles_folder_error(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test metadata push handles folder creation error."""
        # get_or_create_folder raises
        remote_ops.get_or_create_folder = MagicMock(
            side_effect=RuntimeError("Folder error")
        )

        with pytest.raises(RuntimeError):
            remote_ops.push_metadata()

    def test_push_metadata_with_no_branches(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test metadata push with repository having no branches."""
        remote_ops.repo.list_branches.return_value = []
        remote_ops.repo.get_branch_commit.return_value = None
        remote_ops.connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        remote_ops.connection.gis.content.add.return_value = new_item

        result = remote_ops.push_metadata()

        assert result == new_item
        # Verify add was called
        call_kwargs = remote_ops.connection.gis.content.add.call_args
        data = json.loads(call_kwargs.kwargs["data"])
        assert data["branches"] == {}


# ---- Folder Fallback Search Tests ----------------------------------------------------------------------------


class TestFolderFallbackSearch:
    """Tests for folder fallback search scenarios."""

    def test_folder_creation_fallback_search_through_items(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test fallback searches through items when folder not in list."""
        config = RepoConfig(
            project_name="HiddenProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # No folder in direct list
        # But we have items in folders
        item1 = MagicMock()
        item1.ownerFolder = "folder-aaa"

        mock_connection.gis.users.me.items.return_value = [item1]

        # First get_folder returns some other folder
        def get_folder_side_effect(folder_id, username):
            if folder_id == "folder-aaa":
                folder = MagicMock()
                folder.title = "HiddenProject"  # This matches!
                folder.id = "found-via-items"
                return folder
            return None

        mock_connection.gis.content.get_folder.side_effect = get_folder_side_effect

        # But folder creation fails with exists error
        mock_connection.gis.content.folders.create.side_effect = Exception(
            "Folder name is not available"
        )

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        # Should find via items fallback
        assert result == "found-via-items"

    def test_folder_creation_with_nonexistent_error_code(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation with error code that doesn't match 'exists' patterns."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []
        mock_connection.gis.users.me.items.return_value = []

        # Creation fails with unexpected error (not 'exists' related)
        mock_connection.gis.content.folders.create.side_effect = Exception(
            "Permission denied"
        )

        ops = RemoteOperations(mock_repository, mock_connection)

        with pytest.raises(RuntimeError) as exc_info:
            ops.get_or_create_folder()

        assert "Failed to create folder" in str(exc_info.value)

    def test_folder_get_returns_none(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder creation when get_folder returns None."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # Item in folder but get_folder returns None
        item_in_folder = MagicMock()
        item_in_folder.ownerFolder = "some-folder"
        mock_connection.gis.users.me.items.return_value = [item_in_folder]
        mock_connection.gis.content.get_folder.return_value = None

        # Folder creation succeeds
        mock_connection.gis.content.folders.create.return_value = {"id": "new-folder"}

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "new-folder"


# ---- Item Creation Fallback Tests ----------------------------------------------------------------------------


class TestItemCreationFallback:
    """Tests for item creation fallback between folder API versions."""

    def test_create_webmap_item_legacy_api_fallback(
        self,
        remote_ops: RemoteOperations,
        sample_map_data: dict,
        sample_commit: Commit,
    ) -> None:
        """Test item creation falls back to legacy API when folder.add fails."""
        # Mock folder API throws AttributeError (older API)
        mock_folder = MagicMock()
        mock_folder.add.side_effect = AttributeError("no folder.add")
        remote_ops.connection.gis.content.folders.get.return_value = mock_folder

        # Legacy API should work
        legacy_item = MagicMock()
        remote_ops.connection.gis.content.add.return_value = legacy_item

        result = remote_ops._create_webmap_item(
            branch="feature/test",
            map_data=sample_map_data,
            commit=sample_commit,
            folder_id="folder-123",
        )

        assert result == legacy_item
        # Verify legacy add was called with folder parameter
        call_kwargs = remote_ops.connection.gis.content.add.call_args
        assert call_kwargs.kwargs["folder"] == "folder-123"

    def test_create_webmap_item_legacy_api_typeerror_fallback(
        self,
        remote_ops: RemoteOperations,
        sample_map_data: dict,
        sample_commit: Commit,
    ) -> None:
        """Test item creation falls back to legacy API when folder.add throws TypeError."""
        # Mock folder API throws TypeError
        mock_folder = MagicMock()
        mock_folder.add.side_effect = TypeError("folder.add not callable")
        remote_ops.connection.gis.content.folders.get.return_value = mock_folder

        # Legacy API should work
        legacy_item = MagicMock()
        remote_ops.connection.gis.content.add.return_value = legacy_item

        result = remote_ops._create_webmap_item(
            branch="feature/test",
            map_data=sample_map_data,
            commit=sample_commit,
            folder_id="folder-123",
        )

        assert result == legacy_item


# ---- Additional Notification Edge Cases -----------------------------------------------------------------------


class TestAdditionalNotificationEdgeCases:
    """Additional edge case tests for notifications."""

    def test_notification_user_query_exception_continues(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification handles exception during user group query."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # Empty sharing data in properties
        mock_portal_item.properties = {}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # User exists but groups throws exception
        mock_user = MagicMock()
        mock_user.groups = Exception("Cannot load groups")
        mock_connection.gis.users.me = mock_user

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        # Should handle gracefully and continue
        assert notification_status["attempted"] is True
        assert notification_status["sent"] is False

    def test_notification_item_has_no_properties_attribute(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification when item lacks properties attribute entirely."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # No properties attribute at all
        del mock_portal_item.properties
        mock_connection.gis.content.get.return_value = mock_portal_item

        # User has groups
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-999"
        mock_group_item = MagicMock()
        mock_group_item.id = "original-item-id"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user-x"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True


# ---- Root Content Push Tests ----------------------------------------------------------------------------------


class TestRootContentPush:
    """Tests for push operations using root content (no folder)."""

    def test_push_to_root_content_new_item(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push creates new item in root content when no existing item."""
        config = RepoConfig(
            project_name="RootProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item exists but get_data returns None (empty)
        original_item = MagicMock()
        original_item.type = "Web Map"
        original_item.get_data.return_value = None

        # No existing items in root content
        mock_connection.gis.users.me.items.return_value = []

        # Create new in root
        new_item = MagicMock()
        new_item.id = "root-new-id"
        new_item.access = "public"
        new_item.tags = ["GitMap"]  # Simulate returned item has GitMap tag

        def content_add(**kwargs):
            return new_item

        mock_connection.gis.content.add.side_effect = content_add

        ops = RemoteOperations(mock_repository, mock_connection)
        result_item, _ = ops.push()

        assert result_item == new_item

    def test_push_to_root_content_existing_item(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push updates existing item in root content."""
        config = RepoConfig(
            project_name="RootProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="original-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item fails
        mock_connection.gis.content.get.side_effect = Exception("Not found")

        # Existing item in root content
        existing_item = MagicMock()
        existing_item.type = "Web Map"
        existing_item.title = "RootProject_main"
        existing_item.tags = ["GitMap"]
        existing_item.access = "org"
        mock_connection.gis.users.me.items.return_value = [existing_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result_item, _ = ops.push()

        # Should update existing
        existing_item.update.assert_called_once()
        assert result_item == existing_item


# ---- Pull from Main Fallback Tests --------------------------------------------------------------------------


class TestPullFromMainFallback:
    """Tests for pull fallback from main branch."""

    def test_pull_main_falls_through_when_original_empty_data(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_map_data: dict,
    ) -> None:
        """Test pull from main falls through when original item has empty data."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="main-item-id",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_head_commit.return_value = "head-commit"
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # Original item returns empty data
        original = MagicMock()
        original.type = "Web Map"
        original.get_data.return_value = ""  # Empty string
        mock_connection.gis.content.get.return_value = original

        # Folder item has data
        folder_item = MagicMock()
        folder_item.title = "main"
        folder_item.type = "Web Map"
        folder_item.get_data.return_value = sample_map_data
        mock_connection.gis.users.me.items.return_value = [folder_item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.pull()

        assert result == sample_map_data


# ---- Non-Main Branch Notification Tests -----------------------------------------------------------------------


class TestNonMainBranchNotifications:
    """Tests for notification logic when pushing to non-main branch."""

    def test_push_feature_branch_with_production_notification_not_triggered(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification is NOT triggered for feature branch even with production config."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="item-id",
                production_branch="main",  # Production is main
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "feature/test"  # NOT main
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        # No existing item in root
        mock_connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        new_item.id = "new-item"
        new_item.access = "public"
        mock_connection.gis.content.add.return_value = new_item

        ops = RemoteOperations(mock_repository, mock_connection)
        _, notification_status = ops.push()

        # Notification should NOT be attempted since branch != production_branch
        assert notification_status["attempted"] is False

    def test_push_main_with_production_triggers_notification_public_access(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification triggered for main branch with production config, public access."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        new_item.id = "item-123"
        new_item.access = "public"  # Public item
        new_item.title = "Test Map"
        new_item.homepage = "https://test.com/home"
        new_item.tags = ["GitMap"]
        mock_connection.gis.content.add.return_value = new_item

        # Mock user with groups
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-1"
        mock_group_item = MagicMock()
        mock_group_item.id = "item-123"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1", "user2"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True
            assert len(notification_status["users_notified"]) == 2

    def test_push_main_with_production_handles_notification_failure(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test push succeeds even if notification fails for main/production branch."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                folder_id="folder-123",
                item_id="item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit
        mock_repository.remotes_dir = Path(tempfile.mkdtemp()) / "remotes"
        mock_repository.remotes_dir.mkdir(parents=True)

        mock_connection.gis.users.me.items.return_value = []

        new_item = MagicMock()
        new_item.id = "item-123"
        new_item.access = "public"
        new_item.title = "Test Map"
        new_item.homepage = "https://test.com/home"
        new_item.tags = ["GitMap"]
        mock_connection.gis.content.add.return_value = new_item

        # Mock user with groups
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-1"
        mock_group_item = MagicMock()
        mock_group_item.id = "item-123"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        # Notification fails with exception
        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.side_effect = Exception("Notification service down")

            ops = RemoteOperations(mock_repository, mock_connection)
            item, notification_status = ops.push()

            # Push should succeed despite notification failure
            assert item == new_item
            assert notification_status["attempted"] is True
            assert "Notification error" in notification_status["reason"]


# ---- Additional Root Content Item Tests ----------------------------------------------------------------------


class TestRootContentItemDetails:
    """Additional tests for root content item edge cases."""

    def test_find_branch_item_in_root_matches_without_prefix(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test finding branch item in root matches title without prefix."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        # Item without prefix but with GitMap tag
        item = MagicMock()
        item.type = "Web Map"
        item.title = "feature_simple"
        item.tags = ["GitMap"]
        mock_connection.gis.users.me.items.return_value = [item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._find_branch_item_in_root("feature/simple")

        assert result == item

    def test_find_branch_item_in_root_empty_tags(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test finding branch item handles empty tags list."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com"),
        )
        mock_repository.get_config.return_value = config

        # Item with empty tags
        item = MagicMock()
        item.type = "Web Map"
        item.title = "feature_test"
        item.tags = []  # Empty
        mock_connection.gis.users.me.items.return_value = [item]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops._find_branch_item_in_root("feature/test")

        assert result is None


# ---- Additional Folder Search Edge Cases --------------------------------------------------------------------


class TestAdditionalFolderSearchEdgeCases:
    """Additional folder search edge cases."""

    def test_folder_search_item_get_folder_returns_dict(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder search when get_folder returns dict instead of object."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config
        mock_connection.gis.users.me.folders = []

        # Item in folder
        item_in_folder = MagicMock()
        item_in_folder.ownerFolder = "dict-folder"
        mock_connection.gis.users.me.items.return_value = [item_in_folder]

        # get_folder returns dict
        mock_connection.gis.content.get_folder.return_value = {
            "title": "TestProject",
            "id": "dict-id"
        }

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "dict-id"

    def test_folder_search_case_difference_only(
        self, mock_repository: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test folder search matches with case difference only."""
        config = RepoConfig(
            project_name="TESTPROJECT",
            remote=Remote(name="origin", url="https://test.com", folder_id=None),
        )
        mock_repository.get_config.return_value = config

        # Folder with different case
        folder = MagicMock()
        folder.title = "testproject"
        folder.id = "case-diff-id"
        mock_connection.gis.users.me.folders = [folder]

        ops = RemoteOperations(mock_repository, mock_connection)
        result = ops.get_or_create_folder()

        assert result == "case-diff-id"


# ---- Notification Sharing Data Type Tests ---------------------------------------------------------------------


class TestNotificationSharingDataTypes:
    """Tests for notification with various sharing data types."""

    def test_notification_sharing_data_not_dict(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification when sharing data in properties is not a dict."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # Sharing data is NOT a dict (it's a string)
        mock_portal_item.properties = {"sharing": "not-a-dict"}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # User has groups with the item
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-1"
        mock_group_item = MagicMock()
        mock_group_item.id = "original-item-id"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            # Should fall through to group query
            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True

    def test_notification_properties_has_sharing_string(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification when properties has sharing as string (not dict)."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # sharing key exists but value is a string
        mock_portal_item.properties = {"sharing": "public"}
        mock_connection.gis.content.get.return_value = mock_portal_item

        # User has groups with the item
        mock_user = MagicMock()
        mock_group = MagicMock()
        mock_group.id = "group-1"
        mock_group_item = MagicMock()
        mock_group_item.id = "original-item-id"
        mock_group.content.return_value = [mock_group_item]
        mock_user.groups = [mock_group]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            # Should fall through to group query
            assert notification_status["attempted"] is True

    def test_notification_user_groups_query_with_item_in_group(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification queries user groups and finds item in group."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        # No sharing in properties
        mock_portal_item.properties = None
        mock_connection.gis.content.get.return_value = mock_portal_item

        # Mock user with groups that contain the item
        mock_user = MagicMock()
        mock_group1 = MagicMock()
        mock_group1.id = "group-1"
        mock_group1_item = MagicMock()
        mock_group1_item.id = "original-item-id"
        mock_group1.content.return_value = [mock_group1_item]

        mock_group2 = MagicMock()
        mock_group2.id = "group-2"
        mock_group2_item = MagicMock()
        mock_group2_item.id = "other-item"  # Different item
        mock_group2.content.return_value = [mock_group2_item]

        mock_user.groups = [mock_group1, mock_group2]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            # Should find item in group-1 and send notification
            assert notification_status["attempted"] is True
            assert notification_status["sent"] is True

    def test_notification_user_groups_query_handles_group_exception(
        self,
        mock_repository: MagicMock,
        mock_connection: MagicMock,
        mock_portal_item: MagicMock,
        sample_commit: Commit,
    ) -> None:
        """Test notification handles exception when querying group content."""
        config = RepoConfig(
            project_name="TestProject",
            remote=Remote(
                name="origin",
                url="https://test.com",
                item_id="original-item-id",
                production_branch="main",
            ),
        )
        mock_repository.get_config.return_value = config
        mock_repository.get_current_branch.return_value = "main"
        mock_repository.get_branch_commit.return_value = sample_commit.id
        mock_repository.get_commit.return_value = sample_commit

        mock_portal_item.access = "org"
        mock_portal_item.id = "original-item-id"
        mock_portal_item.title = "Test Map"
        mock_portal_item.homepage = "https://test.com/item"
        mock_portal_item.properties = None
        mock_connection.gis.content.get.return_value = mock_portal_item

        # First group raises exception
        mock_user = MagicMock()
        mock_group1 = MagicMock()
        mock_group1.id = "group-1"
        mock_group1.content.side_effect = Exception("Group API error")

        # Second group has the item
        mock_group2 = MagicMock()
        mock_group2.id = "group-2"
        mock_group2_item = MagicMock()
        mock_group2_item.id = "original-item-id"
        mock_group2.content.return_value = [mock_group2_item]

        mock_user.groups = [mock_group1, mock_group2]
        mock_connection.gis.users.me = mock_user

        with patch("gitmap_core.remote.notify_item_group_users") as mock_notify:
            mock_notify.return_value = ["user1"]

            ops = RemoteOperations(mock_repository, mock_connection)
            _, notification_status = ops.push()

            # Should continue to second group
            assert notification_status["attempted"] is True


# ---- Metadata Item Exception Handling ------------------------------------------------------------------------


class TestMetadataItemExceptionHandling:
    """Tests for metadata item exception handling."""

    def test_find_metadata_item_raises_on_query(
        self, remote_ops: RemoteOperations
    ) -> None:
        """Test _find_metadata_item handles exception and returns None."""
        # items() raises exception
        remote_ops.connection.gis.users.me.items.side_effect = Exception("Query failed")

        result = remote_ops._find_metadata_item("folder-123")

        assert result is None
