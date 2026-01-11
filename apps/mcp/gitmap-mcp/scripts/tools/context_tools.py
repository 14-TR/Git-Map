"""Context graph tools for GitMap MCP server.

Provides tools for searching history, getting timelines,
explaining changes, recording lessons, and visualization.

Execution Context:
    MCP tool module - imported by MCP server

Dependencies:
    - gitmap_core: Repository and context operations

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gitmap_core.repository import find_repository
from gitmap_core.visualize import visualize_context

from .utils import find_repo_from_path


def context_search_history(
    query: str,
    event_types: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
    path: str | None = None,
) -> dict[str, Any]:
    """Search through context history.

    Performs full-text search across events and annotations
    to find relevant history entries.

    Args:
        query: Search query string.
        event_types: Filter by event types (commit, push, pull, merge, etc.).
        start_date: Filter events after this date (ISO format).
        end_date: Filter events before this date (ISO format).
        limit: Maximum results to return.
        path: Optional path to repository directory.

    Returns:
        Dictionary with search results and metadata.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        with repo.get_context_store() as store:
            events = store.search_events(
                query=query,
                event_types=event_types,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            results = []
            for event in events:
                annotations = store.get_annotations(event.id)
                results.append({
                    "event_id": event.id,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "actor": event.actor,
                    "ref": event.ref,
                    "payload": event.payload,
                    "annotations": [
                        {
                            "type": ann.annotation_type,
                            "content": ann.content,
                            "source": ann.source,
                        }
                        for ann in annotations
                    ],
                })

        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results,
        }

    except Exception as search_error:
        return {
            "success": False,
            "error": f"Search failed: {search_error}",
        }


def context_get_timeline(
    ref: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_annotations: bool = True,
    limit: int = 100,
    path: str | None = None,
) -> dict[str, Any]:
    """Get chronological timeline of events.

    Retrieves events in chronological order, optionally filtered
    by ref (commit/branch) and date range.

    Args:
        ref: Filter by specific ref (commit ID or branch name).
        start_date: Filter events after this date (ISO format).
        end_date: Filter events before this date (ISO format).
        include_annotations: Include annotations with events.
        limit: Maximum events to return.
        path: Optional path to repository directory.

    Returns:
        Dictionary with timeline entries.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        with repo.get_context_store() as store:
            timeline = store.get_timeline(
                ref=ref,
                start_date=start_date,
                end_date=end_date,
                include_annotations=include_annotations,
                limit=limit,
            )

        return {
            "success": True,
            "timeline_count": len(timeline),
            "timeline": timeline,
        }

    except Exception as timeline_error:
        return {
            "success": False,
            "error": f"Timeline failed: {timeline_error}",
        }


def context_explain_changes(
    ref: str,
    include_related: bool = True,
    path: str | None = None,
) -> dict[str, Any]:
    """Explain changes for a specific commit or branch.

    Retrieves the event, its annotations (rationale, lessons),
    and related events to explain why changes were made.

    Args:
        ref: Commit ID or branch name to explain.
        include_related: Include related events in explanation.
        path: Optional path to repository directory.

    Returns:
        Dictionary with explanation details.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        with repo.get_context_store() as store:
            # Get events for this ref
            events = store.get_events_by_ref(ref, limit=10)

            if not events:
                return {
                    "success": True,
                    "ref": ref,
                    "explanation": "No recorded context for this ref.",
                    "events": [],
                }

            explanations = []
            for event in events:
                annotations = store.get_annotations(event.id)

                explanation: dict[str, Any] = {
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "actor": event.actor,
                    "payload": event.payload,
                    "rationale": None,
                    "lessons": [],
                    "outcomes": [],
                    "issues": [],
                }

                for ann in annotations:
                    if ann.annotation_type == "rationale":
                        explanation["rationale"] = ann.content
                    elif ann.annotation_type == "lesson":
                        explanation["lessons"].append(ann.content)
                    elif ann.annotation_type == "outcome":
                        explanation["outcomes"].append(ann.content)
                    elif ann.annotation_type == "issue":
                        explanation["issues"].append(ann.content)

                if include_related:
                    related = store.get_related_events(event.id)
                    explanation["related_events"] = [
                        {
                            "event_id": rel_event.id,
                            "event_type": rel_event.event_type,
                            "relationship": relationship,
                            "timestamp": rel_event.timestamp,
                        }
                        for rel_event, relationship in related
                    ]

                explanations.append(explanation)

        return {
            "success": True,
            "ref": ref,
            "explanations": explanations,
        }

    except Exception as explain_error:
        return {
            "success": False,
            "error": f"Explain failed: {explain_error}",
        }


def context_record_lesson(
    content: str,
    related_ref: str | None = None,
    source: str = "agent",
    path: str | None = None,
) -> dict[str, Any]:
    """Record a learned lesson.

    Captures knowledge gained from changes, optionally linked
    to a specific commit or event.

    Args:
        content: The lesson learned.
        related_ref: Optional commit/branch this lesson relates to.
        source: Source of lesson ('user', 'agent', 'auto').
        path: Optional path to repository directory.

    Returns:
        Dictionary with recorded lesson details.
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        with repo.get_context_store() as store:
            # Find related event if ref provided
            related_event_id = None
            if related_ref:
                events = store.get_events_by_ref(related_ref, limit=1)
                if events:
                    related_event_id = events[0].id

            annotation = store.record_lesson(
                content=content,
                related_event_id=related_event_id,
                source=source,
            )

        return {
            "success": True,
            "lesson_id": annotation.id,
            "content": annotation.content,
            "related_event_id": annotation.event_id,
            "timestamp": annotation.timestamp,
            "message": "Lesson recorded successfully.",
        }

    except Exception as lesson_error:
        return {
            "success": False,
            "error": f"Record lesson failed: {lesson_error}",
        }


def context_visualize(
    output_format: str = "mermaid",
    limit: int = 50,
    event_types: list[str] | None = None,
    output_file: str | None = None,
    title: str | None = None,
    direction: str = "TB",
    show_annotations: bool = True,
    theme: str = "light",
    path: str | None = None,
) -> dict[str, Any]:
    """Generate context graph visualization.

    Creates visual representations of the context graph in formats
    viewable directly in IDEs (Mermaid, ASCII, HTML).

    Args:
        output_format: Format for visualization. Options:
            - 'mermaid': Flowchart diagram (default)
            - 'mermaid-timeline': Timeline diagram
            - 'mermaid-git': Git-style commit graph
            - 'ascii': ASCII art timeline
            - 'ascii-graph': ASCII art relationship graph
            - 'html': Interactive HTML page
        limit: Maximum events to include in visualization.
        event_types: Filter by event types (commit, push, pull, merge, branch, diff).
        output_file: Optional file path to save visualization.
        title: Title for the visualization.
        direction: Graph direction for Mermaid flowcharts (TB, BT, LR, RL).
        show_annotations: Include annotations in visualization.
        theme: Color theme for HTML output ('light' or 'dark').
        path: Optional path to repository directory.

    Returns:
        Dictionary with visualization content and metadata.

    Examples:
        # Generate Mermaid diagram
        context_visualize(output_format="mermaid")

        # Export HTML visualization to file
        context_visualize(output_format="html", output_file="graph.html")

        # Get ASCII timeline of commits only
        context_visualize(output_format="ascii", event_types=["commit"])
    """
    try:
        repo = find_repo_from_path(path)

        if not repo:
            return {
                "success": False,
                "error": "Not a GitMap repository. Run gitmap_init first.",
            }

        # Generate visualization
        with repo.get_context_store() as store:
            viz_content = visualize_context(
                store,
                output_format=output_format,
                limit=limit,
                event_types=event_types,
                title=title or "Context Graph",
                direction=direction,
                show_annotations=show_annotations,
                theme=theme,
            )

        result: dict[str, Any] = {
            "success": True,
            "format": output_format,
            "content": viz_content,
        }

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)

            # Wrap Mermaid in markdown code block for .md files
            if output_format.startswith("mermaid") and output_path.suffix == ".md":
                file_content = f"# {title or 'Context Graph'}\n\n```mermaid\n{viz_content}\n```\n"
            else:
                file_content = viz_content

            output_path.write_text(file_content, encoding="utf-8")
            result["output_file"] = str(output_path.absolute())
            result["message"] = f"Visualization saved to {output_file}"

        # Add viewing hints
        if output_format.startswith("mermaid"):
            result["viewing_hint"] = "View in VS Code with Mermaid extension, or paste into GitHub markdown"
        elif output_format == "html":
            result["viewing_hint"] = "Open in browser or IDE HTML preview panel"
        elif output_format.startswith("ascii"):
            result["viewing_hint"] = "View directly in terminal or text editor"

        return result

    except ValueError as format_error:
        return {
            "success": False,
            "error": str(format_error),
        }
    except Exception as viz_error:
        return {
            "success": False,
            "error": f"Visualization failed: {viz_error}",
        }
