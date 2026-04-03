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

from dataclasses import dataclass, field
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


    def to_dict(self) -> dict[str, Any]:
        """Serialize the diff to a plain dictionary for JSON output.

        Returns:
            Dictionary with layer_changes, table_changes, property_changes,
            and summary statistics.
        """
        def _change_to_dict(c: LayerChange) -> dict[str, Any]:
            d: dict[str, Any] = {
                "layer_id": c.layer_id,
                "title": c.layer_title,
                "change_type": c.change_type,
            }
            if c.details:
                d["details"] = c.details
            return d

        return {
            "has_changes": self.has_changes,
            "stats": format_diff_stats(self),
            "layer_changes": [_change_to_dict(c) for c in self.layer_changes],
            "table_changes": [_change_to_dict(c) for c in self.table_changes],
            "property_changes": self.property_changes,
        }

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
            changes.append(
                LayerChange(
                    layer_id=str(layer_id),
                    layer_title=layer.get("title", "Untitled"),
                    change_type="added",
                )
            )

    # Find removed layers (in layers2 but not layers1)
    for layer_id, layer in index2.items():
        if layer_id not in index1:
            changes.append(
                LayerChange(
                    layer_id=str(layer_id),
                    layer_title=layer.get("title", "Untitled"),
                    change_type="removed",
                )
            )

    # Find modified layers (in both but different)
    for layer_id in index1:
        if layer_id in index2:
            layer1 = index1[layer_id]
            layer2 = index2[layer_id]

            if layer1 != layer2:
                deep_diff = DeepDiff(layer2, layer1, ignore_order=True)
                changes.append(
                    LayerChange(
                        layer_id=str(layer_id),
                        layer_title=layer1.get("title", "Untitled"),
                        change_type="modified",
                        details=deep_diff.to_dict() if deep_diff else {},
                    )
                )

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


def format_diff_visual(
    map_diff: MapDiff,
    label_a: str = "source",
    label_b: str = "target",
) -> list[tuple[str, str, str]]:
    """Format MapDiff as a list of rows for table rendering.

    Each row is (status_symbol, item_name, change_detail) suitable
    for use in a Rich Table or similar renderer.

    Args:
        map_diff: MapDiff object to format.
        label_a: Label for the source state.
        label_b: Label for the target state.

    Returns:
        List of (symbol, name, detail) tuples.
        Returns empty list when there are no changes.
    """
    rows: list[tuple[str, str, str]] = []

    for change in map_diff.added_layers:
        rows.append(("+", change.layer_title, f"Added in {label_a}"))

    for change in map_diff.removed_layers:
        rows.append(("-", change.layer_title, f"Removed in {label_a} (present in {label_b})"))

    for change in map_diff.modified_layers:
        num_changes = len(change.details) if change.details else 1
        detail = f"{num_changes} field(s) changed"
        rows.append(("~", change.layer_title, detail))

    for change in map_diff.added_tables:
        rows.append(("+", f"[table] {change.layer_title}", f"Added in {label_a}"))

    for change in map_diff.removed_tables:
        rows.append(("-", f"[table] {change.layer_title}", f"Removed in {label_a} (present in {label_b})"))

    for change in map_diff.modified_tables:
        num_changes = len(change.details) if change.details else 1
        rows.append(("~", f"[table] {change.layer_title}", f"{num_changes} field(s) changed"))

    if map_diff.property_changes:
        rows.append(("*", "Map properties", f"{len(map_diff.property_changes)} top-level field(s) changed"))

    return rows


def format_diff_stats(map_diff: MapDiff) -> dict[str, int]:
    """Return a summary statistics dict for a MapDiff.

    Args:
        map_diff: MapDiff object.

    Returns:
        Dict with counts: added, removed, modified, total.
    """
    added = len(map_diff.added_layers) + len(map_diff.added_tables)
    removed = len(map_diff.removed_layers) + len(map_diff.removed_tables)
    modified = len(map_diff.modified_layers) + len(map_diff.modified_tables)
    if map_diff.property_changes:
        modified += 1
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "total": added + removed + modified,
    }


def format_diff_html(
        map_diff: "MapDiff",
        label_a: str = "source",
        label_b: str = "target",
        title: str = "GitMap Diff Report",
) -> str:
    """Render MapDiff as a self-contained HTML report.

    Produces a single-file HTML page with embedded CSS suitable for
    sharing with stakeholders who don't have GitMap installed.

    Args:
        map_diff: MapDiff object to render.
        label_a: Label for the source (left) state.
        label_b: Label for the target (right) state.
        title: Page title and report heading.

    Returns:
        Complete HTML document as a string.
    """
    import html
    import json
    from datetime import datetime, timezone

    stats = format_diff_stats(map_diff)
    rows = format_diff_visual(map_diff, label_a, label_b)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build stats badges
    badge_parts: list[str] = []
    if stats["added"]:
        badge_parts.append(
            f'<span class="badge badge-added">+{stats["added"]} added</span>'
        )
    if stats["removed"]:
        badge_parts.append(
            f'<span class="badge badge-removed">-{stats["removed"]} removed</span>'
        )
    if stats["modified"]:
        badge_parts.append(
            f'<span class="badge badge-modified">~{stats["modified"]} modified</span>'
        )
    if not badge_parts:
        badge_parts.append('<span class="badge badge-clean">✓ no changes</span>')
    badges_html = " ".join(badge_parts)

    # Build table rows
    symbol_class = {"+": "added", "-": "removed", "~": "modified", "*": "property"}
    symbol_label = {"+": "added", "-": "removed", "~": "modified", "*": "changed"}

    row_html_parts: list[str] = []
    for symbol, name, detail in rows:
        cls = symbol_class.get(symbol, "modified")
        lbl = symbol_label.get(symbol, symbol)
        esc_name = html.escape(name)
        esc_detail = html.escape(detail)
        row_html_parts.append(
            f'<tr class="row-{cls}">'
            f'<td class="symbol">{html.escape(symbol)}</td>'
            f'<td class="name">{esc_name}</td>'
            f'<td class="status {cls}">{lbl}</td>'
            f'<td class="detail">{esc_detail}</td>'
            f"</tr>"
        )

    # Build detailed changes section
    detail_sections: list[str] = []
    for change in map_diff.modified_layers:
        if change.details:
            details_str = html.escape(json.dumps(change.details, indent=2))
            detail_sections.append(
                f'<div class="detail-block">'
                f'<h3>Layer: {html.escape(change.layer_title)}'
                f' <code class="layer-id">{html.escape(change.layer_id)}</code></h3>'
                f'<pre class="json-block">{details_str}</pre>'
                f"</div>"
            )

    details_html = ""
    if detail_sections:
        details_html = (
            '<section class="details-section">'
            "<h2>Detailed Field Changes</h2>"
            + "".join(detail_sections)
            + "</section>"
        )

    rows_html = "".join(row_html_parts) if row_html_parts else (
        '<tr><td colspan="4" class="no-changes">No changes detected.</td></tr>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #0f172a; --surface: #1e293b; --border: #334155;
      --text: #e2e8f0; --muted: #94a3b8;
      --added: #22c55e; --removed: #ef4444; --modified: #f59e0b; --prop: #38bdf8;
      --font-mono: 'Cascadia Code', 'Fira Code', Consolas, monospace;
    }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg); color: var(--text); padding: 2rem; line-height: 1.5; }}
    header {{ border-bottom: 1px solid var(--border); padding-bottom: 1.25rem; margin-bottom: 1.5rem; }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 0.35rem; }}
    .subtitle {{ color: var(--muted); font-size: 0.875rem; }}
    .badges {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.75rem; }}
    .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px;
              font-size: 0.8rem; font-weight: 600; }}
    .badge-added   {{ background: #14532d; color: var(--added); }}
    .badge-removed {{ background: #450a0a; color: var(--removed); }}
    .badge-modified{{ background: #451a03; color: var(--modified); }}
    .badge-clean   {{ background: #0c4a1a; color: var(--added); }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem;
             background: var(--surface); border-radius: 0.5rem; overflow: hidden; }}
    thead th {{ background: #0f172a; color: var(--muted); text-align: left;
                padding: 0.6rem 1rem; font-size: 0.8rem; text-transform: uppercase;
                letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }}
    tbody tr {{ border-bottom: 1px solid var(--border); }}
    tbody tr:last-child {{ border-bottom: none; }}
    td {{ padding: 0.6rem 1rem; font-size: 0.9rem; }}
    td.symbol {{ font-family: var(--font-mono); font-weight: 700; width: 2rem; }}
    td.name {{ font-family: var(--font-mono); }}
    td.status {{ font-size: 0.8rem; width: 6rem; text-transform: uppercase;
                  font-weight: 600; letter-spacing: 0.03em; }}
    td.detail {{ color: var(--muted); font-size: 0.85rem; }}
    td.no-changes {{ text-align: center; color: var(--muted); padding: 1.5rem; }}
    .row-added   td.symbol, .row-added   td.status {{ color: var(--added); }}
    .row-removed td.symbol, .row-removed td.status {{ color: var(--removed); }}
    .row-modified td.symbol, .row-modified td.status {{ color: var(--modified); }}
    .row-property td.symbol, .row-property td.status {{ color: var(--prop); }}
    .details-section {{ margin-top: 1rem; }}
    .details-section h2 {{ font-size: 1.1rem; margin-bottom: 1rem;
                           border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
    .detail-block {{ background: var(--surface); border-radius: 0.5rem;
                     margin-bottom: 1rem; overflow: hidden; }}
    .detail-block h3 {{ padding: 0.75rem 1rem; font-size: 0.95rem;
                         border-bottom: 1px solid var(--border); }}
    code.layer-id {{ font-family: var(--font-mono); font-size: 0.8rem;
                      color: var(--muted); margin-left: 0.5rem; }}
    pre.json-block {{ font-family: var(--font-mono); font-size: 0.78rem; color: #a5f3fc;
                       padding: 1rem; overflow-x: auto; white-space: pre-wrap; }}
    footer {{ margin-top: 2rem; font-size: 0.75rem; color: var(--muted);
              border-top: 1px solid var(--border); padding-top: 1rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">
      Comparing <strong>{html.escape(label_a)}</strong>
      &rarr; <strong>{html.escape(label_b)}</strong>
    </p>
    <div class="badges">{badges_html}</div>
  </header>
  <table>
    <thead>
      <tr>
        <th></th>
        <th>Layer / Table</th>
        <th>Status</th>
        <th>Change Detail</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  {details_html}
  <footer>Generated by GitMap &mdash; {generated}</footer>
</body>
</html>
"""
