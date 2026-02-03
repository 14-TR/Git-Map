"""Tests for the communication module.

Tests cover Portal/AGOL notification helpers using mocked GIS connections.
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch

from communication import (
    _ensure_gis,
    _resolve_group,
    get_group_member_usernames,
    list_groups,
    send_group_notification,
    get_item_group_users,
    notify_item_group_users,
)


class TestEnsureGis:
    """Tests for _ensure_gis validation function."""

    def test_raises_when_gis_module_unavailable(self):
        """Should raise RuntimeError if arcgis module not installed."""
        with patch("communication.GIS", None):
            with pytest.raises(RuntimeError, match="not installed"):
                _ensure_gis(Mock())

    def test_raises_when_gis_is_none(self):
        """Should raise RuntimeError if gis connection is None."""
        with pytest.raises(RuntimeError, match="valid GIS connection"):
            _ensure_gis(None)

    def test_passes_with_valid_gis(self):
        """Should not raise when valid GIS object provided."""
        mock_gis = Mock()
        _ensure_gis(mock_gis)  # Should not raise


class TestResolveGroup:
    """Tests for _resolve_group helper function."""

    def test_resolves_by_id_directly(self):
        """Should return group when found by ID."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group

        result = _resolve_group(mock_gis, "group-123")

        mock_gis.groups.get.assert_called_once_with("group-123")
        assert result is mock_group

    def test_resolves_by_title_search(self):
        """Should search by title when ID lookup fails."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = None
        mock_gis.groups.search.return_value = [mock_group]

        result = _resolve_group(mock_gis, "My Group")

        mock_gis.groups.search.assert_called_once_with('title:"My Group"')
        assert result is mock_group

    def test_returns_none_when_not_found(self):
        """Should return None when group not found by ID or title."""
        mock_gis = Mock()
        mock_gis.groups.get.return_value = None
        mock_gis.groups.search.return_value = []

        result = _resolve_group(mock_gis, "nonexistent")

        assert result is None


class TestGetGroupMemberUsernames:
    """Tests for get_group_member_usernames function."""

    def test_collects_owner(self):
        """Should include group owner in usernames."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner_user",
            "admins": [],
            "users": [],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert "owner_user" in result

    def test_collects_admins_and_users(self):
        """Should include admins and users in results."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": ["admin1", "admin2"],
            "users": ["user1", "user2"],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert set(result) == {"owner", "admin1", "admin2", "user1", "user2"}

    def test_collects_invited_users(self):
        """Should include invited admins and users."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": [],
            "users": [],
            "admins_invited": ["invited_admin"],
            "users_invited": ["invited_user"],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert "invited_admin" in result
        assert "invited_user" in result

    def test_deduplicates_usernames(self):
        """Should return unique usernames only."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "shared_user",
            "admins": ["shared_user"],
            "users": ["shared_user", "unique_user"],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert result == ["shared_user", "unique_user"]

    def test_returns_sorted_usernames(self):
        """Should return usernames in sorted order."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "zack",
            "admins": [],
            "users": ["alice", "bob"],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert result == ["alice", "bob", "zack"]

    def test_raises_when_group_not_found(self):
        """Should raise RuntimeError if group cannot be found."""
        mock_gis = Mock()
        mock_gis.groups.get.return_value = None
        mock_gis.groups.search.return_value = []

        with pytest.raises(RuntimeError, match="not found"):
            get_group_member_usernames(mock_gis, "nonexistent")

    def test_raises_when_no_members(self):
        """Should raise RuntimeError if group has no members."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": None,
            "admins": [],
            "users": [],
        }

        with pytest.raises(RuntimeError, match="No members found"):
            get_group_member_usernames(mock_gis, "empty-group")

    def test_handles_none_values_in_member_lists(self):
        """Should skip None values in member lists."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": [None, "admin1"],
            "users": ["user1", None, ""],
        }

        result = get_group_member_usernames(mock_gis, "group-123")

        assert "owner" in result
        assert "admin1" in result
        assert "user1" in result
        assert None not in result
        assert "" not in result


class TestListGroups:
    """Tests for list_groups function."""

    def test_returns_group_info(self):
        """Should return list of group dictionaries."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_group.id = "group-123"
        mock_group.title = "Test Group"
        mock_group.owner = "owner_user"
        mock_gis.groups.search.return_value = [mock_group]

        result = list_groups(mock_gis)

        assert len(result) == 1
        assert result[0]["id"] == "group-123"
        assert result[0]["title"] == "Test Group"
        assert result[0]["owner"] == "owner_user"

    def test_respects_max_results(self):
        """Should limit results to max_results."""
        mock_gis = Mock()
        mock_groups = [Mock(id=f"g{i}", title=f"Group {i}", owner="owner") for i in range(10)]
        mock_gis.groups.search.return_value = mock_groups

        result = list_groups(mock_gis, max_results=3)

        assert len(result) == 3

    def test_passes_query_to_search(self):
        """Should pass query string to groups.search."""
        mock_gis = Mock()
        mock_gis.groups.search.return_value = []

        list_groups(mock_gis, query="title:MyGroup")

        mock_gis.groups.search.assert_called_once_with("title:MyGroup")

    def test_handles_missing_attributes(self):
        """Should handle groups with missing attributes."""
        mock_gis = Mock()
        mock_group = Mock(spec=[])  # No attributes
        mock_gis.groups.search.return_value = [mock_group]

        result = list_groups(mock_gis)

        assert result[0]["id"] == ""
        assert result[0]["title"] == ""
        assert result[0]["owner"] == ""

    def test_raises_on_search_error(self):
        """Should raise RuntimeError if search fails."""
        mock_gis = Mock()
        mock_gis.groups.search.side_effect = Exception("Search failed")

        with pytest.raises(RuntimeError, match="Failed to search groups"):
            list_groups(mock_gis)


class TestSendGroupNotification:
    """Tests for send_group_notification function."""

    def test_sends_notification_to_group(self):
        """Should call group.notify with correct parameters."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": [],
            "users": ["user1"],
        }

        result = send_group_notification(
            mock_gis, "group-123", "Subject", "Body text"
        )

        mock_group.notify.assert_called_once()
        call_kwargs = mock_group.notify.call_args[1]
        assert call_kwargs["subject"] == "Subject"
        assert call_kwargs["message"] == "Body text"
        assert set(call_kwargs["users"]) == {"owner", "user1"}

    def test_sends_to_specific_users(self):
        """Should send to specified users when provided."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group

        result = send_group_notification(
            mock_gis, "group-123", "Subject", "Body",
            users=["specific_user1", "specific_user2"]
        )

        call_kwargs = mock_group.notify.call_args[1]
        assert set(call_kwargs["users"]) == {"specific_user1", "specific_user2"}

    def test_returns_notified_users(self):
        """Should return list of users that were notified."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group

        result = send_group_notification(
            mock_gis, "group-123", "Subject", "Body",
            users=["user1", "user2"]
        )

        assert set(result) == {"user1", "user2"}

    def test_raises_when_group_not_found(self):
        """Should raise RuntimeError if group not found."""
        mock_gis = Mock()
        mock_gis.groups.get.return_value = None
        mock_gis.groups.search.return_value = []

        with pytest.raises(RuntimeError, match="not found"):
            send_group_notification(mock_gis, "nonexistent", "Subject", "Body")

    def test_raises_when_no_target_users(self):
        """Should raise RuntimeError if no users to notify."""
        mock_gis = Mock()
        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": None,
            "admins": [],
            "users": [],
        }

        # Error comes from get_group_member_usernames (called by send_group_notification)
        with pytest.raises(RuntimeError, match="No members found"):
            send_group_notification(mock_gis, "group-123", "Subject", "Body")


class TestGetItemGroupUsers:
    """Tests for get_item_group_users function."""

    def test_returns_empty_for_private_item(self):
        """Should return empty list for private items."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "private"

        result = get_item_group_users(mock_gis, mock_item)

        assert result == []

    def test_returns_empty_when_no_groups(self):
        """Should return empty list when item has no group shares."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "public"
        mock_item.properties = None
        mock_gis.users.me = None

        result = get_item_group_users(mock_gis, mock_item)

        assert result == []

    def test_collects_users_from_item_properties(self):
        """Should collect users from groups in item properties."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "org"
        mock_item.properties = {"sharing": {"groups": ["group-123"]}}

        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": [],
            "users": ["user1"],
        }

        result = get_item_group_users(mock_gis, mock_item)

        assert set(result) == {"owner", "user1"}

    def test_deduplicates_across_groups(self):
        """Should deduplicate users across multiple groups."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "org"
        mock_item.properties = {"sharing": {"groups": ["group-1", "group-2"]}}

        mock_group1 = Mock()
        mock_group1.get_members.return_value = {
            "owner": "shared_user",
            "admins": [],
            "users": ["user1"],
        }
        mock_group2 = Mock()
        mock_group2.get_members.return_value = {
            "owner": "shared_user",
            "admins": [],
            "users": ["user2"],
        }
        mock_gis.groups.get.side_effect = [mock_group1, mock_group2]

        result = get_item_group_users(mock_gis, mock_item)

        # shared_user should appear only once
        assert result.count("shared_user") == 1
        assert set(result) == {"shared_user", "user1", "user2"}

    def test_handles_inaccessible_groups(self):
        """Should skip groups that raise exceptions."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "org"
        mock_item.properties = {"sharing": {"groups": ["group-ok", "group-fail"]}}

        mock_group_ok = Mock()
        mock_group_ok.get_members.return_value = {
            "owner": "owner",
            "admins": [],
            "users": [],
        }
        mock_gis.groups.get.side_effect = [mock_group_ok, Exception("Access denied")]

        result = get_item_group_users(mock_gis, mock_item)

        assert "owner" in result


class TestNotifyItemGroupUsers:
    """Tests for notify_item_group_users function."""

    def test_returns_empty_for_private_item(self):
        """Should return empty list for private items."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "private"

        result = notify_item_group_users(mock_gis, mock_item, "Subject", "Body")

        assert result == []

    def test_returns_empty_when_no_groups(self):
        """Should return empty list when item has no group shares."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "public"
        mock_item.properties = None
        mock_gis.users.me = None

        result = notify_item_group_users(mock_gis, mock_item, "Subject", "Body")

        assert result == []

    def test_notifies_all_group_users(self):
        """Should notify users from all groups sharing the item."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "org"
        mock_item.properties = {"sharing": {"groups": ["group-123"]}}

        mock_group = Mock()
        mock_gis.groups.get.return_value = mock_group
        mock_group.get_members.return_value = {
            "owner": "owner",
            "admins": [],
            "users": ["user1"],
        }

        result = notify_item_group_users(mock_gis, mock_item, "Subject", "Body")

        mock_group.notify.assert_called()
        assert set(result) == {"owner", "user1"}

    def test_continues_on_notify_failure(self):
        """Should continue notifying other groups if one fails."""
        mock_gis = Mock()
        mock_item = Mock()
        mock_item.access = "org"
        mock_item.properties = {"sharing": {"groups": ["group-1", "group-2"]}}

        mock_group1 = Mock()
        mock_group1.get_members.return_value = {
            "owner": "owner1",
            "admins": [],
            "users": [],
        }
        mock_group1.notify.side_effect = Exception("Notify failed")

        mock_group2 = Mock()
        mock_group2.get_members.return_value = {
            "owner": "owner2",
            "admins": [],
            "users": [],
        }

        mock_gis.groups.get.side_effect = [mock_group1, mock_group1, mock_group2, mock_group2]

        result = notify_item_group_users(mock_gis, mock_item, "Subject", "Body")

        # Should still include users from both groups even if notify fails for one
        assert "owner1" in result
        assert "owner2" in result
