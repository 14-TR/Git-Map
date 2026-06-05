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


PORTAL_CREDENTIAL_ENV_PAIRS = (
    ("PORTAL_USER", "PORTAL_PASSWORD"),
    ("ARCGIS_USERNAME", "ARCGIS_PASSWORD"),
)


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


def resolve_portal_env_credentials() -> dict[str, str | bool | None]:
    """Resolve Portal credentials from supported env var pairs.

    Returns a dictionary describing the resolved pair, whether any pair is
    complete, and whether the environment configuration is invalid.
    """
    pair_states: list[dict[str, str | bool | None]] = []
    for username_var, password_var in PORTAL_CREDENTIAL_ENV_PAIRS:
        username = os.environ.get(username_var)
        password = os.environ.get(password_var)
        pair_states.append(
            {
                "username_var": username_var,
                "username": username,
                "password_var": password_var,
                "password": password,
                "has_username": bool(username),
                "has_password": bool(password),
                "is_complete": bool(username and password),
            }
        )

    complete_pairs = [pair for pair in pair_states if pair["is_complete"]]
    partial_pairs = [
        pair for pair in pair_states if bool(pair["has_username"]) != bool(pair["has_password"])
    ]
    usernames_without_password = [pair for pair in pair_states if pair["has_username"] and not pair["has_password"]]
    passwords_without_username = [pair for pair in pair_states if pair["has_password"] and not pair["has_username"]]

    if len(complete_pairs) > 1:
        first_pair = complete_pairs[0]
        if any(
            pair["username"] != first_pair["username"] or pair["password"] != first_pair["password"]
            for pair in complete_pairs[1:]
        ):
            return {
                "ok": False,
                "kind": "conflicting_pairs",
                "message": "Conflicting Portal credential env pairs are set; keep only one matching pair.",
                "username_var": None,
                "username": None,
                "password_var": None,
                "password": None,
            }

    if usernames_without_password and passwords_without_username:
        return {
            "ok": False,
            "kind": "mixed_pairs",
            "message": (
                "Mixed Portal credential env pairs are set; use either "
                "PORTAL_USER/PORTAL_PASSWORD or ARCGIS_USERNAME/ARCGIS_PASSWORD."
            ),
            "username_var": None,
            "username": None,
            "password_var": None,
            "password": None,
        }

    if partial_pairs:
        partial = partial_pairs[0]
        missing_var = partial["password_var"] if partial["has_username"] else partial["username_var"]
        present_var = partial["username_var"] if partial["has_username"] else partial["password_var"]
        return {
            "ok": False,
            "kind": "incomplete_pair",
            "message": f"Incomplete Portal credentials: found {present_var} but missing {missing_var}",
            "present_var": present_var,
            "missing_var": missing_var,
            "username_var": partial["username_var"] if partial["has_username"] else None,
            "username": partial["username"] if partial["has_username"] else None,
            "password_var": partial["password_var"] if partial["has_password"] else None,
            "password": partial["password"] if partial["has_password"] else None,
        }

    if complete_pairs:
        pair = complete_pairs[0]
        return {
            "ok": True,
            "kind": "complete_pair",
            "message": None,
            "username_var": pair["username_var"],
            "username": pair["username"],
            "password_var": pair["password_var"],
            "password": pair["password"],
        }

    return {
        "ok": True,
        "kind": "no_env_credentials",
        "message": None,
        "username_var": None,
        "username": None,
        "password_var": None,
        "password": None,
    }


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
            env_creds = resolve_portal_env_credentials()
            if not env_creds["ok"]:
                raise RuntimeError(str(env_creds["message"]))
            env_username = env_creds["username"]
            env_password = env_creds["password"]
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
