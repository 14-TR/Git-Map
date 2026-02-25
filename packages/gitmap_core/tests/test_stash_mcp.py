"""Tests for GitMap MCP stash tools.

Exercises the MCP-layer stash functions (push, pop, list, drop) using a
real in-memory repository via ``init_repository``.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.repository: Repository management
    - tools.stash_tools: MCP stash tool functions (path-injected)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

from gitmap_core.repository import init_repository, Repository

# Inject the MCP scripts directory so stash_tools can be imported directly.
_MCP_SCRIPTS = str(
    Path(__file__).parent.parent.parent.parent
    / "apps" / "mcp" / "gitmap-mcp" / "scripts"
)
if _MCP_SCRIPTS not in sys.path:
    sys.path.insert(0, _MCP_SCRIPTS)

from tools.stash_tools import (
    gitmap_stash_drop,
    gitmap_stash_list,
    gitmap_stash_pop,
    gitmap_stash_push,
)


# ---- Fixtures -------------------------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    """Initialized repository with one commit on main."""
    r = init_repository(tmp_path, user_name="tester", user_email="t@t.com")
    r.update_index({"operationalLayers": [{"id": "l0", "title": "Base Layer"}]})
    r.create_commit(message="initial commit")
    return r


@pytest.fixture
def dirty_repo(repo: Repository, tmp_path: Path) -> Repository:
    """Repository with uncommitted index changes."""
    repo.update_index({
        "operationalLayers": [
            {"id": "l0", "title": "Base Layer"},
            {"id": "l1", "title": "Uncommitted Layer"},
        ]
    })
    return repo


# ---- gitmap_stash_push ----------------------------------------------------------------------------------


class TestGitmapStashPush:
    """Tests for gitmap_stash_push MCP tool."""

    def test_push_saves_changes(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """Pushing creates a stash entry and resets index to HEAD."""
        result = gitmap_stash_push(path=str(tmp_path))

        assert result["success"] is True
        assert "stash_id" in result
        assert "stash@" in result["stash_id"]

        # Index should be reset to HEAD (only the base layer)
        index = dirty_repo.get_index()
        layer_ids = [lyr["id"] for lyr in index.get("operationalLayers", [])]
        assert "l1" not in layer_ids
        assert "l0" in layer_ids

    def test_push_records_stash_entry(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """After push the stash list contains one entry."""
        gitmap_stash_push(path=str(tmp_path))
        stashes = dirty_repo.stash_list()
        assert len(stashes) == 1

    def test_push_custom_message(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """Custom message is stored with the stash entry."""
        result = gitmap_stash_push(message="WIP: my feature", path=str(tmp_path))
        assert result["success"] is True
        assert "WIP: my feature" in result["message"]

    def test_push_no_changes_returns_error(self, repo: Repository, tmp_path: Path) -> None:
        """Pushing with a clean index returns a structured error."""
        result = gitmap_stash_push(path=str(tmp_path))
        assert result["success"] is False
        assert "error" in result

    def test_push_invalid_path_returns_error(self, tmp_path: Path) -> None:
        """A path that is not a GitMap repo returns a structured error."""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        result = gitmap_stash_push(path=str(non_repo))
        assert result["success"] is False
        assert "error" in result


# ---- gitmap_stash_list ----------------------------------------------------------------------------------


class TestGitmapStashList:
    """Tests for gitmap_stash_list MCP tool."""

    def test_list_empty(self, repo: Repository, tmp_path: Path) -> None:
        """Empty stash list returns success with zero entries."""
        result = gitmap_stash_list(path=str(tmp_path))
        assert result["success"] is True
        assert result["count"] == 0
        assert result["entries"] == []

    def test_list_shows_entries(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """After pushing, list returns one entry."""
        gitmap_stash_push(message="stash A", path=str(tmp_path))
        result = gitmap_stash_list(path=str(tmp_path))
        assert result["success"] is True
        assert result["count"] == 1
        assert result["entries"][0]["index"] == 0

    def test_list_multiple_entries_newest_first(
        self, repo: Repository, tmp_path: Path
    ) -> None:
        """Multiple stash entries are returned newest-first."""
        for label in ("first", "second"):
            repo.update_index({
                "operationalLayers": [{"id": label, "title": label}]
            })
            gitmap_stash_push(message=label, path=str(tmp_path))

        result = gitmap_stash_list(path=str(tmp_path))
        assert result["count"] == 2
        assert "second" in result["entries"][0]["message"]
        assert "first" in result["entries"][1]["message"]

    def test_list_invalid_path_returns_error(self, tmp_path: Path) -> None:
        """Non-repo path returns a structured error."""
        result = gitmap_stash_list(path=str(tmp_path / "nowhere"))
        assert result["success"] is False


# ---- gitmap_stash_pop -----------------------------------------------------------------------------------


class TestGitmapStashPop:
    """Tests for gitmap_stash_pop MCP tool."""

    def test_pop_applies_and_removes(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """Popping the latest stash restores changes and removes the entry."""
        gitmap_stash_push(path=str(tmp_path))

        # Index should be clean before pop
        assert not dirty_repo.has_uncommitted_changes()

        result = gitmap_stash_pop(path=str(tmp_path))
        assert result["success"] is True
        assert "stash_id" in result

        # Stash list should now be empty
        assert dirty_repo.stash_list() == []

        # Uncommitted changes should be restored
        assert dirty_repo.has_uncommitted_changes()

    def test_pop_empty_stash_returns_error(self, repo: Repository, tmp_path: Path) -> None:
        """Popping with no stash entries returns a structured error."""
        result = gitmap_stash_pop(path=str(tmp_path))
        assert result["success"] is False
        assert "error" in result

    def test_pop_invalid_index_returns_error(
        self, dirty_repo: Repository, tmp_path: Path
    ) -> None:
        """Popping an out-of-range index returns a structured error."""
        gitmap_stash_push(path=str(tmp_path))
        result = gitmap_stash_pop(index=99, path=str(tmp_path))
        assert result["success"] is False
        assert "error" in result

    def test_pop_specific_index(self, repo: Repository, tmp_path: Path) -> None:
        """Pop at index 1 applies the older of two stash entries."""
        for label in ("older", "newer"):
            repo.update_index({"operationalLayers": [{"id": label, "title": label}]})
            gitmap_stash_push(message=label, path=str(tmp_path))

        result = gitmap_stash_pop(index=1, path=str(tmp_path))
        assert result["success"] is True
        assert "older" in result["message"]
        assert repo.stash_list().__len__() == 1


# ---- gitmap_stash_drop ----------------------------------------------------------------------------------


class TestGitmapStashDrop:
    """Tests for gitmap_stash_drop MCP tool."""

    def test_drop_removes_entry(self, dirty_repo: Repository, tmp_path: Path) -> None:
        """Dropping an entry removes it without changing the index."""
        gitmap_stash_push(path=str(tmp_path))
        assert dirty_repo.stash_list().__len__() == 1

        result = gitmap_stash_drop(path=str(tmp_path))
        assert result["success"] is True
        assert "stash_id" in result
        assert dirty_repo.stash_list().__len__() == 0

    def test_drop_does_not_restore_index(
        self, dirty_repo: Repository, tmp_path: Path
    ) -> None:
        """Dropping does not restore the working index (unlike pop)."""
        gitmap_stash_push(path=str(tmp_path))

        # Index is clean before drop
        assert not dirty_repo.has_uncommitted_changes()

        gitmap_stash_drop(path=str(tmp_path))

        # Index should still be clean after drop
        assert not dirty_repo.has_uncommitted_changes()

    def test_drop_empty_stash_returns_error(self, repo: Repository, tmp_path: Path) -> None:
        """Dropping with an empty stash returns a structured error."""
        result = gitmap_stash_drop(path=str(tmp_path))
        assert result["success"] is False
        assert "error" in result

    def test_drop_invalid_path_returns_error(self, tmp_path: Path) -> None:
        """Non-repo path returns a structured error."""
        result = gitmap_stash_drop(path=str(tmp_path / "nowhere"))
        assert result["success"] is False
