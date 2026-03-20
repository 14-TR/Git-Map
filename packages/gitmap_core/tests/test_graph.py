"""Tests for commit graph builder (gitmap_core.graph).

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.graph: Module under test
    - gitmap_core.repository: Repository fixture
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from gitmap_core.graph import GraphNode, _collect_commits, _topological_sort, build_graph
from gitmap_core.repository import Repository


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def temp_dir() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def repo(temp_dir: Path) -> Repository:
    r = Repository(temp_dir)
    r.init(project_name="GraphTest", user_name="Tester")
    return r


@pytest.fixture
def map_a() -> dict[str, Any]:
    return {
        "operationalLayers": [
            {"id": "l1", "title": "Roads", "visibility": True},
        ],
    }


@pytest.fixture
def map_b() -> dict[str, Any]:
    return {
        "operationalLayers": [
            {"id": "l1", "title": "Roads", "visibility": True},
            {"id": "l2", "title": "Parcels", "visibility": False},
        ],
    }


@pytest.fixture
def map_c() -> dict[str, Any]:
    return {
        "operationalLayers": [
            {"id": "l1", "title": "Roads", "visibility": True},
            {"id": "l2", "title": "Parcels", "visibility": False},
            {"id": "l3", "title": "Flood Zones", "visibility": True},
        ],
    }


# ---- _collect_commits -----------------------------------------------------------------------


class TestCollectCommits:
    def test_empty_repo_returns_no_commits(self, repo):
        all_commits, labels = _collect_commits(repo, limit=10)
        assert all_commits == {}
        assert labels == {}

    def test_single_commit(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial commit", author="Tester")
        all_commits, labels = _collect_commits(repo, limit=10)
        assert len(all_commits) == 1

    def test_labels_on_tip(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial commit", author="Tester")
        all_commits, labels = _collect_commits(repo, limit=10)
        head_id = repo.get_head_commit()
        assert head_id in labels
        label_texts = labels[head_id]
        assert any("HEAD" in lbl for lbl in label_texts)

    def test_multiple_commits_collected(self, repo, map_a, map_b, map_c):
        repo.update_index(map_a)
        repo.create_commit("Commit 1", author="Tester")
        repo.update_index(map_b)
        repo.create_commit("Commit 2", author="Tester")
        repo.update_index(map_c)
        repo.create_commit("Commit 3", author="Tester")
        all_commits, _ = _collect_commits(repo, limit=10)
        assert len(all_commits) == 3

    def test_feature_branch_collected(self, repo, map_a, map_b):
        repo.update_index(map_a)
        repo.create_commit("Initial", author="Tester")
        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        repo.create_commit("Feature commit", author="Tester")

        # Switch back to main
        repo.checkout_branch("main")
        all_commits, labels = _collect_commits(repo, limit=10)

        # Should have commits from both branches
        assert len(all_commits) == 2

        # Feature branch tip should have label
        feature_tip = repo.get_branch_commit("feature/x")
        assert feature_tip in labels


# ---- _topological_sort -----------------------------------------------------------------------


class TestTopologicalSort:
    def test_empty_returns_empty(self):
        result = _topological_sort({})
        assert result == []

    def test_single_commit(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Only commit", author="Tester")
        all_commits, _ = _collect_commits(repo, limit=10)
        result = _topological_sort(all_commits)
        assert len(result) == 1

    def test_linear_chain_ordered_newest_first(self, repo, map_a, map_b, map_c):
        repo.update_index(map_a)
        c1 = repo.create_commit("First", author="Tester")
        repo.update_index(map_b)
        c2 = repo.create_commit("Second", author="Tester")
        repo.update_index(map_c)
        c3 = repo.create_commit("Third", author="Tester")

        all_commits, _ = _collect_commits(repo, limit=10)
        result = _topological_sort(all_commits)

        assert len(result) == 3
        # Newest first: c3, c2, c1
        assert result[0].id == c3.id
        assert result[1].id == c2.id
        assert result[2].id == c1.id

    def test_parents_come_after_children(self, repo, map_a, map_b):
        repo.update_index(map_a)
        c1 = repo.create_commit("First", author="Tester")
        repo.update_index(map_b)
        c2 = repo.create_commit("Second", author="Tester")

        all_commits, _ = _collect_commits(repo, limit=10)
        result = _topological_sort(all_commits)

        ids = [c.id for c in result]
        assert ids.index(c2.id) < ids.index(c1.id)


# ---- build_graph -----------------------------------------------------------------------


class TestBuildGraph:
    def test_empty_repo_returns_empty(self, repo):
        nodes = build_graph(repo, limit=10)
        assert nodes == []

    def test_single_commit_produces_one_node(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial", author="Tester")
        nodes = build_graph(repo, limit=10)
        assert len(nodes) == 1

    def test_node_has_correct_type(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial", author="Tester")
        nodes = build_graph(repo, limit=10)
        assert isinstance(nodes[0], GraphNode)

    def test_head_label_on_current_branch_tip(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial", author="Tester")
        nodes = build_graph(repo, limit=10)
        labels = nodes[0].labels
        assert any("HEAD" in lbl for lbl in labels)

    def test_prefix_line_contains_star(self, repo, map_a):
        repo.update_index(map_a)
        repo.create_commit("Initial", author="Tester")
        nodes = build_graph(repo, limit=10)
        assert "*" in nodes[0].prefix_line

    def test_linear_three_commits(self, repo, map_a, map_b, map_c):
        repo.update_index(map_a)
        repo.create_commit("C1", author="Tester")
        repo.update_index(map_b)
        repo.create_commit("C2", author="Tester")
        repo.update_index(map_c)
        repo.create_commit("C3", author="Tester")

        nodes = build_graph(repo, limit=10)
        assert len(nodes) == 3
        # All nodes should be in lane 0 for linear history
        for node in nodes:
            assert node.lane == 0

    def test_limit_respected(self, repo, map_a, map_b, map_c):
        repo.update_index(map_a)
        repo.create_commit("C1", author="Tester")
        repo.update_index(map_b)
        repo.create_commit("C2", author="Tester")
        repo.update_index(map_c)
        repo.create_commit("C3", author="Tester")

        nodes = build_graph(repo, limit=2)
        assert len(nodes) == 2

    def test_feature_branch_uses_separate_lane(self, repo, map_a, map_b, map_c):
        # main: C1 -> C2 (HEAD)
        # feature: C1 -> C3 (HEAD -> feature/x)
        repo.update_index(map_a)
        repo.create_commit("C1 common", author="Tester")

        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        repo.create_commit("C2 feature", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_c)
        repo.create_commit("C3 main", author="Tester")

        nodes = build_graph(repo, limit=10)
        # Should have 3 nodes
        assert len(nodes) == 3
        # The diverging commits should be in different lanes
        lanes_used = {n.lane for n in nodes}
        assert len(lanes_used) >= 2  # both lane 0 and lane 1 used

    def test_connector_lines_empty_for_linear(self, repo, map_a, map_b):
        repo.update_index(map_a)
        repo.create_commit("C1", author="Tester")
        repo.update_index(map_b)
        repo.create_commit("C2", author="Tester")

        nodes = build_graph(repo, limit=10)
        for node in nodes:
            assert node.connector_lines == []

    def test_prefix_shows_pipe_for_parallel_lanes(self, repo, map_a, map_b, map_c):
        # Setup diverging branches
        repo.update_index(map_a)
        repo.create_commit("Common", author="Tester")

        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        repo.create_commit("Feature", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_c)
        repo.create_commit("Main ahead", author="Tester")

        nodes = build_graph(repo, limit=10)
        # At least one prefix line should have both * and |
        all_prefixes = [n.prefix_line for n in nodes]
        has_pipe = any("|" in p for p in all_prefixes)
        assert has_pipe

    def test_branch_label_on_feature_tip(self, repo, map_a, map_b):
        repo.update_index(map_a)
        repo.create_commit("Common", author="Tester")

        repo.create_branch("feature/my-work")
        repo.checkout_branch("feature/my-work")
        repo.update_index(map_b)
        repo.create_commit("Feature work", author="Tester")

        repo.checkout_branch("main")

        nodes = build_graph(repo, limit=10)
        # Find the node for the feature branch tip
        feature_tip = repo.get_branch_commit("feature/my-work")
        feature_nodes = [n for n in nodes if n.commit.id == feature_tip]
        assert len(feature_nodes) == 1
        labels = feature_nodes[0].labels
        assert any("feature/my-work" in lbl for lbl in labels)


# ---- Merge commit graph (parent2) tests -----------------------------------------------------------------------


class TestMergeCommitGraph:
    """Tests for graph rendering when merge commits have two parents (parent2).

    These tests exercise the parent2 code paths in _collect_commits,
    _topological_sort, and build_graph that were previously untested.
    """

    def test_collect_commits_traverses_parent2(self, repo, map_a, map_b, map_c):
        """_collect_commits must walk parent2 when collecting merge commits."""
        # Create common base
        repo.update_index(map_a)
        c_base = repo.create_commit("Base", author="Tester")

        # Create feature branch commit
        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        c_feature = repo.create_commit("Feature work", author="Tester")

        # Return to main, make a commit, then a merge commit
        repo.checkout_branch("main")
        repo.update_index(map_c)
        c_main = repo.create_commit("Main work", author="Tester")

        # Simulate merge: create commit with parent2 pointing to feature tip
        repo.update_index({**map_c, "operationalLayers": map_c["operationalLayers"] + map_b["operationalLayers"]})
        c_merge = repo.create_commit("Merge feature/x into main", author="Tester", parent2=c_feature.id)

        all_commits, labels = _collect_commits(repo, limit=20)

        # All 4 commits should be reachable
        assert c_base.id in all_commits
        assert c_feature.id in all_commits
        assert c_main.id in all_commits
        assert c_merge.id in all_commits

    def test_topological_sort_handles_merge_commit(self, repo, map_a, map_b, map_c):
        """_topological_sort must process merge commits with parent2 correctly."""
        repo.update_index(map_a)
        c_base = repo.create_commit("Base", author="Tester")

        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        c_feature = repo.create_commit("Feature", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_c)
        repo.create_commit("Main", author="Tester")

        repo.update_index(map_a)
        c_merge = repo.create_commit("Merge", author="Tester", parent2=c_feature.id)

        all_commits, _ = _collect_commits(repo, limit=20)
        result = _topological_sort(all_commits)

        ids = [c.id for c in result]
        # Merge commit must come before its parents
        assert ids.index(c_merge.id) < ids.index(c_base.id)
        # All commits present
        assert len(result) == len(all_commits)

    def test_build_graph_merge_commit_has_connector_lines(self, repo, map_a, map_b, map_c):
        """build_graph must produce connector lines for a merge commit with parent2."""
        repo.update_index(map_a)
        repo.create_commit("Base", author="Tester")

        repo.create_branch("feature/x")
        repo.checkout_branch("feature/x")
        repo.update_index(map_b)
        c_feature = repo.create_commit("Feature", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_c)
        repo.create_commit("Main", author="Tester")

        # Merge commit links main and feature
        repo.update_index(map_a)
        c_merge = repo.create_commit("Merge feature/x", author="Tester", parent2=c_feature.id)

        nodes = build_graph(repo, limit=20)

        # The merge node must exist
        merge_nodes = [n for n in nodes if n.commit.id == c_merge.id]
        assert len(merge_nodes) == 1
        merge_node = merge_nodes[0]

        # A merge commit with parent2 must produce connector lines (the |\ decoration)
        assert len(merge_node.connector_lines) > 0
        connector = merge_node.connector_lines[0]
        assert "\\" in connector

    def test_build_graph_merge_commit_uses_two_lanes(self, repo, map_a, map_b, map_c):
        """Graph must use at least two lanes when a merge commit has two parents."""
        repo.update_index(map_a)
        repo.create_commit("Base", author="Tester")

        repo.create_branch("feature/y")
        repo.checkout_branch("feature/y")
        repo.update_index(map_b)
        c_feature = repo.create_commit("Feature Y", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_c)
        repo.create_commit("Main ahead", author="Tester")

        repo.update_index(map_a)
        repo.create_commit("Merge feature/y", author="Tester", parent2=c_feature.id)

        nodes = build_graph(repo, limit=20)
        lanes_used = {n.lane for n in nodes}
        assert len(lanes_used) >= 2

    def test_create_commit_stores_parent2(self, repo, map_a, map_b):
        """repository.create_commit must persist parent2 on the commit object."""
        repo.update_index(map_a)
        c1 = repo.create_commit("First", author="Tester")

        repo.create_branch("feature/z")
        repo.checkout_branch("feature/z")
        repo.update_index(map_b)
        c_feature = repo.create_commit("Feature Z", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_a)
        c_merge = repo.create_commit("Merge", author="Tester", parent2=c_feature.id)

        # Reload from disk to confirm persistence
        loaded = repo.get_commit(c_merge.id)
        assert loaded is not None
        assert loaded.parent2 == c_feature.id

    def test_collect_commits_follows_sub_parent_chain(self, repo, map_a, map_b, map_c):
        """_collect_commits must walk the entire parent chain off parent2, not just one hop."""
        repo.update_index(map_a)
        c_root = repo.create_commit("Root", author="Tester")

        repo.create_branch("feature/deep")
        repo.checkout_branch("feature/deep")
        repo.update_index(map_b)
        c_f1 = repo.create_commit("Feature 1", author="Tester")
        repo.update_index(map_c)
        c_f2 = repo.create_commit("Feature 2", author="Tester")

        repo.checkout_branch("main")
        repo.update_index(map_a)
        # Merge commit: parent2 is c_f2 (which itself chains to c_f1 and c_root)
        c_merge = repo.create_commit("Merge deep feature", author="Tester", parent2=c_f2.id)

        all_commits, _ = _collect_commits(repo, limit=20)

        # The full chain through parent2 must be included
        assert c_root.id in all_commits
        assert c_f1.id in all_commits
        assert c_f2.id in all_commits
        assert c_merge.id in all_commits
