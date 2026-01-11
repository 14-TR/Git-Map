"""Shared utilities for GitMap MCP tools.

Execution Context:
    MCP tool module - imported by other tool modules

Dependencies:
    - gitmap_core: Repository finding

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gitmap_core.repository import Repository


def get_workspace_directory() -> Path:
    """Get the workspace directory path.
    
    Tries multiple methods to detect the workspace:
    1. WORKSPACE_DIR or CURSOR_WORKSPACE environment variable
    2. Find workspace root by looking for .env file
    3. Try common workspace paths (/app if it exists)
    4. Fall back to current working directory
    
    Returns:
        Path to workspace directory.
    """
    # Check environment variable first
    workspace_env = os.getenv("WORKSPACE_DIR") or os.getenv("CURSOR_WORKSPACE")
    if workspace_env:
        workspace_path = Path(workspace_env).resolve()
        if workspace_path.exists():
            return workspace_path
    
    # Try to find workspace root by looking for .env file
    # Start from the current file location and search up
    current = Path(__file__).resolve().parent
    
    # Search up to 5 levels to find workspace root with .env
    for _ in range(5):
        env_file = current / ".env"
        if env_file.exists():
            return current.resolve()
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    
    # Try common workspace locations
    common_paths = [
        Path("/app"),  # Common workspace path in containers
        Path.cwd(),
    ]
    
    for workspace_path in common_paths:
        if workspace_path.exists():
            return workspace_path.resolve()
    
    # Fall back to current working directory
    return Path.cwd().resolve()


def resolve_path(path: str, base: Path | None = None) -> Path:
    """Resolve a path relative to workspace directory or provided base.
    
    Args:
        path: Path to resolve (can be absolute or relative).
        base: Base directory for relative paths (defaults to workspace).
    
    Returns:
        Resolved absolute Path.
    """
    path_obj = Path(path)
    
    # If already absolute, return as-is
    if path_obj.is_absolute():
        return path_obj.resolve()
    
    # Use provided base or workspace directory
    base_dir = base or get_workspace_directory()
    return (base_dir / path_obj).resolve()


def get_portal_url(url: str | None = None) -> str:
    """Get Portal URL from parameter or environment variable.
    
    Portal URL MUST be provided either as a parameter or via PORTAL_URL
    environment variable. No default fallback to arcgis.com is provided.
    
    Args:
        url: Optional Portal URL parameter (takes precedence if provided).
    
    Returns:
        Portal URL string.
    
    Raises:
        ValueError: If neither url parameter nor PORTAL_URL env var is set.
    """
    # If URL is explicitly provided, use it
    if url:
        return url
    
    # Otherwise, require PORTAL_URL environment variable
    portal_url = os.getenv("PORTAL_URL")
    if not portal_url:
        raise ValueError(
            "Portal URL is required. Set PORTAL_URL environment variable "
            "in your .env file or provide url parameter."
        )
    
    return portal_url


def find_repo_from_path(path: str | None = None) -> "Repository | None":
    """Find a GitMap repository from an optional path.
    
    If path is provided, looks for a repository at that path (directly or
    by searching upward). If path is not provided, searches from the
    workspace directory.
    
    This enables MCP tools to work with multiple repositories in a
    repositories directory structure.
    
    Args:
        path: Optional path to a repository directory. Can be:
              - Direct path to a repo root (containing .gitmap/)
              - Path inside a repo (will search upward)
              - None to search from workspace directory
    
    Returns:
        Repository if found, None otherwise.
    
    Examples:
        >>> find_repo_from_path("repositories/Master")
        <Repository at /app/repositories/Master>
        >>> find_repo_from_path()  # Uses workspace directory
        None  # If no .gitmap at workspace root
    """
    from gitmap_core.repository import Repository
    from gitmap_core.repository import find_repository
    
    if path:
        # Resolve the provided path
        repo_path = resolve_path(path)
        
        # First, check if the path directly contains a .gitmap folder
        repo = Repository(repo_path)
        if repo.exists() and repo.is_valid():
            return repo
        
        # Otherwise, search upward from that path
        return find_repository(start_path=repo_path)
    
    # No path provided - search from workspace directory
    workspace_dir = get_workspace_directory()
    return find_repository(start_path=workspace_dir)
