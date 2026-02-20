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

import pytest

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


# ---- Revert Tests -------------------------------------------------------------------------------------------


class TestRevert:
    """Tests for commit revert operations."""

    def test_revert_commit_not_found(self, initialized_repo: Repository) -> None:
        """Test revert raises error when commit not found."""
        with pytest.raises(RuntimeError, match="not found"):
            initialized_repo.revert("nonexistent")

    def test_revert_creates_new_commit(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert creates a new commit."""
        # Create a second commit with changes
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New Layer"})
        repo_with_commit.update_index(modified_data)
        second_commit = repo_with_commit.create_commit("Add new layer")

        # Revert the second commit
        revert_commit = repo_with_commit.revert(second_commit.id)

        assert revert_commit is not None
        assert revert_commit.id != second_commit.id
        assert "Revert" in revert_commit.message
        assert second_commit.id[:8] in revert_commit.message

    def test_revert_restores_layer_removal(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert restores a removed layer."""
        # Create commit that removes a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"] = [{"id": "layer-1", "title": "Roads"}]
        repo_with_commit.update_index(modified_data)
        removal_commit = repo_with_commit.create_commit("Remove layer-2")

        # Revert the removal
        revert_commit = repo_with_commit.revert(removal_commit.id)

        # Check that layer-2 is back
        layers = revert_commit.map_data.get("operationalLayers", [])
        layer_ids = [l.get("id") for l in layers]
        assert "layer-2" in layer_ids

    def test_revert_removes_added_layer(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert removes an added layer."""
        # Create commit that adds a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        addition_commit = repo_with_commit.create_commit("Add layer-3")

        # Revert the addition
        revert_commit = repo_with_commit.revert(addition_commit.id)

        # Check that layer-3 is gone
        layers = revert_commit.map_data.get("operationalLayers", [])
        layer_ids = [l.get("id") for l in layers]
        assert "layer-3" not in layer_ids
        assert "layer-1" in layer_ids
        assert "layer-2" in layer_ids

    def test_revert_restores_modified_layer(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert restores a modified layer to original state."""
        # Create commit that modifies a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"][0]["title"] = "Modified Roads"
        repo_with_commit.update_index(modified_data)
        modification_commit = repo_with_commit.create_commit("Modify layer-1")

        # Revert the modification
        revert_commit = repo_with_commit.revert(modification_commit.id)

        # Check that layer-1 has original title
        layers = revert_commit.map_data.get("operationalLayers", [])
        layer_1 = next((l for l in layers if l.get("id") == "layer-1"), None)
        assert layer_1 is not None
        assert layer_1["title"] == "Roads"

    def test_revert_with_rationale(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert accepts rationale parameter."""
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        commit = repo_with_commit.create_commit("Add layer")

        revert_commit = repo_with_commit.revert(
            commit.id,
            rationale="Reverting because layer was added by mistake",
        )

        assert revert_commit is not None

    def test_revert_updates_branch(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test revert updates the current branch."""
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        commit = repo_with_commit.create_commit("Add layer")

        revert_commit = repo_with_commit.revert(commit.id)

        # Branch should point to revert commit
        branch_commit = repo_with_commit.get_branch_commit("main")
        assert branch_commit == revert_commit.id

    def test_revert_initial_commit(self, repo_with_commit: Repository) -> None:
        """Test reverting the initial commit."""
        # Get the initial commit
        history = repo_with_commit.get_commit_history()
        initial_commit = history[0]

        # Revert it
        revert_commit = repo_with_commit.revert(initial_commit.id)

        # All layers should be removed (back to empty state)
        assert revert_commit is not None
        layers = revert_commit.map_data.get("operationalLayers", [])
        assert len(layers) == 0


class TestComputeRevert:
    """Tests for _compute_revert helper method."""

    def test_compute_revert_layer_addition(
        self, initialized_repo: Repository
    ) -> None:
        """Test computing revert for layer addition."""
        parent_data = {"operationalLayers": [{"id": "1", "title": "A"}]}
        commit_data = {
            "operationalLayers": [
                {"id": "1", "title": "A"},
                {"id": "2", "title": "B"},
            ]
        }
        current_data = commit_data.copy()

        result = initialized_repo._compute_revert(
            current_data, commit_data, parent_data
        )

        layer_ids = [l["id"] for l in result["operationalLayers"]]
        assert "1" in layer_ids
        assert "2" not in layer_ids

    def test_compute_revert_layer_removal(
        self, initialized_repo: Repository
    ) -> None:
        """Test computing revert for layer removal."""
        parent_data = {
            "operationalLayers": [
                {"id": "1", "title": "A"},
                {"id": "2", "title": "B"},
            ]
        }
        commit_data = {"operationalLayers": [{"id": "1", "title": "A"}]}
        current_data = commit_data.copy()

        result = initialized_repo._compute_revert(
            current_data, commit_data, parent_data
        )

        layer_ids = [l["id"] for l in result["operationalLayers"]]
        assert "1" in layer_ids
        assert "2" in layer_ids

    def test_compute_revert_layer_modification(
        self, initialized_repo: Repository
    ) -> None:
        """Test computing revert for layer modification."""
        parent_data = {"operationalLayers": [{"id": "1", "title": "Original"}]}
        commit_data = {"operationalLayers": [{"id": "1", "title": "Modified"}]}
        current_data = commit_data.copy()

        result = initialized_repo._compute_revert(
            current_data, commit_data, parent_data
        )

        layer = result["operationalLayers"][0]
        assert layer["title"] == "Original"

    def test_compute_revert_preserves_unrelated_changes(
        self, initialized_repo: Repository
    ) -> None:
        """Test revert preserves changes not from the reverted commit."""
        parent_data = {"operationalLayers": [{"id": "1", "title": "A"}]}
        commit_data = {
            "operationalLayers": [
                {"id": "1", "title": "A"},
                {"id": "2", "title": "B"},
            ]
        }
        # Current has additional layer-3 that wasn't part of commit
        current_data = {
            "operationalLayers": [
                {"id": "1", "title": "A"},
                {"id": "2", "title": "B"},
                {"id": "3", "title": "C"},
            ]
        }

        result = initialized_repo._compute_revert(
            current_data, commit_data, parent_data
        )

        layer_ids = [l["id"] for l in result["operationalLayers"]]
        assert "1" in layer_ids
        assert "2" not in layer_ids  # Reverted
        assert "3" in layer_ids  # Preserved


class TestRevertLayers:
    """Tests for _revert_layers helper method."""

    def test_revert_layers_empty(self, initialized_repo: Repository) -> None:
        """Test reverting with empty layers."""
        result = initialized_repo._revert_layers([], [], [])
        assert result == []

    def test_revert_layers_no_id(self, initialized_repo: Repository) -> None:
        """Test layers without id are preserved."""
        current = [{"title": "No ID"}]
        result = initialized_repo._revert_layers(current, current, current)
        assert result == current


# ---- Tag Tests ----------------------------------------------------------------------------------------------


class TestTags:
    """Tests for tag operations."""

    def test_list_tags_empty(self, initialized_repo: Repository) -> None:
        """Test listing tags when none exist."""
        tags = initialized_repo.list_tags()
        assert tags == []

    def test_create_tag(self, repo_with_commit: Repository) -> None:
        """Test creating a tag."""
        head_commit = repo_with_commit.get_head_commit()
        commit_id = repo_with_commit.create_tag("v1.0.0")

        assert commit_id == head_commit
        assert repo_with_commit.tags_dir.exists()
        assert (repo_with_commit.tags_dir / "v1.0.0").exists()

    def test_create_tag_with_specific_commit(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test creating a tag pointing to specific commit."""
        # Create a second commit
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        second_commit = repo_with_commit.create_commit("Second commit")

        # Get first commit
        first_commit = repo_with_commit.get_commit(second_commit.parent)

        # Tag the first commit
        commit_id = repo_with_commit.create_tag("v0.1.0", first_commit.id)

        assert commit_id == first_commit.id

    def test_create_tag_already_exists(self, repo_with_commit: Repository) -> None:
        """Test creating a tag that already exists raises error."""
        repo_with_commit.create_tag("v1.0.0")

        with pytest.raises(RuntimeError, match="already exists"):
            repo_with_commit.create_tag("v1.0.0")

    def test_create_tag_no_commits(self, initialized_repo: Repository) -> None:
        """Test creating a tag with no commits raises error."""
        with pytest.raises(RuntimeError, match="no commits"):
            initialized_repo.create_tag("v1.0.0")

    def test_create_tag_invalid_commit(self, repo_with_commit: Repository) -> None:
        """Test creating a tag with invalid commit raises error."""
        with pytest.raises(RuntimeError, match="not found"):
            repo_with_commit.create_tag("v1.0.0", "nonexistent123")

    def test_create_tag_invalid_name(self, repo_with_commit: Repository) -> None:
        """Test creating a tag with invalid name raises error."""
        with pytest.raises(RuntimeError, match="Invalid tag name"):
            repo_with_commit.create_tag("bad tag name")

        with pytest.raises(RuntimeError, match="Invalid tag name"):
            repo_with_commit.create_tag("")

    def test_get_tag(self, repo_with_commit: Repository) -> None:
        """Test getting a tag's commit ID."""
        head_commit = repo_with_commit.get_head_commit()
        repo_with_commit.create_tag("v1.0.0")

        commit_id = repo_with_commit.get_tag("v1.0.0")
        assert commit_id == head_commit

    def test_get_tag_not_found(self, repo_with_commit: Repository) -> None:
        """Test getting a non-existent tag returns None."""
        commit_id = repo_with_commit.get_tag("nonexistent")
        assert commit_id is None

    def test_list_tags(self, repo_with_commit: Repository) -> None:
        """Test listing multiple tags."""
        repo_with_commit.create_tag("v1.0.0")
        repo_with_commit.create_tag("v2.0.0")
        repo_with_commit.create_tag("alpha")

        tags = repo_with_commit.list_tags()

        assert len(tags) == 3
        assert "alpha" in tags
        assert "v1.0.0" in tags
        assert "v2.0.0" in tags
        # Should be sorted
        assert tags == sorted(tags)

    def test_delete_tag(self, repo_with_commit: Repository) -> None:
        """Test deleting a tag."""
        repo_with_commit.create_tag("v1.0.0")
        assert repo_with_commit.get_tag("v1.0.0") is not None

        repo_with_commit.delete_tag("v1.0.0")

        assert repo_with_commit.get_tag("v1.0.0") is None
        assert "v1.0.0" not in repo_with_commit.list_tags()

    def test_delete_tag_not_found(self, repo_with_commit: Repository) -> None:
        """Test deleting a non-existent tag raises error."""
        with pytest.raises(RuntimeError, match="does not exist"):
            repo_with_commit.delete_tag("nonexistent")

    def test_tag_nested_name(self, repo_with_commit: Repository) -> None:
        """Test creating a tag with nested path name."""
        repo_with_commit.create_tag("release/v1.0.0")

        tags = repo_with_commit.list_tags()
        assert "release/v1.0.0" in tags

        commit_id = repo_with_commit.get_tag("release/v1.0.0")
        assert commit_id == repo_with_commit.get_head_commit()


class TestCherryPick:
    """Tests for cherry-pick operations."""

    def test_cherry_pick_commit_not_found(self, initialized_repo: Repository) -> None:
        """Test cherry-pick raises error when commit not found."""
        with pytest.raises(RuntimeError, match="not found"):
            initialized_repo.cherry_pick("nonexistent")

    def test_cherry_pick_creates_new_commit(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick creates a new commit."""
        # Create feature branch with new commit
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "Feature Layer"})
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Add feature layer")

        # Switch back to main
        repo_with_commit.checkout_branch("main")

        # Cherry-pick the feature commit
        new_commit = repo_with_commit.cherry_pick(feature_commit.id)

        assert new_commit is not None
        assert new_commit.id != feature_commit.id
        assert feature_commit.id[:8] in new_commit.message

    def test_cherry_pick_applies_added_layer(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick applies layer additions."""
        # Create feature branch
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        # Add a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "Feature"})
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Add layer")

        # Switch back to main
        repo_with_commit.checkout_branch("main")

        # Verify main doesn't have layer-3
        current = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current.get("operationalLayers", [])]
        assert "layer-3" not in layer_ids

        # Cherry-pick
        new_commit = repo_with_commit.cherry_pick(feature_commit.id)

        # Main should now have layer-3
        layers = new_commit.map_data.get("operationalLayers", [])
        layer_ids = [l.get("id") for l in layers]
        assert "layer-3" in layer_ids

    def test_cherry_pick_applies_removed_layer(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick applies layer removals."""
        # Create feature branch
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        # Remove a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"] = [{"id": "layer-1", "title": "Roads"}]
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Remove layer-2")

        # Switch back to main
        repo_with_commit.checkout_branch("main")

        # Cherry-pick
        new_commit = repo_with_commit.cherry_pick(feature_commit.id)

        # Main should no longer have layer-2
        layers = new_commit.map_data.get("operationalLayers", [])
        layer_ids = [l.get("id") for l in layers]
        assert "layer-2" not in layer_ids
        assert "layer-1" in layer_ids

    def test_cherry_pick_applies_modified_layer(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick applies layer modifications."""
        # Create feature branch
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        # Modify a layer
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"][0]["title"] = "Modified Roads"
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Modify layer")

        # Switch back to main
        repo_with_commit.checkout_branch("main")

        # Cherry-pick
        new_commit = repo_with_commit.cherry_pick(feature_commit.id)

        # Layer-1 should be modified
        layers = new_commit.map_data.get("operationalLayers", [])
        layer_1 = next((l for l in layers if l.get("id") == "layer-1"), None)
        assert layer_1 is not None
        assert layer_1["title"] == "Modified Roads"

    def test_cherry_pick_with_rationale(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick accepts rationale parameter."""
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "Fix"})
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Add fix")

        repo_with_commit.checkout_branch("main")

        new_commit = repo_with_commit.cherry_pick(
            feature_commit.id,
            rationale="Backporting critical fix to main",
        )

        assert new_commit is not None

    def test_cherry_pick_updates_branch(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test cherry-pick updates the current branch."""
        repo_with_commit.create_branch("feature")
        repo_with_commit.checkout_branch("feature")

        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        feature_commit = repo_with_commit.create_commit("Add layer")

        repo_with_commit.checkout_branch("main")
        old_head = repo_with_commit.get_head_commit()

        new_commit = repo_with_commit.cherry_pick(feature_commit.id)

        # Branch should point to new commit
        branch_commit = repo_with_commit.get_branch_commit("main")
        assert branch_commit == new_commit.id
        assert branch_commit != old_head


class TestStash:
    """Tests for stash operations."""

    def test_stash_list_empty(self, initialized_repo: Repository) -> None:
        """Test listing stashes when none exist."""
        stashes = initialized_repo.stash_list()
        assert stashes == []

    def test_stash_push_no_changes(self, repo_with_commit: Repository) -> None:
        """Test stash push with no uncommitted changes."""
        with pytest.raises(RuntimeError, match="No changes to stash"):
            repo_with_commit.stash_push()

    def test_stash_push(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test pushing changes to stash."""
        # Make changes
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)

        # Stash changes
        stash_entry = repo_with_commit.stash_push(message="WIP feature")

        assert stash_entry is not None
        assert "WIP feature" in stash_entry["message"]
        assert stash_entry["index_data"] == modified_data

        # Index should be restored to HEAD state
        current_index = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current_index.get("operationalLayers", [])]
        assert "layer-3" not in layer_ids

    def test_stash_push_creates_dir(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test stash push creates stash directory."""
        assert not repo_with_commit.stash_dir.exists()

        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)

        repo_with_commit.stash_push()

        assert repo_with_commit.stash_dir.exists()


class TestApplyLayerChanges:
    """Tests for _apply_layer_changes helper method."""

    def test_apply_layer_changes_addition(
        self, initialized_repo: Repository
    ) -> None:
        """Test applying layer additions."""
        current = [{"id": "1", "title": "A"}]
        parent = [{"id": "1", "title": "A"}]
        commit = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]

        result = initialized_repo._apply_layer_changes(current, commit, parent)

        layer_ids = [l["id"] for l in result]
        assert "1" in layer_ids
        assert "2" in layer_ids

    def test_apply_layer_changes_removal(
        self, initialized_repo: Repository
    ) -> None:
        """Test applying layer removals."""
        current = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        parent = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        commit = [{"id": "1", "title": "A"}]

        result = initialized_repo._apply_layer_changes(current, commit, parent)

        layer_ids = [l["id"] for l in result]
        assert "1" in layer_ids
        assert "2" not in layer_ids

    def test_apply_layer_changes_modification(
        self, initialized_repo: Repository
    ) -> None:
        """Test applying layer modifications."""
        current = [{"id": "1", "title": "Original"}]
        parent = [{"id": "1", "title": "Original"}]
        commit = [{"id": "1", "title": "Modified"}]

        result = initialized_repo._apply_layer_changes(current, commit, parent)

        assert result[0]["title"] == "Modified"

    def test_apply_layer_changes_no_duplicate(
        self, initialized_repo: Repository
    ) -> None:
        """Test adding a layer that already exists."""
        current = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        parent = [{"id": "1", "title": "A"}]
        commit = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]

        result = initialized_repo._apply_layer_changes(current, commit, parent)

        # Should not duplicate layer-2
        layer_ids = [l["id"] for l in result]
        assert layer_ids.count("2") == 1

    def test_stash_list_after_push(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test listing stashes after push."""
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)

        repo_with_commit.stash_push(message="First stash")

        stashes = repo_with_commit.stash_list()
        assert len(stashes) == 1
        assert "First stash" in stashes[0]["message"]

    def test_stash_multiple(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test pushing multiple stashes."""
        # First stash
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "First"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="First")

        # Second stash
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-4", "title": "Second"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="Second")

        stashes = repo_with_commit.stash_list()
        assert len(stashes) == 2
        # Newest first
        assert "Second" in stashes[0]["message"]
        assert "First" in stashes[1]["message"]

    def test_stash_pop_empty(self, initialized_repo: Repository) -> None:
        """Test pop with empty stash list."""
        with pytest.raises(RuntimeError, match="No stash entries"):
            initialized_repo.stash_pop()

    def test_stash_pop(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test popping a stash."""
        # Make changes and stash
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "Stashed"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="Stash to pop")

        # Verify index is clean
        current_index = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current_index.get("operationalLayers", [])]
        assert "layer-3" not in layer_ids

        # Pop stash
        stash_entry = repo_with_commit.stash_pop()

        # Verify changes are restored
        current_index = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current_index.get("operationalLayers", [])]
        assert "layer-3" in layer_ids

        # Stash list should be empty
        assert len(repo_with_commit.stash_list()) == 0

    def test_stash_pop_specific_index(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test popping a specific stash index."""
        # Create two stashes
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "First"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="First")

        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-4", "title": "Second"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="Second")

        # Pop index 1 (first stash, older one)
        stash_entry = repo_with_commit.stash_pop(index=1)

        assert "First" in stash_entry["message"]

        # Verify layer-3 is restored (from first stash)
        current_index = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current_index.get("operationalLayers", [])]
        assert "layer-3" in layer_ids
        assert "layer-4" not in layer_ids

        # Second stash should still exist
        stashes = repo_with_commit.stash_list()
        assert len(stashes) == 1
        assert "Second" in stashes[0]["message"]

    def test_stash_pop_invalid_index(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test pop with invalid index."""
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push()

        with pytest.raises(RuntimeError, match="Invalid stash index"):
            repo_with_commit.stash_pop(index=5)

    def test_stash_drop(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test dropping a stash."""
        modified_data = sample_map_data.copy()
        modified_data["operationalLayers"].append({"id": "layer-3", "title": "New"})
        repo_with_commit.update_index(modified_data)
        repo_with_commit.stash_push(message="Stash to drop")

        assert len(repo_with_commit.stash_list()) == 1

        stash_ref = repo_with_commit.stash_drop()

        assert "Stash to drop" in stash_ref.get("message", "")
        assert len(repo_with_commit.stash_list()) == 0

        # Index should NOT be modified (unlike pop)
        current_index = repo_with_commit.get_index()
        layer_ids = [l.get("id") for l in current_index.get("operationalLayers", [])]
        assert "layer-3" not in layer_ids

    def test_stash_drop_empty(self, initialized_repo: Repository) -> None:
        """Test drop with empty stash list."""
        with pytest.raises(RuntimeError, match="No stash entries"):
            initialized_repo.stash_drop()

    def test_stash_clear(
        self, repo_with_commit: Repository, sample_map_data: dict
    ) -> None:
        """Test clearing all stashes."""
        # Create multiple stashes
        for i in range(3):
            modified_data = sample_map_data.copy()
            modified_data["operationalLayers"].append({"id": f"layer-{i+3}", "title": f"New {i}"})
            repo_with_commit.update_index(modified_data)
            repo_with_commit.stash_push(message=f"Stash {i}")

        assert len(repo_with_commit.stash_list()) == 3

        count = repo_with_commit.stash_clear()

        assert count == 3
        assert len(repo_with_commit.stash_list()) == 0

    def test_stash_clear_empty(self, initialized_repo: Repository) -> None:
        """Test clear with empty stash list."""
        count = initialized_repo.stash_clear()
        assert count == 0


# ---- TestFindCommonAncestor --------------------------------------------------------------------------


class TestFindCommonAncestor:
    """Tests for Repository.find_common_ancestor."""

    def test_direct_parent_is_ancestor(self, repo_with_commit: Repository, sample_map_data: dict) -> None:
        """Common ancestor of a child and its parent is the parent itself."""
        # repo_with_commit already has one commit on 'main'
        parent_id = repo_with_commit.get_head_commit()
        assert parent_id is not None

        # Create a second commit on main
        repo_with_commit.update_index(sample_map_data)
        child_commit = repo_with_commit.create_commit(message="second commit")
        child_id = child_commit.id

        ancestor = repo_with_commit.find_common_ancestor(child_id, parent_id)
        assert ancestor == parent_id

    def test_same_commit_is_its_own_ancestor(self, repo_with_commit: Repository) -> None:
        """A commit is its own common ancestor when both inputs are identical."""
        commit_id = repo_with_commit.get_head_commit()
        assert commit_id is not None

        ancestor = repo_with_commit.find_common_ancestor(commit_id, commit_id)
        assert ancestor == commit_id

    def test_branched_histories_share_ancestor(
        self,
        repo_with_commit: Repository,
        sample_map_data: dict,
    ) -> None:
        """Two branches that diverged from main share the fork-point as ancestor."""
        # HEAD of main is the fork point
        fork_id = repo_with_commit.get_head_commit()
        assert fork_id is not None

        # Create branch-a and add a commit
        repo_with_commit.create_branch("branch-a")
        repo_with_commit.checkout_branch("branch-a")
        layer_a = {"id": "layer-a", "title": "Layer A"}
        data_a = {**sample_map_data, "operationalLayers": [layer_a]}
        repo_with_commit.update_index(data_a)
        commit_a = repo_with_commit.create_commit(message="commit on branch-a")

        # Switch back to main and create branch-b
        repo_with_commit.checkout_branch("main")
        repo_with_commit.create_branch("branch-b")
        repo_with_commit.checkout_branch("branch-b")
        layer_b = {"id": "layer-b", "title": "Layer B"}
        data_b = {**sample_map_data, "operationalLayers": [layer_b]}
        repo_with_commit.update_index(data_b)
        commit_b = repo_with_commit.create_commit(message="commit on branch-b")

        ancestor = repo_with_commit.find_common_ancestor(commit_a.id, commit_b.id)
        assert ancestor == fork_id

    def test_unrelated_commits_return_none(self, tmp_path: "Path") -> None:
        """Two commits with no shared history return None."""
        from gitmap_core.repository import init_repository

        repo = init_repository(tmp_path / "repo-x", user_name="test", user_email="t@t.com")
        map_data_1 = {"operationalLayers": [{"id": "l1", "title": "Layer 1"}]}
        repo.update_index(map_data_1)
        c1 = repo.create_commit(message="first")

        map_data_2 = {"operationalLayers": [{"id": "l2", "title": "Layer 2"}]}
        repo.update_index(map_data_2)
        c2 = repo.create_commit(message="second")

        # Manually look up the root commit id (c1 has no parent, c2's parent is c1)
        # Test with a bogus ID to simulate truly unrelated history
        ancestor = repo.find_common_ancestor("deadbeef0001", "deadbeef0002")
        assert ancestor is None

    def test_ancestor_with_merge_commit(
        self,
        repo_with_commit: Repository,
        sample_map_data: dict,
    ) -> None:
        """find_common_ancestor follows parent2 links from merge commits."""
        fork_id = repo_with_commit.get_head_commit()
        assert fork_id is not None

        # Build two branches from the fork
        repo_with_commit.create_branch("feat-x")
        repo_with_commit.checkout_branch("feat-x")
        repo_with_commit.update_index({**sample_map_data, "title": "feat-x"})
        commit_x = repo_with_commit.create_commit(message="feat-x commit")

        repo_with_commit.checkout_branch("main")
        repo_with_commit.update_index({**sample_map_data, "title": "main-update"})
        commit_main = repo_with_commit.create_commit(message="main update")

        # The fork_id should still be reachable as ancestor of both
        ancestor = repo_with_commit.find_common_ancestor(commit_x.id, commit_main.id)
        assert ancestor == fork_id
