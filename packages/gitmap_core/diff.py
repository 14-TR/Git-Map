"""JSON diffing and comparison module.

Provides utilities for comparing web map JSON structures,
detecting changes at the layer and property level.

Execution Context:
    Library module - imported by CLI diff and merge commands

Dependencies:
    - deepdiff: Deep dictionary comparison

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from deepdiff import DeepDiff


# ---- Data Classes -------------------------------------------------------------------------------------------


@dataclass
class LayerChange:
    """Represents a change to a single layer.

    Attributes:
        layer_id: ID of the changed layer.
        layer_title: Title of the layer.
        change_type: Type of change (added, removed, modified).
        details: Detailed change information.
    """

    layer_id: str
    layer_title: str
    change_type: str  # 'added', 'removed', 'modified'
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class MapDiff:
    """Represents differences between two map states.

    Attributes:
        layer_changes: List of layer-level changes.
        table_changes: List of table-level changes.
        property_changes: Map-level property changes.
        has_changes: Whether any changes were detected.
    """

    layer_changes: list[LayerChange] = field(default_factory=list)
    table_changes: list[LayerChange] = field(default_factory=list)
    property_changes: dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(
            self,
    ) -> bool:
        """Check if any changes exist."""
        return bool(self.layer_changes or self.table_changes or self.property_changes)

    @property
    def added_layers(
            self,
    ) -> list[LayerChange]:
        """Get added layers."""
        return [c for c in self.layer_changes if c.change_type == "added"]

    @property
    def removed_layers(
            self,
    ) -> list[LayerChange]:
        """Get removed layers."""
        return [c for c in self.layer_changes if c.change_type == "removed"]

    @property
    def modified_layers(
            self,
    ) -> list[LayerChange]:
        """Get modified layers."""
        return [c for c in self.layer_changes if c.change_type == "modified"]

    @property
    def added_tables(
            self,
    ) -> list[LayerChange]:
        """Get added tables."""
        return [c for c in self.table_changes if c.change_type == "added"]

    @property
    def removed_tables(
            self,
    ) -> list[LayerChange]:
        """Get removed tables."""
        return [c for c in self.table_changes if c.change_type == "removed"]

    @property
    def modified_tables(
            self,
    ) -> list[LayerChange]:
        """Get modified tables."""
        return [c for c in self.table_changes if c.change_type == "modified"]


# ---- Diff Functions -----------------------------------------------------------------------------------------


def diff_maps(
        map1: dict[str, Any],
        map2: dict[str, Any],
) -> MapDiff:
    """Compare two web map JSON structures.

    Args:
        map1: First map (typically current/index state).
        map2: Second map (typically committed state).

    Returns:
        MapDiff object describing all differences.
    """
    result = MapDiff()

    # Compare operational layers
    layers1 = map1.get("operationalLayers", [])
    layers2 = map2.get("operationalLayers", [])

    layer_changes = diff_layers(layers1, layers2)
    result.layer_changes = layer_changes

    # Compare tables (same structure as layers)
    tables1 = map1.get("tables", [])
    tables2 = map2.get("tables", [])

    table_changes = diff_layers(tables1, tables2)
    result.table_changes = table_changes

    # Compare map-level properties (excluding layers and tables)
    map1_props = {k: v for k, v in map1.items() if k not in ("operationalLayers", "tables")}
    map2_props = {k: v for k, v in map2.items() if k not in ("operationalLayers", "tables")}

    if map1_props != map2_props:
        deep_diff = DeepDiff(map2_props, map1_props, ignore_order=True)
        result.property_changes = deep_diff.to_dict() if deep_diff else {}

    return result


def diff_layers(
        layers1: list[dict[str, Any]],
        layers2: list[dict[str, Any]],
) -> list[LayerChange]:
    """Compare two lists of operational layers.

    Args:
        layers1: First layer list (current state).
        layers2: Second layer list (previous state).

    Returns:
        List of LayerChange objects.
    """
    changes = []

    # Index layers by ID
    index1 = {layer.get("id"): layer for layer in layers1 if layer.get("id")}
    index2 = {layer.get("id"): layer for layer in layers2 if layer.get("id")}

    # Find added layers (in layers1 but not layers2)
    for layer_id, layer in index1.items():
        if layer_id not in index2:
            changes.append(LayerChange(
                layer_id=str(layer_id),
                layer_title=layer.get("title", "Untitled"),
                change_type="added",
            ))

    # Find removed layers (in layers2 but not layers1)
    for layer_id, layer in index2.items():
        if layer_id not in index1:
            changes.append(LayerChange(
                layer_id=str(layer_id),
                layer_title=layer.get("title", "Untitled"),
                change_type="removed",
            ))

    # Find modified layers (in both but different)
    for layer_id in index1:
        if layer_id in index2:
            layer1 = index1[layer_id]
            layer2 = index2[layer_id]

            if layer1 != layer2:
                deep_diff = DeepDiff(layer2, layer1, ignore_order=True)
                changes.append(LayerChange(
                    layer_id=str(layer_id),
                    layer_title=layer1.get("title", "Untitled"),
                    change_type="modified",
                    details=deep_diff.to_dict() if deep_diff else {},
                ))

    return changes


def diff_json(
        obj1: Any,
        obj2: Any,
        ignore_order: bool = True,
) -> dict[str, Any]:
    """Generic JSON diff using DeepDiff.

    Args:
        obj1: First object (current state).
        obj2: Second object (previous state).
        ignore_order: Whether to ignore list ordering.

    Returns:
        Dictionary of differences.
    """
    deep_diff = DeepDiff(obj2, obj1, ignore_order=ignore_order)
    return deep_diff.to_dict() if deep_diff else {}


# ---- Formatting Functions -----------------------------------------------------------------------------------


def format_diff_summary(
        map_diff: MapDiff,
) -> str:
    """Format MapDiff as human-readable summary.

    Args:
        map_diff: MapDiff object.

    Returns:
        Formatted string summary.
    """
    if not map_diff.has_changes:
        return "No changes detected."

    lines = []

    if map_diff.added_layers:
        lines.append(f"Added layers ({len(map_diff.added_layers)}):")
        for change in map_diff.added_layers:
            lines.append(f"  + {change.layer_title} ({change.layer_id})")

    if map_diff.removed_layers:
        lines.append(f"Removed layers ({len(map_diff.removed_layers)}):")
        for change in map_diff.removed_layers:
            lines.append(f"  - {change.layer_title} ({change.layer_id})")

    if map_diff.modified_layers:
        lines.append(f"Modified layers ({len(map_diff.modified_layers)}):")
        for change in map_diff.modified_layers:
            lines.append(f"  ~ {change.layer_title} ({change.layer_id})")

    if map_diff.added_tables:
        lines.append(f"Added tables ({len(map_diff.added_tables)}):")
        for change in map_diff.added_tables:
            lines.append(f"  + {change.layer_title} ({change.layer_id})")

    if map_diff.removed_tables:
        lines.append(f"Removed tables ({len(map_diff.removed_tables)}):")
        for change in map_diff.removed_tables:
            lines.append(f"  - {change.layer_title} ({change.layer_id})")

    if map_diff.modified_tables:
        lines.append(f"Modified tables ({len(map_diff.modified_tables)}):")
        for change in map_diff.modified_tables:
            lines.append(f"  ~ {change.layer_title} ({change.layer_id})")

    if map_diff.property_changes:
        lines.append("Map properties changed:")
        for key in map_diff.property_changes:
            lines.append(f"  * {key}")

    return "\n".join(lines)


