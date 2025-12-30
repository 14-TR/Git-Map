"""Data models for GitMap version control.

Defines core data structures for commits, branches, remotes, and
repository configuration used throughout the GitMap system.

Execution Context:
    Library module - imported by other gitmap_core modules

Dependencies:
    - dataclasses: Data class decorators
    - typing: Type annotations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any


# ---- Data Model Classes -------------------------------------------------------------------------------------


@dataclass
class Commit:
    """Snapshot of map JSON with version control metadata.

    Attributes:
        id: Unique commit identifier (hash).
        message: Commit message describing changes.
        author: Author name or identifier.
        timestamp: ISO 8601 formatted timestamp.
        parent: Parent commit ID (None for initial commit).
        parent2: Second parent ID for merge commits.
        map_data: Complete web map JSON snapshot.
    """

    id: str
    message: str
    author: str
    timestamp: str
    parent: str | None = None
    parent2: str | None = None
    map_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
            cls,
            commit_id: str,
            message: str,
            author: str,
            parent: str | None = None,
            parent2: str | None = None,
            map_data: dict[str, Any] | None = None,
    ) -> Commit:
        """Create a new commit with current timestamp.

        Args:
            commit_id: Unique identifier for the commit.
            message: Commit message.
            author: Author name.
            parent: Parent commit ID.
            parent2: Second parent for merge commits.
            map_data: Web map JSON data.

        Returns:
            New Commit instance.
        """
        return cls(
            id=commit_id,
            message=message,
            author=author,
            timestamp=datetime.now().isoformat(),
            parent=parent,
            parent2=parent2,
            map_data=map_data or {},
        )

    def to_dict(
            self,
    ) -> dict[str, Any]:
        """Convert commit to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the commit.
        """
        return asdict(self)

    @classmethod
    def from_dict(
            cls,
            data: dict[str, Any],
    ) -> Commit:
        """Create commit from dictionary.

        Args:
            data: Dictionary with commit fields.

        Returns:
            Commit instance.
        """
        return cls(**data)

    def save(
            self,
            commits_dir: Path,
    ) -> Path:
        """Save commit to file.

        Args:
            commits_dir: Directory to store commit files.

        Returns:
            Path to saved commit file.
        """
        filepath = commits_dir / f"{self.id}.json"
        filepath.write_text(json.dumps(self.to_dict(), indent=2))
        return filepath

    @classmethod
    def load(
            cls,
            filepath: Path,
    ) -> Commit:
        """Load commit from file.

        Args:
            filepath: Path to commit JSON file.

        Returns:
            Commit instance.

        Raises:
            RuntimeError: If commit file cannot be loaded.
        """
        try:
            data = json.loads(filepath.read_text())
            return cls.from_dict(data)
        except Exception as file_error:
            msg = f"Failed to load commit from {filepath}: {file_error}"
            raise RuntimeError(msg) from file_error


@dataclass
class Branch:
    """Named pointer to a commit.

    Attributes:
        name: Branch name (e.g., 'main', 'feature/new-layer').
        commit_id: ID of the commit this branch points to.
    """

    name: str
    commit_id: str

    def to_dict(
            self,
    ) -> dict[str, str]:
        """Convert branch to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(
            cls,
            data: dict[str, str],
    ) -> Branch:
        """Create branch from dictionary.

        Args:
            data: Dictionary with branch fields.

        Returns:
            Branch instance.
        """
        return cls(**data)


@dataclass
class Remote:
    """Portal connection info and folder location.

    Attributes:
        name: Remote name (e.g., 'origin').
        url: Portal URL.
        folder_id: Portal folder ID for GitMap items.
        folder_name: Portal folder name.
        item_id: Original web map item ID (for cloned repos).
    """

    name: str
    url: str
    folder_id: str | None = None
    folder_name: str | None = None
    item_id: str | None = None

    def to_dict(
            self,
    ) -> dict[str, Any]:
        """Convert remote to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(
            cls,
            data: dict[str, Any],
    ) -> Remote:
        """Create remote from dictionary.

        Args:
            data: Dictionary with remote fields.

        Returns:
            Remote instance.
        """
        return cls(**data)


@dataclass
class RepoConfig:
    """Repository configuration stored in .gitmap/config.json.

    Attributes:
        version: GitMap format version.
        user_name: Default author name for commits.
        user_email: Default author email.
        remote: Remote connection configuration.
        project_name: Project name for Portal folder naming.
    """

    version: str = "1.0"
    user_name: str = ""
    user_email: str = ""
    remote: Remote | None = None
    project_name: str = ""

    def to_dict(
            self,
    ) -> dict[str, Any]:
        """Convert config to dictionary for JSON serialization.

        Returns:
            Dictionary representation.
        """
        result = {
            "version": self.version,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "project_name": self.project_name,
        }
        if self.remote:
            result["remote"] = self.remote.to_dict()
        return result

    @classmethod
    def from_dict(
            cls,
            data: dict[str, Any],
    ) -> RepoConfig:
        """Create config from dictionary.

        Args:
            data: Dictionary with config fields.

        Returns:
            RepoConfig instance.
        """
        remote_data = data.get("remote")
        remote = Remote.from_dict(remote_data) if remote_data else None
        return cls(
            version=data.get("version", "1.0"),
            user_name=data.get("user_name", ""),
            user_email=data.get("user_email", ""),
            remote=remote,
            project_name=data.get("project_name", ""),
        )

    def save(
            self,
            config_path: Path,
    ) -> None:
        """Save config to file.

        Args:
            config_path: Path to config.json file.
        """
        config_path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(
            cls,
            config_path: Path,
    ) -> RepoConfig:
        """Load config from file.

        Args:
            config_path: Path to config.json file.

        Returns:
            RepoConfig instance.

        Raises:
            RuntimeError: If config file cannot be loaded.
        """
        try:
            data = json.loads(config_path.read_text())
            return cls.from_dict(data)
        except Exception as file_error:
            msg = f"Failed to load config from {config_path}: {file_error}"
            raise RuntimeError(msg) from file_error


