"""ArcGIS API compatibility layer.

Provides version detection and shims for different arcgis package versions.
Supports arcgis 2.2.x through 2.4.x with graceful fallbacks.

Execution Context:
    Library module - imported by modules that interact with arcgis

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from arcgis.gis import GIS

logger = logging.getLogger(__name__)


# ---- Version Detection --------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_arcgis_version() -> tuple[int, int, int]:
    """Get the installed arcgis package version.

    Returns:
        Tuple of (major, minor, patch) version numbers.

    Raises:
        ImportError: If arcgis package is not installed.
    """
    try:
        import arcgis
        version_str = getattr(arcgis, "__version__", "0.0.0")
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split("-")[0].split("+")[0]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except ImportError as e:
        raise ImportError("arcgis package is not installed") from e


def get_arcgis_version_string() -> str:
    """Get the installed arcgis package version as a string.

    Returns:
        Version string (e.g., "2.4.0").
    """
    major, minor, patch = get_arcgis_version()
    return f"{major}.{minor}.{patch}"


def check_minimum_version(min_major: int, min_minor: int = 0, min_patch: int = 0) -> bool:
    """Check if installed arcgis meets minimum version requirement.

    Args:
        min_major: Minimum major version.
        min_minor: Minimum minor version.
        min_patch: Minimum patch version.

    Returns:
        True if installed version meets or exceeds minimum.
    """
    major, minor, patch = get_arcgis_version()
    installed = (major, minor, patch)
    required = (min_major, min_minor, min_patch)
    return installed >= required


def check_maximum_version(max_major: int, max_minor: int = 99, max_patch: int = 99) -> bool:
    """Check if installed arcgis is at or below maximum version.

    Args:
        max_major: Maximum major version.
        max_minor: Maximum minor version.
        max_patch: Maximum patch version.

    Returns:
        True if installed version is at or below maximum.
    """
    major, minor, patch = get_arcgis_version()
    installed = (major, minor, patch)
    maximum = (max_major, max_minor, max_patch)
    return installed <= maximum


# ---- Version Constants --------------------------------------------------------------------------------------


# Minimum supported version
MIN_SUPPORTED_VERSION = (2, 2, 0)

# Maximum tested version (warn above this)
MAX_TESTED_VERSION = (2, 4, 99)

# Version where folders API changed
FOLDERS_API_CHANGE_VERSION = (2, 3, 0)


# ---- Compatibility Check ------------------------------------------------------------------------------------


def check_compatibility() -> dict[str, Any]:
    """Check arcgis package compatibility and return status.

    Returns:
        Dict with keys:
            - compatible: bool - True if version is supported
            - version: str - Installed version string
            - warnings: list[str] - Any compatibility warnings
            - errors: list[str] - Any compatibility errors
    """
    result = {
        "compatible": True,
        "version": "unknown",
        "warnings": [],
        "errors": [],
    }

    try:
        version = get_arcgis_version()
        result["version"] = get_arcgis_version_string()

        # Check minimum version
        if not check_minimum_version(*MIN_SUPPORTED_VERSION):
            result["compatible"] = False
            min_ver = ".".join(str(v) for v in MIN_SUPPORTED_VERSION)
            result["errors"].append(
                f"arcgis version {result['version']} is below minimum supported version {min_ver}. "
                f"Please upgrade: pip install --upgrade arcgis"
            )

        # Check if above tested version (warning only)
        if not check_maximum_version(*MAX_TESTED_VERSION):
            max_ver = ".".join(str(v) for v in MAX_TESTED_VERSION[:2]) + ".x"
            result["warnings"].append(
                f"arcgis version {result['version']} is newer than tested version {max_ver}. "
                f"GitMap may work but has not been validated against this version."
            )

        # Check for major version 3+ (future breaking changes)
        if version[0] >= 3:
            result["warnings"].append(
                f"arcgis version {result['version']} is a major version upgrade. "
                f"Some APIs may have changed. Please report any issues."
            )

    except ImportError as e:
        result["compatible"] = False
        result["errors"].append(str(e))

    return result


def validate_or_warn() -> None:
    """Validate arcgis compatibility and log warnings/errors.

    Call this at module import time to surface compatibility issues early.
    Does not raise - just logs warnings.
    """
    status = check_compatibility()

    for error in status["errors"]:
        logger.error(f"ArcGIS compatibility: {error}")

    for warning in status["warnings"]:
        logger.warning(f"ArcGIS compatibility: {warning}")

    if status["compatible"]:
        logger.debug(f"ArcGIS version {status['version']} is compatible")


# ---- Folder API Shims ---------------------------------------------------------------------------------------


def create_folder(gis: GIS, folder_name: str) -> dict[str, Any] | None:
    """Create a folder in Portal with version-appropriate API.

    Args:
        gis: Authenticated GIS connection.
        folder_name: Name for the new folder.

    Returns:
        Dict with folder info including 'id', or None if creation failed.

    Note:
        - arcgis >= 2.3.0: Uses gis.content.folders.create()
        - arcgis < 2.3.0: Uses gis.content.create_folder()

    The function will search for the folder after creation if the API
    returns an empty result (common on some Portal versions).
    """
    def _extract_folder_info(result: Any) -> dict[str, Any] | None:
        """Extract folder info from API result."""
        if not result:
            return None
        if isinstance(result, dict):
            folder_id = result.get("id") or result.get("folderId") or result.get("folder_id")
            if folder_id:
                return {"id": folder_id, "title": result.get("title", folder_name)}
        else:
            # Object with attributes - try multiple attribute names
            folder_id = (
                getattr(result, "id", None) or
                getattr(result, "folderId", None) or
                getattr(result, "folder_id", None)
            )
            if folder_id:
                return {"id": folder_id, "title": getattr(result, "title", folder_name)}
        return None

    def _search_for_folder() -> dict[str, Any] | None:
        """Search for folder in user's folders after creation."""
        try:
            user = gis.users.me
            # Refresh folder list
            folders = user.folders
            for folder in folders:
                if isinstance(folder, dict):
                    if folder.get("title") == folder_name:
                        return {"id": folder.get("id"), "title": folder_name}
                else:
                    if getattr(folder, "title", None) == folder_name:
                        return {"id": getattr(folder, "id", None), "title": folder_name}
        except Exception:
            pass
        return None

    try:
        result = None

        if check_minimum_version(*FOLDERS_API_CHANGE_VERSION):
            # New API (2.3.0+)
            result = gis.content.folders.create(folder_name)
        else:
            # Legacy API (< 2.3.0)
            result = gis.content.create_folder(folder_name)

        # Try to extract folder info from result
        folder_info = _extract_folder_info(result)
        if folder_info and folder_info.get("id"):
            return folder_info

        # If result was empty/missing ID, search for the folder
        # (some Portal versions create the folder but return empty result)
        logger.debug(f"Folder creation returned no ID, searching for folder '{folder_name}'...")
        folder_info = _search_for_folder()
        if folder_info and folder_info.get("id"):
            logger.debug(f"Found folder '{folder_name}' with ID {folder_info['id']}")
            return folder_info

        return None

    except Exception as e:
        error_msg = str(e).lower()
        # If folder already exists, try to find it
        if "not available" in error_msg or "already exists" in error_msg or "unable to create" in error_msg:
            logger.debug(f"Folder '{folder_name}' may already exist, searching...")
            folder_info = _search_for_folder()
            if folder_info and folder_info.get("id"):
                return folder_info
        logger.debug(f"Folder creation failed: {e}")
        raise


def get_user_folders(gis: GIS) -> list[dict[str, Any]]:
    """Get user's folders with version-appropriate API.

    Tries multiple approaches to ensure folder discovery works across
    different Portal versions and configurations.

    Args:
        gis: Authenticated GIS connection.

    Returns:
        List of folder dicts with 'id' and 'title' keys.
    """
    result = []
    seen_ids: set[str] = set()

    def _add_folder(folder: Any) -> None:
        """Extract and add folder info if not already seen."""
        if isinstance(folder, dict):
            fid = folder.get("id") or folder.get("folderId")
            title = folder.get("title") or folder.get("name")
        else:
            fid = getattr(folder, "id", None) or getattr(folder, "folderId", None)
            title = getattr(folder, "title", None) or getattr(folder, "name", None)

        if fid and fid not in seen_ids:
            seen_ids.add(fid)
            result.append({"id": fid, "title": title})

    try:
        user = gis.users.me

        # Method 1: user.folders (standard approach)
        try:
            folders = user.folders
            for folder in folders:
                _add_folder(folder)
        except Exception:
            pass

        # Method 2: gis.content.folders.list() (newer API, 2.3.0+)
        if check_minimum_version(*FOLDERS_API_CHANGE_VERSION):
            try:
                folders = gis.content.folders.list()
                for folder in folders:
                    _add_folder(folder)
            except Exception:
                pass

        # Method 3: Search through user's items to discover folders
        try:
            user_items = user.items()
            for item in user_items:
                owner_folder = getattr(item, "ownerFolder", None)
                if owner_folder and owner_folder not in seen_ids:
                    # Try to get folder info
                    try:
                        folder_info = gis.content.get_folder(owner_folder, user.username)
                        if folder_info:
                            _add_folder(folder_info)
                    except Exception:
                        # If we can't get info, just add the ID
                        seen_ids.add(owner_folder)
                        result.append({"id": owner_folder, "title": None})
        except Exception:
            pass

        return result

    except Exception as e:
        logger.debug(f"Failed to get folders: {e}")
        return result


# ---- Content API Shims --------------------------------------------------------------------------------------


def search_content(
    gis: GIS,
    query: str,
    max_items: int = 100,
    item_type: str | None = None,
) -> list[Any]:
    """Search Portal content with version-appropriate API.

    Args:
        gis: Authenticated GIS connection.
        query: Search query string.
        max_items: Maximum results to return.
        item_type: Optional item type filter.

    Returns:
        List of Item objects matching the query.
    """
    try:
        search_params = {
            "query": query,
            "max_items": max_items,
        }

        # item_type parameter name varies by version
        if item_type:
            if check_minimum_version(2, 3, 0):
                search_params["item_type"] = item_type
            else:
                # Append to query for older versions
                search_params["query"] = f"{query} type:\"{item_type}\""

        return gis.content.search(**search_params)
    except Exception as e:
        logger.debug(f"Content search failed: {e}")
        return []


def get_item_data(item: Any) -> dict[str, Any] | None:
    """Get item data with consistent error handling.

    Args:
        item: Portal Item object.

    Returns:
        Item data dict, or None if retrieval failed.
    """
    try:
        data = item.get_data()
        return data if isinstance(data, dict) else None
    except Exception as e:
        logger.debug(f"Failed to get item data: {e}")
        return None


# ---- Initialize on import -----------------------------------------------------------------------------------


# Run compatibility check when module is imported
validate_or_warn()
