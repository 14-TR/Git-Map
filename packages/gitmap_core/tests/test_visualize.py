"""Tests for context graph visualization module.

Tests Mermaid diagram generation, ASCII art output, HTML generation,
and the main visualization function.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core: Module under test
"""
from __future__ import annotations

import tempfile
from datetime import datetime
from datetime import timedelta
from pathlib import Path

import pytest

from gitmap_core.context import Annotation
from gitmap_core.context import ContextStore
from gitmap_core.context import Edge
from gitmap_core.context import Event
from gitmap_core.visualize import (
    GraphData,
    _format_event_label,
    _sanitize_mermaid_text,
    _wrap_text,
    generate_ascii_graph,
    generate_ascii_timeline,
    generate_html_visualization,
    generate_mermaid_flowchart,
    generate_mermaid_git_graph,
    generate_mermaid_timeline,
    visualize_context,
)


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def sample_events() -> list[Event]:
    """Create sample events for testing."""
    base_time = datetime.now()
    return [
        Event(
            id="event-001-uuid",
            timestamp=(base_time - timedelta(hours=2)).isoformat(),
            event_type="commit",
            actor="user1",
            repo="/test/repo",
            ref="abc12345",
            payload={"message": "Initial commit", "layers": 3},
        ),
        Event(
            id="event-002-uuid",
            timestamp=(base_time - timedelta(hours=1)).isoformat(),
            event_type="push",
            actor="user1",
            repo="/test/repo",
            ref="abc12345",
            payload={"remote": "portal", "status": "success"},
        ),
        Event(
            id="event-003-uuid",
            timestamp=base_time.isoformat(),
            event_type="commit",
            actor="user2",
            repo="/test/repo",
            ref="def67890",
            payload={"message": "Add accessibility layer", "layers": 4},
        ),
    ]


@pytest.fixture
def sample_edges() -> list[Edge]:
    """Create sample edges for testing."""
    return [
        Edge(
            source_id="event-002-uuid",
            target_id="event-001-uuid",
            relationship="caused_by",
            metadata={"auto": True},
        ),
        Edge(
            source_id="event-003-uuid",
            target_id="event-001-uuid",
            relationship="related_to",
            metadata=None,
        ),
    ]


@pytest.fixture
def sample_annotations() -> dict[str, list[Annotation]]:
    """Create sample annotations for testing."""
    base_time = datetime.now()
    return {
        "event-001-uuid": [
            Annotation(
                id="ann-001",
                event_id="event-001-uuid",
                annotation_type="rationale",
                content="Setting up initial map structure",
                source="user",
                timestamp=base_time.isoformat(),
            ),
        ],
        "event-003-uuid": [
            Annotation(
                id="ann-002",
                event_id="event-003-uuid",
                annotation_type="rationale",
                content="Client requested accessibility features",
                source="user",
                timestamp=base_time.isoformat(),
            ),
            Annotation(
                id="ann-003",
                event_id="event-003-uuid",
                annotation_type="lesson",
                content="Always test color contrast",
                source="agent",
                timestamp=base_time.isoformat(),
            ),
        ],
    }


@pytest.fixture
def graph_data(
    sample_events: list[Event],
    sample_edges: list[Edge],
    sample_annotations: dict[str, list[Annotation]],
) -> GraphData:
    """Create GraphData instance for testing."""
    return GraphData(
        events=sample_events,
        edges=sample_edges,
        annotations=sample_annotations,
    )


@pytest.fixture
def temp_db() -> Path:
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "context.db"


# ---- Helper Function Tests -----------------------------------------------------------------------------------


class TestSanitizeMermaidText:
    """Tests for _sanitize_mermaid_text function."""

    def test_removes_quotes(self) -> None:
        """Test that double quotes are replaced."""
        result = _sanitize_mermaid_text('Hello "world"')
        assert '"' not in result
        assert "'" in result

    def test_removes_brackets(self) -> None:
        """Test that brackets are replaced."""
        result = _sanitize_mermaid_text("Test [brackets] {braces}")
        assert "[" not in result
        assert "]" not in result
        assert "{" not in result
        assert "}" not in result

    def test_removes_angle_brackets(self) -> None:
        """Test that angle brackets are replaced."""
        result = _sanitize_mermaid_text("Test <html> tags")
        assert "<" not in result
        assert ">" not in result

    def test_truncates_long_text(self) -> None:
        """Test that long text is truncated."""
        long_text = "x" * 100
        result = _sanitize_mermaid_text(long_text)
        assert len(result) <= 40
        assert result.endswith("...")

    def test_replaces_newlines(self) -> None:
        """Test that newlines are replaced with spaces."""
        result = _sanitize_mermaid_text("Line 1\nLine 2")
        assert "\n" not in result
        assert "Line 1 Line 2" == result


class TestFormatEventLabel:
    """Tests for _format_event_label function."""

    def test_includes_event_type(self, sample_events: list[Event]) -> None:
        """Test that event type is included."""
        label = _format_event_label(sample_events[0])
        assert "COMMIT" in label

    def test_includes_short_ref(self, sample_events: list[Event]) -> None:
        """Test that ref is truncated."""
        label = _format_event_label(sample_events[0])
        assert "abc12345" in label

    def test_hides_time_when_disabled(self, sample_events: list[Event]) -> None:
        """Test that time can be hidden."""
        label_with_time = _format_event_label(sample_events[0], show_time=True)
        label_no_time = _format_event_label(sample_events[0], show_time=False)
        assert len(label_no_time) < len(label_with_time)


class TestWrapText:
    """Tests for _wrap_text function."""

    def test_wraps_long_text(self) -> None:
        """Test that long text is wrapped."""
        text = "This is a very long line of text that should be wrapped"
        result = _wrap_text(text, width=20)
        assert len(result) > 1
        assert all(len(line) <= 20 for line in result)

    def test_preserves_short_text(self) -> None:
        """Test that short text is not wrapped."""
        text = "Short text"
        result = _wrap_text(text, width=50)
        assert len(result) == 1
        assert result[0] == text

    def test_handles_empty_text(self) -> None:
        """Test that empty text returns single empty line."""
        result = _wrap_text("", width=20)
        assert result == [""]


# ---- Mermaid Generation Tests --------------------------------------------------------------------------------


class TestMermaidFlowchart:
    """Tests for generate_mermaid_flowchart function."""

    def test_generates_valid_mermaid(self, graph_data: GraphData) -> None:
        """Test that valid Mermaid syntax is generated."""
        result = generate_mermaid_flowchart(graph_data)
        assert result.startswith("flowchart")
        assert "TB" in result  # Default direction

    def test_includes_event_nodes(self, graph_data: GraphData) -> None:
        """Test that events are included as nodes."""
        result = generate_mermaid_flowchart(graph_data)
        assert "e_event-00" in result

    def test_includes_edges(self, graph_data: GraphData) -> None:
        """Test that edges are included."""
        result = generate_mermaid_flowchart(graph_data)
        assert "-->" in result or "---" in result

    def test_respects_direction(self, graph_data: GraphData) -> None:
        """Test that direction parameter is respected."""
        result = generate_mermaid_flowchart(graph_data, direction="LR")
        assert "flowchart LR" in result

    def test_includes_annotations_when_enabled(self, graph_data: GraphData) -> None:
        """Test that annotations are included when enabled."""
        result = generate_mermaid_flowchart(graph_data, show_annotations=True)
        assert "a_" in result  # Annotation node prefix

    def test_excludes_annotations_when_disabled(self, graph_data: GraphData) -> None:
        """Test that annotations are excluded when disabled."""
        result = generate_mermaid_flowchart(graph_data, show_annotations=False)
        assert "rationale" not in result.lower()

    def test_includes_styling(self, graph_data: GraphData) -> None:
        """Test that styling classes are included."""
        result = generate_mermaid_flowchart(graph_data)
        assert "classDef commit" in result
        assert "classDef push" in result

    def test_adds_title_comment(self, graph_data: GraphData) -> None:
        """Test that title is added as comment."""
        result = generate_mermaid_flowchart(graph_data, title="Test Graph")
        assert "Test Graph" in result

    def test_links_branch_with_source_commit(self) -> None:
        """Test that branch events with source_commit link FROM that commit."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Initial commit", "branch": "main"},
            ),
            Event(
                id="branch-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="branch",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={
                    "action": "create",
                    "branch_name": "feature/test",
                    "commit_id": "abc12345",  # Source commit
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_flowchart(data)
        # Should have dotted link from source commit to branch
        assert "e_commit-0" in result
        assert "e_branch-0" in result
        assert "-.->" in result  # Dotted arrow for branch creation

    def test_links_branch_to_first_commit_on_branch(self) -> None:
        """Test that branch events link to first commit ON that branch."""
        base_time = datetime.now()
        events = [
            Event(
                id="branch-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="branch",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={"action": "create", "branch_name": "feature/new"},
            ),
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Feature commit", "branch": "feature/new"},
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_flowchart(data)
        # Branch should link to commit on that branch
        assert "e_branch-0" in result
        assert "e_commit-0" in result
        assert "-->" in result

    def test_links_initial_branch_to_next_commit(self) -> None:
        """Test that initial branch without tracking links to first commit after it."""
        base_time = datetime.now()
        events = [
            Event(
                id="branch-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="branch",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={"action": "create", "branch_name": "main"},
            ),
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Initial commit"},  # No branch tracking
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_flowchart(data)
        # Branch should link to next commit
        assert "e_branch-0" in result
        assert "e_commit-0" in result

    def test_merge_commit_connects_to_both_parents(self) -> None:
        """Test that merge commits connect to both parent branches."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=3)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Main commit", "branch": "main"},
            ),
            Event(
                id="commit-002-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="def67890",
                payload={"message": "Feature commit", "branch": "feature"},
            ),
            Event(
                id="commit-003-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="merge1234",
                payload={
                    "message": "Merge feature into main",
                    "parent": "abc12345",
                    "parent2": "def67890",
                    "branch": "main",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_flowchart(data)
        # Merge commit should show as merge shape
        assert "{{" in result  # Merge shape
        # Should have MERGE label instead of COMMIT
        assert "MERGE" in result

    def test_merge_event_connects_source_and_target_branches(self) -> None:
        """Test that merge events connect source and target branches."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=3)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Main commit", "branch": "main"},
            ),
            Event(
                id="commit-002-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="def67890",
                payload={"message": "Feature commit", "branch": "feature"},
            ),
            Event(
                id="merge-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="merge",
                actor="user1",
                repo="/test/repo",
                ref="merge1234",
                payload={
                    "source_branch": "feature",
                    "target_branch": "main",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_flowchart(data)
        # Merge event should use merge shape
        assert "{{" in result
        # Should show MERGE label
        assert "MERGE" in result


class TestMermaidTimeline:
    """Tests for generate_mermaid_timeline function."""

    def test_generates_timeline_syntax(self, graph_data: GraphData) -> None:
        """Test that valid timeline syntax is generated."""
        result = generate_mermaid_timeline(graph_data)
        assert result.startswith("timeline")

    def test_includes_title(self, graph_data: GraphData) -> None:
        """Test that title is included."""
        result = generate_mermaid_timeline(graph_data, title="My Timeline")
        assert "My Timeline" in result

    def test_groups_by_date(self, graph_data: GraphData) -> None:
        """Test that events are grouped by date."""
        result = generate_mermaid_timeline(graph_data)
        assert "section" in result


class TestMermaidGitGraph:
    """Tests for generate_mermaid_git_graph function."""

    def test_generates_git_graph_syntax(self, graph_data: GraphData) -> None:
        """Test that valid gitGraph syntax is generated."""
        result = generate_mermaid_git_graph(graph_data)
        assert result.startswith("gitGraph")

    def test_includes_commits(self, graph_data: GraphData) -> None:
        """Test that commit events are included."""
        result = generate_mermaid_git_graph(graph_data)
        assert "commit" in result

    def test_handles_empty_commits(self) -> None:
        """Test handling of no commit events."""
        data = GraphData(events=[], edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "No commits yet" in result

    def test_handles_merge_commits_with_parent2(self) -> None:
        """Test that merge commits with parent2 are highlighted."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Initial commit"},
            ),
            Event(
                id="commit-002-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="def67890",
                payload={
                    "message": "Merge feature into main",
                    "parent": "abc12345",
                    "parent2": "xyz98765",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "HIGHLIGHT" in result

    def test_handles_merge_events(self) -> None:
        """Test that merge events generate proper merge commands."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Initial commit"},
            ),
            Event(
                id="merge-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="merge",
                actor="user1",
                repo="/test/repo",
                ref="def67890",
                payload={
                    "source_branch": "feature/login",
                    "target_branch": "main",
                    "commit_id": "def67890",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "merge" in result
        # Branch name should be sanitized (slashes become dashes)
        assert "feature-login" in result

    def test_handles_lsm_events(self) -> None:
        """Test that LSM events are rendered as reverse commits."""
        base_time = datetime.now()
        events = [
            Event(
                id="lsm-001-uuid",
                timestamp=base_time.isoformat(),
                event_type="lsm",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={
                    "source": "Portal",
                    "transferred_count": 5,
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "REVERSE" in result
        assert "LSM from Portal" in result
        assert "5 transferred" in result

    def test_handles_branch_creation_events(self) -> None:
        """Test that branch creation events generate branch commands."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={"message": "Initial commit"},
            ),
            Event(
                id="branch-001-uuid",
                timestamp=(base_time - timedelta(hours=1)).isoformat(),
                event_type="branch",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={
                    "action": "create",
                    "branch_name": "feature/new-feature",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "branch feature-new-feature" in result

    def test_handles_commit_without_message(self) -> None:
        """Test that commits without messages get default message."""
        base_time = datetime.now()
        events = [
            Event(
                id="commit-001-uuid",
                timestamp=base_time.isoformat(),
                event_type="commit",
                actor="user1",
                repo="/test/repo",
                ref="abc12345",
                payload={},  # No message
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "Commit abc12345" in result

    def test_handles_checkout_on_merge(self) -> None:
        """Test that merge to different branch triggers checkout."""
        base_time = datetime.now()
        events = [
            Event(
                id="branch-001-uuid",
                timestamp=(base_time - timedelta(hours=2)).isoformat(),
                event_type="branch",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={"action": "create", "branch_name": "develop"},
            ),
            Event(
                id="merge-001-uuid",
                timestamp=base_time.isoformat(),
                event_type="merge",
                actor="user1",
                repo="/test/repo",
                ref=None,
                payload={
                    "source_branch": "develop",
                    "target_branch": "main",
                },
            ),
        ]
        data = GraphData(events=events, edges=[], annotations={})
        result = generate_mermaid_git_graph(data)
        assert "checkout main" in result
        assert "merge develop" in result


# ---- ASCII Generation Tests ----------------------------------------------------------------------------------


class TestAsciiTimeline:
    """Tests for generate_ascii_timeline function."""

    def test_generates_ascii_output(self, graph_data: GraphData) -> None:
        """Test that ASCII output is generated."""
        result = generate_ascii_timeline(graph_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_uses_unicode_by_default(self, graph_data: GraphData) -> None:
        """Test that Unicode characters are used by default."""
        result = generate_ascii_timeline(graph_data, use_unicode=True)
        assert "┌" in result or "─" in result

    def test_uses_simple_ascii_when_requested(self, graph_data: GraphData) -> None:
        """Test that simple ASCII can be used."""
        result = generate_ascii_timeline(graph_data, use_unicode=False)
        assert "+" in result or "-" in result

    def test_respects_width(self, graph_data: GraphData) -> None:
        """Test that width parameter is respected."""
        result = generate_ascii_timeline(graph_data, width=40)
        lines = result.split("\n")
        # Box lines should respect width
        assert all(len(line) <= 42 for line in lines)  # Allow slight overflow

    def test_handles_empty_events(self) -> None:
        """Test handling of no events."""
        data = GraphData(events=[], edges=[], annotations={})
        result = generate_ascii_timeline(data)
        assert "No events" in result


class TestAsciiGraph:
    """Tests for generate_ascii_graph function."""

    def test_generates_ascii_output(self, graph_data: GraphData) -> None:
        """Test that ASCII output is generated."""
        result = generate_ascii_graph(graph_data)
        assert isinstance(result, str)

    def test_includes_legend(self, graph_data: GraphData) -> None:
        """Test that legend is included."""
        result = generate_ascii_graph(graph_data)
        assert "Legend" in result

    def test_shows_relationships(self, graph_data: GraphData) -> None:
        """Test that relationships are shown."""
        result = generate_ascii_graph(graph_data)
        # Should include arrow or relationship indicator
        assert "→" in result or "->" in result


# ---- HTML Generation Tests -----------------------------------------------------------------------------------


class TestHtmlVisualization:
    """Tests for generate_html_visualization function."""

    def test_generates_valid_html(self, graph_data: GraphData) -> None:
        """Test that valid HTML is generated."""
        result = generate_html_visualization(graph_data)
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result

    def test_includes_mermaid_script(self, graph_data: GraphData) -> None:
        """Test that Mermaid.js is included."""
        result = generate_html_visualization(graph_data)
        assert "mermaid" in result.lower()

    def test_includes_title(self, graph_data: GraphData) -> None:
        """Test that title is included."""
        result = generate_html_visualization(graph_data, title="My Graph")
        assert "My Graph" in result

    def test_respects_theme(self, graph_data: GraphData) -> None:
        """Test that theme affects colors."""
        light = generate_html_visualization(graph_data, theme="light")
        dark = generate_html_visualization(graph_data, theme="dark")
        # Dark theme should have different background color
        assert "#1e1e1e" in dark
        assert "#ffffff" in light

    def test_includes_stats(self, graph_data: GraphData) -> None:
        """Test that statistics are included."""
        result = generate_html_visualization(graph_data)
        assert "Events" in result
        assert "Relationships" in result
        assert "Annotations" in result


# ---- Main Visualization Function Tests -----------------------------------------------------------------------


class TestVisualizeContext:
    """Tests for visualize_context function."""

    def test_supports_mermaid_format(self, temp_db: Path) -> None:
        """Test mermaid format output."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Test"}, ref="abc123")

        result = visualize_context(store, output_format="mermaid")
        assert "flowchart" in result
        store.close()

    def test_supports_mermaid_timeline_format(self, temp_db: Path) -> None:
        """Test mermaid-timeline format output."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Test"})

        result = visualize_context(store, output_format="mermaid-timeline")
        assert "timeline" in result
        store.close()

    def test_supports_ascii_format(self, temp_db: Path) -> None:
        """Test ascii format output."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Test"})

        result = visualize_context(store, output_format="ascii")
        assert isinstance(result, str)
        store.close()

    def test_supports_html_format(self, temp_db: Path) -> None:
        """Test html format output."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Test"})

        result = visualize_context(store, output_format="html")
        assert "<!DOCTYPE html>" in result
        store.close()

    def test_raises_for_unknown_format(self, temp_db: Path) -> None:
        """Test that unknown format raises ValueError."""
        store = ContextStore(temp_db)

        with pytest.raises(ValueError) as exc_info:
            visualize_context(store, output_format="invalid")

        assert "Unknown output format" in str(exc_info.value)
        store.close()

    def test_respects_limit(self, temp_db: Path) -> None:
        """Test that limit parameter is respected."""
        store = ContextStore(temp_db)
        # Create many events
        for i in range(10):
            store.record_event("commit", "/repo", {"message": f"Commit {i}"})

        result = visualize_context(store, output_format="ascii", limit=3)
        # Should only show limited events
        store.close()

    def test_filters_by_event_type(self, temp_db: Path) -> None:
        """Test that event_types filter works."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Commit"}, ref="c1")
        store.record_event("push", "/repo", {"remote": "portal"}, ref="c1")

        result = visualize_context(
            store,
            output_format="mermaid",
            event_types=["commit"],
        )
        # Should only include commit events
        assert "COMMIT" in result
        store.close()


# ---- GraphData Tests -----------------------------------------------------------------------------------------


class TestGraphData:
    """Tests for GraphData class."""

    def test_from_context_store(self, temp_db: Path) -> None:
        """Test building GraphData from context store."""
        store = ContextStore(temp_db)
        event = store.record_event(
            "commit",
            "/repo",
            {"message": "Test"},
            rationale="Test rationale",
        )

        data = GraphData.from_context_store(store)

        assert len(data.events) == 1
        assert data.events[0].id == event.id
        assert event.id in data.annotations
        store.close()

    def test_from_context_store_with_limit(self, temp_db: Path) -> None:
        """Test that limit is respected."""
        store = ContextStore(temp_db)
        for i in range(10):
            store.record_event("commit", "/repo", {"message": f"Commit {i}"})

        data = GraphData.from_context_store(store, limit=5)

        assert len(data.events) == 5
        store.close()

    def test_from_context_store_with_event_types(self, temp_db: Path) -> None:
        """Test filtering by event types."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"message": "Commit"})
        store.record_event("push", "/repo", {"remote": "portal"})

        data = GraphData.from_context_store(store, event_types=["commit"])

        assert len(data.events) == 1
        assert data.events[0].event_type == "commit"
        store.close()

    def test_from_context_store_includes_edges(self, temp_db: Path) -> None:
        """Test that edges between events are included."""
        store = ContextStore(temp_db)
        event1 = store.record_event("commit", "/repo", {"message": "First"})
        event2 = store.record_event("push", "/repo", {"remote": "portal"})
        store.add_edge(event2.id, event1.id, "caused_by")

        data = GraphData.from_context_store(store)

        assert len(data.edges) == 1
        assert data.edges[0].source_id == event2.id
        assert data.edges[0].target_id == event1.id
        store.close()
