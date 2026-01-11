"""Context graph storage for GitMap.

Provides SQLite-backed event store for tracking operations, rationales,
and relationships between events. Enables episodic memory and context
awareness for IDE agents.

Execution Context:
    Library module - imported by other gitmap_core modules

Dependencies:
    - sqlite3: Database operations (stdlib)
    - uuid: ID generation (stdlib)

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


# ---- Data Model Classes -------------------------------------------------------------------------------------


@dataclass
class Event:
    """Context graph event.

    Attributes:
        id: Unique event identifier.
        timestamp: ISO 8601 timestamp.
        event_type: Type of event (commit, push, pull, merge, branch, diff).
        actor: Who performed the event.
        repo: Repository path.
        ref: Related reference (commit ID, branch name).
        payload: Event-specific data.
    """

    id: str
    timestamp: str
    event_type: str
    actor: str | None
    repo: str
    ref: str | None
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Create event from dictionary.

        Args:
            data: Dictionary with event fields.

        Returns:
            Event instance.
        """
        return cls(**data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Event:
        """Create event from database row.

        Args:
            row: SQLite row with event data.

        Returns:
            Event instance.
        """
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            actor=row["actor"],
            repo=row["repo"],
            ref=row["ref"],
            payload=json.loads(row["payload"]),
        )


@dataclass
class Annotation:
    """Annotation attached to an event.

    Attributes:
        id: Unique annotation identifier.
        event_id: ID of associated event (can be None for standalone lessons).
        annotation_type: Type (rationale, lesson, outcome, issue).
        content: Annotation text content.
        source: Who created the annotation (user, agent, auto).
        timestamp: ISO 8601 timestamp.
    """

    id: str
    event_id: str | None
    annotation_type: str
    content: str
    source: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert annotation to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Annotation:
        """Create annotation from dictionary.

        Args:
            data: Dictionary with annotation fields.

        Returns:
            Annotation instance.
        """
        return cls(**data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Annotation:
        """Create annotation from database row.

        Args:
            row: SQLite row with annotation data.

        Returns:
            Annotation instance.
        """
        return cls(
            id=row["id"],
            event_id=row["event_id"],
            annotation_type=row["annotation_type"],
            content=row["content"],
            source=row["source"],
            timestamp=row["timestamp"],
        )


@dataclass
class Edge:
    """Relationship between events.

    Attributes:
        source_id: Source event ID.
        target_id: Target event ID.
        relationship: Type of relationship (caused_by, reverts, related_to, learned_from).
        metadata: Optional additional data.
    """

    source_id: str
    target_id: str
    relationship: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        """Create edge from dictionary.

        Args:
            data: Dictionary with edge fields.

        Returns:
            Edge instance.
        """
        return cls(**data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Edge:
        """Create edge from database row.

        Args:
            row: SQLite row with edge data.

        Returns:
            Edge instance.
        """
        metadata = row["metadata"]
        return cls(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relationship=row["relationship"],
            metadata=json.loads(metadata) if metadata else None,
        )


# ---- Context Store Class ------------------------------------------------------------------------------------


class ContextStore:
    """SQLite-backed context graph storage.

    Manages events, annotations, and edges for context-aware
    version control operations.

    Attributes:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize context store with SQLite database.

        Args:
            db_path: Path to context.db file.
        """
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._ensure_schema()

    @property
    def _connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            SQLite connection with row factory.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _ensure_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self._connection
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT,
                repo TEXT NOT NULL,
                ref TEXT,
                payload JSON NOT NULL
            );

            CREATE TABLE IF NOT EXISTS annotations (
                id TEXT PRIMARY KEY,
                event_id TEXT REFERENCES events(id),
                annotation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT REFERENCES events(id),
                target_id TEXT REFERENCES events(id),
                relationship TEXT NOT NULL,
                metadata JSON,
                PRIMARY KEY (source_id, target_id, relationship)
            );

            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_ref ON events(ref);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_annotations_event ON annotations(event_id);
            CREATE INDEX IF NOT EXISTS idx_annotations_type ON annotations(annotation_type);
        """)
        conn.commit()

    @staticmethod
    def generate_id() -> str:
        """Generate unique identifier.

        Returns:
            UUID string.
        """
        return str(uuid4())

    # ---- Event Operations -----------------------------------------------------------------------------------

    def record_event(
        self,
        event_type: str,
        repo: str,
        payload: dict[str, Any],
        actor: str | None = None,
        ref: str | None = None,
        rationale: str | None = None,
    ) -> Event:
        """Record a new event, optionally with rationale annotation.

        Args:
            event_type: Type of event (commit, push, pull, merge, branch, diff).
            repo: Repository path.
            payload: Event-specific data.
            actor: Who performed the event.
            ref: Related reference (commit ID, branch name).
            rationale: Optional rationale to annotate immediately.

        Returns:
            Created Event instance.
        """
        event_id = self.generate_id()
        timestamp = datetime.now().isoformat()

        conn = self._connection
        conn.execute(
            """
            INSERT INTO events (id, timestamp, event_type, actor, repo, ref, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [event_id, timestamp, event_type, actor, repo, ref, json.dumps(payload)],
        )
        conn.commit()

        event = Event(
            id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            actor=actor,
            repo=repo,
            ref=ref,
            payload=payload,
        )

        # If rationale provided, annotate immediately
        if rationale:
            self.add_annotation(
                event_id=event_id,
                annotation_type="rationale",
                content=rationale,
                source="user",
            )

        return event

    def get_event(self, event_id: str) -> Event | None:
        """Retrieve event by ID.

        Args:
            event_id: Event identifier.

        Returns:
            Event instance or None if not found.
        """
        conn = self._connection
        cursor = conn.execute(
            "SELECT * FROM events WHERE id = ?",
            [event_id],
        )
        row = cursor.fetchone()
        return Event.from_row(row) if row else None

    def get_events_by_type(
        self,
        event_type: str,
        limit: int = 50,
    ) -> list[Event]:
        """Get events filtered by type.

        Args:
            event_type: Event type to filter by.
            limit: Maximum results to return.

        Returns:
            List of matching events.
        """
        conn = self._connection
        cursor = conn.execute(
            """
            SELECT * FROM events
            WHERE event_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [event_type, limit],
        )
        return [Event.from_row(row) for row in cursor.fetchall()]

    def get_events_by_ref(
        self,
        ref: str,
        limit: int = 50,
    ) -> list[Event]:
        """Get events related to a specific ref.

        Args:
            ref: Commit ID or branch name.
            limit: Maximum results to return.

        Returns:
            List of matching events.
        """
        conn = self._connection
        cursor = conn.execute(
            """
            SELECT * FROM events
            WHERE ref = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [ref, limit],
        )
        return [Event.from_row(row) for row in cursor.fetchall()]

    def search_events(
        self,
        query: str,
        event_types: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
    ) -> list[Event]:
        """Search across events and annotations by keyword.

        Args:
            query: Search query string.
            event_types: Filter by event types.
            start_date: Filter events after this date (ISO format).
            end_date: Filter events before this date (ISO format).
            limit: Maximum results to return.

        Returns:
            List of matching events.
        """
        conn = self._connection

        # Build query with search in payload and annotations
        sql = """
            SELECT DISTINCT e.* FROM events e
            LEFT JOIN annotations a ON e.id = a.event_id
            WHERE (
                e.payload LIKE ?
                OR a.content LIKE ?
            )
        """
        params: list[Any] = [f"%{query}%", f"%{query}%"]

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            sql += f" AND e.event_type IN ({placeholders})"
            params.extend(event_types)

        if start_date:
            sql += " AND e.timestamp >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND e.timestamp <= ?"
            params.append(end_date)

        sql += " ORDER BY e.timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        return [Event.from_row(row) for row in cursor.fetchall()]

    # ---- Annotation Operations ------------------------------------------------------------------------------

    def add_annotation(
        self,
        event_id: str | None,
        annotation_type: str,
        content: str,
        source: str = "user",
    ) -> Annotation:
        """Add annotation to an event.

        Args:
            event_id: ID of event to annotate (can be None for standalone).
            annotation_type: Type (rationale, lesson, outcome, issue).
            content: Annotation text content.
            source: Who created the annotation.

        Returns:
            Created Annotation instance.
        """
        annotation_id = self.generate_id()
        timestamp = datetime.now().isoformat()

        conn = self._connection
        conn.execute(
            """
            INSERT INTO annotations (id, event_id, annotation_type, content, source, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [annotation_id, event_id, annotation_type, content, source, timestamp],
        )
        conn.commit()

        return Annotation(
            id=annotation_id,
            event_id=event_id,
            annotation_type=annotation_type,
            content=content,
            source=source,
            timestamp=timestamp,
        )

    def get_annotations(
        self,
        event_id: str,
    ) -> list[Annotation]:
        """Get all annotations for an event.

        Args:
            event_id: Event identifier.

        Returns:
            List of annotations.
        """
        conn = self._connection
        cursor = conn.execute(
            """
            SELECT * FROM annotations
            WHERE event_id = ?
            ORDER BY timestamp ASC
            """,
            [event_id],
        )
        return [Annotation.from_row(row) for row in cursor.fetchall()]

    def record_lesson(
        self,
        content: str,
        related_event_id: str | None = None,
        source: str = "user",
    ) -> Annotation:
        """Record a learned lesson.

        Args:
            content: The lesson learned.
            related_event_id: Optional event this lesson relates to.
            source: Source of lesson (user, agent, auto).

        Returns:
            Created Annotation instance.
        """
        return self.add_annotation(
            event_id=related_event_id,
            annotation_type="lesson",
            content=content,
            source=source,
        )

    # ---- Edge Operations ------------------------------------------------------------------------------------

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        metadata: dict[str, Any] | None = None,
    ) -> Edge:
        """Create relationship between events.

        Args:
            source_id: Source event ID.
            target_id: Target event ID.
            relationship: Type of relationship (caused_by, reverts, related_to, learned_from).
            metadata: Optional additional data.

        Returns:
            Created Edge instance.
        """
        conn = self._connection
        conn.execute(
            """
            INSERT OR REPLACE INTO edges (source_id, target_id, relationship, metadata)
            VALUES (?, ?, ?, ?)
            """,
            [source_id, target_id, relationship, json.dumps(metadata) if metadata else None],
        )
        conn.commit()

        return Edge(
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            metadata=metadata,
        )

    def get_related_events(
        self,
        event_id: str,
        relationship: str | None = None,
    ) -> list[tuple[Event, str]]:
        """Get events related to given event.

        Args:
            event_id: Event identifier.
            relationship: Filter by relationship type.

        Returns:
            List of (event, relationship) tuples.
        """
        conn = self._connection

        sql = """
            SELECT e.*, ed.relationship FROM events e
            JOIN edges ed ON (e.id = ed.target_id OR e.id = ed.source_id)
            WHERE (ed.source_id = ? OR ed.target_id = ?)
            AND e.id != ?
        """
        params: list[Any] = [event_id, event_id, event_id]

        if relationship:
            sql += " AND ed.relationship = ?"
            params.append(relationship)

        cursor = conn.execute(sql, params)
        return [(Event.from_row(row), row["relationship"]) for row in cursor.fetchall()]

    # ---- Timeline Operations --------------------------------------------------------------------------------

    def get_timeline(
        self,
        ref: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        include_annotations: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get chronological timeline of events with annotations.

        Args:
            ref: Filter by specific ref.
            start_date: Filter events after this date.
            end_date: Filter events before this date.
            include_annotations: Include annotations with events.
            limit: Maximum events to return.

        Returns:
            List of timeline entries with events and annotations.
        """
        conn = self._connection

        sql = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []

        if ref:
            sql += " AND ref = ?"
            params.append(ref)

        if start_date:
            sql += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND timestamp <= ?"
            params.append(end_date)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        events = [Event.from_row(row) for row in cursor.fetchall()]

        timeline = []
        for event in events:
            entry: dict[str, Any] = {
                "event_id": event.id,
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "actor": event.actor,
                "ref": event.ref,
                "payload": event.payload,
            }

            if include_annotations:
                annotations = self.get_annotations(event.id)
                entry["annotations"] = [ann.to_dict() for ann in annotations]

            timeline.append(entry)

        return timeline

    # ---- Utility Methods ------------------------------------------------------------------------------------

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> ContextStore:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
