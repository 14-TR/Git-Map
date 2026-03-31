"""Tests for the gitmap show command logic.

Validates that the show command correctly resolves commits, handles
edge cases (no commits, missing parent, branch refs), and that the
diff rendering helpers behave as expected.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.repository: Module under test
    - gitmap_core.diff: Diff utilities
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from gitmap_core.diff import diff_maps
from gitmap_core.repository import Repository

# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def temp_dir() -> Path:
    """Temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def repo(temp_dir: Path) -> Repository:
    """Initialized empty repository."""
    r = Repository(temp_dir)
    r.init(project_name="ShowTest", user_name="Tester")
    return r


@pytest.fixture
def map_data_v1() -> dict[str, Any]:
    return {
        "operationalLayers": [
            {"id": "l1", "title": "Roads", "visibility": True},
            {"id": "l2", "title": "Parcels", "visibility": False},
        ],
        "baseMap": {"baseMapLayers": []},
        "spatialReference": {"wkid": 102100},
    }


@pytest.fixture
def map_data_v2() -> dict[str, Any]:
    return {
        "operationalLayers": [
            {"id": "l1", "title": "Roads", "visibility": True},
            {"id": "l2", "title": "Parcels", "visibility": True},  # changed
            {"id": "l3", "title": "Flood Risk", "visibility": True},  # added
        ],
        "baseMap": {"baseMapLayers": []},
        "spatialReference": {"wkid": 102100},
    }


@pytest.fixture
def repo_with_two_commits(
    repo: Repository,
    map_data_v1: dict,
    map_data_v2: dict,
) -> tuple[Repository, str, str]:
    """Repository with two commits; returns (repo, commit1_id, commit2_id)."""
    repo.update_index(map_data_v1)
    c1 = repo.create_commit("Initial commit", author="Tester")
    repo.update_index(map_data_v2)
    c2 = repo.create_commit("Add Flood Risk layer", author="Tester")
    return repo, c1.id, c2.id


# ---- Helper: _resolve_ref ------------------------------------------------------------------------------------


class TestResolveRef:
    """Tests for the commit/branch reference resolver used by show."""

    def _resolve(self, repo: Repository, ref: str) -> str | None:
        """Mirror the _resolve_ref logic from show.py."""
        branches = repo.list_branches()
        if ref in branches:
            return repo.get_branch_commit(ref)
        return ref if repo.get_commit(ref) else None

    def test_resolves_full_commit_id(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        assert self._resolve(repo, c1_id) == c1_id

    def test_resolves_branch_name(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        branch_name = repo.get_current_branch()
        result = self._resolve(repo, branch_name)
        assert result == c2_id

    def test_returns_none_for_unknown_ref(self, repo_with_two_commits):
        repo, _, _ = repo_with_two_commits
        assert self._resolve(repo, "deadbeef12345678") is None

    def test_returns_none_for_unknown_branch(self, repo_with_two_commits):
        repo, _, _ = repo_with_two_commits
        assert self._resolve(repo, "no-such-branch") is None


# ---- Commit retrieval ----------------------------------------------------------------------------------------


class TestCommitRetrieval:
    """Tests for retrieving commits that show would display."""

    def test_get_head_commit_returns_latest(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        head = repo.get_head_commit()
        assert head == c2_id

    def test_get_commit_by_id(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        assert c1 is not None
        assert c1.id == c1_id
        assert c1.message == "Initial commit"

    def test_commit_has_parent(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        c2 = repo.get_commit(c2_id)
        assert c2 is not None
        assert c2.parent == c1_id

    def test_root_commit_has_no_parent(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        assert c1 is not None
        assert c1.parent is None or c1.parent == ""

    def test_commit_has_author(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        assert c1.author == "Tester"

    def test_commit_has_timestamp(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        assert c1.timestamp  # non-empty string


# ---- Diff computation ----------------------------------------------------------------------------------------


class TestShowDiff:
    """Tests for the diff shown by the show command."""

    def test_diff_between_commits_detects_added_layer(self, repo_with_two_commits, map_data_v1, map_data_v2):
        repo, c1_id, c2_id = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        c2 = repo.get_commit(c2_id)
        # show compares commit vs its parent, so c2 vs c1
        map_diff = diff_maps(c2.map_data, c1.map_data)
        assert map_diff.has_changes

        added_titles = [ch.layer_title for ch in map_diff.added_layers]
        assert "Flood Risk" in added_titles

    def test_diff_between_commits_detects_modified_layer(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        c2 = repo.get_commit(c2_id)
        map_diff = diff_maps(c2.map_data, c1.map_data)

        modified_titles = [ch.layer_title for ch in map_diff.modified_layers]
        assert "Parcels" in modified_titles

    def test_diff_root_commit_has_no_parent(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        # Root commit has no parent — show should handle this gracefully
        assert not c1.parent or c1.parent == ""

    def test_diff_identical_commits_has_no_changes(self, repo: Repository, map_data_v1: dict):
        """If two consecutive commits have the same data, diff shows no changes."""
        repo.update_index(map_data_v1)
        c1 = repo.create_commit("First", author="Tester")
        repo.update_index(map_data_v1)
        c2 = repo.create_commit("Second (no change)", author="Tester")

        diff = diff_maps(c2.map_data, c1.map_data)
        assert not diff.has_changes


# ---- Layer summary -------------------------------------------------------------------------------------------


class TestLayerSummary:
    """Tests for the layer summary data that show would display."""

    def test_layer_count_matches_map_data(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        c2 = repo.get_commit(c2_id)
        layers = c2.map_data.get("operationalLayers", [])
        assert len(layers) == 3

    def test_tables_field_defaults_to_empty(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        tables = c1.map_data.get("tables", [])
        assert isinstance(tables, list)

    def test_layer_titles_preserved(self, repo_with_two_commits):
        repo, c1_id, _ = repo_with_two_commits
        c1 = repo.get_commit(c1_id)
        titles = {l["title"] for l in c1.map_data.get("operationalLayers", [])}
        assert "Roads" in titles
        assert "Parcels" in titles


# ---- No-commit edge case -------------------------------------------------------------------------------------


class TestShowNoCommits:
    """Tests for show behavior on a repo with no commits."""

    def test_head_commit_is_none_when_no_commits(self, repo: Repository):
        assert repo.get_head_commit() is None

    def test_get_commit_returns_none_for_unknown_id(self, repo: Repository):
        assert repo.get_commit("abc123") is None


# ---- Branch resolution ---------------------------------------------------------------------------------------


class TestBranchResolution:
    """Tests for resolving branch names in show."""

    def test_feature_branch_resolves_to_correct_commit(self, repo_with_two_commits, map_data_v2):
        repo, c1_id, c2_id = repo_with_two_commits

        # Create a feature branch from HEAD
        repo.create_branch("feature/test-show")
        branch_commit = repo.get_branch_commit("feature/test-show")
        assert branch_commit == c2_id

    def test_list_branches_includes_new_branch(self, repo_with_two_commits):
        repo, _, _ = repo_with_two_commits
        repo.create_branch("feature/another")
        branches = repo.list_branches()
        assert "feature/another" in branches

    def test_show_main_branch_returns_latest_commit(self, repo_with_two_commits):
        repo, c1_id, c2_id = repo_with_two_commits
        main_branch = repo.get_current_branch()
        branch_commit = repo.get_branch_commit(main_branch)
        assert branch_commit == c2_id
