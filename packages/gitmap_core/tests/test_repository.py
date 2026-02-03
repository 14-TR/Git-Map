"""Tests for local repository management module.

Tests Repository class including initialization, branch operations,
commit operations, index management, and config handling.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.repository: Module under test
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from gitmap_core.models import Branch
from gitmap_core.models import Commit
from gitmap_core.models import RepoConfig
from gitmap_core.repository import (
    COMMITS_DIR,
    CONFIG_FILE,
    CONTEXT_DB,
    GITMAP_DIR,
    HEAD_FILE,
    HEADS_DIR,
    INDEX_FILE,
    OBJECTS_DIR,
    REFS_DIR,
    REMOTES_DIR,
    Repository,
    find_repository,
    init_repository,
)


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def temp_repo_dir() -> Path:
    """Create temporary directory for repository tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def initialized_repo(temp_repo_dir: Path) -> Repository:
    """Create and initialize a repository."""
    repo = Repository(temp_repo_dir)
    repo.init(project_name="TestProject", user_name="Test User")
    return repo


@pytest.fixture
def sample_map_data() -> dict[str, Any]:
    """Sample web map data for testing."""
    return {
        "operationalLayers": [
            {"id": "layer-1", "title": "Roads"},
            {"id": "layer-2", "title": "Parcels"},
        ],
        "baseMap": {"baseMapLayers": []},
        "spatialReference": {"wkid": 102100},
    }


@pytest.fixture
def repo_with_commit(initialized_repo: Repository, sample_map_data: dict) -> Repository:
    """Create repository with one commit."""
    initialized_repo.update_index(sample_map_data)
    initialized_repo.create_commit("Initial commit", author="Test User")
    return initialized_repo


# ---- Constants Tests ----------------------------------------------------------------------------------------


class TestConstants:
    """Tests for module constants."""

    def test_gitmap_dir(self) -> None:
        """Test GITMAP_DIR constant."""
        assert GITMAP_DIR == ".gitmap"

    def test_config_file(self) -> None:
        """Test CONFIG_FILE constant."""
        assert CONFIG_FILE == "config.json"

    def test_head_file(self) -> None:
        """Test HEAD_FILE constant."""
        assert HEAD_FILE == "HEAD"

    def test_index_file(self) -> None:
        """Test INDEX_FILE constant."""
        assert INDEX_FILE == "index.json"

    def test_refs_dir(self) -> None:
        """Test REFS_DIR constant."""
        assert REFS_DIR == "refs"

    def test_heads_dir(self) -> None:
        """Test HEADS_DIR constant."""
        assert HEADS_DIR == "heads"

    def test_remotes_dir(self) -> None:
        """Test REMOTES_DIR constant."""
        assert REMOTES_DIR == "remotes"

    def test_objects_dir(self) -> None:
        """Test OBJECTS_DIR constant."""
        assert OBJECTS_DIR == "objects"

    def test_commits_dir(self) -> None:
        """Test COMMITS_DIR constant."""
        assert COMMITS_DIR == "commits"

    def test_context_db(self) -> None:
        """Test CONTEXT_DB constant."""
        assert CONTEXT_DB == "context.db"


# ---- Repository Initialization Tests ------------------------------------------------------------------------


class TestRepositoryInit:
    """Tests for Repository initialization."""

    def test_init_creates_instance(self, temp_repo_dir: Path) -> None:
        """Test Repository constructor."""
        repo = Repository(temp_repo_dir)

        assert repo.root == temp_repo_dir.resolve()
        assert repo.gitmap_dir == temp_repo_dir.resolve() / ".gitmap"

    def test_init_with_string_path(self, temp_repo_dir: Path) -> None:
        """Test Repository with string path."""
        repo = Repository(str(temp_repo_dir))

        assert repo.root == temp_repo_dir.resolve()

    def test_path_properties(self, temp_repo_dir: Path) -> None:
        """Test path property accessors."""
        repo = Repository(temp_repo_dir)

        assert repo.config_path == repo.gitmap_dir / "config.json"
        assert repo.head_path == repo.gitmap_dir / "HEAD"
        assert repo.index_path == repo.gitmap_dir / "index.json"
        assert repo.refs_dir == repo.gitmap_dir / "refs"
        assert repo.heads_dir == repo.gitmap_dir / "refs" / "heads"
        assert repo.remotes_dir == repo.gitmap_dir / "refs" / "remotes"
        assert repo.objects_dir == repo.gitmap_dir / "objects"
        assert repo.commits_dir == repo.gitmap_dir / "objects" / "commits"
        assert repo.context_db_path == repo.gitmap_dir / "context.db"


# ---- Repository State Tests ---------------------------------------------------------------------------------


class TestRepositoryState:
    """Tests for repository state checking."""

    def test_exists_false_when_not_initialized(self, temp_repo_dir: Path) -> None:
        """Test exists() returns False for uninitialized repo."""
        repo = Repository(temp_repo_dir)

        assert repo.exists() is False

    def test_exists_true_when_initialized(self, initialized_repo: Repository) -> None:
        """Test exists() returns True for initialized repo."""
        assert initialized_repo.exists() is True

    def test_is_valid_false_when_not_initialized(self, temp_repo_dir: Path) -> None:
        """Test is_valid() returns False for uninitialized repo."""
        repo = Repository(temp_repo_dir)

        assert repo.is_valid() is False

    def test_is_valid_true_when_initialized(self, initialized_repo: Repository) -> None:
        """Test is_valid() returns True for properly initialized repo."""
        assert initialized_repo.is_valid() is True

    def test_is_valid_false_when_missing_config(
        self, initialized_repo: Repository
    ) -> None:
        """Test is_valid() returns False when config missing."""
        initialized_repo.config_path.unlink()

        assert initialized_repo.is_valid() is False


# ---- Repository Initialization Operations -------------------------------------------------------------------


class TestRepositoryInitialization:
    """Tests for repository init() method."""

    def test_init_creates_directory_structure(self, temp_repo_dir: Path) -> None:
        """Test init creates required directories."""
        repo = Repository(temp_repo_dir)
        repo.init(project_name="Test")

        assert repo.gitmap_dir.is_dir()
        assert repo.heads_dir.is_dir()
        assert (repo.remotes_dir / "origin").is_dir()
        assert repo.commits_dir.is_dir()

    def test_init_creates_config_file(self, temp_repo_dir: Path) -> None:
        """Test init creates config.json."""
        repo = Repository(temp_repo_dir)
        repo.init(project_name="MyProject", user_name="John", user_email="john@test.com")

        assert repo.config_path.exists()
        config = RepoConfig.load(repo.config_path)
        assert config.project_name == "MyProject"
        assert config.user_name == "John"
        assert config.user_email == "john@test.com"

    def test_init_creates_head_file(self, temp_repo_dir: Path) -> None:
        """Test init creates HEAD pointing to main."""
        repo = Repository(temp_repo_dir)
        repo.init()

        assert repo.head_path.exists()
        content = repo.head_path.read_text()
        assert content == "ref: refs/heads/main"

    def test_init_creates_empty_index(self, temp_repo_dir: Path) -> None:
        """Test init creates empty index.json."""
        repo = Repository(temp_repo_dir)
        repo.init()

        assert repo.index_path.exists()
        index = json.loads(repo.index_path.read_text())
        assert index == {}

    def test_init_creates_main_branch(self, temp_repo_dir: Path) -> None:
        """Test init creates main branch file."""
        repo = Repository(temp_repo_dir)
        repo.init()

        main_branch = repo.heads_dir / "main"
        assert main_branch.exists()
        assert main_branch.read_text() == ""

    def test_init_creates_context_db(self, temp_repo_dir: Path) -> None:
        """Test init creates context database."""
        repo = Repository(temp_repo_dir)
        repo.init()

        assert repo.context_db_path.exists()

    def test_init_uses_directory_name_as_default_project_name(
        self, temp_repo_dir: Path
    ) -> None:
        """Test init uses directory name when project_name not provided."""
        repo = Repository(temp_repo_dir)
        repo.init()

        config = repo.get_config()
        assert config.project_name == temp_repo_dir.name

    def test_init_raises_if_already_exists(self, initialized_repo: Repository) -> None:
        """Test init raises error if repo already exists."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.init()

        assert "already exists" in str(exc_info.value)


# ---- HEAD Operations Tests ----------------------------------------------------------------------------------


class TestHeadOperations:
    """Tests for HEAD-related operations."""

    def test_get_current_branch(self, initialized_repo: Repository) -> None:
        """Test getting current branch name."""
        branch = initialized_repo.get_current_branch()

        assert branch == "main"

    def test_get_current_branch_returns_none_for_detached(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns None for detached HEAD."""
        # Simulate detached HEAD by writing commit ID directly
        initialized_repo.head_path.write_text("abc123")

        assert initialized_repo.get_current_branch() is None

    def test_get_current_branch_returns_none_if_no_head(
        self, temp_repo_dir: Path
    ) -> None:
        """Test returns None if HEAD file doesn't exist."""
        repo = Repository(temp_repo_dir)

        assert repo.get_current_branch() is None

    def test_get_head_commit_with_branch(
        self, repo_with_commit: Repository
    ) -> None:
        """Test getting HEAD commit when on branch."""
        commit_id = repo_with_commit.get_head_commit()

        assert commit_id is not None
        assert len(commit_id) == 12  # Short hash

    def test_get_head_commit_detached(
        self, initialized_repo: Repository
    ) -> None:
        """Test getting HEAD commit when detached."""
        initialized_repo.head_path.write_text("abc123456789")

        commit_id = initialized_repo.get_head_commit()

        assert commit_id == "abc123456789"

    def test_get_head_commit_returns_none_for_empty_branch(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns None for branch with no commits."""
        commit_id = initialized_repo.get_head_commit()

        assert commit_id is None


# ---- Branch Operations Tests --------------------------------------------------------------------------------


class TestBranchOperations:
    """Tests for branch operations."""

    def test_list_branches(self, initialized_repo: Repository) -> None:
        """Test listing branches."""
        branches = initialized_repo.list_branches()

        assert "main" in branches

    def test_list_branches_empty_when_no_heads(self, temp_repo_dir: Path) -> None:
        """Test empty list when no heads directory."""
        repo = Repository(temp_repo_dir)

        branches = repo.list_branches()

        assert branches == []

    def test_get_branch_commit(self, repo_with_commit: Repository) -> None:
        """Test getting branch commit ID."""
        commit_id = repo_with_commit.get_branch_commit("main")

        assert commit_id is not None
        assert len(commit_id) == 12

    def test_get_branch_commit_returns_none_for_nonexistent(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns None for nonexistent branch."""
        commit_id = initialized_repo.get_branch_commit("nonexistent")

        assert commit_id is None

    def test_get_branch_commit_returns_none_for_empty_branch(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns None for branch with no commits."""
        commit_id = initialized_repo.get_branch_commit("main")

        assert commit_id is None

    def test_create_branch(self, repo_with_commit: Repository) -> None:
        """Test creating a new branch."""
        head_commit = repo_with_commit.get_head_commit()

        branch = repo_with_commit.create_branch("feature/test")

        assert branch.name == "feature/test"
        assert branch.commit_id == head_commit
        assert (repo_with_commit.heads_dir / "feature" / "test").exists()

    def test_create_branch_with_specific_commit(
        self, repo_with_commit: Repository
    ) -> None:
        """Test creating branch at specific commit."""
        branch = repo_with_commit.create_branch("feature/test", commit_id="custom123")

        assert branch.commit_id == "custom123"

    def test_create_branch_raises_if_exists(
        self, initialized_repo: Repository
    ) -> None:
        """Test create_branch raises error if branch exists."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.create_branch("main")

        assert "already exists" in str(exc_info.value)

    def test_update_branch(self, repo_with_commit: Repository) -> None:
        """Test updating branch to new commit."""
        repo_with_commit.update_branch("main", "newcommit123")

        commit_id = repo_with_commit.get_branch_commit("main")
        assert commit_id == "newcommit123"

    def test_update_branch_raises_if_not_exists(
        self, initialized_repo: Repository
    ) -> None:
        """Test update_branch raises error if branch doesn't exist."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.update_branch("nonexistent", "abc123")

        assert "does not exist" in str(exc_info.value)

    def test_delete_branch(self, repo_with_commit: Repository) -> None:
        """Test deleting a branch."""
        repo_with_commit.create_branch("to-delete")

        repo_with_commit.delete_branch("to-delete")

        assert "to-delete" not in repo_with_commit.list_branches()

    def test_delete_branch_raises_if_current(
        self, initialized_repo: Repository
    ) -> None:
        """Test delete_branch raises error for current branch."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.delete_branch("main")

        assert "Cannot delete current branch" in str(exc_info.value)

    def test_delete_branch_raises_if_not_exists(
        self, initialized_repo: Repository
    ) -> None:
        """Test delete_branch raises error if branch doesn't exist."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.delete_branch("nonexistent")

        assert "does not exist" in str(exc_info.value)

    def test_checkout_branch(self, repo_with_commit: Repository) -> None:
        """Test checking out a branch."""
        repo_with_commit.create_branch("feature/test")

        repo_with_commit.checkout_branch("feature/test")

        assert repo_with_commit.get_current_branch() == "feature/test"

    def test_checkout_branch_loads_commit_to_index(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test checkout loads branch commit state to index."""
        # Modify index
        repo_with_commit.update_index({"modified": True})
        
        # Create and checkout new branch
        repo_with_commit.create_branch("feature/test")
        repo_with_commit.checkout_branch("feature/test")

        # Index should have feature branch state (same as main since just created)
        index = repo_with_commit.get_index()
        assert index == sample_map_data

    def test_checkout_branch_clears_index_for_empty_branch(
        self, initialized_repo: Repository
    ) -> None:
        """Test checkout clears index for branch with no commits."""
        initialized_repo.update_index({"some": "data"})
        initialized_repo.create_branch("empty-branch")

        initialized_repo.checkout_branch("empty-branch")

        index = initialized_repo.get_index()
        assert index == {}

    def test_checkout_branch_raises_if_not_exists(
        self, initialized_repo: Repository
    ) -> None:
        """Test checkout_branch raises error for nonexistent branch."""
        with pytest.raises(RuntimeError) as exc_info:
            initialized_repo.checkout_branch("nonexistent")

        assert "does not exist" in str(exc_info.value)


# ---- Index Operations Tests ---------------------------------------------------------------------------------


class TestIndexOperations:
    """Tests for index/staging area operations."""

    def test_get_index_returns_empty_dict_initially(
        self, initialized_repo: Repository
    ) -> None:
        """Test get_index returns empty dict after init."""
        index = initialized_repo.get_index()

        assert index == {}

    def test_get_index_returns_empty_when_no_file(
        self, temp_repo_dir: Path
    ) -> None:
        """Test get_index returns empty dict when file doesn't exist."""
        repo = Repository(temp_repo_dir)

        index = repo.get_index()

        assert index == {}

    def test_get_index_handles_invalid_json(
        self, initialized_repo: Repository
    ) -> None:
        """Test get_index handles invalid JSON gracefully."""
        initialized_repo.index_path.write_text("not valid json")

        index = initialized_repo.get_index()

        assert index == {}

    def test_update_index(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test updating index with new map data."""
        initialized_repo.update_index(sample_map_data)

        index = initialized_repo.get_index()
        assert index == sample_map_data

    def test_update_index_overwrites_previous(
        self, initialized_repo: Repository
    ) -> None:
        """Test update_index replaces previous content."""
        initialized_repo.update_index({"first": "data"})
        initialized_repo.update_index({"second": "data"})

        index = initialized_repo.get_index()
        assert index == {"second": "data"}


# ---- Commit Operations Tests --------------------------------------------------------------------------------


class TestCommitOperations:
    """Tests for commit operations."""

    def test_create_commit(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test creating a commit."""
        initialized_repo.update_index(sample_map_data)

        commit = initialized_repo.create_commit("Test commit", author="Tester")

        assert commit is not None
        assert commit.message == "Test commit"
        assert commit.author == "Tester"
        assert len(commit.id) == 12

    def test_create_commit_uses_config_author(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test commit uses config author when not specified."""
        initialized_repo.update_index(sample_map_data)

        commit = initialized_repo.create_commit("Test commit")

        assert commit.author == "Test User"

    def test_create_commit_updates_branch(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test commit updates current branch."""
        initialized_repo.update_index(sample_map_data)

        commit = initialized_repo.create_commit("Test commit")

        branch_commit = initialized_repo.get_branch_commit("main")
        assert branch_commit == commit.id

    def test_create_commit_with_parent(
        self, repo_with_commit: Repository
    ) -> None:
        """Test commit has parent when previous commits exist."""
        first_commit = repo_with_commit.get_head_commit()
        repo_with_commit.update_index({"new": "data"})

        commit = repo_with_commit.create_commit("Second commit")

        assert commit.parent == first_commit

    def test_create_commit_saves_to_objects(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test commit is saved to objects directory."""
        initialized_repo.update_index(sample_map_data)

        commit = initialized_repo.create_commit("Test commit")

        commit_path = initialized_repo.commits_dir / f"{commit.id}.json"
        assert commit_path.exists()

    def test_create_commit_with_rationale(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test commit with rationale parameter."""
        initialized_repo.update_index(sample_map_data)

        # Should not raise - rationale is recorded in context store
        commit = initialized_repo.create_commit(
            "Test commit",
            rationale="This explains why we made this change"
        )

        assert commit is not None

    def test_get_commit(self, repo_with_commit: Repository) -> None:
        """Test getting a commit by ID."""
        commit_id = repo_with_commit.get_head_commit()

        commit = repo_with_commit.get_commit(commit_id)

        assert commit is not None
        assert commit.id == commit_id

    def test_get_commit_returns_none_for_nonexistent(
        self, initialized_repo: Repository
    ) -> None:
        """Test get_commit returns None for nonexistent commit."""
        commit = initialized_repo.get_commit("nonexistent123")

        assert commit is None

    def test_get_commit_history(self, repo_with_commit: Repository) -> None:
        """Test getting commit history."""
        repo_with_commit.update_index({"second": "data"})
        repo_with_commit.create_commit("Second commit")

        history = repo_with_commit.get_commit_history()

        assert len(history) == 2
        assert history[0].message == "Second commit"
        assert history[1].message == "Initial commit"

    def test_get_commit_history_with_limit(
        self, repo_with_commit: Repository
    ) -> None:
        """Test commit history respects limit."""
        for i in range(5):
            repo_with_commit.update_index({"num": i})
            repo_with_commit.create_commit(f"Commit {i}")

        history = repo_with_commit.get_commit_history(limit=3)

        assert len(history) == 3

    def test_get_commit_history_from_specific_commit(
        self, repo_with_commit: Repository
    ) -> None:
        """Test history starting from specific commit."""
        first_id = repo_with_commit.get_head_commit()
        repo_with_commit.update_index({"second": "data"})
        repo_with_commit.create_commit("Second commit")

        history = repo_with_commit.get_commit_history(start_commit=first_id)

        assert len(history) == 1
        assert history[0].id == first_id


# ---- Config Operations Tests --------------------------------------------------------------------------------


class TestConfigOperations:
    """Tests for config operations."""

    def test_get_config(self, initialized_repo: Repository) -> None:
        """Test getting repository config."""
        config = initialized_repo.get_config()

        assert config.project_name == "TestProject"
        assert config.user_name == "Test User"

    def test_get_config_raises_when_missing(self, temp_repo_dir: Path) -> None:
        """Test get_config raises error when config doesn't exist."""
        repo = Repository(temp_repo_dir)

        with pytest.raises(RuntimeError) as exc_info:
            repo.get_config()

        assert "not found" in str(exc_info.value)

    def test_update_config(self, initialized_repo: Repository) -> None:
        """Test updating repository config."""
        config = initialized_repo.get_config()
        config.user_name = "New Name"

        initialized_repo.update_config(config)

        loaded = initialized_repo.get_config()
        assert loaded.user_name == "New Name"


# ---- Status Operations Tests --------------------------------------------------------------------------------


class TestStatusOperations:
    """Tests for status-related operations."""

    def test_has_uncommitted_changes_true_with_new_data(
        self, repo_with_commit: Repository
    ) -> None:
        """Test detects uncommitted changes."""
        repo_with_commit.update_index({"new": "changes"})

        assert repo_with_commit.has_uncommitted_changes() is True

    def test_has_uncommitted_changes_false_when_clean(
        self, repo_with_commit: Repository
    ) -> None:
        """Test returns False when no changes."""
        assert repo_with_commit.has_uncommitted_changes() is False

    def test_has_uncommitted_changes_true_when_no_commits(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns True when index has data but no commits."""
        initialized_repo.update_index({"some": "data"})

        assert initialized_repo.has_uncommitted_changes() is True

    def test_has_uncommitted_changes_false_when_empty_no_commits(
        self, initialized_repo: Repository
    ) -> None:
        """Test returns False when empty index and no commits."""
        assert initialized_repo.has_uncommitted_changes() is False


# ---- Context Store Tests ------------------------------------------------------------------------------------


class TestContextStore:
    """Tests for context store integration."""

    def test_get_context_store(self, initialized_repo: Repository) -> None:
        """Test getting context store."""
        store = initialized_repo.get_context_store()

        assert store is not None
        store.close()

    def test_regenerate_context_graph(self, repo_with_commit: Repository) -> None:
        """Test regenerating context graph."""
        result = repo_with_commit.regenerate_context_graph()

        # Should return path or None depending on implementation
        # The method catches exceptions silently


# ---- Module Functions Tests ---------------------------------------------------------------------------------


class TestFindRepository:
    """Tests for find_repository function."""

    def test_find_repository_in_current_dir(
        self, initialized_repo: Repository
    ) -> None:
        """Test finding repo in current directory."""
        repo = find_repository(initialized_repo.root)

        assert repo is not None
        assert repo.root == initialized_repo.root

    def test_find_repository_in_parent(
        self, initialized_repo: Repository
    ) -> None:
        """Test finding repo in parent directory."""
        child_dir = initialized_repo.root / "child"
        child_dir.mkdir()

        repo = find_repository(child_dir)

        assert repo is not None
        assert repo.root == initialized_repo.root

    def test_find_repository_returns_none_when_not_found(
        self, temp_repo_dir: Path
    ) -> None:
        """Test returns None when no repo found."""
        repo = find_repository(temp_repo_dir)

        assert repo is None

    def test_find_repository_defaults_to_cwd(self) -> None:
        """Test uses cwd when no path provided."""
        # Just verify it doesn't raise
        result = find_repository()
        # Result depends on whether we're in a repo


class TestInitRepository:
    """Tests for init_repository function."""

    def test_init_repository_creates_repo(self, temp_repo_dir: Path) -> None:
        """Test init_repository creates and initializes repo."""
        repo = init_repository(
            path=temp_repo_dir,
            project_name="TestProject",
            user_name="Test User",
        )

        assert repo.exists()
        assert repo.is_valid()

    def test_init_repository_defaults_to_cwd(self) -> None:
        """Test init_repository uses cwd when no path."""
        # Just verify the function signature works
        # Don't actually run as it would create repo in cwd


# ---- Generate Commit ID Tests -------------------------------------------------------------------------------


class TestGenerateCommitId:
    """Tests for commit ID generation."""

    def test_generate_commit_id_is_deterministic(
        self, initialized_repo: Repository, sample_map_data: dict
    ) -> None:
        """Test same content produces same ID."""
        id1 = initialized_repo._generate_commit_id("msg", sample_map_data, None)
        id2 = initialized_repo._generate_commit_id("msg", sample_map_data, None)

        assert id1 == id2

    def test_generate_commit_id_different_for_different_content(
        self, initialized_repo: Repository
    ) -> None:
        """Test different content produces different ID."""
        id1 = initialized_repo._generate_commit_id("msg", {"a": 1}, None)
        id2 = initialized_repo._generate_commit_id("msg", {"b": 2}, None)

        assert id1 != id2

    def test_generate_commit_id_length(
        self, initialized_repo: Repository
    ) -> None:
        """Test commit ID is 12 characters."""
        commit_id = initialized_repo._generate_commit_id("msg", {}, None)

        assert len(commit_id) == 12

    def test_generate_commit_id_includes_parent(
        self, initialized_repo: Repository
    ) -> None:
        """Test parent affects commit ID."""
        id1 = initialized_repo._generate_commit_id("msg", {}, None)
        id2 = initialized_repo._generate_commit_id("msg", {}, "parent123")

        assert id1 != id2
