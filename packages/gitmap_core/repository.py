"""Local repository management for GitMap.

Handles creation, validation, and manipulation of the .gitmap
directory structure including refs, objects, and configuration.

Execution Context:
    Library module - imported by CLI commands

Dependencies:
    - gitmap_core.models: Data models

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gitmap_core.models import Branch
from gitmap_core.models import Commit
from gitmap_core.models import RepoConfig


# ---- Constants ----------------------------------------------------------------------------------------------


GITMAP_DIR = ".gitmap"
CONFIG_FILE = "config.json"
HEAD_FILE = "HEAD"
INDEX_FILE = "index.json"
REFS_DIR = "refs"
HEADS_DIR = "heads"
REMOTES_DIR = "remotes"
TAGS_DIR = "tags"
OBJECTS_DIR = "objects"
COMMITS_DIR = "commits"
STASH_DIR = "stash"
CONTEXT_DB = "context.db"


# ---- Repository Class ---------------------------------------------------------------------------------------


class Repository:
    """Manages a local GitMap repository.

    Provides methods for creating, reading, and manipulating the
    .gitmap directory structure and its contents.

    Attributes:
        root: Root directory containing .gitmap folder.
        gitmap_dir: Path to .gitmap directory.
    """

    def __init__(
            self,
            root: Path | str,
    ) -> None:
        """Initialize repository at given root path.

        Args:
            root: Directory containing or to contain .gitmap folder.
        """
        self.root = Path(root).resolve()
        self.gitmap_dir = self.root / GITMAP_DIR

    # ---- Path Properties ------------------------------------------------------------------------------------

    @property
    def config_path(
            self,
    ) -> Path:
        """Path to config.json."""
        return self.gitmap_dir / CONFIG_FILE

    @property
    def head_path(
            self,
    ) -> Path:
        """Path to HEAD file."""
        return self.gitmap_dir / HEAD_FILE

    @property
    def index_path(
            self,
    ) -> Path:
        """Path to index.json staging area."""
        return self.gitmap_dir / INDEX_FILE

    @property
    def refs_dir(
            self,
    ) -> Path:
        """Path to refs directory."""
        return self.gitmap_dir / REFS_DIR

    @property
    def heads_dir(
            self,
    ) -> Path:
        """Path to refs/heads directory (local branches)."""
        return self.refs_dir / HEADS_DIR

    @property
    def remotes_dir(
            self,
    ) -> Path:
        """Path to refs/remotes directory."""
        return self.refs_dir / REMOTES_DIR

    @property
    def tags_dir(
            self,
    ) -> Path:
        """Path to refs/tags directory."""
        return self.refs_dir / TAGS_DIR

    @property
    def stash_dir(
            self,
    ) -> Path:
        """Path to stash directory."""
        return self.gitmap_dir / STASH_DIR

    @property
    def objects_dir(
            self,
    ) -> Path:
        """Path to objects directory."""
        return self.gitmap_dir / OBJECTS_DIR

    @property
    def commits_dir(
            self,
    ) -> Path:
        """Path to objects/commits directory."""
        return self.objects_dir / COMMITS_DIR

    @property
    def context_db_path(
            self,
    ) -> Path:
        """Path to context.db database."""
        return self.gitmap_dir / CONTEXT_DB

    def get_context_store(
            self,
    ) -> "ContextStore":
        """Get context store for this repository.

        Returns:
            ContextStore instance for this repository.

        Note:
            Caller is responsible for closing the store when done,
            or use it as a context manager.
        """
        from gitmap_core.context import ContextStore
        return ContextStore(self.context_db_path)

    def regenerate_context_graph(
            self,
            output_file: str = "context-graph.md",
            output_format: str = "mermaid",
            limit: int = 50,
    ) -> Path | None:
        """Regenerate the context graph visualization.

        Args:
            output_file: Output file name (relative to repo root).
            output_format: Output format ('mermaid', 'html', etc.).
            limit: Maximum events to include.

        Returns:
            Path to generated file, or None if generation failed.
        """
        try:
            from gitmap_core.visualize import visualize_context

            config = self.get_config()
            title = f"{config.project_name} Context Graph" if config.project_name else "Context Graph"

            with self.get_context_store() as store:
                viz = visualize_context(
                    store,
                    output_format=output_format,
                    limit=limit,
                    title=title,
                    direction="BT",  # Bottom-to-top: newest events at top
                    show_annotations=True,
                )

            output_path = self.root / output_file

            # Wrap Mermaid in markdown code block
            if output_format.startswith("mermaid") and output_path.suffix == ".md":
                content = f"# {title}\n\n```mermaid\n{viz}\n```\n"
            else:
                content = viz

            output_path.write_text(content, encoding="utf-8")
            return output_path

        except Exception:
            # Don't fail operations if visualization fails
            return None

    # ---- Repository State -----------------------------------------------------------------------------------

    def exists(
            self,
    ) -> bool:
        """Check if repository exists.

        Returns:
            True if .gitmap directory exists.
        """
        return self.gitmap_dir.is_dir()

    def is_valid(
            self,
    ) -> bool:
        """Validate repository structure.

        Returns:
            True if all required files/directories exist.
        """
        required = [
            self.config_path,
            self.head_path,
            self.heads_dir,
            self.commits_dir,
        ]
        return all(p.exists() for p in required)

    # ---- Initialization -------------------------------------------------------------------------------------

    def init(
            self,
            project_name: str = "",
            user_name: str = "",
            user_email: str = "",
    ) -> None:
        """Initialize a new GitMap repository.

        Creates .gitmap directory structure with initial config,
        empty index, and main branch.

        Args:
            project_name: Name of the project.
            user_name: Default commit author name.
            user_email: Default commit author email.

        Raises:
            RuntimeError: If repository already exists.
        """
        if self.exists():
            msg = f"GitMap repository already exists at {self.gitmap_dir}"
            raise RuntimeError(msg)

        try:
            # Create directory structure
            self.gitmap_dir.mkdir(parents=True)
            self.heads_dir.mkdir(parents=True)
            (self.remotes_dir / "origin").mkdir(parents=True)
            self.commits_dir.mkdir(parents=True)

            # Create config
            config = RepoConfig(
                project_name=project_name or self.root.name,
                user_name=user_name,
                user_email=user_email,
            )
            config.save(self.config_path)

            # Create HEAD pointing to main
            self._write_head("main")

            # Create empty index
            self._write_index({})

            # Create initial main branch file (empty until first commit)
            (self.heads_dir / "main").write_text("")

            # Initialize context database
            from gitmap_core.context import ContextStore
            with ContextStore(self.context_db_path):
                pass  # Schema created on init

        except Exception as init_error:
            msg = f"Failed to initialize repository: {init_error}"
            raise RuntimeError(msg) from init_error

    # ---- HEAD Operations ------------------------------------------------------------------------------------

    def get_current_branch(
            self,
    ) -> str | None:
        """Get name of current branch.

        Returns:
            Branch name or None if HEAD is detached.
        """
        if not self.head_path.exists():
            return None

        head_content = self.head_path.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content.replace("ref: refs/heads/", "")
        return None  # Detached HEAD

    def get_head_commit(
            self,
    ) -> str | None:
        """Get commit ID that HEAD points to.

        Returns:
            Commit ID or None if no commits.
        """
        branch = self.get_current_branch()
        if branch:
            return self.get_branch_commit(branch)

        # Detached HEAD - contains commit ID directly
        head_content = self.head_path.read_text().strip()
        if not head_content.startswith("ref:"):
            return head_content if head_content else None
        return None

    def _write_head(
            self,
            branch: str,
    ) -> None:
        """Write branch reference to HEAD.

        Args:
            branch: Branch name to reference.
        """
        self.head_path.write_text(f"ref: refs/heads/{branch}")

    def _write_head_detached(
            self,
            commit_id: str,
    ) -> None:
        """Write commit ID directly to HEAD (detached state).

        Args:
            commit_id: Commit ID to reference.
        """
        self.head_path.write_text(commit_id)

    # ---- Branch Operations ----------------------------------------------------------------------------------

    def list_branches(
            self,
    ) -> list[str]:
        """List all local branches.

        Returns:
            List of branch names.
        """
        if not self.heads_dir.exists():
            return []

        branches = []
        for path in self.heads_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.heads_dir)
                branches.append(str(rel_path))
        return sorted(branches)

    def get_branch_commit(
            self,
            branch: str,
    ) -> str | None:
        """Get commit ID for a branch.

        Args:
            branch: Branch name.

        Returns:
            Commit ID or None if branch has no commits.
        """
        branch_path = self.heads_dir / branch
        if not branch_path.exists():
            return None

        content = branch_path.read_text().strip()
        return content if content else None

    def create_branch(
            self,
            name: str,
            commit_id: str | None = None,
    ) -> Branch:
        """Create a new branch.

        Args:
            name: Branch name.
            commit_id: Commit to point to (defaults to HEAD).

        Returns:
            Created Branch object.

        Raises:
            RuntimeError: If branch already exists or commit not found.
        """
        branch_path = self.heads_dir / name

        if branch_path.exists():
            msg = f"Branch '{name}' already exists"
            raise RuntimeError(msg)

        # Use HEAD commit if not specified
        if commit_id is None:
            commit_id = self.get_head_commit()

        # Create parent directories for nested branch names
        branch_path.parent.mkdir(parents=True, exist_ok=True)
        branch_path.write_text(commit_id or "")

        return Branch(name=name, commit_id=commit_id or "")

    def update_branch(
            self,
            name: str,
            commit_id: str,
    ) -> None:
        """Update branch to point to new commit.

        Args:
            name: Branch name.
            commit_id: New commit ID.

        Raises:
            RuntimeError: If branch doesn't exist.
        """
        branch_path = self.heads_dir / name
        if not branch_path.exists():
            msg = f"Branch '{name}' does not exist"
            raise RuntimeError(msg)

        branch_path.write_text(commit_id)

    def delete_branch(
            self,
            name: str,
    ) -> None:
        """Delete a branch.

        Args:
            name: Branch name to delete.

        Raises:
            RuntimeError: If branch is current or doesn't exist.
        """
        if name == self.get_current_branch():
            msg = f"Cannot delete current branch '{name}'"
            raise RuntimeError(msg)

        branch_path = self.heads_dir / name
        if not branch_path.exists():
            msg = f"Branch '{name}' does not exist"
            raise RuntimeError(msg)

        branch_path.unlink()

    def checkout_branch(
            self,
            name: str,
    ) -> None:
        """Switch to a different branch.

        Args:
            name: Branch name to checkout.

        Raises:
            RuntimeError: If branch doesn't exist.
        """
        branch_path = self.heads_dir / name
        if not branch_path.exists():
            msg = f"Branch '{name}' does not exist"
            raise RuntimeError(msg)

        self._write_head(name)

        # Load branch's commit state to index
        commit_id = self.get_branch_commit(name)
        if commit_id:
            commit = self.get_commit(commit_id)
            if commit:
                self._write_index(commit.map_data)
        else:
            # Branch has no commits - clear index to empty state
            self._write_index({})

    # ---- Index Operations -----------------------------------------------------------------------------------

    def get_index(
            self,
    ) -> dict[str, Any]:
        """Get current staging area (index) contents.

        Returns:
            Map data from index.json.
        """
        if not self.index_path.exists():
            return {}

        try:
            return json.loads(self.index_path.read_text())
        except json.JSONDecodeError:
            return {}

    def _write_index(
            self,
            data: dict[str, Any],
    ) -> None:
        """Write data to index.json.

        Args:
            data: Map data to stage.
        """
        self.index_path.write_text(json.dumps(data, indent=2))

    def update_index(
            self,
            map_data: dict[str, Any],
    ) -> None:
        """Update staging area with new map data.

        Args:
            map_data: Web map JSON to stage.
        """
        self._write_index(map_data)

    # ---- Commit Operations ----------------------------------------------------------------------------------

    def get_commit(
            self,
            commit_id: str,
    ) -> Commit | None:
        """Load a commit by ID.

        Args:
            commit_id: Commit identifier.

        Returns:
            Commit object or None if not found.
        """
        commit_path = self.commits_dir / f"{commit_id}.json"
        if not commit_path.exists():
            return None

        return Commit.load(commit_path)

    def create_commit(
            self,
            message: str,
            author: str | None = None,
            rationale: str | None = None,
    ) -> Commit:
        """Create a new commit from current index.

        Args:
            message: Commit message.
            author: Author name (uses config if not provided).
            rationale: Optional rationale explaining why this change was made.

        Returns:
            Created Commit object.

        Raises:
            RuntimeError: If commit creation fails.
        """
        try:
            # Get author from config if not provided
            if not author:
                config = self.get_config()
                author = config.user_name or "Unknown"

            # Get current state
            map_data = self.get_index()
            parent = self.get_head_commit()

            # Generate commit ID from content
            commit_id = self._generate_commit_id(message, map_data, parent)

            # Create commit
            commit = Commit.create(
                commit_id=commit_id,
                message=message,
                author=author,
                parent=parent,
                map_data=map_data,
            )

            # Save commit
            commit.save(self.commits_dir)

            # Update current branch
            branch = self.get_current_branch()
            if branch:
                self.update_branch(branch, commit_id)

            # Record event in context store (non-blocking)
            try:
                with self.get_context_store() as store:
                    layers_count = len(map_data.get("operationalLayers", []))
                    store.record_event(
                        event_type="commit",
                        repo=str(self.root),
                        ref=commit_id,
                        actor=author,
                        payload={
                            "message": message,
                            "parent": parent,
                            "parent2": None,
                            "layers_count": layers_count,
                            "branch": branch,  # Track which branch the commit was made on
                        },
                        rationale=rationale,
                    )

                # Auto-regenerate context graph if enabled
                config = self.get_config()
                if config.auto_visualize:
                    self.regenerate_context_graph()

            except Exception:
                # Don't fail commit if context recording fails
                pass

            return commit

        except Exception as commit_error:
            msg = f"Failed to create commit: {commit_error}"
            raise RuntimeError(msg) from commit_error

    def _generate_commit_id(
            self,
            message: str,
            map_data: dict[str, Any],
            parent: str | None,
    ) -> str:
        """Generate unique commit ID.

        Args:
            message: Commit message.
            map_data: Map data to hash.
            parent: Parent commit ID.

        Returns:
            Short hash string for commit ID.
        """
        content = json.dumps({
            "message": message,
            "map_data": map_data,
            "parent": parent,
        }, sort_keys=True)

        full_hash = hashlib.sha256(content.encode()).hexdigest()
        return full_hash[:12]

    def get_commit_history(
            self,
            start_commit: str | None = None,
            limit: int | None = None,
    ) -> list[Commit]:
        """Get commit history starting from a commit.

        Args:
            start_commit: Starting commit ID (defaults to HEAD).
            limit: Maximum number of commits to return.

        Returns:
            List of commits in reverse chronological order.
        """
        commits = []
        current_id = start_commit or self.get_head_commit()

        while current_id:
            if limit and len(commits) >= limit:
                break

            commit = self.get_commit(current_id)
            if not commit:
                break

            commits.append(commit)
            current_id = commit.parent

        return commits

    # ---- Config Operations ----------------------------------------------------------------------------------

    def get_config(
            self,
    ) -> RepoConfig:
        """Load repository configuration.

        Returns:
            RepoConfig object.

        Raises:
            RuntimeError: If config cannot be loaded.
        """
        if not self.config_path.exists():
            msg = f"Config file not found at {self.config_path}"
            raise RuntimeError(msg)

        return RepoConfig.load(self.config_path)

    def update_config(
            self,
            config: RepoConfig,
    ) -> None:
        """Save updated configuration.

        Args:
            config: RepoConfig to save.
        """
        config.save(self.config_path)

    # ---- Status Operations ----------------------------------------------------------------------------------

    def has_uncommitted_changes(
            self,
    ) -> bool:
        """Check if index differs from HEAD commit.

        Returns:
            True if there are uncommitted changes.
        """
        head_commit_id = self.get_head_commit()
        if not head_commit_id:
            # No commits yet - check if index has data
            index = self.get_index()
            return bool(index)

        commit = self.get_commit(head_commit_id)
        if not commit:
            return True

        index = self.get_index()
        return index != commit.map_data

    # ---- Revert Operations ----------------------------------------------------------------------------------

    def revert(
            self,
            commit_id: str,
            rationale: str | None = None,
    ) -> Commit:
        """Revert a specific commit by creating an inverse commit.

        Creates a new commit that undoes the changes introduced by the
        specified commit. Does not remove history - adds a new commit
        that reverses the changes.

        Args:
            commit_id: ID of the commit to revert.
            rationale: Optional rationale explaining why the revert is being made.

        Returns:
            The new revert Commit object.

        Raises:
            RuntimeError: If commit not found or revert fails.
        """
        try:
            # Get the commit to revert
            commit_to_revert = self.get_commit(commit_id)
            if not commit_to_revert:
                msg = f"Commit '{commit_id}' not found"
                raise RuntimeError(msg)

            # Get the parent state (state before the commit)
            parent_data: dict[str, Any] = {}
            if commit_to_revert.parent:
                parent_commit = self.get_commit(commit_to_revert.parent)
                if parent_commit:
                    parent_data = parent_commit.map_data

            # Get current HEAD state
            current_data = self.get_index()

            # Compute the reverted state by applying inverse changes
            reverted_data = self._compute_revert(
                current_data=current_data,
                commit_data=commit_to_revert.map_data,
                parent_data=parent_data,
            )

            # Update index with reverted data
            self.update_index(reverted_data)

            # Create the revert commit
            config = self.get_config()
            author = config.user_name or "Unknown"
            message = f"Revert \"{commit_to_revert.message}\"\n\nThis reverts commit {commit_id[:8]}."

            revert_commit = self.create_commit(
                message=message,
                author=author,
                rationale=rationale,
            )

            # Record revert event in context store
            try:
                with self.get_context_store() as store:
                    event = store.record_event(
                        event_type="revert",
                        repo=str(self.root),
                        ref=revert_commit.id,
                        actor=author,
                        payload={
                            "reverted_commit": commit_id,
                            "reverted_message": commit_to_revert.message,
                            "revert_commit": revert_commit.id,
                            "branch": self.get_current_branch(),
                        },
                        rationale=rationale,
                    )
                    # Link revert to original commit
                    store.add_edge(
                        source_id=event.id,
                        target_id=commit_id,
                        relationship="reverts",
                        metadata={"commit_id": revert_commit.id},
                    )
            except Exception:
                # Don't fail revert if context recording fails
                pass

            return revert_commit

        except Exception as revert_error:
            if isinstance(revert_error, RuntimeError):
                raise
            msg = f"Failed to revert commit: {revert_error}"
            raise RuntimeError(msg) from revert_error

    def _compute_revert(
            self,
            current_data: dict[str, Any],
            commit_data: dict[str, Any],
            parent_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute the reverted state by applying inverse changes.

        For each change introduced by the commit (comparing commit_data to parent_data),
        apply the inverse change to the current_data.

        Args:
            current_data: Current HEAD state.
            commit_data: State at the commit to revert.
            parent_data: State before the commit to revert.

        Returns:
            New state with the commit's changes reverted.
        """
        reverted = json.loads(json.dumps(current_data))  # Deep copy

        # Handle operationalLayers
        reverted["operationalLayers"] = self._revert_layers(
            current_layers=current_data.get("operationalLayers", []),
            commit_layers=commit_data.get("operationalLayers", []),
            parent_layers=parent_data.get("operationalLayers", []),
        )

        # Handle tables
        reverted["tables"] = self._revert_layers(
            current_layers=current_data.get("tables", []),
            commit_layers=commit_data.get("tables", []),
            parent_layers=parent_data.get("tables", []),
        )

        # Handle baseMap (simpler - just restore if changed)
        if commit_data.get("baseMap") != parent_data.get("baseMap"):
            # Commit changed baseMap, revert to parent's baseMap
            if "baseMap" in parent_data:
                reverted["baseMap"] = parent_data["baseMap"]
            elif "baseMap" in reverted:
                del reverted["baseMap"]

        return reverted

    def _revert_layers(
            self,
            current_layers: list[dict[str, Any]],
            commit_layers: list[dict[str, Any]],
            parent_layers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Revert layer changes from a commit.

        Args:
            current_layers: Current layers in HEAD.
            commit_layers: Layers at the commit to revert.
            parent_layers: Layers before the commit to revert.

        Returns:
            Layers with the commit's changes reverted.
        """
        # Build ID maps for efficient lookup
        current_by_id = {l.get("id"): l for l in current_layers if l.get("id")}
        commit_by_id = {l.get("id"): l for l in commit_layers if l.get("id")}
        parent_by_id = {l.get("id"): l for l in parent_layers if l.get("id")}

        result = []

        # Process current layers
        for layer in current_layers:
            layer_id = layer.get("id")
            if not layer_id:
                result.append(layer)
                continue

            # Was this layer added by the commit? (in commit but not in parent)
            if layer_id in commit_by_id and layer_id not in parent_by_id:
                # Skip it - reverting the addition
                continue

            # Was this layer modified by the commit?
            if layer_id in commit_by_id and layer_id in parent_by_id:
                if commit_by_id[layer_id] != parent_by_id[layer_id]:
                    # Restore to parent version
                    result.append(parent_by_id[layer_id])
                    continue

            # No changes from this commit, keep as is
            result.append(layer)

        # Add back any layers that were removed by the commit
        for layer_id, layer in parent_by_id.items():
            if layer_id not in commit_by_id and layer_id not in current_by_id:
                # Layer was removed by the commit, add it back
                result.append(layer)

        return result

    # ---- Tag Operations -------------------------------------------------------------------------------------

    def list_tags(
            self,
    ) -> list[str]:
        """List all tags in the repository.

        Returns:
            List of tag names sorted alphabetically.
        """
        if not self.tags_dir.exists():
            return []

        tags = []
        for path in self.tags_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.tags_dir)
                tags.append(str(rel_path))
        return sorted(tags)

    def get_tag(
            self,
            name: str,
    ) -> str | None:
        """Get the commit ID a tag points to.

        Args:
            name: Tag name.

        Returns:
            Commit ID or None if tag doesn't exist.
        """
        tag_path = self.tags_dir / name
        if not tag_path.exists():
            return None

        return tag_path.read_text().strip()

    def create_tag(
            self,
            name: str,
            commit_id: str | None = None,
    ) -> str:
        """Create a new tag pointing to a commit.

        Args:
            name: Tag name (e.g., 'v1.0.0').
            commit_id: Commit to tag (defaults to HEAD).

        Returns:
            The commit ID the tag points to.

        Raises:
            RuntimeError: If tag already exists or commit not found.
        """
        # Validate tag name (no spaces, no special chars except - _ /)
        if not name or " " in name:
            msg = f"Invalid tag name: '{name}'"
            raise RuntimeError(msg)

        tag_path = self.tags_dir / name

        if tag_path.exists():
            msg = f"Tag '{name}' already exists"
            raise RuntimeError(msg)

        # Use HEAD commit if not specified
        if commit_id is None:
            commit_id = self.get_head_commit()

        if not commit_id:
            msg = "Cannot create tag: no commits in repository"
            raise RuntimeError(msg)

        # Verify commit exists
        if not self.get_commit(commit_id):
            msg = f"Commit '{commit_id}' not found"
            raise RuntimeError(msg)

        # Create tags directory if needed
        tag_path.parent.mkdir(parents=True, exist_ok=True)

        # Write tag
        tag_path.write_text(commit_id)

        # Record event in context store
        try:
            config = self.get_config()
            actor = config.user_name if config else None
            with self.get_context_store() as store:
                store.record_event(
                    event_type="tag",
                    repo=str(self.root),
                    ref=commit_id,
                    actor=actor,
                    payload={
                        "tag_name": name,
                        "commit_id": commit_id,
                        "action": "create",
                    },
                )
        except Exception:
            pass  # Don't fail tag creation if context recording fails

        return commit_id

    def delete_tag(
            self,
            name: str,
    ) -> None:
        """Delete a tag.

        Args:
            name: Tag name to delete.

        Raises:
            RuntimeError: If tag doesn't exist.
        """
        tag_path = self.tags_dir / name

        if not tag_path.exists():
            msg = f"Tag '{name}' does not exist"
            raise RuntimeError(msg)

        commit_id = tag_path.read_text().strip()
        tag_path.unlink()

        # Record event in context store
        try:
            config = self.get_config()
            actor = config.user_name if config else None
            with self.get_context_store() as store:
                store.record_event(
                    event_type="tag",
                    repo=str(self.root),
                    ref=commit_id,
                    actor=actor,
                    payload={
                        "tag_name": name,
                        "commit_id": commit_id,
                        "action": "delete",
                    },
                )
        except Exception:
            pass  # Don't fail tag deletion if context recording fails



    # ---- Cherry-Pick Operations ---------------------------------------------------------------------------------

    def cherry_pick(
            self,
            commit_id: str,
            rationale: str | None = None,
    ) -> Commit:
        """Apply changes from a specific commit to the current branch.

        Creates a new commit with the same changes as the source commit
        but with a new commit ID. The original commit is not modified.

        Args:
            commit_id: ID of the commit to cherry-pick.
            rationale: Optional rationale explaining why this cherry-pick is being made.

        Returns:
            The new Commit object.

        Raises:
            RuntimeError: If commit not found or cherry-pick fails.
        """
        try:
            # Get the commit to cherry-pick
            source_commit = self.get_commit(commit_id)
            if not source_commit:
                msg = f"Commit '{commit_id}' not found"
                raise RuntimeError(msg)

            # Get the parent of the source commit to compute the diff
            source_parent_data: dict[str, Any] = {}
            if source_commit.parent:
                source_parent = self.get_commit(source_commit.parent)
                if source_parent:
                    source_parent_data = source_parent.map_data

            # Get current HEAD state
            current_data = self.get_index()

            # Apply the changes from source commit to current state
            cherry_picked_data = self._apply_cherry_pick(
                current_data=current_data,
                commit_data=source_commit.map_data,
                parent_data=source_parent_data,
            )

            # Update index with cherry-picked data
            self.update_index(cherry_picked_data)

            # Create the new commit
            config = self.get_config()
            author = config.user_name or "Unknown"
            message = f"{source_commit.message}\n\n(cherry picked from commit {commit_id[:8]})"

            new_commit = self.create_commit(
                message=message,
                author=author,
                rationale=rationale,
            )

            # Record cherry-pick event in context store
            try:
                with self.get_context_store() as store:
                    event = store.record_event(
                        event_type="cherry-pick",
                        repo=str(self.root),
                        ref=new_commit.id,
                        actor=author,
                        payload={
                            "source_commit": commit_id,
                            "source_message": source_commit.message,
                            "new_commit": new_commit.id,
                            "branch": self.get_current_branch(),
                        },
                        rationale=rationale,
                    )
                    # Link cherry-pick to source commit
                    store.add_edge(
                        source_id=event.id,
                        target_id=commit_id,
                        relationship="cherry_picked_from",
                        metadata={"new_commit_id": new_commit.id},
                    )
            except Exception:
                # Don't fail cherry-pick if context recording fails
                pass

            return new_commit

        except Exception as cherry_pick_error:
            if isinstance(cherry_pick_error, RuntimeError):
                raise
            msg = f"Failed to cherry-pick commit: {cherry_pick_error}"
            raise RuntimeError(msg) from cherry_pick_error

    def _apply_cherry_pick(
            self,
            current_data: dict[str, Any],
            commit_data: dict[str, Any],
            parent_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply changes from a commit to the current state.

        Computes the diff between commit and its parent, then applies
        those changes to the current state.

        Args:
            current_data: Current HEAD state.
            commit_data: State at the commit to cherry-pick.
            parent_data: State before the commit to cherry-pick (its parent).

        Returns:
            New state with the commit's changes applied.
        """
        result = json.loads(json.dumps(current_data))  # Deep copy

        # Apply layer changes
        result["operationalLayers"] = self._apply_layer_changes(
            current_layers=current_data.get("operationalLayers", []),
            commit_layers=commit_data.get("operationalLayers", []),
            parent_layers=parent_data.get("operationalLayers", []),
        )

        # Apply table changes
        result["tables"] = self._apply_layer_changes(
            current_layers=current_data.get("tables", []),
            commit_layers=commit_data.get("tables", []),
            parent_layers=parent_data.get("tables", []),
        )

        # Apply baseMap changes (if changed in commit)
        if commit_data.get("baseMap") != parent_data.get("baseMap"):
            result["baseMap"] = commit_data.get("baseMap", {})

        return result

    def _apply_layer_changes(
            self,
            current_layers: list[dict[str, Any]],
            commit_layers: list[dict[str, Any]],
            parent_layers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply layer changes from a commit to current state.

        Args:
            current_layers: Current layers in HEAD.
            commit_layers: Layers at the commit to cherry-pick.
            parent_layers: Layers before the commit to cherry-pick.

        Returns:
            Layers with the commit's changes applied.
        """
        # Build ID maps for efficient lookup
        current_by_id = {l.get("id"): l for l in current_layers if l.get("id")}
        commit_by_id = {l.get("id"): l for l in commit_layers if l.get("id")}
        parent_by_id = {l.get("id"): l for l in parent_layers if l.get("id")}

        result = list(current_layers)  # Start with current layers

        # Find layers added by the commit (in commit but not in parent)
        for layer_id, layer in commit_by_id.items():
            if layer_id not in parent_by_id:
                # This layer was added by the commit
                if layer_id not in current_by_id:
                    # Add it to current if not already present
                    result.append(layer)

        # Find layers modified by the commit
        for layer_id, layer in commit_by_id.items():
            if layer_id in parent_by_id and commit_by_id[layer_id] != parent_by_id[layer_id]:
                # This layer was modified by the commit
                if layer_id in current_by_id:
                    # Update the layer in result
                    for i, l in enumerate(result):
                        if l.get("id") == layer_id:
                            result[i] = layer
                            break

        # Find layers removed by the commit (in parent but not in commit)
        for layer_id in parent_by_id:
            if layer_id not in commit_by_id:
                # This layer was removed by the commit
                result = [l for l in result if l.get("id") != layer_id]

        return result



# ---- Module Functions ---------------------------------------------------------------------------------------


def find_repository(
        start_path: Path | str | None = None,
) -> Repository | None:
    """Find GitMap repository in current or parent directories.

    Args:
        start_path: Directory to start searching from.

    Returns:
        Repository if found, None otherwise.
    """
    current = Path(start_path or Path.cwd()).resolve()

    while current != current.parent:
        repo = Repository(current)
        if repo.exists():
            return repo
        current = current.parent

    return None


def init_repository(
        path: Path | str | None = None,
        project_name: str = "",
        user_name: str = "",
        user_email: str = "",
) -> Repository:
    """Initialize a new GitMap repository.

    Args:
        path: Directory for new repository (defaults to cwd).
        project_name: Project name.
        user_name: Default author name.
        user_email: Default author email.

    Returns:
        Initialized Repository.
    """
    repo = Repository(path or Path.cwd())
    repo.init(
        project_name=project_name,
        user_name=user_name,
        user_email=user_email,
    )
    return repo


