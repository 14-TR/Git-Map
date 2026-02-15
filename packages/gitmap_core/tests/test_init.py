"""Tests for gitmap_core package __init__ lazy import wrappers.

This module tests that the lazy import wrapper functions in __init__.py
correctly delegate to their underlying implementations in visualize.py.
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import gitmap_core
from gitmap_core.context import ContextStore, Event, Edge
from gitmap_core.visualize import GraphData


@pytest.fixture
def temp_db() -> Path:
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "context.db"


@pytest.fixture
def sample_events() -> list[Event]:
    """Create sample events for testing lazy imports."""
    base_time = datetime.now()
    return [
        Event(
            id="init-event-001",
            timestamp=(base_time - timedelta(hours=2)).isoformat(),
            event_type="commit",
            actor="user1",
            repo="/test/repo",
            ref="abc12345",
            payload={"message": "Initial commit"},
        ),
        Event(
            id="init-event-002",
            timestamp=(base_time - timedelta(hours=1)).isoformat(),
            event_type="branch",
            actor="user1",
            repo="/test/repo",
            ref="main",
            payload={"source_ref": "abc12345"},
        ),
    ]


@pytest.fixture
def sample_edges() -> list[Edge]:
    """Create sample edges for testing."""
    return [
        Edge(
            source_id="init-event-002",
            target_id="init-event-001",
            relationship="derived_from",
            metadata=None,
        ),
    ]


@pytest.fixture
def graph_data(sample_events: list[Event], sample_edges: list[Edge]) -> GraphData:
    """Create GraphData for testing lazy imports."""
    return GraphData(events=sample_events, edges=sample_edges, annotations={})


class TestLazyImports:
    """Test lazy import wrapper functions in __init__.py."""

    def test_generate_ascii_graph_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_ascii_graph lazy import wrapper."""
        result = gitmap_core.generate_ascii_graph(graph_data)

        assert isinstance(result, str)
        # Should contain box drawing characters or ASCII representation
        assert len(result) > 0

    def test_generate_ascii_timeline_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_ascii_timeline lazy import wrapper."""
        result = gitmap_core.generate_ascii_timeline(graph_data)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_html_visualization_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_html_visualization lazy import wrapper."""
        result = gitmap_core.generate_html_visualization(graph_data)

        assert isinstance(result, str)
        assert "<html" in result.lower()

    def test_generate_mermaid_flowchart_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_mermaid_flowchart lazy import wrapper."""
        result = gitmap_core.generate_mermaid_flowchart(graph_data)

        assert isinstance(result, str)
        # Mermaid flowcharts start with flowchart or graph
        assert "flowchart" in result.lower() or "graph" in result.lower()

    def test_generate_mermaid_git_graph_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_mermaid_git_graph lazy import wrapper."""
        result = gitmap_core.generate_mermaid_git_graph(graph_data)

        assert isinstance(result, str)
        assert "gitGraph" in result

    def test_generate_mermaid_timeline_delegates_to_visualize(self, graph_data: GraphData) -> None:
        """Test generate_mermaid_timeline lazy import wrapper."""
        result = gitmap_core.generate_mermaid_timeline(graph_data)

        assert isinstance(result, str)
        assert "timeline" in result.lower()

    def test_visualize_context_delegates_to_visualize(self, temp_db: Path) -> None:
        """Test visualize_context lazy import wrapper."""
        store = ContextStore(temp_db)

        result = gitmap_core.visualize_context(store, output_format="ascii")

        assert isinstance(result, str)


class TestPublicAPI:
    """Test that all public API exports are accessible."""

    def test_version_is_string(self) -> None:
        """Test __version__ is a valid version string."""
        assert isinstance(gitmap_core.__version__, str)
        # Version should follow semver pattern (at least major.minor.patch)
        parts = gitmap_core.__version__.split(".")
        assert len(parts) >= 2

    def test_all_exports_are_accessible(self) -> None:
        """Test all items in __all__ are accessible."""
        for name in gitmap_core.__all__:
            attr = getattr(gitmap_core, name)
            assert attr is not None, f"{name} should be accessible"

    def test_core_models_are_exported(self) -> None:
        """Test core data model classes are exported."""
        assert gitmap_core.Annotation is not None
        assert gitmap_core.Branch is not None
        assert gitmap_core.Commit is not None
        assert gitmap_core.ContextStore is not None
        assert gitmap_core.Edge is not None
        assert gitmap_core.Event is not None
        assert gitmap_core.GraphData is not None
        assert gitmap_core.Remote is not None
        assert gitmap_core.RepoConfig is not None
