"""Tests for ArcGIS compatibility layer.

Tests version detection, compatibility checking, and API shims.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock
from unittest.mock import patch


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

    def test_search_content_exception_returns_empty(self) -> None:
        """Test that search_content returns empty list when API raises."""
        mock_gis = MagicMock()
        mock_gis.content.search.side_effect = Exception("Network error")

        results = compat.search_content(mock_gis, "test query")

        assert results == []


# ---- Version Detection Edge Cases ---------------------------------------------------------------------------


class TestVersionDetectionEdgeCases:
    """Tests for edge cases in version detection."""

    def test_get_arcgis_version_import_error(self) -> None:
        """Test that ImportError is raised when arcgis is not installed."""
        import pytest

        compat.get_arcgis_version.cache_clear()

        # Hide all arcgis sub-modules from sys.modules so `import arcgis` fails
        arcgis_keys = [k for k in sys.modules if k == "arcgis" or k.startswith("arcgis.")]
        saved = {k: sys.modules.pop(k) for k in arcgis_keys}

        try:
            # Also patch the real __import__ only for the 'arcgis' name
            real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

            def _fake_import(name, *args, **kwargs):
                if name == "arcgis":
                    raise ImportError("No module named 'arcgis'")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=_fake_import):
                with pytest.raises(ImportError, match="arcgis package is not installed"):
                    compat.get_arcgis_version()
        finally:
            compat.get_arcgis_version.cache_clear()
            sys.modules.update(saved)

    @patch("gitmap_core.compat.get_arcgis_version")
    def test_check_compatibility_import_error(self, mock_version: MagicMock) -> None:
        """Test check_compatibility when arcgis import fails."""
        mock_version.side_effect = ImportError("arcgis package is not installed")

        status = compat.check_compatibility()

        assert status["compatible"] is False
        assert any("arcgis" in e.lower() for e in status["errors"])

    @patch("gitmap_core.compat.check_compatibility")
    def test_validate_or_warn_logs_errors(self, mock_check: MagicMock) -> None:
        """Test validate_or_warn logs errors when incompatible."""
        mock_check.return_value = {
            "compatible": False,
            "version": "2.0.0",
            "errors": ["version 2.0.0 is below minimum 2.2.0"],
            "warnings": [],
        }

        with patch("gitmap_core.compat.logger") as mock_logger:
            compat.validate_or_warn()
            mock_logger.error.assert_called_once()
            assert "compatibility" in mock_logger.error.call_args[0][0].lower()

    @patch("gitmap_core.compat.check_compatibility")
    def test_validate_or_warn_logs_warnings(self, mock_check: MagicMock) -> None:
        """Test validate_or_warn logs warnings when version is above tested."""
        mock_check.return_value = {
            "compatible": True,
            "version": "2.9.0",
            "errors": [],
            "warnings": ["version 2.9.0 is newer than tested"],
        }

        with patch("gitmap_core.compat.logger") as mock_logger:
            compat.validate_or_warn()
            mock_logger.warning.assert_called_once()
            assert "compatibility" in mock_logger.warning.call_args[0][0].lower()


# ---- Folder Creation Edge Cases -----------------------------------------------------------------------------


class TestFolderCreationEdgeCases:
    """Tests for edge cases in folder creation."""

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_object_result_no_id_falls_through(
        self, mock_check: MagicMock
    ) -> None:
        """Test _extract_folder_info returns None for object with no valid id."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # Return an object where id/folderId/folder_id are all None/falsy
        no_id_result = MagicMock(spec=[])  # spec=[] prevents auto-attribute creation
        mock_gis.content.folders.create.return_value = no_id_result

        # Also make search_for_folder find nothing
        mock_gis.users.me.folders = []

        result = compat.create_folder(mock_gis, "TestFolder")

        # Falls all the way through to return None
        assert result is None

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_search_finds_dict_folder(
        self, mock_check: MagicMock
    ) -> None:
        """Test _search_for_folder finds folder when list returns dicts."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # Creation returns nothing useful
        mock_gis.content.folders.create.return_value = None

        # But the folder appears as a dict in user.folders
        mock_gis.users.me.folders = [
            {"id": "dict-folder-id", "title": "MyFolder"},
        ]

        result = compat.create_folder(mock_gis, "MyFolder")

        assert result is not None
        assert result["id"] == "dict-folder-id"

    @patch("gitmap_core.compat.check_minimum_version")
    def test_create_folder_search_finds_object_folder(
        self, mock_check: MagicMock
    ) -> None:
        """Test _search_for_folder finds folder when list returns objects."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # Creation returns nothing useful
        mock_gis.content.folders.create.return_value = None

        # But the folder appears as an object in user.folders
        folder_obj = MagicMock()
        folder_obj.title = "ObjFolder"
        folder_obj.id = "obj-folder-id"
        mock_gis.users.me.folders = [folder_obj]

        result = compat.create_folder(mock_gis, "ObjFolder")

        assert result is not None
        assert result["id"] == "obj-folder-id"


# ---- get_user_folders Edge Cases ----------------------------------------------------------------------------


class TestGetUserFoldersEdgeCases:
    """Tests for edge cases in get_user_folders."""

    def test_get_user_folders_method1_exception_falls_through(self) -> None:
        """Test that Method 1 exception is swallowed and returns empty list."""
        mock_gis = MagicMock()
        # user.folders raises
        type(mock_gis.users.me).folders = property(
            lambda self: (_ for _ in ()).throw(Exception("API down"))
        )
        # user.items() also raises to avoid Method 3 complicating things
        mock_gis.users.me.items.side_effect = Exception("also down")

        with patch("gitmap_core.compat.check_minimum_version", return_value=False):
            result = compat.get_user_folders(mock_gis)

        assert isinstance(result, list)

    @patch("gitmap_core.compat.check_minimum_version")
    def test_get_user_folders_includes_method2_results(
        self, mock_check: MagicMock
    ) -> None:
        """Test Method 2 (gis.content.folders.list) is used when version >= 2.3.0."""
        mock_check.return_value = True

        mock_gis = MagicMock()
        # Method 1 returns one folder
        mock_gis.users.me.folders = [{"id": "f1", "title": "Folder1"}]
        # Method 2 returns a different folder
        method2_folder = MagicMock()
        method2_folder.id = "f2"
        method2_folder.title = "Folder2"
        mock_gis.content.folders.list.return_value = [method2_folder]
        # Method 3: no extra items
        mock_gis.users.me.items.return_value = []

        result = compat.get_user_folders(mock_gis)

        ids = {f["id"] for f in result}
        assert "f1" in ids
        assert "f2" in ids

    @patch("gitmap_core.compat.check_minimum_version")
    def test_get_user_folders_method3_uses_get_folder_info(
        self, mock_check: MagicMock
    ) -> None:
        """Test Method 3 calls get_folder and adds folder info when found."""
        mock_check.return_value = False  # skip Method 2

        mock_gis = MagicMock()
        mock_gis.users.me.folders = []

        # Method 3: one item with an ownerFolder
        item = MagicMock()
        item.ownerFolder = "folder-abc"
        mock_gis.users.me.items.return_value = [item]

        # get_folder returns folder info dict
        mock_gis.content.get_folder.return_value = {"id": "folder-abc", "title": "FromItem"}

        result = compat.get_user_folders(mock_gis)

        ids = {f["id"] for f in result}
        assert "folder-abc" in ids
