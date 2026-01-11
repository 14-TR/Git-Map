"""Context graph visualization for GitMap.

Provides lightweight visualization of context graph data in formats
viewable directly in IDEs: Mermaid diagrams, ASCII art, and HTML.

Execution Context:
    Library module - imported by CLI and MCP tools

Dependencies:
    - None (stdlib only for lightweight deployment)

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gitmap_core.context import Annotation
from gitmap_core.context import ContextStore
from gitmap_core.context import Edge
from gitmap_core.context import Event


# ---- Configuration Constants ---------------------------------------------------------------------------------


# Event type icons for Mermaid flowcharts
EVENT_ICONS = {
    "commit": "fa:fa-code-commit",
    "push": "fa:fa-cloud-upload",
    "pull": "fa:fa-cloud-download",
    "merge": "fa:fa-code-merge",
    "branch": "fa:fa-code-branch",
    "diff": "fa:fa-file-diff",
}

# Event type shapes for Mermaid
EVENT_SHAPES = {
    "commit": ("([", "])"),  # Stadium shape
    "push": ("[[", "]]"),  # Subroutine shape
    "pull": ("[[", "]]"),  # Subroutine shape
    "merge": ("{{", "}}"),  # Hexagon shape
    "branch": (">", "]"),  # Asymmetric shape
    "diff": ("[/", "/]"),  # Parallelogram shape
}

# Relationship arrow styles for Mermaid
EDGE_STYLES = {
    "caused_by": "-->",  # Standard arrow
    "reverts": "-. reverts .->",  # Dotted with label
    "related_to": "---",  # Line without arrow
    "learned_from": "-.->",  # Dotted arrow
}

# ASCII box characters
ASCII_BOX = {
    "tl": "┌",
    "tr": "┐",
    "bl": "└",
    "br": "┘",
    "h": "─",
    "v": "│",
    "t": "┬",
    "b": "┴",
    "l": "├",
    "r": "┤",
    "c": "┼",
}

# Simple ASCII (fallback)
ASCII_BOX_SIMPLE = {
    "tl": "+",
    "tr": "+",
    "bl": "+",
    "br": "+",
    "h": "-",
    "v": "|",
    "t": "+",
    "b": "+",
    "l": "+",
    "r": "+",
    "c": "+",
}


# ---- Data Classes --------------------------------------------------------------------------------------------


@dataclass
class GraphData:
    """Container for graph visualization data.

    Attributes:
        events: List of events to visualize.
        edges: List of edges connecting events.
        annotations: Dictionary mapping event IDs to their annotations.
    """

    events: list[Event]
    edges: list[Edge]
    annotations: dict[str, list[Annotation]]

    @classmethod
    def from_context_store(
        cls,
        store: ContextStore,
        limit: int = 50,
        event_types: list[str] | None = None,
    ) -> GraphData:
        """Build graph data from context store.

        Args:
            store: Context store to query.
            limit: Maximum events to include.
            event_types: Filter by event types.

        Returns:
            GraphData instance with events, edges, and annotations.
        """
        # Get events
        conn = store._connection
        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            cursor = conn.execute(
                f"""
                SELECT * FROM events
                WHERE event_type IN ({placeholders})
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [*event_types, limit],
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM events
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [limit],
            )

        events = [Event.from_row(row) for row in cursor.fetchall()]
        event_ids = {e.id for e in events}

        # Get edges between these events
        edges = []
        if event_ids:
            placeholders = ",".join("?" for _ in event_ids)
            cursor = conn.execute(
                f"""
                SELECT * FROM edges
                WHERE source_id IN ({placeholders})
                AND target_id IN ({placeholders})
                """,
                [*event_ids, *event_ids],
            )
            edges = [Edge.from_row(row) for row in cursor.fetchall()]

        # Get annotations for all events
        annotations: dict[str, list[Annotation]] = {}
        for event in events:
            annotations[event.id] = store.get_annotations(event.id)

        return cls(events=events, edges=edges, annotations=annotations)


# ---- Mermaid Generation --------------------------------------------------------------------------------------


def _sanitize_mermaid_text(text: str) -> str:
    """Sanitize text for Mermaid diagram inclusion.

    Args:
        text: Text to sanitize.

    Returns:
        Sanitized text safe for Mermaid.
    """
    # Replace problematic characters
    text = text.replace('"', "'")
    text = text.replace("\n", " ")
    text = text.replace("[", "(")
    text = text.replace("]", ")")
    text = text.replace("{", "(")
    text = text.replace("}", ")")
    text = text.replace("<", "‹")
    text = text.replace(">", "›")
    text = text.replace("#", "")
    # Truncate long text
    if len(text) > 40:
        text = text[:37] + "..."
    return text


def _format_event_label(event: Event, show_time: bool = True) -> str:
    """Format event label for display.

    Args:
        event: Event to format.
        show_time: Include timestamp in label.

    Returns:
        Formatted label string.
    """
    # Parse timestamp for display
    try:
        dt = datetime.fromisoformat(event.timestamp)
        time_str = dt.strftime("%m/%d %H:%M")
    except (ValueError, TypeError):
        time_str = event.timestamp[:16] if event.timestamp else ""

    # Get short ref
    ref_str = ""
    if event.ref:
        ref_str = event.ref[:8] if len(event.ref) > 8 else event.ref

    # Build label parts
    parts = [event.event_type.upper()]
    if ref_str:
        parts.append(ref_str)
    if show_time:
        parts.append(time_str)

    return " | ".join(parts)


def generate_mermaid_flowchart(
    data: GraphData,
    direction: str = "TB",
    show_annotations: bool = True,
    title: str | None = None,
) -> str:
    """Generate Mermaid flowchart from graph data.

    Args:
        data: Graph data to visualize.
        direction: Graph direction (TB, BT, LR, RL).
        show_annotations: Include annotation nodes.
        title: Optional chart title.

    Returns:
        Mermaid flowchart diagram string.
    """
    lines = []

    # Header with direction
    lines.append(f"flowchart {direction}")

    # Add title as comment if provided
    if title:
        lines.insert(0, f"%% {title}")

    # Add event nodes
    for event in data.events:
        node_id = f"e_{event.id[:8]}"
        label = _sanitize_mermaid_text(_format_event_label(event))

        # Get shape for event type
        shape_l, shape_r = EVENT_SHAPES.get(event.event_type, ("[", "]"))

        lines.append(f"    {node_id}{shape_l}\"{label}\"{shape_r}")

        # Add annotation nodes if enabled
        if show_annotations and event.id in data.annotations:
            for i, ann in enumerate(data.annotations[event.id][:3]):  # Max 3 annotations
                ann_id = f"a_{event.id[:6]}_{i}"
                ann_label = _sanitize_mermaid_text(f"{ann.annotation_type}: {ann.content}")
                lines.append(f"    {ann_id}[\"{ann_label}\"]")
                lines.append(f"    {node_id} -.- {ann_id}")

    # Add edge connections
    for edge in data.edges:
        source_id = f"e_{edge.source_id[:8]}"
        target_id = f"e_{edge.target_id[:8]}"
        arrow = EDGE_STYLES.get(edge.relationship, "-->")

        # Check if both nodes exist
        source_exists = any(e.id == edge.source_id for e in data.events)
        target_exists = any(e.id == edge.target_id for e in data.events)

        if source_exists and target_exists:
            if edge.relationship in ("reverts", "learned_from"):
                lines.append(f"    {source_id} {arrow} {target_id}")
            else:
                lines.append(f"    {source_id} --> |{edge.relationship}| {target_id}")

    # Add styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef commit fill:#4CAF50,color:#fff")
    lines.append("    classDef push fill:#2196F3,color:#fff")
    lines.append("    classDef pull fill:#9C27B0,color:#fff")
    lines.append("    classDef merge fill:#FF9800,color:#fff")
    lines.append("    classDef branch fill:#00BCD4,color:#fff")
    lines.append("    classDef annotation fill:#FFF9C4,color:#333")

    # Apply styles to nodes
    for event in data.events:
        node_id = f"e_{event.id[:8]}"
        if event.event_type in ("commit", "push", "pull", "merge", "branch"):
            lines.append(f"    class {node_id} {event.event_type}")

    # Style annotation nodes
    if show_annotations:
        for event_id, annotations in data.annotations.items():
            for i in range(min(3, len(annotations))):
                ann_id = f"a_{event_id[:6]}_{i}"
                lines.append(f"    class {ann_id} annotation")

    return "\n".join(lines)


def generate_mermaid_timeline(
    data: GraphData,
    title: str = "Context Timeline",
) -> str:
    """Generate Mermaid timeline diagram from graph data.

    Args:
        data: Graph data to visualize.
        title: Timeline title.

    Returns:
        Mermaid timeline diagram string.
    """
    lines = []
    lines.append("timeline")
    lines.append(f"    title {title}")

    # Group events by date
    events_by_date: dict[str, list[Event]] = {}
    for event in sorted(data.events, key=lambda e: e.timestamp):
        try:
            dt = datetime.fromisoformat(event.timestamp)
            date_key = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_key = "Unknown"

        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(event)

    # Generate timeline sections
    for date_key in sorted(events_by_date.keys()):
        lines.append(f"    section {date_key}")
        for event in events_by_date[date_key]:
            # Get time
            try:
                dt = datetime.fromisoformat(event.timestamp)
                time_str = dt.strftime("%H:%M")
            except (ValueError, TypeError):
                time_str = ""

            # Build event description
            ref_str = event.ref[:8] if event.ref and len(event.ref) > 8 else (event.ref or "")
            desc = f"{event.event_type}"
            if ref_str:
                desc += f" {ref_str}"
            if time_str:
                desc = f"{time_str} - {desc}"

            lines.append(f"        {_sanitize_mermaid_text(desc)}")

    return "\n".join(lines)


def generate_mermaid_git_graph(
    data: GraphData,
    branch_name: str = "main",
) -> str:
    """Generate Mermaid gitGraph diagram from commit events.

    This focuses on commit events and their relationships,
    mimicking a git log visualization.

    Args:
        data: Graph data to visualize.
        branch_name: Name for the main branch.

    Returns:
        Mermaid gitGraph diagram string.
    """
    lines = []
    lines.append("gitGraph")

    # Filter to commit events only
    commits = [e for e in data.events if e.event_type == "commit"]
    commits.sort(key=lambda e: e.timestamp)

    # Build commit chain
    for commit in commits:
        # Get commit message from payload
        msg = commit.payload.get("message", "")
        if not msg:
            msg = f"Commit {commit.ref[:8] if commit.ref else commit.id[:8]}"
        msg = _sanitize_mermaid_text(msg)

        # Get commit ID
        commit_id = commit.ref[:8] if commit.ref else commit.id[:8]

        lines.append(f'    commit id: "{commit_id}" msg: "{msg}"')

    if not commits:
        lines.append('    commit id: "initial" msg: "No commits yet"')

    return "\n".join(lines)


# ---- ASCII Art Generation ------------------------------------------------------------------------------------


def _wrap_text(text: str, width: int) -> list[str]:
    """Wrap text to specified width.

    Args:
        text: Text to wrap.
        width: Maximum line width.

    Returns:
        List of wrapped lines.
    """
    words = text.split()
    lines = []
    current_line: list[str] = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines or [""]


def generate_ascii_timeline(
    data: GraphData,
    width: int = 60,
    use_unicode: bool = True,
) -> str:
    """Generate ASCII art timeline from graph data.

    Args:
        data: Graph data to visualize.
        width: Maximum width of output.
        use_unicode: Use Unicode box-drawing characters.

    Returns:
        ASCII art timeline string.
    """
    box = ASCII_BOX if use_unicode else ASCII_BOX_SIMPLE
    lines = []

    # Sort events by timestamp
    events = sorted(data.events, key=lambda e: e.timestamp, reverse=True)

    content_width = width - 4  # Account for box borders

    for i, event in enumerate(events):
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(event.timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = event.timestamp[:16] if event.timestamp else "Unknown"

        # Build header
        event_type = event.event_type.upper()
        ref_str = ""
        if event.ref:
            ref_str = event.ref[:12] if len(event.ref) > 12 else event.ref

        header = f"{event_type}"
        if ref_str:
            header += f" [{ref_str}]"

        # Add actor if present
        if event.actor:
            header += f" by {event.actor}"

        # Top border
        if i == 0:
            lines.append(box["tl"] + box["h"] * (width - 2) + box["tr"])
        else:
            lines.append(box["l"] + box["h"] * (width - 2) + box["r"])

        # Time line
        time_line = f" {time_str}"
        time_line = time_line.ljust(content_width)
        lines.append(f"{box['v']} {time_line} {box['v']}")

        # Header line
        header_lines = _wrap_text(header, content_width)
        for hline in header_lines:
            lines.append(f"{box['v']} {hline.ljust(content_width)} {box['v']}")

        # Separator
        lines.append(f"{box['v']} {'-' * content_width} {box['v']}")

        # Annotations
        if event.id in data.annotations:
            for ann in data.annotations[event.id][:2]:  # Max 2 annotations
                ann_prefix = f"[{ann.annotation_type[:3].upper()}] "
                ann_text = ann_prefix + ann.content
                ann_lines = _wrap_text(ann_text, content_width)
                for aline in ann_lines:
                    lines.append(f"{box['v']} {aline.ljust(content_width)} {box['v']}")

        # Payload summary (if has message)
        msg = event.payload.get("message", "")
        if msg:
            msg_lines = _wrap_text(f'"{msg}"', content_width)
            for mline in msg_lines:
                lines.append(f"{box['v']} {mline.ljust(content_width)} {box['v']}")

    # Bottom border
    if events:
        lines.append(box["bl"] + box["h"] * (width - 2) + box["br"])
    else:
        lines.append("(No events to display)")

    return "\n".join(lines)


def generate_ascii_graph(
    data: GraphData,
    width: int = 80,
    use_unicode: bool = True,
) -> str:
    """Generate ASCII art graph showing relationships.

    Args:
        data: Graph data to visualize.
        width: Maximum width of output.
        use_unicode: Use Unicode characters.

    Returns:
        ASCII art graph string.
    """
    lines = []
    node_char = "●" if use_unicode else "*"
    arrow_r = "→" if use_unicode else "->"
    arrow_d = "↓" if use_unicode else "v"

    # Sort events by timestamp
    events = sorted(data.events, key=lambda e: e.timestamp)

    # Build node lookup
    node_positions: dict[str, int] = {}
    for i, event in enumerate(events):
        node_positions[event.id] = i

    # Generate node lines
    for i, event in enumerate(events):
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(event.timestamp)
            time_str = dt.strftime("%m/%d %H:%M")
        except (ValueError, TypeError):
            time_str = ""

        # Build node line
        type_str = event.event_type[:6].ljust(6)
        ref_str = (event.ref[:8] if event.ref else event.id[:8]).ljust(8)

        node_line = f"  {node_char} {type_str} {ref_str} {time_str}"

        # Find outgoing edges
        outgoing = [e for e in data.edges if e.source_id == event.id]
        if outgoing:
            edge_info = []
            for edge in outgoing[:2]:  # Max 2 edges shown
                target_pos = node_positions.get(edge.target_id)
                if target_pos is not None:
                    edge_info.append(f"{arrow_r} {edge.relationship}")
            if edge_info:
                node_line += f"  ({', '.join(edge_info)})"

        lines.append(node_line)

        # Add connector to next node
        if i < len(events) - 1:
            lines.append(f"  {arrow_d}")

    if not events:
        lines.append("(No events to display)")

    # Add legend
    lines.append("")
    lines.append("Legend:")
    lines.append(f"  {node_char} = Event node")
    lines.append(f"  {arrow_r} = Relationship")

    return "\n".join(lines)


# ---- HTML Generation -----------------------------------------------------------------------------------------


def generate_html_visualization(
    data: GraphData,
    title: str = "Context Graph",
    theme: str = "light",
) -> str:
    """Generate standalone HTML file with interactive visualization.

    Uses embedded Mermaid.js for rendering. Can be opened directly
    in IDE preview panes or browsers.

    Args:
        data: Graph data to visualize.
        title: Page title.
        theme: Color theme ('light' or 'dark').

    Returns:
        Complete HTML document string.
    """
    # Generate Mermaid diagram
    mermaid_flowchart = generate_mermaid_flowchart(data, show_annotations=True)
    mermaid_timeline = generate_mermaid_timeline(data)

    # Escape for HTML embedding
    mermaid_flowchart_escaped = html.escape(mermaid_flowchart)
    mermaid_timeline_escaped = html.escape(mermaid_timeline)

    # Theme-based colors
    if theme == "dark":
        bg_color = "#1e1e1e"
        text_color = "#d4d4d4"
        card_bg = "#252526"
        border_color = "#3c3c3c"
        mermaid_theme = "dark"
    else:
        bg_color = "#ffffff"
        text_color = "#333333"
        card_bg = "#f5f5f5"
        border_color = "#e0e0e0"
        mermaid_theme = "default"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2 {{
            margin-bottom: 16px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .mermaid {{
            text-align: center;
        }}
        .tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .tab {{
            padding: 8px 16px;
            border: 1px solid {border_color};
            border-radius: 4px;
            cursor: pointer;
            background: transparent;
            color: {text_color};
        }}
        .tab.active {{
            background: #4CAF50;
            color: white;
            border-color: #4CAF50;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .stat {{
            text-align: center;
            padding: 16px;
            background: {card_bg};
            border-radius: 8px;
            border: 1px solid {border_color};
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        pre {{
            background: {card_bg};
            padding: 16px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{html.escape(title)}</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(data.events)}</div>
                <div class="stat-label">Events</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(data.edges)}</div>
                <div class="stat-label">Relationships</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(len(v) for v in data.annotations.values())}</div>
                <div class="stat-label">Annotations</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('flowchart')">Flowchart</button>
            <button class="tab" onclick="showTab('timeline')">Timeline</button>
            <button class="tab" onclick="showTab('source')">Source</button>
        </div>

        <div id="flowchart" class="tab-content active">
            <div class="card">
                <h2>Event Graph</h2>
                <pre class="mermaid">
{mermaid_flowchart_escaped}
                </pre>
            </div>
        </div>

        <div id="timeline" class="tab-content">
            <div class="card">
                <h2>Timeline View</h2>
                <pre class="mermaid">
{mermaid_timeline_escaped}
                </pre>
            </div>
        </div>

        <div id="source" class="tab-content">
            <div class="card">
                <h2>Mermaid Source</h2>
                <h3>Flowchart</h3>
                <pre>{mermaid_flowchart_escaped}</pre>
                <h3 style="margin-top: 16px;">Timeline</h3>
                <pre>{mermaid_timeline_escaped}</pre>
            </div>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{mermaid_theme}',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});

        function showTab(tabId) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(el => {{
                el.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(el => {{
                el.classList.remove('active');
            }});

            // Show selected tab
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');

            // Re-render mermaid diagrams
            mermaid.contentLoaded();
        }}
    </script>
</body>
</html>"""

    return html_template


# ---- Convenience Functions -----------------------------------------------------------------------------------


def visualize_context(
    store: ContextStore,
    output_format: str = "mermaid",
    limit: int = 50,
    event_types: list[str] | None = None,
    **kwargs: Any,
) -> str:
    """Generate visualization from context store.

    Main entry point for visualization generation.

    Args:
        store: Context store to visualize.
        output_format: Output format ('mermaid', 'mermaid-timeline',
                       'mermaid-git', 'ascii', 'ascii-graph', 'html').
        limit: Maximum events to include.
        event_types: Filter by event types.
        **kwargs: Additional format-specific options.

    Returns:
        Visualization string in requested format.

    Raises:
        ValueError: If output_format is not recognized.
    """
    # Build graph data
    data = GraphData.from_context_store(
        store,
        limit=limit,
        event_types=event_types,
    )

    # Generate requested format
    if output_format == "mermaid":
        return generate_mermaid_flowchart(
            data,
            direction=kwargs.get("direction", "TB"),
            show_annotations=kwargs.get("show_annotations", True),
            title=kwargs.get("title"),
        )
    elif output_format == "mermaid-timeline":
        return generate_mermaid_timeline(
            data,
            title=kwargs.get("title", "Context Timeline"),
        )
    elif output_format == "mermaid-git":
        return generate_mermaid_git_graph(
            data,
            branch_name=kwargs.get("branch_name", "main"),
        )
    elif output_format == "ascii":
        return generate_ascii_timeline(
            data,
            width=kwargs.get("width", 60),
            use_unicode=kwargs.get("use_unicode", True),
        )
    elif output_format == "ascii-graph":
        return generate_ascii_graph(
            data,
            width=kwargs.get("width", 80),
            use_unicode=kwargs.get("use_unicode", True),
        )
    elif output_format == "html":
        return generate_html_visualization(
            data,
            title=kwargs.get("title", "Context Graph"),
            theme=kwargs.get("theme", "light"),
        )
    else:
        msg = f"Unknown output format: {output_format}. "
        msg += "Supported: mermaid, mermaid-timeline, mermaid-git, ascii, ascii-graph, html"
        raise ValueError(msg)
