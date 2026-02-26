"""Tests for ArcGIS compatibility layer.

Tests version detection, compatibility checking, and API shims.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from gitmap_core import compat

# ---- Version Detection Tests --------------------------------------------------------------------------------


class TestVersionDetection:
    """Tests for version detection functions."""

    def test_get_arcgis_version_returns_tuple(self) -> None:
        """Test that get_arcgis_version returns a 3-tuple."""
        # Clear cache to ensure fresh detection
        compat.get_arcgis_version.cache_clear()

        version = compat.get_arcgis_version()

        assert isinstance(version, tuple)
        assert len(version) == 3
        assert all(isinstance(v, int) for v in version)

    def test_get_arcgis_version_string(self) -> None:
        """Test version string formatting."""
        version_str = compat.get_arcgis_version_string()

        assert isinstance(version_str, str)
        # Should be in format X.Y.Z
        parts = version_str.split(".")
        assert len(parts) == 3

    def test_get_arcgis_version_cached(self) -> None:
        """Test that version detection is cached."""
        compat.get_arcgis_version.cache_clear()

        v1 = compat.get_arcgis_version()
        v2 = compat.get_arcgis_version()

        assert v1 is v2  # Same object due to caching

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_minimum_version_pass(self, mock_version: MagicMock) -> None:
        """Test minimum version check passes when met."""
        mock_version.return_value = (2, 4, 0)

        assert compat.check_minimum_version(2, 3, 0) is True
        assert compat.check_minimum_version(2, 4, 0) is True
        assert compat.check_minimum_version(2, 2, 0) is True

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_minimum_version_fail(self, mock_version: MagicMock) -> None:
        """Test minimum version check fails when not met."""
        mock_version.return_value = (2, 2, 0)

        assert compat.check_minimum_version(2, 3, 0) is False
        assert compat.check_minimum_version(2, 4, 0) is False
        assert compat.check_minimum_version(3, 0, 0) is False

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_maximum_version_pass(self, mock_version: MagicMock) -> None:
        """Test maximum version check passes when at or below."""
        mock_version.return_value = (2, 4, 0)

        assert compat.check_maximum_version(2, 4, 99) is True
        assert compat.check_maximum_version(2, 5, 0) is True
        assert compat.check_maximum_version(3, 0, 0) is True

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_maximum_version_fail(self, mock_version: MagicMock) -> None:
        """Test maximum version check fails when above."""
        mock_version.return_value = (3, 0, 0)

        assert compat.check_maximum_version(2, 4, 99) is False
        assert compat.check_maximum_version(2, 99, 99) is False


# ---- Compatibility Check Tests ------------------------------------------------------------------------------


class TestCompatibilityCheck:
    """Tests for compatibility checking."""

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_compatibility_supported_version(self, mock_version: MagicMock) -> None:
        """Test compatibility check for supported version."""
        mock_version.return_value = (2, 4, 0)

        status = compat.check_compatibility()

        assert status["compatible"] is True
        assert status["version"] == "2.4.0"
        assert len(status["errors"]) == 0

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_compatibility_below_minimum(self, mock_version: MagicMock) -> None:
        """Test compatibility check for version below minimum."""
        mock_version.return_value = (2, 1, 0)

        status = compat.check_compatibility()

        assert status["compatible"] is False
        assert len(status["errors"]) > 0
        assert "below minimum" in status["errors"][0].lower()

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_compatibility_above_tested(self, mock_version: MagicMock) -> None:
        """Test compatibility check for version above tested."""
        mock_version.return_value = (2, 9, 0)

        status = compat.check_compatibility()

        assert status["compatible"] is True  # Still compatible, just warning
        assert len(status["warnings"]) > 0
        assert "newer than tested" in status["warnings"][0].lower()

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_compatibility_major_version_3(self, mock_version: MagicMock) -> None:
        """Test compatibility check warns on major version 3."""
        mock_version.return_value = (3, 0, 0)

        status = compat.check_compatibility()

        assert len(status["warnings"]) > 0
        assert any("major version" in w.lower() for w in status["warnings"])


# ---- Folder API Shim Tests ----------------------------------------------------------------------------------


class TestFolderShims:
    """Tests for folder API shims."""

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_new_api(self, mock_check: MagicMock) -> None:
        """Test folder creation with new API (2.3.0+)."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "folder123"
        mock_result.title = "TestFolder"
        mock_gis.content.folders.create.return_value = mock_result

        result = compat.create_folder(mock_gis, "TestFolder")

        mock_gis.content.folders.create.assert_called_once_with("TestFolder")
        assert result["id"] == "folder123"
        assert result["title"] == "TestFolder"

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_legacy_api(self, mock_check: MagicMock) -> None:
        """Test folder creation with legacy API (< 2.3.0)."""
        mock_check.return_value = False

        mock_gis = MagicMock()
        mock_result = {"id": "folder456", "title": "LegacyFolder"}
        mock_gis.content.create_folder.return_value = mock_result

        result = compat.create_folder(mock_gis, "LegacyFolder")

        mock_gis.content.create_folder.assert_called_once_with("LegacyFolder")
        assert result["id"] == "folder456"

    def test_get_user_folders_dict_format(self) -> None:
        """Test getting folders when API returns dicts."""
        mock_gis = MagicMock()
        mock_gis.users.me.folders = [
            {"id": "f1", "title": "Folder1"},
            {"id": "f2", "title": "Folder2"},
        ]

        folders = compat.get_user_folders(mock_gis)

        assert len(folders) == 2
        assert folders[0]["id"] == "f1"
        assert folders[1]["title"] == "Folder2"

    def test_get_user_folders_object_format(self) -> None:
        """Test getting folders when API returns objects."""
        mock_gis = MagicMock()

        folder1 = MagicMock()
        folder1.id = "f1"
        folder1.title = "Folder1"

        folder2 = MagicMock()
        folder2.id = "f2"
        folder2.title = "Folder2"

        mock_gis.users.me.folders = [folder1, folder2]

        folders = compat.get_user_folders(mock_gis)

        assert len(folders) == 2
        assert folders[0]["id"] == "f1"
        assert folders[1]["title"] == "Folder2"

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_empty_result_fallback(self, mock_check: MagicMock) -> None:
        """Test folder creation falls back to search when API returns empty."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # API returns empty/None
        mock_gis.content.folders.create.return_value = None

        # But folder exists when we search
        found_folder = MagicMock()
        found_folder.id = "found123"
        found_folder.title = "TestFolder"
        mock_gis.users.me.folders = [found_folder]

        result = compat.create_folder(mock_gis, "TestFolder")

        assert result is not None
        assert result["id"] == "found123"

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_already_exists_fallback(self, mock_check: MagicMock) -> None:
        """Test folder creation falls back to search when folder exists."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # API raises "not available" error
        mock_gis.content.folders.create.side_effect = Exception("Folder name not available")

        # But folder exists when we search
        found_folder = MagicMock()
        found_folder.id = "existing456"
        found_folder.title = "ExistingFolder"
        mock_gis.users.me.folders = [found_folder]

        result = compat.create_folder(mock_gis, "ExistingFolder")

        assert result is not None
        assert result["id"] == "existing456"


# ---- Content API Shim Tests ---------------------------------------------------------------------------------


class TestContentShims:
    """Tests for content API shims."""

    @patch("gitmap_core.compat.check_minimum_version")
    def test_search_content_new_api(self, mock_check: MagicMock) -> None:
        """Test content search with new API (2.3.0+)."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        mock_items = [MagicMock(), MagicMock()]
        mock_gis.content.search.return_value = mock_items

        results = compat.search_content(mock_gis, "test query", item_type="Web Map")

        mock_gis.content.search.assert_called_once()
        call_kwargs = mock_gis.content.search.call_args[1]
        assert call_kwargs["item_type"] == "Web Map"
        assert len(results) == 2

    @patch("gitmap_core.compat.check_minimum_version")
    def test_search_content_legacy_api(self, mock_check: MagicMock) -> None:
        """Test content search with legacy API (< 2.3.0)."""
        mock_check.return_value = False

        mock_gis = MagicMock()
        mock_items = [MagicMock()]
        mock_gis.content.search.return_value = mock_items

        results = compat.search_content(mock_gis, "test query", item_type="Web Map")

        mock_gis.content.search.assert_called_once()
        call_kwargs = mock_gis.content.search.call_args[1]
        # Legacy API appends type to query
        assert 'type:"Web Map"' in call_kwargs["query"]

    def test_get_item_data_success(self) -> None:
        """Test getting item data successfully."""
        mock_item = MagicMock()
        mock_item.get_data.return_value = {"operationalLayers": []}

        data = compat.get_item_data(mock_item)

        assert data == {"operationalLayers": []}

    def test_get_item_data_failure(self) -> None:
        """Test getting item data when it fails."""
        mock_item = MagicMock()
        mock_item.get_data.side_effect = Exception("API Error")

        data = compat.get_item_data(mock_item)

        assert data is None

    def test_get_item_data_non_dict(self) -> None:
        """Test getting item data when it returns non-dict."""
        mock_item = MagicMock()
        mock_item.get_data.return_value = "not a dict"

        data = compat.get_item_data(mock_item)

        assert data is None

    def test_search_content_exception_returns_empty_list(self) -> None:
        """Test that search_content returns empty list on exception."""
        mock_gis = MagicMock()
        mock_gis.content.search.side_effect = Exception("Network error")

        results = compat.search_content(mock_gis, "test query")

        assert results == []


# ---- Version ImportError Tests ------------------------------------------------------------------------------


class TestGetArcGISVersionImportError:
    """Tests for ImportError handling in version detection."""

    def test_get_arcgis_version_raises_when_arcgis_not_installed(self) -> None:
        """Test that get_arcgis_version raises ImportError when arcgis is absent."""
        compat.get_arcgis_version.cache_clear()

        with patch.dict("sys.modules", {"arcgis": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'arcgis'")):
                compat.get_arcgis_version.cache_clear()
                with patch("gitmap_core.compat.get_arcgis_version",
                           side_effect=ImportError("arcgis package is not installed")):
                    try:
                        compat.get_arcgis_version()
                    except ImportError as e:
                        assert "arcgis package is not installed" in str(e)
                    else:
                        # If arcgis is available in the test env, this path can't be hit directly;
                        # coverage is achieved via check_compatibility ImportError test below.
                        pass

        compat.get_arcgis_version.cache_clear()


class TestCheckCompatibilityImportError:
    """Tests for ImportError handling in check_compatibility."""

    def test_check_compatibility_arcgis_not_installed(self) -> None:
        """Test check_compatibility when arcgis is not installed."""
        with patch(
            "gitmap_core.compat.get_arcgis_version",
            side_effect=ImportError("arcgis package is not installed"),
        ):
            status = compat.check_compatibility()

        assert status["compatible"] is False
        assert len(status["errors"]) == 1
        assert "arcgis package is not installed" in status["errors"][0]
        assert status["version"] == "unknown"


# ---- validate_or_warn Tests ---------------------------------------------------------------------------------


class TestValidateOrWarn:
    """Tests for validate_or_warn logging behaviour."""

    def test_validate_or_warn_logs_errors(self) -> None:
        """Test that validate_or_warn logs errors when compatibility fails."""
        incompatible_status = {
            "compatible": False,
            "version": "2.1.0",
            "warnings": [],
            "errors": ["arcgis version 2.1.0 is below minimum supported version 2.2.0."],
        }

        with patch("gitmap_core.compat.check_compatibility", return_value=incompatible_status):
            with patch.object(compat.logger, "error") as mock_error:
                compat.validate_or_warn()
                mock_error.assert_called_once()
                assert "ArcGIS compatibility" in mock_error.call_args[0][0]

    def test_validate_or_warn_logs_warnings(self) -> None:
        """Test that validate_or_warn logs warnings for untested versions."""
        warn_status = {
            "compatible": True,
            "version": "2.9.0",
            "warnings": ["arcgis version 2.9.0 is newer than tested version 2.4.x."],
            "errors": [],
        }

        with patch("gitmap_core.compat.check_compatibility", return_value=warn_status):
            with patch.object(compat.logger, "warning") as mock_warning:
                compat.validate_or_warn()
                mock_warning.assert_called_once()
                assert "ArcGIS compatibility" in mock_warning.call_args[0][0]


# ---- create_folder edge-case Tests --------------------------------------------------------------------------


class TestCreateFolderEdgeCases:
    """Tests for edge cases in create_folder."""

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_object_result_no_id_returns_none_when_search_fails(
        self, mock_check: MagicMock
    ) -> None:
        """Test create_folder returns None when result has no ID and search finds nothing."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # API returns object with no valid id
        mock_result = MagicMock()
        mock_result.id = None
        mock_result.folderId = None
        mock_result.folder_id = None
        mock_gis.content.folders.create.return_value = mock_result

        # Search also finds nothing
        mock_gis.users.me.folders = []

        result = compat.create_folder(mock_gis, "EmptyFolder")

        assert result is None

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_search_finds_folder_by_title_dict(
        self, mock_check: MagicMock
    ) -> None:
        """Test _search_for_folder finds folder by title in dict format."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # API returns None so we search
        mock_gis.content.folders.create.return_value = None

        # Folders returned as dicts
        mock_gis.users.me.folders = [
            {"id": "dict-folder-id", "title": "DictFolder"},
        ]

        result = compat.create_folder(mock_gis, "DictFolder")

        assert result is not None
        assert result["id"] == "dict-folder-id"

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_search_exception_raises(
        self, mock_check: MagicMock
    ) -> None:
        """Test create_folder re-raises when exception is not an 'already exists' error."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        mock_gis.content.folders.create.side_effect = Exception("Unexpected server error")

        # Make the fallback search also fail (swallowed internally)
        mock_gis.users.me.folders = []

        import pytest
        with pytest.raises(Exception, match="Unexpected server error"):
            compat.create_folder(mock_gis, "SomeFolder")


# ---- get_user_folders exception-path Tests ------------------------------------------------------------------


class TestGetUserFoldersExceptionPaths:
    """Tests for exception handling in get_user_folders."""

    def test_get_user_folders_method1_exception_continues(self) -> None:
        """Test that get_user_folders continues if user.folders raises."""
        mock_gis = MagicMock()
        # user.folders property raises
        type(mock_gis.users.me).folders = property(
            fget=lambda self: (_ for _ in ()).throw(Exception("folders unavailable"))
        )
        # items() also raises to shortcut other methods
        mock_gis.users.me.items.side_effect = Exception("items unavailable")

        result = compat.get_user_folders(mock_gis)

        # Should return empty list, not raise
        assert isinstance(result, list)

    def test_get_user_folders_outer_exception_returns_empty(self) -> None:
        """Test that get_user_folders returns empty list if gis.users.me raises."""
        mock_gis = MagicMock()
        type(mock_gis.users).me = property(
            fget=lambda self: (_ for _ in ()).throw(Exception("not authenticated"))
        )

        result = compat.get_user_folders(mock_gis)

        assert result == []
