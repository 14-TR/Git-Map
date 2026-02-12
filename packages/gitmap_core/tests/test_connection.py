"""Tests for the connection module.

Covers:
    - Environment file loading
    - PortalConnection dataclass and methods
    - Connection factory functions

Uses mocks to avoid actual ArcGIS API calls.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from gitmap_core.connection import (
    PortalConnection,
    _load_env_file,
    get_agol_connection,
    get_connection,
)

if TYPE_CHECKING:
    pass


# ---- Fixtures -----------------------------------------------------------------------------------------


@pytest.fixture
def mock_gis_class():
    """Create a mock GIS class for testing."""
    with patch("arcgis.gis.GIS", autospec=False) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.users.me = None
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def mock_gis_with_user():
    """Create a mock GIS class that returns a logged-in user."""
    with patch("arcgis.gis.GIS", autospec=False) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.users.me.username = "test_user"
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("ARCGIS_USERNAME=file_user\nARCGIS_PASSWORD=file_pass\n")
    return env_file


# ---- _load_env_file Tests -------------------------------------------------------------------------


class TestLoadEnvFile:
    """Tests for _load_env_file function."""

    def test_load_env_file_no_dotenv(self):
        """Test that function handles missing dotenv gracefully."""
        with patch("gitmap_core.connection.load_dotenv", None):
            # Should not raise
            _load_env_file()

    def test_load_env_file_explicit_path(self, temp_env_file):
        """Test loading from explicit path."""
        with patch("gitmap_core.connection.load_dotenv") as mock_load:
            _load_env_file(temp_env_file)
            mock_load.assert_called_once_with(temp_env_file, override=True)

    def test_load_env_file_explicit_path_not_exists(self, tmp_path):
        """Test explicit path that doesn't exist."""
        with patch("gitmap_core.connection.load_dotenv") as mock_load:
            nonexistent = tmp_path / "nonexistent.env"
            _load_env_file(nonexistent)
            mock_load.assert_not_called()

    def test_load_env_file_cwd(self, tmp_path, monkeypatch):
        """Test loading from current working directory."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST=value\n")
        monkeypatch.chdir(tmp_path)

        with patch("gitmap_core.connection.load_dotenv") as mock_load:
            _load_env_file()
            mock_load.assert_called_once_with(env_file, override=True)

    def test_load_env_file_parent_search(self, tmp_path, monkeypatch):
        """Test searching parent directories for .env."""
        # Create nested structure
        parent = tmp_path / "parent"
        child = parent / "child"
        child.mkdir(parents=True)

        env_file = parent / ".env"
        env_file.write_text("PARENT_TEST=value\n")

        monkeypatch.chdir(child)

        with patch("gitmap_core.connection.load_dotenv") as mock_load:
            _load_env_file()
            mock_load.assert_called_once_with(env_file, override=True)

    def test_load_env_file_no_file_found(self, tmp_path, monkeypatch):
        """Test when no .env file exists anywhere."""
        # Create isolated directory with no .env
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        monkeypatch.chdir(isolated)

        with patch("gitmap_core.connection.load_dotenv") as mock_load:
            _load_env_file()
            mock_load.assert_not_called()


# ---- PortalConnection Tests -----------------------------------------------------------------------


class TestPortalConnection:
    """Tests for PortalConnection dataclass."""

    def test_init_defaults(self):
        """Test default initialization."""
        conn = PortalConnection(url="https://test.portal.com")
        assert conn.url == "https://test.portal.com"
        assert conn.username is None
        assert conn._gis is None

    def test_init_with_username(self):
        """Test initialization with username."""
        conn = PortalConnection(url="https://test.portal.com", username="testuser")
        assert conn.username == "testuser"

    def test_gis_property_not_connected(self):
        """Test gis property raises when not connected."""
        conn = PortalConnection(url="https://test.portal.com")
        with pytest.raises(RuntimeError, match="Not connected"):
            _ = conn.gis

    def test_gis_property_connected(self, mock_gis_class):
        """Test gis property returns connection when connected."""
        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()

        gis = conn.gis
        assert gis is not None
        assert gis == mock_gis_class.return_value

    def test_is_connected_false(self):
        """Test is_connected returns False initially."""
        conn = PortalConnection(url="https://test.portal.com")
        assert conn.is_connected is False

    def test_is_connected_true(self, mock_gis_class):
        """Test is_connected returns True after connect."""
        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()
        assert conn.is_connected is True

    def test_connect_with_password(self, mock_gis_class):
        """Test connect with username and password."""
        conn = PortalConnection(url="https://test.portal.com", username="testuser")
        result = conn.connect(password="testpass")

        mock_gis_class.assert_called_once_with(
            url="https://test.portal.com",
            username="testuser",
            password="testpass",
        )
        assert result == mock_gis_class.return_value

    def test_connect_with_env_vars(self, mock_gis_class, monkeypatch):
        """Test connect using environment variables."""
        monkeypatch.setenv("ARCGIS_USERNAME", "env_user")
        monkeypatch.setenv("ARCGIS_PASSWORD", "env_pass")

        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()

        mock_gis_class.assert_called_once_with(
            url="https://test.portal.com",
            username="env_user",
            password="env_pass",
        )
        assert conn.username == "env_user"

    def test_connect_with_portal_env_vars(self, mock_gis_class, monkeypatch):
        """Test connect using PORTAL_USER/PORTAL_PASSWORD env vars."""
        monkeypatch.setenv("PORTAL_USER", "portal_user")
        monkeypatch.setenv("PORTAL_PASSWORD", "portal_pass")

        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()

        mock_gis_class.assert_called_once_with(
            url="https://test.portal.com",
            username="portal_user",
            password="portal_pass",
        )

    def test_connect_anonymous(self, mock_gis_class, monkeypatch):
        """Test anonymous connection (no credentials)."""
        # Clear any env vars
        monkeypatch.delenv("ARCGIS_USERNAME", raising=False)
        monkeypatch.delenv("ARCGIS_PASSWORD", raising=False)
        monkeypatch.delenv("PORTAL_USER", raising=False)
        monkeypatch.delenv("PORTAL_PASSWORD", raising=False)

        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()

        mock_gis_class.assert_called_once_with(url="https://test.portal.com")

    def test_connect_pro_auth_sets_username(self, mock_gis_with_user, monkeypatch):
        """Test Pro authentication sets username from logged-in user."""
        monkeypatch.delenv("ARCGIS_USERNAME", raising=False)
        monkeypatch.delenv("ARCGIS_PASSWORD", raising=False)
        monkeypatch.delenv("PORTAL_USER", raising=False)
        monkeypatch.delenv("PORTAL_PASSWORD", raising=False)

        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()

        assert conn.username == "test_user"

    def test_connect_failure(self, monkeypatch):
        """Test connect raises RuntimeError on failure."""
        monkeypatch.delenv("ARCGIS_USERNAME", raising=False)
        monkeypatch.delenv("ARCGIS_PASSWORD", raising=False)

        with patch("arcgis.gis.GIS", side_effect=Exception("Connection refused")):
            conn = PortalConnection(url="https://bad.portal.com")

            with pytest.raises(RuntimeError, match="Failed to connect"):
                conn.connect()

    def test_disconnect(self, mock_gis_class):
        """Test disconnect clears connection."""
        conn = PortalConnection(url="https://test.portal.com")
        conn.connect()
        assert conn.is_connected is True

        conn.disconnect()
        assert conn.is_connected is False
        assert conn._gis is None


# ---- Factory Function Tests -----------------------------------------------------------------------


class TestGetConnection:
    """Tests for get_connection factory function."""

    def test_get_connection_default_url(self, mock_gis_class):
        """Test get_connection with default AGOL URL."""
        conn = get_connection()

        assert conn.url == "https://www.arcgis.com"
        assert conn.is_connected is True

    def test_get_connection_custom_url(self, mock_gis_class):
        """Test get_connection with custom portal URL."""
        conn = get_connection(url="https://custom.portal.com")

        assert conn.url == "https://custom.portal.com"
        mock_gis_class.assert_called()

    def test_get_connection_with_credentials(self, mock_gis_class):
        """Test get_connection with username and password."""
        conn = get_connection(
            url="https://test.portal.com",
            username="testuser",
            password="testpass",
        )

        mock_gis_class.assert_called_once_with(
            url="https://test.portal.com",
            username="testuser",
            password="testpass",
        )
        assert conn.username == "testuser"

    def test_get_connection_failure_propagates(self):
        """Test connection failure raises RuntimeError."""
        with patch("arcgis.gis.GIS", side_effect=Exception("Auth failed")):
            with pytest.raises(RuntimeError):
                get_connection(username="bad", password="creds")


class TestGetAgolConnection:
    """Tests for get_agol_connection convenience function."""

    def test_get_agol_connection_default(self, mock_gis_class):
        """Test get_agol_connection uses AGOL URL."""
        conn = get_agol_connection()

        assert conn.url == "https://www.arcgis.com"
        assert conn.is_connected is True

    def test_get_agol_connection_with_credentials(self, mock_gis_class):
        """Test get_agol_connection with credentials."""
        conn = get_agol_connection(username="agol_user", password="agol_pass")

        mock_gis_class.assert_called_once_with(
            url="https://www.arcgis.com",
            username="agol_user",
            password="agol_pass",
        )
