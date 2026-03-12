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
