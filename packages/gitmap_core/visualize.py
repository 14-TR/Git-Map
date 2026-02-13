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
    "lsm": "fa:fa-layer-group",
    "diff": "fa:fa-file-diff",
}

# Event type shapes for Mermaid
# Using simpler shapes that render reliably across Mermaid versions
EVENT_SHAPES = {
    "commit": ("([", "])"),  # Stadium shape (pill)
    "push": ("[[", "]]"),  # Subroutine shape (double border)
    "pull": ("[[", "]]"),  # Subroutine shape (double border)
    "merge": ("{{", "}}"),  # Hexagon shape
    "branch": ("[", "]"),  # Rectangle (simple, reliable)
    "lsm": ("[", "]"),  # Rectangle (trapezoid syntax unreliable)
    "diff": ("[", "]"),  # Rectangle (parallelogram syntax unreliable)
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

    # Track merge commits for special handling
    merge_commits: set[str] = set()
    # Track commit refs that have merge events (to deduplicate)
    merge_commit_refs: set[str] = set()
    # Events to skip (duplicates)
    skip_events: set[str] = set()
    # Map merge commit IDs to their source branch (from merge events)
    merge_source_branches: dict[str, str] = {}  # commit_id[:8] -> source_branch

    # First pass: identify merge events and their associated commits
    # If a merge event has a commit_id, we'll skip it if there's a matching commit
    for event in data.events:
        if event.event_type == "merge":
            payload = event.payload or {}
            commit_id = payload.get("commit_id")
            source_branch = payload.get("source_branch")
            if commit_id:
                merge_commit_refs.add(commit_id[:8])
                if source_branch:
                    merge_source_branches[commit_id[:8]] = source_branch

    # Check for duplicate merge events (skip merge event if commit exists)
    for event in data.events:
        if event.event_type == "merge":
            payload = event.payload or {}
            commit_id = payload.get("commit_id")
            if commit_id:
                # Check if there's a commit event with matching ref
                for other in data.events:
                    if other.event_type == "commit" and other.ref:
                        if other.ref.startswith(commit_id[:8]):
                            # Skip this merge event, keep the commit
                            skip_events.add(event.id)
                            break

    # Add event nodes
    for event in data.events:
        # Skip duplicate events
        if event.id in skip_events:
            continue

        node_id = f"e_{event.id[:8]}"
        label = _sanitize_mermaid_text(_format_event_label(event))
        payload = event.payload or {}

        # Check if this is a merge commit:
        # 1. Has parent2 set, OR
        # 2. Message starts with "Merge", OR
        # 3. It's a merge event type
        is_merge_commit = False
        if event.event_type == "commit":
            message = payload.get("message", "")
            has_parent2 = payload.get("parent2") is not None
            is_merge_message = message.lower().startswith("merge")
            is_merge_commit = has_parent2 or is_merge_message
        elif event.event_type == "merge":
            is_merge_commit = True

        if is_merge_commit:
            merge_commits.add(event.id)
            # Use merge shape for merge commits
            shape_l, shape_r = EVENT_SHAPES.get("merge", ("{{", "}}"))
            # Update label to indicate it's a merge
            if "COMMIT" in label:
                label = label.replace("COMMIT", "MERGE")
        else:
            # Get shape for event type
            shape_l, shape_r = EVENT_SHAPES.get(event.event_type, ("[", "]"))

        lines.append(f"    {node_id}{shape_l}\"{label}\"{shape_r}")

    # Track which node pairs are connected by explicit edges
    connected_pairs: set[tuple[str, str]] = set()

    # Add explicit edge connections
    for edge in data.edges:
        source_id = f"e_{edge.source_id[:8]}"
        target_id = f"e_{edge.target_id[:8]}"
        arrow = EDGE_STYLES.get(edge.relationship, "-->")

        # Check if both nodes exist
        source_exists = any(e.id == edge.source_id for e in data.events)
        target_exists = any(e.id == edge.target_id for e in data.events)

        if source_exists and target_exists:
            connected_pairs.add((source_id, target_id))
            connected_pairs.add((target_id, source_id))  # Mark both directions
            if edge.relationship in ("reverts", "learned_from"):
                lines.append(f"    {source_id} {arrow} {target_id}")
            else:
                lines.append(f"    {source_id} --> |{edge.relationship}| {target_id}")

    # Sort events oldest first for chronological flow (excluding skipped duplicates)
    sorted_events = sorted(
        [e for e in data.events if e.id not in skip_events],
        key=lambda e: e.timestamp
    )
    branch_events = [e for e in sorted_events if e.event_type == "branch"]
    commit_events = [e for e in sorted_events if e.event_type == "commit"]
    non_branch_events = [e for e in sorted_events if e.event_type != "branch"]

    # Group commits by branch for proper parallel visualization
    commits_by_branch: dict[str, list[Event]] = {}
    commits_without_branch: list[Event] = []

    for event in non_branch_events:
        payload = event.payload or {}
        branch_name = payload.get("branch")
        if branch_name:
            if branch_name not in commits_by_branch:
                commits_by_branch[branch_name] = []
            commits_by_branch[branch_name].append(event)
        else:
            commits_without_branch.append(event)

    # Link events within the same branch chronologically
    for branch_name, events in commits_by_branch.items():
        sorted_branch_events = sorted(events, key=lambda e: e.timestamp)
        for i in range(len(sorted_branch_events) - 1):
            current_event = sorted_branch_events[i]
            next_event = sorted_branch_events[i + 1]
            current_id = f"e_{current_event.id[:8]}"
            next_id = f"e_{next_event.id[:8]}"
            if (current_id, next_id) not in connected_pairs:
                lines.append(f"    {current_id} --> {next_id}")

    # For events without branch info, link them chronologically (legacy support)
    for i in range(len(commits_without_branch) - 1):
        current_event = commits_without_branch[i]
        next_event = commits_without_branch[i + 1]
        current_id = f"e_{current_event.id[:8]}"
        next_id = f"e_{next_event.id[:8]}"
        if (current_id, next_id) not in connected_pairs:
            lines.append(f"    {current_id} --> {next_id}")

    # Link branch events properly
    # 1. If branch has a source commit, link FROM that commit (fork point)
    # 2. If branch has no source commit (initial branch), link TO the first commit on that branch
    for branch_event in branch_events:
        branch_id = f"e_{branch_event.id[:8]}"
        payload = branch_event.payload or {}
        source_commit = payload.get("commit_id")
        branch_name = payload.get("branch_name")

        if source_commit:
            # Branch was created from a specific commit - link FROM that commit
            for commit in commit_events:
                if commit.ref and commit.ref.startswith(source_commit[:8]):
                    commit_id = f"e_{commit.id[:8]}"
                    if (commit_id, branch_id) not in connected_pairs:
                        lines.append(f"    {commit_id} -.-> {branch_id}")
                    break

        # Link branch to first commit ON that branch
        if branch_name and branch_name in commits_by_branch:
            first_commit_on_branch = commits_by_branch[branch_name][0]
            first_commit_id = f"e_{first_commit_on_branch.id[:8]}"
            if (branch_id, first_commit_id) not in connected_pairs:
                lines.append(f"    {branch_id} --> {first_commit_id}")
        elif not source_commit:
            # Initial branch without branch tracking - link to first commit after it
            for commit in commit_events:
                if commit.timestamp > branch_event.timestamp:
                    commit_id = f"e_{commit.id[:8]}"
                    if (branch_id, commit_id) not in connected_pairs:
                        lines.append(f"    {branch_id} --> {commit_id}")
                    break

    # Connect merge commits to BOTH parent branches
    # This shows where branches rejoin
    for event in data.events:
        if event.id in merge_commits:
            payload = event.payload or {}
            merge_id = f"e_{event.id[:8]}"

            if event.event_type == "commit":
                # For commit events, use parent and parent2
                parent1 = payload.get("parent")
                parent2 = payload.get("parent2")

                # Find parent1 commit event and connect
                if parent1:
                    for commit in commit_events:
                        if commit.ref and commit.ref.startswith(parent1[:8]):
                            parent1_id = f"e_{commit.id[:8]}"
                            if (parent1_id, merge_id) not in connected_pairs:
                                lines.append(f"    {parent1_id} --> {merge_id}")
                                connected_pairs.add((parent1_id, merge_id))
                            break

                # Find parent2 commit event and connect (the merged-in branch)
                if parent2:
                    for commit in commit_events:
                        if commit.ref and commit.ref.startswith(parent2[:8]):
                            parent2_id = f"e_{commit.id[:8]}"
                            if (parent2_id, merge_id) not in connected_pairs:
                                lines.append(f"    {parent2_id} --> {merge_id}")
                                connected_pairs.add((parent2_id, merge_id))
                            break

                # If no parent2 but we have source_branch info from merge event
                if not parent2 and event.ref:
                    source_branch = merge_source_branches.get(event.ref[:8])
                    if source_branch and source_branch in commits_by_branch:
                        source_commits = commits_by_branch[source_branch]
                        if source_commits:
                            last_source = source_commits[-1]
                            source_id = f"e_{last_source.id[:8]}"
                            if (source_id, merge_id) not in connected_pairs:
                                lines.append(f"    {source_id} --> {merge_id}")
                                connected_pairs.add((source_id, merge_id))

            elif event.event_type == "merge":
                # For merge events, use source_branch and target_branch
                source_branch = payload.get("source_branch")
                target_branch = payload.get("target_branch")

                # Find the last commit on source branch and connect to merge
                if source_branch and source_branch in commits_by_branch:
                    source_commits = commits_by_branch[source_branch]
                    if source_commits:
                        last_source = source_commits[-1]  # Last commit on source branch
                        source_id = f"e_{last_source.id[:8]}"
                        if (source_id, merge_id) not in connected_pairs:
                            lines.append(f"    {source_id} --> {merge_id}")
                            connected_pairs.add((source_id, merge_id))

                # Find the last commit on target branch before merge and connect
                if target_branch and target_branch in commits_by_branch:
                    target_commits = [c for c in commits_by_branch[target_branch]
                                      if c.timestamp < event.timestamp]
                    if target_commits:
                        last_target = target_commits[-1]
                        target_id = f"e_{last_target.id[:8]}"
                        if (target_id, merge_id) not in connected_pairs:
                            lines.append(f"    {target_id} --> {merge_id}")
                            connected_pairs.add((target_id, merge_id))

    # Add annotation nodes when enabled
    annotation_node_ids: list[str] = []
    if show_annotations and data.annotations:
        lines.append("")
        lines.append("    %% Annotations")
        for event_id, annotations in data.annotations.items():
            event_node_id = f"e_{event_id[:8]}"
            for ann in annotations:
                ann_node_id = f"a_{ann.id[:8]}"
                annotation_node_ids.append(ann_node_id)
                # Use note shape for annotations (asymmetric)
                ann_label = _sanitize_mermaid_text(
                    f"{ann.annotation_type.upper()}: {ann.content}"
                )
                lines.append(f"    {ann_node_id}>{{\"{ann_label}\"}}")
                # Connect annotation to its event with dashed line
                lines.append(f"    {ann_node_id} -.-> {event_node_id}")

    # Add styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef commit fill:#4CAF50,color:#fff")
    lines.append("    classDef push fill:#2196F3,color:#fff")
    lines.append("    classDef pull fill:#9C27B0,color:#fff")
    lines.append("    classDef merge fill:#FF9800,color:#fff")
    lines.append("    classDef branch fill:#00BCD4,color:#fff")
    lines.append("    classDef annotation fill:#FFF9C4,color:#333")

    # Apply styles to nodes (skip duplicates)
    for event in data.events:
        if event.id in skip_events:
            continue
        node_id = f"e_{event.id[:8]}"
        if event.id in merge_commits:
            # Merge commits get merge styling (orange hexagon)
            lines.append(f"    class {node_id} merge")
        elif event.event_type in ("commit", "push", "pull", "merge", "branch"):
            lines.append(f"    class {node_id} {event.event_type}")

    # Apply annotation styling
    for ann_node_id in annotation_node_ids:
        lines.append(f"    class {ann_node_id} annotation")

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
    """Generate Mermaid gitGraph diagram from commit/merge/branch events.

    This shows the git history with proper branch topology including:
    - Commits on branches
    - Branch creation points
    - Merge points where branches join

    Args:
        data: Graph data to visualize.
        branch_name: Name for the main branch.

    Returns:
        Mermaid gitGraph diagram string.
    """
    lines = []
    lines.append("gitGraph")

    # Filter relevant events (commits, merges, branches)
    commits = [e for e in data.events if e.event_type == "commit"]
    merges = [e for e in data.events if e.event_type == "merge"]
    branches = [e for e in data.events if e.event_type == "branch"]
    lsms = [e for e in data.events if e.event_type == "lsm"]

    # Sort all events by timestamp
    all_events = commits + merges + branches + lsms
    all_events.sort(key=lambda e: e.timestamp)

    # Track active branches
    active_branches: set[str] = {branch_name}
    current_branch = branch_name

    # Build parent-to-children map for branch detection
    parent_to_children: dict[str, list[str]] = {}
    commit_to_branch: dict[str, str] = {}

    # First pass: analyze branch structure from events
    for event in all_events:
        if event.event_type == "branch":
            payload = event.payload or {}
            action = payload.get("action", "")
            br_name = payload.get("branch_name", "")
            if action == "create" and br_name:
                active_branches.add(br_name)
        elif event.event_type == "commit":
            payload = event.payload or {}
            parent = payload.get("parent")
            commit_id = event.ref or event.id[:12]
            if parent:
                if parent not in parent_to_children:
                    parent_to_children[parent] = []
                parent_to_children[parent].append(commit_id)

    # Second pass: generate mermaid commands
    for event in all_events:
        if event.event_type == "branch":
            payload = event.payload or {}
            action = payload.get("action", "")
            br_name = payload.get("branch_name", "")
            if action == "create" and br_name and br_name != branch_name:
                lines.append(f"    branch {_sanitize_branch_name(br_name)}")
                current_branch = br_name

        elif event.event_type == "commit":
            payload = event.payload or {}
            msg = payload.get("message", "")
            if not msg:
                msg = f"Commit {event.ref[:8] if event.ref else event.id[:8]}"
            msg = _sanitize_mermaid_text(msg)
            commit_id = (event.ref[:8] if event.ref else event.id[:8])

            # Check if this is a merge commit (has parent2)
            parent2 = payload.get("parent2")
            if parent2:
                lines.append(f'    commit id: "{commit_id}" msg: "{msg}" type: HIGHLIGHT')
            else:
                lines.append(f'    commit id: "{commit_id}" msg: "{msg}"')

        elif event.event_type == "merge":
            payload = event.payload or {}
            source_branch = payload.get("source_branch", "feature")
            target_branch = payload.get("target_branch", branch_name)
            commit_id = payload.get("commit_id", "")

            # Checkout target branch and merge
            if target_branch != current_branch:
                lines.append(f"    checkout {_sanitize_branch_name(target_branch)}")
                current_branch = target_branch

            lines.append(f"    merge {_sanitize_branch_name(source_branch)}")

        elif event.event_type == "lsm":
            payload = event.payload or {}
            source = payload.get("source", "source")
            transferred = payload.get("transferred_count", 0)
            msg = f"LSM from {source} ({transferred} transferred)"
            msg = _sanitize_mermaid_text(msg)
            lines.append(f'    commit id: "lsm-{event.id[:6]}" msg: "{msg}" type: REVERSE')

    if not all_events:
        lines.append('    commit id: "initial" msg: "No commits yet"')

    return "\n".join(lines)


def _sanitize_branch_name(name: str) -> str:
    """Sanitize branch name for Mermaid gitGraph.

    Args:
        name: Branch name to sanitize.

    Returns:
        Sanitized branch name (alphanumeric and dashes only).
    """
    # Replace slashes and other special chars with dashes
    sanitized = re.sub(r"[^a-zA-Z0-9-]", "-", name)
    # Remove consecutive dashes
    sanitized = re.sub(r"-+", "-", sanitized)
    # Remove leading/trailing dashes
    return sanitized.strip("-") or "branch"


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
