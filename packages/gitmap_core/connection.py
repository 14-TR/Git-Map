"""Portal and ArcGIS Online authentication module.

Handles authentication to ArcGIS Portal and ArcGIS Online (AGOL)
using the ArcGIS API for Python.

Execution Context:
    Library module - imported by remote operations

Dependencies:
    - arcgis: GIS authentication and Portal interaction
    - python-dotenv: Load environment variables from .env file

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if TYPE_CHECKING:
    from arcgis.gis import GIS


# ---- Environment Loading ---------------------------------------------------------------------------------------


def _load_env_file(
        env_path: Path | None = None,
) -> None:
    """Load environment variables from .env file.

    Searches for .env file in:
    1. Specified path (if provided)
    2. Current working directory
    3. Parent directories up to workspace root

    Args:
        env_path: Explicit path to .env file (optional).
    """
    if load_dotenv is None:
        return

    if env_path:
        if env_path.exists():
            load_dotenv(env_path, override=True)
        return

    # Try current directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
        return

    # Try parent directories (up to 3 levels)
    current = Path.cwd()
    for _ in range(3):
        parent = current.parent
        parent_env = parent / ".env"
        if parent_env.exists():
            load_dotenv(parent_env, override=True)
            return
        current = parent


# ---- Connection Classes -------------------------------------------------------------------------------------


@dataclass
class PortalConnection:
    """Manages authenticated connection to ArcGIS Portal or AGOL.

    Attributes:
        url: Portal URL (use 'https://www.arcgis.com' for AGOL).
        username: Portal username.
        _gis: Cached GIS connection object.
    """

    url: str
    username: str | None = None
    _gis: GIS | None = None

    @property
    def gis(
            self,
    ) -> GIS:
        """Get authenticated GIS connection.

        Returns:
            Authenticated GIS object.

        Raises:
            RuntimeError: If connection fails.
        """
        if self._gis is None:
            msg = "Not connected. Call connect() first."
            raise RuntimeError(msg)
        return self._gis

    @property
    def is_connected(
            self,
    ) -> bool:
        """Check if connected to Portal.

        Returns:
            True if connected, False otherwise.
        """
        return self._gis is not None

    def connect(
            self,
            password: str | None = None,
    ) -> GIS:
        """Establish connection to Portal.

        Attempts connection in order:
        1. Username/password if provided
        2. Environment variables (ARCGIS_USERNAME, ARCGIS_PASSWORD) from .env file
        3. Pro authentication (if running in ArcGIS Pro)
        4. Anonymous access

        Args:
            password: Portal password (optional).

        Returns:
            Authenticated GIS object.

        Raises:
            RuntimeError: If connection fails.
        """
        try:
            from arcgis.gis import GIS

            # Load .env file if available
            _load_env_file()

            # Try username/password authentication
            if self.username and password:
                self._gis = GIS(
                    url=self.url,
                    username=self.username,
                    password=password,
                )
                return self._gis

            # Try environment variables (from .env or shell)
            # Check both PORTAL_USER/PORTAL_PASSWORD and ARCGIS_USERNAME/ARCGIS_PASSWORD
            env_username = os.environ.get("PORTAL_USER") or os.environ.get("ARCGIS_USERNAME")
            env_password = os.environ.get("PORTAL_PASSWORD") or os.environ.get("ARCGIS_PASSWORD")
            if env_username and env_password:
                self._gis = GIS(
                    url=self.url,
                    username=env_username,
                    password=env_password,
                )
                self.username = env_username
                return self._gis

            # Try Pro authentication or anonymous
            self._gis = GIS(url=self.url)
            if self._gis.users.me:
                self.username = self._gis.users.me.username
            return self._gis

        except Exception as connection_error:
            msg = f"Failed to connect to Portal at {self.url}: {connection_error}"
            raise RuntimeError(msg) from connection_error

    def disconnect(
            self,
    ) -> None:
        """Disconnect from Portal."""
        self._gis = None


# ---- Connection Functions -----------------------------------------------------------------------------------


def get_connection(
        url: str = "https://www.arcgis.com",
        username: str | None = None,
        password: str | None = None,
) -> PortalConnection:
    """Create and authenticate a Portal connection.

    Args:
        url: Portal URL. Defaults to ArcGIS Online.
        username: Portal username (optional).
        password: Portal password (optional).

    Returns:
        Authenticated PortalConnection.

    Raises:
        RuntimeError: If connection fails.
    """
    connection = PortalConnection(url=url, username=username)
    connection.connect(password=password)
    return connection


def get_agol_connection(
        username: str | None = None,
        password: str | None = None,
) -> PortalConnection:
    """Create connection to ArcGIS Online.

    Convenience function for AGOL connections.

    Args:
        username: AGOL username (optional).
        password: AGOL password (optional).

    Returns:
        Authenticated PortalConnection to AGOL.
    """
    return get_connection(
        url="https://www.arcgis.com",
        username=username,
        password=password,
    )


