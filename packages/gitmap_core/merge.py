"""Layer-level merge logic for GitMap.

Provides merging functionality at the operational layer level,
treating each layer as an atomic unit for conflict detection.

Execution Context:
    Library module - imported by CLI merge command

Dependencies:
    - gitmap_core.diff: Diff operations
    - gitmap_core.models: Data models

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any



# ---- Data Classes -------------------------------------------------------------------------------------------


@dataclass
class MergeConflict:
    """Represents a merge conflict for a layer.

    Attributes:
        layer_id: ID of the conflicting layer.
        layer_title: Title of the layer.
        ours: Our version of the layer.
        theirs: Their version of the layer.
        base: Common ancestor version (if available).
    """

    layer_id: str
    layer_title: str
    ours: dict[str, Any]
    theirs: dict[str, Any]
    base: dict[str, Any] | None = None


@dataclass
class MergeResult:
    """Result of a merge operation.

    Attributes:
        success: Whether merge completed without conflicts.
        merged_data: Resulting merged map data.
        conflicts: List of unresolved conflicts.
        added_layers: Layers added from source branch.
        removed_layers: Layers removed.
        modified_layers: Layers modified without conflict.
    """

    success: bool = True
    merged_data: dict[str, Any] = field(default_factory=dict)
    conflicts: list[MergeConflict] = field(default_factory=list)
    added_layers: list[str] = field(default_factory=list)
    removed_layers: list[str] = field(default_factory=list)
    modified_layers: list[str] = field(default_factory=list)

    @property
    def has_conflicts(
            self,
    ) -> bool:
        """Check if there are unresolved conflicts."""
        return len(self.conflicts) > 0


# ---- Merge Functions ----------------------------------------------------------------------------------------


def merge_maps(
        ours: dict[str, Any],
        theirs: dict[str, Any],
        base: dict[str, Any] | None = None,
) -> MergeResult:
    """Merge two web map states.

    Performs a layer-level merge, treating each operational layer
    as an atomic unit. Conflicts occur when the same layer is
    modified in both maps.

    Args:
        ours: Our map state (current branch).
        theirs: Their map state (branch being merged).
        base: Common ancestor (for three-way merge).

    Returns:
        MergeResult with merged data and any conflicts.
    """
    result = MergeResult()

    # Start with our map as base
    result.merged_data = _deep_copy(ours)

    # Get layers from each version
    our_layers = ours.get("operationalLayers", [])
    their_layers = theirs.get("operationalLayers", [])
    base_layers = base.get("operationalLayers", []) if base else []

    # Index layers by ID
    our_index = {layer.get("id"): layer for layer in our_layers if layer.get("id")}
    their_index = {layer.get("id"): layer for layer in their_layers if layer.get("id")}
    base_index = {layer.get("id"): layer for layer in base_layers if layer.get("id")}

    # Track which layers to include in merged result
    merged_layers = []
    processed_ids = set()

    # Process our layers first
    for layer_id, our_layer in our_index.items():
        processed_ids.add(layer_id)

        if layer_id in their_index:
            their_layer = their_index[layer_id]
            base_layer = base_index.get(layer_id)

            # Both have this layer - check for conflict
            if our_layer == their_layer:
                # Same content, no conflict
                merged_layers.append(our_layer)
            elif base_layer:
                # Three-way merge
                if our_layer == base_layer:
                    # We didn't change, use theirs
                    merged_layers.append(their_layer)
                    result.modified_layers.append(layer_id)
                elif their_layer == base_layer:
                    # They didn't change, use ours
                    merged_layers.append(our_layer)
                else:
                    # Both changed - conflict
                    result.conflicts.append(MergeConflict(
                        layer_id=layer_id,
                        layer_title=our_layer.get("title", "Untitled"),
                        ours=our_layer,
                        theirs=their_layer,
                        base=base_layer,
                    ))
                    # Keep ours for now, user must resolve
                    merged_layers.append(our_layer)
            else:
                # No base, both different - conflict
                result.conflicts.append(MergeConflict(
                    layer_id=layer_id,
                    layer_title=our_layer.get("title", "Untitled"),
                    ours=our_layer,
                    theirs=their_layer,
                ))
                merged_layers.append(our_layer)
        else:
            # Only we have this layer
            if layer_id in base_index:
                # Was in base, they deleted it
                # Keep it but note the deletion
                merged_layers.append(our_layer)
            else:
                # We added it
                merged_layers.append(our_layer)

    # Process layers only in theirs
    for layer_id, their_layer in their_index.items():
        if layer_id in processed_ids:
            continue

        processed_ids.add(layer_id)

        if layer_id in base_index:
            # Was in base, we deleted it
            # They may have modified it - treat as conflict if modified
            base_layer = base_index[layer_id]
            if their_layer != base_layer:
                # They modified a layer we deleted - conflict
                result.conflicts.append(MergeConflict(
                    layer_id=layer_id,
                    layer_title=their_layer.get("title", "Untitled"),
                    ours={},  # We deleted it
                    theirs=their_layer,
                    base=base_layer,
                ))
            # Don't add - respect our deletion
        else:
            # They added this layer
            merged_layers.append(their_layer)
            result.added_layers.append(layer_id)

    # Update merged data with layers
    result.merged_data["operationalLayers"] = merged_layers

    # Merge tables using the same logic as layers
    our_tables = ours.get("tables", [])
    their_tables = theirs.get("tables", [])
    base_tables = base.get("tables", []) if base else []

    # Index tables by ID
    our_table_index = {table.get("id"): table for table in our_tables if table.get("id")}
    their_table_index = {table.get("id"): table for table in their_tables if table.get("id")}
    base_table_index = {table.get("id"): table for table in base_tables if table.get("id")}

    # Track which tables to include in merged result
    merged_tables = []
    processed_table_ids = set()

    # Process our tables first
    for table_id, our_table in our_table_index.items():
        processed_table_ids.add(table_id)

        if table_id in their_table_index:
            their_table = their_table_index[table_id]
            base_table = base_table_index.get(table_id)

            # Both have this table - check for conflict
            if our_table == their_table:
                # Same content, no conflict
                merged_tables.append(our_table)
            elif base_table:
                # Three-way merge
                if our_table == base_table:
                    # We didn't change, use theirs
                    merged_tables.append(their_table)
                elif their_table == base_table:
                    # They didn't change, use ours
                    merged_tables.append(our_table)
                else:
                    # Both changed - conflict
                    result.conflicts.append(MergeConflict(
                        layer_id=table_id,
                        layer_title=our_table.get("title", "Untitled"),
                        ours=our_table,
                        theirs=their_table,
                        base=base_table,
                    ))
                    # Keep ours for now, user must resolve
                    merged_tables.append(our_table)
            else:
                # No base, both different - conflict
                result.conflicts.append(MergeConflict(
                    layer_id=table_id,
                    layer_title=our_table.get("title", "Untitled"),
                    ours=our_table,
                    theirs=their_table,
                ))
                merged_tables.append(our_table)
        else:
            # Only we have this table
            if table_id in base_table_index:
                # Was in base, they deleted it - keep it
                merged_tables.append(our_table)
            else:
                # We added it
                merged_tables.append(our_table)

    # Process tables only in theirs
    for table_id, their_table in their_table_index.items():
        if table_id in processed_table_ids:
            continue

        processed_table_ids.add(table_id)

        if table_id in base_table_index:
            # Was in base, we deleted it
            base_table = base_table_index[table_id]
            if their_table != base_table:
                # They modified a table we deleted - conflict
                result.conflicts.append(MergeConflict(
                    layer_id=table_id,
                    layer_title=their_table.get("title", "Untitled"),
                    ours={},  # We deleted it
                    theirs=their_table,
                    base=base_table,
                ))
            # Don't add - respect our deletion
        else:
            # They added this table
            merged_tables.append(their_table)
            result.added_layers.append(table_id)

    # Update merged data with tables
    result.merged_data["tables"] = merged_tables
    result.success = not result.has_conflicts

    return result


def _deep_copy(
        obj: dict[str, Any],
) -> dict[str, Any]:
    """Create a deep copy of a dictionary.

    Args:
        obj: Dictionary to copy.

    Returns:
        Deep copy of the dictionary.
    """
    import json
    return json.loads(json.dumps(obj))


def resolve_conflict(
        conflict: MergeConflict,
        resolution: str,
) -> dict[str, Any]:
    """Resolve a merge conflict.

    Args:
        conflict: The conflict to resolve.
        resolution: Resolution strategy ('ours', 'theirs', or 'base').

    Returns:
        Resolved layer data.

    Raises:
        ValueError: If resolution strategy is invalid.
    """
    if resolution == "ours":
        return conflict.ours
    elif resolution == "theirs":
        return conflict.theirs
    elif resolution == "base":
        if conflict.base is None:
            msg = "No base version available"
            raise ValueError(msg)
        return conflict.base
    else:
        msg = f"Invalid resolution strategy: {resolution}"
        raise ValueError(msg)


def apply_resolution(
        merge_result: MergeResult,
        layer_id: str,
        resolved_layer: dict[str, Any],
) -> MergeResult:
    """Apply a conflict resolution to merge result.

    Args:
        merge_result: Current merge result.
        layer_id: ID of layer/table being resolved.
        resolved_layer: Resolved layer/table data.

    Returns:
        Updated merge result.
    """
    # Find and remove the conflict
    merge_result.conflicts = [
        c for c in merge_result.conflicts
        if c.layer_id != layer_id
    ]

    # Check if this is a table or layer
    tables = merge_result.merged_data.get("tables", [])
    table_ids = {table.get("id") for table in tables if table.get("id")}
    is_table = layer_id in table_ids

    if is_table:
        # Update the table in merged data
        for i, table in enumerate(tables):
            if table.get("id") == layer_id:
                if resolved_layer:
                    tables[i] = resolved_layer
                else:
                    # Empty resolution means delete
                    del tables[i]
                break
        else:
            # Table not found, add it if not empty
            if resolved_layer:
                tables.append(resolved_layer)

        merge_result.merged_data["tables"] = tables
    else:
        # Update the layer in merged data
        layers = merge_result.merged_data.get("operationalLayers", [])
        for i, layer in enumerate(layers):
            if layer.get("id") == layer_id:
                if resolved_layer:
                    layers[i] = resolved_layer
                else:
                    # Empty resolution means delete
                    del layers[i]
                break
        else:
            # Layer not found, add it if not empty
            if resolved_layer:
                layers.append(resolved_layer)

        merge_result.merged_data["operationalLayers"] = layers

    merge_result.success = not merge_result.has_conflicts

    return merge_result


# ---- Formatting Functions -----------------------------------------------------------------------------------


def format_merge_summary(
        result: MergeResult,
) -> str:
    """Format merge result as human-readable summary.

    Args:
        result: MergeResult object.

    Returns:
        Formatted string summary.
    """
    lines = []

    if result.success:
        lines.append("Merge completed successfully.")
    else:
        lines.append(f"Merge has {len(result.conflicts)} conflict(s).")

    if result.added_layers:
        lines.append(f"Added layers: {len(result.added_layers)}")
        for layer_id in result.added_layers:
            lines.append(f"  + {layer_id}")

    if result.removed_layers:
        lines.append(f"Removed layers: {len(result.removed_layers)}")
        for layer_id in result.removed_layers:
            lines.append(f"  - {layer_id}")

    if result.modified_layers:
        lines.append(f"Modified layers: {len(result.modified_layers)}")
        for layer_id in result.modified_layers:
            lines.append(f"  ~ {layer_id}")

    # Count added/removed tables from conflicts and merged data
    merged_tables = result.merged_data.get("tables", [])
    if merged_tables:
        lines.append(f"Merged tables: {len(merged_tables)}")

    if result.conflicts:
        lines.append("Conflicts:")
        for conflict in result.conflicts:
            lines.append(f"  ! {conflict.layer_title} ({conflict.layer_id})")

    return "\n".join(lines)


