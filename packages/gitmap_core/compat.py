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
from typing import TYPE_CHECKING
from typing import Any

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
    """
    try:
        if check_minimum_version(*FOLDERS_API_CHANGE_VERSION):
            # New API (2.3.0+)
            result = gis.content.folders.create(folder_name)
            if result:
                if isinstance(result, dict):
                    return result
                else:
                    # Object with attributes
                    return {
                        "id": getattr(result, "id", None),
                        "title": getattr(result, "title", folder_name),
                    }
        else:
            # Legacy API (< 2.3.0)
            result = gis.content.create_folder(folder_name)
            if result:
                if isinstance(result, dict):
                    return result
                else:
                    return {
                        "id": getattr(result, "id", None),
                        "title": getattr(result, "title", folder_name),
                    }
        return None
    except Exception as e:
        logger.debug(f"Folder creation failed: {e}")
        raise


def get_user_folders(gis: GIS) -> list[dict[str, Any]]:
    """Get user's folders with version-appropriate API.
    
    Args:
        gis: Authenticated GIS connection.
        
    Returns:
        List of folder dicts with 'id' and 'title' keys.
    """
    try:
        user = gis.users.me
        folders = user.folders
        
        result = []
        for folder in folders:
            if isinstance(folder, dict):
                result.append(folder)
            else:
                result.append({
                    "id": getattr(folder, "id", None),
                    "title": getattr(folder, "title", None),
                })
        return result
    except Exception as e:
        logger.debug(f"Failed to get folders: {e}")
        return []


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
