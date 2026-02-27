"""Tests for context graph storage module.

Tests Event, Annotation, Edge data classes and ContextStore functionality
including CRUD operations, search, and timeline queries.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.context: Module under test
"""
from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gitmap_core.context import (
    Annotation,
    ContextStore,
    Edge,
    Event,
)

# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def temp_db() -> Path:
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "context.db"


@pytest.fixture
def context_store(temp_db: Path) -> ContextStore:
    """Create context store instance."""
    store = ContextStore(temp_db)
    yield store
    store.close()


@pytest.fixture
def sample_event_data() -> dict:
    """Sample event data for testing."""
    return {
        "id": "test-event-001",
        "timestamp": datetime.now().isoformat(),
        "event_type": "commit",
        "actor": "test_user",
        "repo": "/test/repo",
        "ref": "abc12345",
        "payload": {"message": "Test commit", "layers": 3},
    }


@pytest.fixture
def sample_annotation_data() -> dict:
    """Sample annotation data for testing."""
    return {
        "id": "ann-001",
        "event_id": "test-event-001",
        "annotation_type": "rationale",
        "content": "Testing the context module",
        "source": "user",
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_edge_data() -> dict:
    """Sample edge data for testing."""
    return {
        "source_id": "event-002",
        "target_id": "event-001",
        "relationship": "caused_by",
        "metadata": {"auto": True},
    }


# ---- Event Tests ---------------------------------------------------------------------------------------------


class TestEvent:
    """Tests for Event dataclass."""

    def test_create_event(self, sample_event_data: dict) -> None:
        """Test creating an Event instance."""
        event = Event(**sample_event_data)

        assert event.id == sample_event_data["id"]
        assert event.event_type == "commit"
        assert event.actor == "test_user"
        assert event.repo == "/test/repo"
        assert event.ref == "abc12345"
        assert event.payload["message"] == "Test commit"

    def test_event_to_dict(self, sample_event_data: dict) -> None:
        """Test Event.to_dict() method."""
        event = Event(**sample_event_data)
        result = event.to_dict()

        assert result == sample_event_data
        assert isinstance(result, dict)

    def test_event_from_dict(self, sample_event_data: dict) -> None:
        """Test Event.from_dict() class method."""
        event = Event.from_dict(sample_event_data)

        assert event.id == sample_event_data["id"]
        assert event.event_type == sample_event_data["event_type"]

    def test_event_from_row(self, temp_db: Path) -> None:
        """Test Event.from_row() class method with actual SQLite row."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE events (
                id TEXT, timestamp TEXT, event_type TEXT,
                actor TEXT, repo TEXT, ref TEXT, payload JSON
            )
        """)
        conn.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
            ["ev-001", "2024-01-01T00:00:00", "push", "user", "/repo", "ref1", '{"key": "value"}'],
        )

        cursor = conn.execute("SELECT * FROM events")
        row = cursor.fetchone()
        event = Event.from_row(row)

        assert event.id == "ev-001"
        assert event.event_type == "push"
        assert event.payload == {"key": "value"}

        conn.close()

    def test_event_with_none_values(self) -> None:
        """Test Event with optional None values."""
        event = Event(
            id="test-id",
            timestamp="2024-01-01",
            event_type="commit",
            actor=None,
            repo="/test",
            ref=None,
            payload={},
        )

        assert event.actor is None
        assert event.ref is None


# ---- Annotation Tests ----------------------------------------------------------------------------------------


class TestAnnotation:
    """Tests for Annotation dataclass."""

    def test_create_annotation(self, sample_annotation_data: dict) -> None:
        """Test creating an Annotation instance."""
        annotation = Annotation(**sample_annotation_data)

        assert annotation.id == sample_annotation_data["id"]
        assert annotation.event_id == "test-event-001"
        assert annotation.annotation_type == "rationale"
        assert annotation.content == "Testing the context module"
        assert annotation.source == "user"

    def test_annotation_to_dict(self, sample_annotation_data: dict) -> None:
        """Test Annotation.to_dict() method."""
        annotation = Annotation(**sample_annotation_data)
        result = annotation.to_dict()

        assert result == sample_annotation_data
        assert isinstance(result, dict)

    def test_annotation_from_dict(self, sample_annotation_data: dict) -> None:
        """Test Annotation.from_dict() class method."""
        annotation = Annotation.from_dict(sample_annotation_data)

        assert annotation.id == sample_annotation_data["id"]
        assert annotation.annotation_type == sample_annotation_data["annotation_type"]

    def test_annotation_from_row(self, temp_db: Path) -> None:
        """Test Annotation.from_row() class method with actual SQLite row."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE annotations (
                id TEXT, event_id TEXT, annotation_type TEXT,
                content TEXT, source TEXT, timestamp TEXT
            )
        """)
        conn.execute(
            "INSERT INTO annotations VALUES (?, ?, ?, ?, ?, ?)",
            ["ann-001", "ev-001", "lesson", "Test lesson", "agent", "2024-01-01"],
        )

        cursor = conn.execute("SELECT * FROM annotations")
        row = cursor.fetchone()
        annotation = Annotation.from_row(row)

        assert annotation.id == "ann-001"
        assert annotation.annotation_type == "lesson"
        assert annotation.source == "agent"

        conn.close()

    def test_annotation_with_none_event_id(self) -> None:
        """Test standalone annotation without event_id."""
        annotation = Annotation(
            id="standalone-001",
            event_id=None,
            annotation_type="lesson",
            content="General lesson learned",
            source="user",
            timestamp="2024-01-01",
        )

        assert annotation.event_id is None


# ---- Edge Tests ----------------------------------------------------------------------------------------------


class TestEdge:
    """Tests for Edge dataclass."""

    def test_create_edge(self, sample_edge_data: dict) -> None:
        """Test creating an Edge instance."""
        edge = Edge(**sample_edge_data)

        assert edge.source_id == "event-002"
        assert edge.target_id == "event-001"
        assert edge.relationship == "caused_by"
        assert edge.metadata == {"auto": True}

    def test_edge_to_dict(self, sample_edge_data: dict) -> None:
        """Test Edge.to_dict() method."""
        edge = Edge(**sample_edge_data)
        result = edge.to_dict()

        assert result == sample_edge_data
        assert isinstance(result, dict)

    def test_edge_from_dict(self, sample_edge_data: dict) -> None:
        """Test Edge.from_dict() class method."""
        edge = Edge.from_dict(sample_edge_data)

        assert edge.source_id == sample_edge_data["source_id"]
        assert edge.relationship == sample_edge_data["relationship"]

    def test_edge_from_row(self, temp_db: Path) -> None:
        """Test Edge.from_row() class method with actual SQLite row."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE edges (
                source_id TEXT, target_id TEXT, relationship TEXT, metadata JSON
            )
        """)
        conn.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            ["src-001", "tgt-001", "related_to", '{"key": "value"}'],
        )

        cursor = conn.execute("SELECT * FROM edges")
        row = cursor.fetchone()
        edge = Edge.from_row(row)

        assert edge.source_id == "src-001"
        assert edge.target_id == "tgt-001"
        assert edge.metadata == {"key": "value"}

        conn.close()

    def test_edge_from_row_with_null_metadata(self, temp_db: Path) -> None:
        """Test Edge.from_row() with NULL metadata."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE edges (
                source_id TEXT, target_id TEXT, relationship TEXT, metadata JSON
            )
        """)
        conn.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            ["src-001", "tgt-001", "related_to", None],
        )

        cursor = conn.execute("SELECT * FROM edges")
        row = cursor.fetchone()
        edge = Edge.from_row(row)

        assert edge.metadata is None

        conn.close()

    def test_edge_with_none_metadata(self) -> None:
        """Test Edge with default None metadata."""
        edge = Edge(
            source_id="src",
            target_id="tgt",
            relationship="related_to",
        )

        assert edge.metadata is None


# ---- ContextStore Tests --------------------------------------------------------------------------------------


class TestContextStoreInit:
    """Tests for ContextStore initialization."""

    def test_create_new_database(self, temp_db: Path) -> None:
        """Test creating a new context store creates database."""
        assert not temp_db.exists()

        store = ContextStore(temp_db)

        assert temp_db.exists()
        store.close()

    def test_schema_created(self, temp_db: Path) -> None:
        """Test that database schema is created on init."""
        store = ContextStore(temp_db)

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "events" in tables
        assert "annotations" in tables
        assert "edges" in tables

        conn.close()
        store.close()

    def test_indexes_created(self, temp_db: Path) -> None:
        """Test that indexes are created on init."""
        store = ContextStore(temp_db)

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_events_type" in indexes
        assert "idx_events_ref" in indexes
        assert "idx_events_timestamp" in indexes
        assert "idx_annotations_event" in indexes
        assert "idx_annotations_type" in indexes

        conn.close()
        store.close()

    def test_context_manager(self, temp_db: Path) -> None:
        """Test ContextStore as context manager."""
        with ContextStore(temp_db) as store:
            store.record_event("commit", "/repo", {"msg": "test"})

        # Connection should be closed after context exits
        assert store._conn is None

    def test_generate_id(self) -> None:
        """Test ID generation."""
        id1 = ContextStore.generate_id()
        id2 = ContextStore.generate_id()

        assert id1 != id2
        assert len(id1) == 36  # UUID format


# ---- Event Operations Tests ---------------------------------------------------------------------------------


class TestContextStoreEventOperations:
    """Tests for ContextStore event operations."""

    def test_record_event_basic(self, context_store: ContextStore) -> None:
        """Test recording a basic event."""
        event = context_store.record_event(
            event_type="commit",
            repo="/test/repo",
            payload={"message": "Initial commit"},
        )

        assert event.id is not None
        assert event.event_type == "commit"
        assert event.repo == "/test/repo"
        assert event.payload["message"] == "Initial commit"
        assert event.timestamp is not None

    def test_record_event_with_all_fields(self, context_store: ContextStore) -> None:
        """Test recording event with all fields."""
        event = context_store.record_event(
            event_type="push",
            repo="/test/repo",
            payload={"remote": "origin"},
            actor="test_user",
            ref="abc12345",
        )

        assert event.actor == "test_user"
        assert event.ref == "abc12345"

    def test_record_event_with_rationale(self, context_store: ContextStore) -> None:
        """Test recording event with rationale creates annotation."""
        event = context_store.record_event(
            event_type="commit",
            repo="/repo",
            payload={},
            rationale="This fixes the bug",
        )

        annotations = context_store.get_annotations(event.id)

        assert len(annotations) == 1
        assert annotations[0].annotation_type == "rationale"
        assert annotations[0].content == "This fixes the bug"

    def test_get_event(self, context_store: ContextStore) -> None:
        """Test retrieving an event by ID."""
        created = context_store.record_event("commit", "/repo", {"msg": "test"})

        retrieved = context_store.get_event(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.event_type == created.event_type

    def test_get_event_not_found(self, context_store: ContextStore) -> None:
        """Test get_event returns None for non-existent ID."""
        result = context_store.get_event("non-existent-id")

        assert result is None

    def test_get_events_by_type(self, context_store: ContextStore) -> None:
        """Test filtering events by type."""
        context_store.record_event("commit", "/repo", {})
        context_store.record_event("push", "/repo", {})
        context_store.record_event("commit", "/repo", {})

        commits = context_store.get_events_by_type("commit")
        pushes = context_store.get_events_by_type("push")

        assert len(commits) == 2
        assert len(pushes) == 1

    def test_get_events_by_type_with_limit(self, context_store: ContextStore) -> None:
        """Test limiting events by type query."""
        for i in range(10):
            context_store.record_event("commit", "/repo", {"num": i})

        events = context_store.get_events_by_type("commit", limit=3)

        assert len(events) == 3

    def test_get_events_by_ref(self, context_store: ContextStore) -> None:
        """Test filtering events by ref."""
        context_store.record_event("commit", "/repo", {}, ref="abc123")
        context_store.record_event("push", "/repo", {}, ref="abc123")
        context_store.record_event("commit", "/repo", {}, ref="def456")

        events = context_store.get_events_by_ref("abc123")

        assert len(events) == 2
        assert all(e.ref == "abc123" for e in events)


# ---- Search Tests -------------------------------------------------------------------------------------------


class TestContextStoreSearch:
    """Tests for ContextStore search functionality."""

    def test_search_events_by_payload(self, context_store: ContextStore) -> None:
        """Test searching events by payload content."""
        context_store.record_event("commit", "/repo", {"message": "Add new feature"})
        context_store.record_event("commit", "/repo", {"message": "Fix bug"})
        context_store.record_event("commit", "/repo", {"message": "Update docs"})

        results = context_store.search_events("feature")

        assert len(results) == 1
        assert "feature" in results[0].payload["message"]

    def test_search_events_by_annotation(self, context_store: ContextStore) -> None:
        """Test searching events by annotation content."""
        event = context_store.record_event("commit", "/repo", {"message": "Change"})
        context_store.add_annotation(event.id, "rationale", "Accessibility improvement", "user")

        results = context_store.search_events("Accessibility")

        assert len(results) == 1
        assert results[0].id == event.id

    def test_search_events_with_type_filter(self, context_store: ContextStore) -> None:
        """Test searching with event type filter."""
        context_store.record_event("commit", "/repo", {"message": "test search"})
        context_store.record_event("push", "/repo", {"message": "test search"})

        results = context_store.search_events("search", event_types=["commit"])

        assert len(results) == 1
        assert results[0].event_type == "commit"

    def test_search_events_with_date_filter(self, context_store: ContextStore) -> None:
        """Test searching with date filters."""
        context_store.record_event("commit", "/repo", {"message": "test"})

        now = datetime.now()
        yesterday = (now - timedelta(days=1)).isoformat()
        tomorrow = (now + timedelta(days=1)).isoformat()

        results = context_store.search_events("test", start_date=yesterday, end_date=tomorrow)

        assert len(results) == 1

    def test_search_events_with_limit(self, context_store: ContextStore) -> None:
        """Test search respects limit parameter."""
        for i in range(10):
            context_store.record_event("commit", "/repo", {"message": f"search term {i}"})

        results = context_store.search_events("search", limit=5)

        assert len(results) == 5


# ---- Annotation Operations Tests ----------------------------------------------------------------------------


class TestContextStoreAnnotationOperations:
    """Tests for ContextStore annotation operations."""

    def test_add_annotation(self, context_store: ContextStore) -> None:
        """Test adding an annotation to an event."""
        event = context_store.record_event("commit", "/repo", {})

        annotation = context_store.add_annotation(
            event_id=event.id,
            annotation_type="rationale",
            content="This explains why",
            source="user",
        )

        assert annotation.id is not None
        assert annotation.event_id == event.id
        assert annotation.annotation_type == "rationale"
        assert annotation.content == "This explains why"

    def test_add_standalone_annotation(self, context_store: ContextStore) -> None:
        """Test adding annotation without event_id."""
        annotation = context_store.add_annotation(
            event_id=None,
            annotation_type="lesson",
            content="General best practice",
            source="agent",
        )

        assert annotation.event_id is None

    def test_get_annotations(self, context_store: ContextStore) -> None:
        """Test retrieving annotations for an event."""
        event = context_store.record_event("commit", "/repo", {})
        context_store.add_annotation(event.id, "rationale", "Reason 1", "user")
        context_store.add_annotation(event.id, "lesson", "Lesson 1", "agent")

        annotations = context_store.get_annotations(event.id)

        assert len(annotations) == 2

    def test_get_annotations_empty(self, context_store: ContextStore) -> None:
        """Test getting annotations for event with none."""
        event = context_store.record_event("commit", "/repo", {})

        annotations = context_store.get_annotations(event.id)

        assert len(annotations) == 0

    def test_record_lesson(self, context_store: ContextStore) -> None:
        """Test recording a lesson."""
        lesson = context_store.record_lesson(
            content="Always test edge cases",
            source="agent",
        )

        assert lesson.annotation_type == "lesson"
        assert lesson.content == "Always test edge cases"
        assert lesson.event_id is None

    def test_record_lesson_with_event(self, context_store: ContextStore) -> None:
        """Test recording a lesson related to an event."""
        event = context_store.record_event("commit", "/repo", {})

        lesson = context_store.record_lesson(
            content="Remember to validate inputs",
            related_event_id=event.id,
            source="user",
        )

        assert lesson.event_id == event.id


# ---- Edge Operations Tests ----------------------------------------------------------------------------------


class TestContextStoreEdgeOperations:
    """Tests for ContextStore edge operations."""

    def test_add_edge(self, context_store: ContextStore) -> None:
        """Test adding an edge between events."""
        event1 = context_store.record_event("commit", "/repo", {"msg": "first"})
        event2 = context_store.record_event("push", "/repo", {"msg": "second"})

        edge = context_store.add_edge(
            source_id=event2.id,
            target_id=event1.id,
            relationship="caused_by",
        )

        assert edge.source_id == event2.id
        assert edge.target_id == event1.id
        assert edge.relationship == "caused_by"

    def test_add_edge_with_metadata(self, context_store: ContextStore) -> None:
        """Test adding edge with metadata."""
        event1 = context_store.record_event("commit", "/repo", {})
        event2 = context_store.record_event("commit", "/repo", {})

        edge = context_store.add_edge(
            source_id=event2.id,
            target_id=event1.id,
            relationship="reverts",
            metadata={"auto_detected": True, "confidence": 0.95},
        )

        assert edge.metadata["auto_detected"] is True
        assert edge.metadata["confidence"] == 0.95

    def test_add_edge_upsert(self, context_store: ContextStore) -> None:
        """Test that adding same edge updates instead of fails."""
        event1 = context_store.record_event("commit", "/repo", {})
        event2 = context_store.record_event("commit", "/repo", {})

        edge1 = context_store.add_edge(event2.id, event1.id, "related_to", {"v": 1})
        edge2 = context_store.add_edge(event2.id, event1.id, "related_to", {"v": 2})

        # Should not raise - INSERT OR REPLACE handles duplicates
        assert edge2.metadata["v"] == 2

    def test_get_related_events(self, context_store: ContextStore) -> None:
        """Test getting events related to a given event."""
        event1 = context_store.record_event("commit", "/repo", {"msg": "first"})
        event2 = context_store.record_event("push", "/repo", {"msg": "second"})
        event3 = context_store.record_event("commit", "/repo", {"msg": "third"})

        context_store.add_edge(event2.id, event1.id, "caused_by")
        context_store.add_edge(event3.id, event1.id, "related_to")

        related = context_store.get_related_events(event1.id)

        assert len(related) == 2
        related_ids = {e[0].id for e in related}
        assert event2.id in related_ids
        assert event3.id in related_ids

    def test_get_related_events_by_relationship(self, context_store: ContextStore) -> None:
        """Test filtering related events by relationship type."""
        event1 = context_store.record_event("commit", "/repo", {})
        event2 = context_store.record_event("push", "/repo", {})
        event3 = context_store.record_event("commit", "/repo", {})

        context_store.add_edge(event2.id, event1.id, "caused_by")
        context_store.add_edge(event3.id, event1.id, "related_to")

        related = context_store.get_related_events(event1.id, relationship="caused_by")

        assert len(related) == 1
        assert related[0][0].id == event2.id
        assert related[0][1] == "caused_by"


# ---- Timeline Operations Tests ------------------------------------------------------------------------------


class TestContextStoreTimeline:
    """Tests for ContextStore timeline operations."""

    def test_get_timeline(self, context_store: ContextStore) -> None:
        """Test getting timeline of events."""
        context_store.record_event("commit", "/repo", {"msg": "1"}, ref="abc")
        context_store.record_event("push", "/repo", {"msg": "2"}, ref="abc")

        timeline = context_store.get_timeline()

        assert len(timeline) == 2
        assert "event_id" in timeline[0]
        assert "timestamp" in timeline[0]
        assert "event_type" in timeline[0]

    def test_get_timeline_with_annotations(self, context_store: ContextStore) -> None:
        """Test timeline includes annotations."""
        event = context_store.record_event("commit", "/repo", {})
        context_store.add_annotation(event.id, "rationale", "Why", "user")

        timeline = context_store.get_timeline(include_annotations=True)

        assert len(timeline) == 1
        assert "annotations" in timeline[0]
        assert len(timeline[0]["annotations"]) == 1

    def test_get_timeline_without_annotations(self, context_store: ContextStore) -> None:
        """Test timeline can exclude annotations."""
        event = context_store.record_event("commit", "/repo", {})
        context_store.add_annotation(event.id, "rationale", "Why", "user")

        timeline = context_store.get_timeline(include_annotations=False)

        assert "annotations" not in timeline[0]

    def test_get_timeline_filter_by_ref(self, context_store: ContextStore) -> None:
        """Test filtering timeline by ref."""
        context_store.record_event("commit", "/repo", {}, ref="branch-a")
        context_store.record_event("commit", "/repo", {}, ref="branch-b")
        context_store.record_event("push", "/repo", {}, ref="branch-a")

        timeline = context_store.get_timeline(ref="branch-a")

        assert len(timeline) == 2
        assert all(entry["ref"] == "branch-a" for entry in timeline)

    def test_get_timeline_with_limit(self, context_store: ContextStore) -> None:
        """Test timeline respects limit."""
        for i in range(20):
            context_store.record_event("commit", "/repo", {"num": i})

        timeline = context_store.get_timeline(limit=5)

        assert len(timeline) == 5

    def test_get_timeline_date_filters(self, context_store: ContextStore) -> None:
        """Test timeline with date range filters."""
        context_store.record_event("commit", "/repo", {"msg": "test"})

        now = datetime.now()
        future = (now + timedelta(days=1)).isoformat()

        # Events before future date
        timeline = context_store.get_timeline(end_date=future)
        assert len(timeline) == 1

        # Events after future date (none)
        timeline = context_store.get_timeline(start_date=future)
        assert len(timeline) == 0


# ---- Utility Tests ------------------------------------------------------------------------------------------


class TestContextStoreUtility:
    """Tests for ContextStore utility methods."""

    def test_close(self, temp_db: Path) -> None:
        """Test closing the database connection."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {})

        store.close()

        assert store._conn is None

    def test_close_multiple_times(self, temp_db: Path) -> None:
        """Test closing multiple times doesn't raise."""
        store = ContextStore(temp_db)

        store.close()
        store.close()  # Should not raise

    def test_reopen_after_close(self, temp_db: Path) -> None:
        """Test that connection is recreated on access after close."""
        store = ContextStore(temp_db)
        store.record_event("commit", "/repo", {"msg": "first"})
        store.close()

        # Accessing connection should recreate it
        event = store.record_event("commit", "/repo", {"msg": "second"})

        assert event is not None
        store.close()

    def test_wal_mode_enabled(self, temp_db: Path) -> None:
        """Test that WAL journal mode is enabled."""
        store = ContextStore(temp_db)

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode.lower() == "wal"

        conn.close()
        store.close()
