"""Web map JSON operations module.

Handles extraction, serialization, and staging of ArcGIS web map JSON
data for version control operations.

Execution Context:
    Library module - imported by CLI commands and remote operations

Dependencies:
    - arcgis: Web map item access
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

if TYPE_CHECKING:
    from arcgis.gis import GIS
    from arcgis.gis import Item


# ---- Map Extraction Functions -------------------------------------------------------------------------------


def get_webmap_json(
        item: Item,
) -> dict[str, Any]:
    """Extract web map JSON from Portal item.

    Args:
        item: ArcGIS web map item.

    Returns:
        Web map JSON as dictionary.

    Raises:
        RuntimeError: If item is not a web map or extraction fails.
    """
    try:
        if item.type != "Web Map":
            msg = f"Item '{item.title}' is not a Web Map (type: {item.type})"
            raise RuntimeError(msg)

        # Get the web map data
        webmap_data = item.get_data()

        if not webmap_data:
            msg = f"Failed to get data from web map '{item.title}'"
            raise RuntimeError(msg)

        return webmap_data

    except Exception as extraction_error:
        if isinstance(extraction_error, RuntimeError):
            raise
        msg = f"Failed to extract web map JSON: {extraction_error}"
        raise RuntimeError(msg) from extraction_error


def get_webmap_by_id(
        gis: GIS,
        item_id: str,
) -> tuple[Item, dict[str, Any]]:
    """Fetch web map item and its JSON by item ID.

    Args:
        gis: Authenticated GIS connection.
        item_id: Portal item ID.

    Returns:
        Tuple of (Item, web map JSON dict).

    Raises:
        RuntimeError: If item not found or is not a web map.
    """
    try:
        item = gis.content.get(item_id)

        if not item:
            msg = f"Item with ID '{item_id}' not found"
            raise RuntimeError(msg)

        webmap_json = get_webmap_json(item)
        return item, webmap_json

    except Exception as fetch_error:
        if isinstance(fetch_error, RuntimeError):
            raise
        msg = f"Failed to fetch web map {item_id}: {fetch_error}"
        raise RuntimeError(msg) from fetch_error


# ---- Layer Operations ---------------------------------------------------------------------------------------


def get_operational_layers(
        map_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract operational layers from web map JSON.

    Args:
        map_data: Web map JSON dictionary.

    Returns:
        List of operational layer dictionaries.
    """
    return map_data.get("operationalLayers", [])


def get_basemap_layers(
        map_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract basemap layers from web map JSON.

    Args:
        map_data: Web map JSON dictionary.

    Returns:
        List of basemap layer dictionaries.
    """
    basemap = map_data.get("baseMap", {})
    return basemap.get("baseMapLayers", [])


def get_layer_by_id(
        map_data: dict[str, Any],
        layer_id: str,
) -> dict[str, Any] | None:
    """Find a layer by its ID.

    Args:
        map_data: Web map JSON dictionary.
        layer_id: Layer ID to find.

    Returns:
        Layer dictionary or None if not found.
    """
    for layer in get_operational_layers(map_data):
        if layer.get("id") == layer_id:
            return layer
    return None


def get_layer_ids(
        map_data: dict[str, Any],
) -> list[str]:
    """Get all operational layer IDs.

    Args:
        map_data: Web map JSON dictionary.

    Returns:
        List of layer IDs.
    """
    return [
        layer.get("id", "")
        for layer in get_operational_layers(map_data)
        if layer.get("id")
    ]


# ---- Map Comparison Functions -------------------------------------------------------------------------------


def compare_layers(
        layers1: list[dict[str, Any]],
        layers2: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two lists of layers.

    Args:
        layers1: First layer list (e.g., from index).
        layers2: Second layer list (e.g., from commit).

    Returns:
        Dictionary with added, removed, and modified layer info.
    """
    ids1 = {layer.get("id"): layer for layer in layers1 if layer.get("id")}
    ids2 = {layer.get("id"): layer for layer in layers2 if layer.get("id")}

    added = [ids1[id] for id in ids1 if id not in ids2]
    removed = [ids2[id] for id in ids2 if id not in ids1]
    modified = []

    for layer_id in ids1:
        if layer_id in ids2:
            if ids1[layer_id] != ids2[layer_id]:
                modified.append({
                    "id": layer_id,
                    "old": ids2[layer_id],
                    "new": ids1[layer_id],
                })

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }


# ---- Serialization Functions --------------------------------------------------------------------------------


def save_map_json(
        map_data: dict[str, Any],
        filepath: Path,
) -> None:
    """Save web map JSON to file.

    Args:
        map_data: Web map JSON dictionary.
        filepath: Path to save file.
    """
    filepath.write_text(json.dumps(map_data, indent=2))


def load_map_json(
        filepath: Path,
) -> dict[str, Any]:
    """Load web map JSON from file.

    Args:
        filepath: Path to JSON file.

    Returns:
        Web map JSON dictionary.

    Raises:
        RuntimeError: If file cannot be loaded.
    """
    try:
        return json.loads(filepath.read_text())
    except Exception as load_error:
        msg = f"Failed to load map JSON from {filepath}: {load_error}"
        raise RuntimeError(msg) from load_error


# ---- Map Creation Functions ---------------------------------------------------------------------------------


def create_empty_webmap(
        title: str = "New Map",
        spatial_reference: int = 102100,
) -> dict[str, Any]:
    """Create an empty web map JSON structure.

    Args:
        title: Map title.
        spatial_reference: Spatial reference WKID.

    Returns:
        Empty web map JSON dictionary.
    """
    return {
        "operationalLayers": [],
        "baseMap": {
            "baseMapLayers": [],
            "title": "Basemap",
        },
        "spatialReference": {
            "wkid": spatial_reference,
        },
        "version": "2.28",
        "authoringApp": "GitMap",
        "authoringAppVersion": "0.1.0",
    }


