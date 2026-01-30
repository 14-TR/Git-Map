"""Tests for data models module.

Tests the core data structures: Commit, Branch, Remote, and RepoConfig.
Covers serialization (to_dict/from_dict), file I/O (save/load), and
factory methods.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.models: Module under test
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from gitmap_core.models import Branch, Commit, Remote, RepoConfig


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def sample_map_data() -> dict:
    """Create sample web map JSON data for testing."""
    return {
        "operationalLayers": [
            {"id": "layer1", "title": "Test Layer", "url": "https://example.com/layer"}
        ],
        "baseMap": {"title": "Topographic"},
        "version": "2.29",
    }


@pytest.fixture
def sample_commit(sample_map_data: dict) -> Commit:
    """Create a sample commit for testing."""
    return Commit(
        id="abc123def456",
        message="Initial commit",
        author="Test User",
        timestamp="2026-01-30T12:00:00",
        parent=None,
        parent2=None,
        map_data=sample_map_data,
    )


@pytest.fixture
def sample_branch() -> Branch:
    """Create a sample branch for testing."""
    return Branch(name="main", commit_id="abc123def456")


@pytest.fixture
def sample_remote() -> Remote:
    """Create a sample remote for testing."""
    return Remote(
        name="origin",
        url="https://www.arcgis.com",
        folder_id="folder123",
        folder_name="GitMap Projects",
        item_id="item456",
        production_branch="main",
    )


@pytest.fixture
def sample_config(sample_remote: Remote) -> RepoConfig:
    """Create a sample config for testing."""
    return RepoConfig(
        version="1.0",
        user_name="Test User",
        user_email="test@example.com",
        remote=sample_remote,
        project_name="Test Project",
        auto_visualize=True,
    )


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for file I/O tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ---- Commit Tests --------------------------------------------------------------------------------------------


class TestCommit:
    """Tests for the Commit dataclass."""

    def test_create_sets_timestamp(self, sample_map_data: dict) -> None:
        """Test that create() sets the current timestamp."""
        before = datetime.now().isoformat()
        commit = Commit.create(
            commit_id="test123",
            message="Test commit",
            author="Author",
            map_data=sample_map_data,
        )
        after = datetime.now().isoformat()

        assert commit.timestamp >= before
        assert commit.timestamp <= after

    def test_create_with_parent(self) -> None:
        """Test creating a commit with a parent."""
        commit = Commit.create(
            commit_id="child123",
            message="Child commit",
            author="Author",
            parent="parent456",
        )

        assert commit.parent == "parent456"
        assert commit.parent2 is None

    def test_create_merge_commit(self) -> None:
        """Test creating a merge commit with two parents."""
        commit = Commit.create(
            commit_id="merge123",
            message="Merge branch",
            author="Author",
            parent="parent1",
            parent2="parent2",
        )

        assert commit.parent == "parent1"
        assert commit.parent2 == "parent2"

    def test_create_defaults_map_data_to_empty_dict(self) -> None:
        """Test that map_data defaults to empty dict when None."""
        commit = Commit.create(
            commit_id="test123",
            message="Test",
            author="Author",
            map_data=None,
        )

        assert commit.map_data == {}

    def test_to_dict_returns_all_fields(self, sample_commit: Commit) -> None:
        """Test that to_dict includes all fields."""
        result = sample_commit.to_dict()

        assert result["id"] == "abc123def456"
        assert result["message"] == "Initial commit"
        assert result["author"] == "Test User"
        assert result["timestamp"] == "2026-01-30T12:00:00"
        assert result["parent"] is None
        assert result["parent2"] is None
        assert "operationalLayers" in result["map_data"]

    def test_from_dict_round_trip(self, sample_commit: Commit) -> None:
        """Test that from_dict(to_dict()) returns equivalent commit."""
        data = sample_commit.to_dict()
        restored = Commit.from_dict(data)

        assert restored.id == sample_commit.id
        assert restored.message == sample_commit.message
        assert restored.author == sample_commit.author
        assert restored.timestamp == sample_commit.timestamp
        assert restored.parent == sample_commit.parent
        assert restored.map_data == sample_commit.map_data

    def test_save_creates_file(self, sample_commit: Commit, temp_dir: Path) -> None:
        """Test that save() creates a JSON file."""
        filepath = sample_commit.save(temp_dir)

        assert filepath.exists()
        assert filepath.name == "abc123def456.json"

    def test_save_writes_valid_json(self, sample_commit: Commit, temp_dir: Path) -> None:
        """Test that saved file contains valid JSON."""
        filepath = sample_commit.save(temp_dir)
        data = json.loads(filepath.read_text())

        assert data["id"] == sample_commit.id
        assert data["message"] == sample_commit.message

    def test_load_restores_commit(self, sample_commit: Commit, temp_dir: Path) -> None:
        """Test that load() restores a saved commit."""
        filepath = sample_commit.save(temp_dir)
        restored = Commit.load(filepath)

        assert restored.id == sample_commit.id
        assert restored.message == sample_commit.message
        assert restored.map_data == sample_commit.map_data

    def test_load_raises_on_missing_file(self, temp_dir: Path) -> None:
        """Test that load() raises RuntimeError for missing file."""
        with pytest.raises(RuntimeError) as exc_info:
            Commit.load(temp_dir / "nonexistent.json")

        assert "Failed to load commit" in str(exc_info.value)

    def test_load_raises_on_invalid_json(self, temp_dir: Path) -> None:
        """Test that load() raises RuntimeError for invalid JSON."""
        bad_file = temp_dir / "bad.json"
        bad_file.write_text("not valid json {{{")

        with pytest.raises(RuntimeError) as exc_info:
            Commit.load(bad_file)

        assert "Failed to load commit" in str(exc_info.value)


# ---- Branch Tests --------------------------------------------------------------------------------------------


class TestBranch:
    """Tests for the Branch dataclass."""

    def test_to_dict_returns_name_and_commit_id(self, sample_branch: Branch) -> None:
        """Test that to_dict includes both fields."""
        result = sample_branch.to_dict()

        assert result["name"] == "main"
        assert result["commit_id"] == "abc123def456"

    def test_from_dict_round_trip(self, sample_branch: Branch) -> None:
        """Test that from_dict(to_dict()) returns equivalent branch."""
        data = sample_branch.to_dict()
        restored = Branch.from_dict(data)

        assert restored.name == sample_branch.name
        assert restored.commit_id == sample_branch.commit_id

    def test_branch_with_feature_name(self) -> None:
        """Test branch with feature branch naming."""
        branch = Branch(name="feature/add-new-layer", commit_id="xyz789")

        assert branch.name == "feature/add-new-layer"
        assert "/" in branch.name  # Verify slash is preserved


# ---- Remote Tests --------------------------------------------------------------------------------------------


class TestRemote:
    """Tests for the Remote dataclass."""

    def test_to_dict_includes_all_fields(self, sample_remote: Remote) -> None:
        """Test that to_dict includes all fields."""
        result = sample_remote.to_dict()

        assert result["name"] == "origin"
        assert result["url"] == "https://www.arcgis.com"
        assert result["folder_id"] == "folder123"
        assert result["folder_name"] == "GitMap Projects"
        assert result["item_id"] == "item456"
        assert result["production_branch"] == "main"

    def test_from_dict_round_trip(self, sample_remote: Remote) -> None:
        """Test that from_dict(to_dict()) returns equivalent remote."""
        data = sample_remote.to_dict()
        restored = Remote.from_dict(data)

        assert restored.name == sample_remote.name
        assert restored.url == sample_remote.url
        assert restored.folder_id == sample_remote.folder_id
        assert restored.production_branch == sample_remote.production_branch

    def test_remote_with_minimal_fields(self) -> None:
        """Test remote with only required fields."""
        remote = Remote(name="origin", url="https://portal.example.com")

        assert remote.folder_id is None
        assert remote.folder_name is None
        assert remote.item_id is None
        assert remote.production_branch is None

    def test_minimal_remote_round_trip(self) -> None:
        """Test that minimal remote survives serialization."""
        remote = Remote(name="origin", url="https://portal.example.com")
        data = remote.to_dict()
        restored = Remote.from_dict(data)

        assert restored.name == "origin"
        assert restored.folder_id is None


# ---- RepoConfig Tests ----------------------------------------------------------------------------------------


class TestRepoConfig:
    """Tests for the RepoConfig dataclass."""

    def test_to_dict_includes_all_fields(self, sample_config: RepoConfig) -> None:
        """Test that to_dict includes all fields."""
        result = sample_config.to_dict()

        assert result["version"] == "1.0"
        assert result["user_name"] == "Test User"
        assert result["user_email"] == "test@example.com"
        assert result["project_name"] == "Test Project"
        assert result["auto_visualize"] is True
        assert "remote" in result

    def test_to_dict_includes_nested_remote(self, sample_config: RepoConfig) -> None:
        """Test that nested remote is serialized."""
        result = sample_config.to_dict()

        assert result["remote"]["name"] == "origin"
        assert result["remote"]["url"] == "https://www.arcgis.com"

    def test_to_dict_without_remote(self) -> None:
        """Test that config without remote omits remote key."""
        config = RepoConfig(user_name="User", user_email="user@example.com")
        result = config.to_dict()

        assert "remote" not in result

    def test_from_dict_round_trip(self, sample_config: RepoConfig) -> None:
        """Test that from_dict(to_dict()) returns equivalent config."""
        data = sample_config.to_dict()
        restored = RepoConfig.from_dict(data)

        assert restored.version == sample_config.version
        assert restored.user_name == sample_config.user_name
        assert restored.user_email == sample_config.user_email
        assert restored.project_name == sample_config.project_name
        assert restored.auto_visualize == sample_config.auto_visualize

    def test_from_dict_restores_nested_remote(self, sample_config: RepoConfig) -> None:
        """Test that nested remote is deserialized."""
        data = sample_config.to_dict()
        restored = RepoConfig.from_dict(data)

        assert restored.remote is not None
        assert restored.remote.name == "origin"
        assert restored.remote.url == "https://www.arcgis.com"

    def test_from_dict_handles_missing_remote(self) -> None:
        """Test that missing remote results in None."""
        data = {"version": "1.0", "user_name": "User"}
        config = RepoConfig.from_dict(data)

        assert config.remote is None

    def test_from_dict_uses_defaults(self) -> None:
        """Test that from_dict uses default values for missing fields."""
        config = RepoConfig.from_dict({})

        assert config.version == "1.0"
        assert config.user_name == ""
        assert config.user_email == ""
        assert config.project_name == ""
        assert config.auto_visualize is False

    def test_save_creates_file(self, sample_config: RepoConfig, temp_dir: Path) -> None:
        """Test that save() creates a JSON file."""
        config_path = temp_dir / "config.json"
        sample_config.save(config_path)

        assert config_path.exists()

    def test_save_writes_valid_json(self, sample_config: RepoConfig, temp_dir: Path) -> None:
        """Test that saved file contains valid JSON."""
        config_path = temp_dir / "config.json"
        sample_config.save(config_path)
        data = json.loads(config_path.read_text())

        assert data["user_name"] == "Test User"
        assert data["remote"]["name"] == "origin"

    def test_load_restores_config(self, sample_config: RepoConfig, temp_dir: Path) -> None:
        """Test that load() restores a saved config."""
        config_path = temp_dir / "config.json"
        sample_config.save(config_path)
        restored = RepoConfig.load(config_path)

        assert restored.user_name == sample_config.user_name
        assert restored.remote.name == sample_config.remote.name

    def test_load_raises_on_missing_file(self, temp_dir: Path) -> None:
        """Test that load() raises RuntimeError for missing file."""
        with pytest.raises(RuntimeError) as exc_info:
            RepoConfig.load(temp_dir / "nonexistent.json")

        assert "Failed to load config" in str(exc_info.value)

    def test_load_raises_on_invalid_json(self, temp_dir: Path) -> None:
        """Test that load() raises RuntimeError for invalid JSON."""
        bad_file = temp_dir / "bad.json"
        bad_file.write_text("not valid json")

        with pytest.raises(RuntimeError) as exc_info:
            RepoConfig.load(bad_file)

        assert "Failed to load config" in str(exc_info.value)

    def test_default_config_values(self) -> None:
        """Test that RepoConfig has sensible defaults."""
        config = RepoConfig()

        assert config.version == "1.0"
        assert config.user_name == ""
        assert config.user_email == ""
        assert config.remote is None
        assert config.project_name == ""
        assert config.auto_visualize is False
