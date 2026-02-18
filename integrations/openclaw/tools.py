"""
GitMap Tools — OpenClaw skill wrappers for the GitMap CLI.

Thin subprocess wrappers around the `gitmap` CLI. Each function builds
the appropriate CLI args and returns structured output.

Key Features:
    - Auto-detects gitmap CLI (PATH → direct Python fallback)
    - Passes Portal credentials via CLI flags or .env in repo dir
    - Returns dict with stdout, stderr, returncode, and parsed data

Dependencies:
    - gitmap CLI (pip install -e ~/Desktop/Git-Map/apps/cli/gitmap)
    - gitmap_core (pip install -e ~/Desktop/Git-Map/packages/gitmap_core)

Metadata:
    Author: OpenClaw
    Version: 1.0
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# ---- Constants -----------------------------------------------------------------------

GITMAP_CLI_DIR = Path.home() / "Desktop" / "Git-Map"
GITMAP_CORE_PKG = str(GITMAP_CLI_DIR / "packages" / "gitmap_core")
GITMAP_CLI_PKG = str(GITMAP_CLI_DIR / "apps" / "cli" / "gitmap")


# ---- Helpers -------------------------------------------------------------------------

def _find_gitmap() -> list[str]:
    """
    Locate the gitmap executable or fallback command.

    Returns:
        list[str]: Command prefix to run gitmap (e.g., ["gitmap"] or
                   ["python3", "-m", "gitmap_cli.main"]).
    """
    # Check if gitmap is in PATH
    if shutil.which("gitmap"):
        return ["gitmap"]

    # Fallback: run as Python module from the source directory
    python = shutil.which("python3") or shutil.which("python") or "python3"
    main_py = GITMAP_CLI_DIR / "apps" / "cli" / "gitmap" / "main.py"
    if main_py.exists():
        return [python, str(main_py)]

    # Last resort: try the module directly
    return [python, "-m", "gitmap_cli.main"]


def _run(
        args: list[str],
        cwd: Optional[str | Path] = None,
        extra_env: Optional[dict[str, str]] = None,
        timeout: int = 60,
) -> dict:
    """
    Run a gitmap CLI command and return structured output.

    Args:
        args: CLI arguments (e.g., ["status"] or ["commit", "-m", "msg"]).
        cwd: Working directory (GitMap repo path).
        extra_env: Extra environment variables to merge in.
        timeout: Seconds before subprocess is killed.

    Returns:
        dict with keys: ok, returncode, stdout, stderr, output (combined).
    """
    cmd_prefix = _find_gitmap()
    full_cmd = cmd_prefix + args

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    try:
        result = subprocess.run(
            full_cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "output": (result.stdout + result.stderr).strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "output": f"Command timed out after {timeout}s",
        }
    except FileNotFoundError as not_found_error:
        msg = (
            f"gitmap CLI not found. Run: pip install -e {GITMAP_CORE_PKG} "
            f"&& pip install -e {GITMAP_CLI_PKG}"
        )
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": msg,
            "output": msg,
        }
    except Exception as general_error:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Unexpected error: {general_error}",
            "output": f"Unexpected error: {general_error}",
        }


def _portal_flags(
        portal_url: Optional[str],
        username: Optional[str],
        password: Optional[str],
) -> list[str]:
    """
    Build Portal credential CLI flags.

    Args:
        portal_url: Portal or ArcGIS Online URL.
        username: Portal username.
        password: Portal password.

    Returns:
        list[str]: CLI flags to append (may be empty).
    """
    flags: list[str] = []
    if portal_url:
        flags += ["--url", portal_url]
    if username:
        flags += ["--username", username]
    if password:
        flags += ["--password", password]
    return flags


# ---- Tools ---------------------------------------------------------------------------

def gitmap_list(
        query: Optional[str] = None,
        owner: Optional[str] = None,
        tag: Optional[str] = None,
        max_results: int = 50,
        portal_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cwd: Optional[str] = None,
) -> dict:
    """
    List available web maps from Portal or ArcGIS Online.

    Uses the Python API directly for better performance and structured output.

    Args:
        query: Search query to filter maps (e.g., 'title:MyMap').
        owner: Filter by owner username.
        tag: Filter by tag.
        max_results: Maximum number of results to return.
        portal_url: Portal URL (defaults to PORTAL_URL env var).
        username: Portal username (or PORTAL_USER env var).
        password: Portal password (or PORTAL_PASSWORD env var).
        cwd: Working directory (optional; uses home if not set).

    Returns:
        dict: ok, output (raw CLI text), and any parsed map info.
    """
    import sys

    # Add Git-Map packages to path
    gitmap_dir = os.path.expanduser("~/Desktop/Git-Map")
    sys.path.insert(0, os.path.join(gitmap_dir, "packages"))
    sys.path.insert(0, os.path.join(gitmap_dir, "apps", "cli"))

    try:
        from gitmap_core.connection import get_connection
        from gitmap_core.maps import list_webmaps

        # Get credentials from args or environment
        portal_url = portal_url or os.environ.get("PORTAL_URL")
        username = username or os.environ.get("ARCGIS_USERNAME")
        password = password or os.environ.get("ARCGIS_PASSWORD")

        if not portal_url:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "PORTAL_URL is required",
                "output": "PORTAL_URL is required",
            }

        # Get connection and list webmaps
        conn = get_connection(portal_url, username, password)
        maps = list_webmaps(
            connection=conn,
            query=query,
            owner=owner,
            tag=tag,
            max_results=max_results,
        )

        # Format output
        map_list = []
        for m in maps:
            map_list.append({
                "id": getattr(m, "id", None),
                "title": getattr(m, "title", None),
                "owner": getattr(m, "owner", None),
                "type": getattr(m, "type", None),
                "tags": getattr(m, "tags", None),
                "modified": str(getattr(m, "modified", None)),
            })

        return {
            "ok": True,
            "returncode": 0,
            "stdout": str(map_list),
            "stderr": "",
            "output": str(map_list),
            "maps": map_list,
        }
    except ImportError as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Failed to import gitmap_core: {e}",
            "output": f"Failed to import gitmap_core: {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "output": str(e),
        }


def gitmap_status(
        cwd: str,
) -> dict:
    """
    Show the working tree status for a local GitMap repository.

    Args:
        cwd: Path to the GitMap repository directory.

    Returns:
        dict: ok, output (status text from CLI).
    """
    return _run(["status"], cwd=cwd)


def gitmap_commit(
        message: str,
        cwd: str,
        author: Optional[str] = None,
) -> dict:
    """
    Commit the current map state.

    Args:
        message: Commit message (required).
        cwd: Path to the GitMap repository directory.
        author: Override commit author (optional).

    Returns:
        dict: ok, output (CLI response).
    """
    args = ["commit", "--message", message]
    if author:
        args += ["--author", author]
    return _run(args, cwd=cwd)


def gitmap_branch(
        cwd: str,
        name: Optional[str] = None,
        delete: bool = False,
) -> dict:
    """
    List all branches or create/delete a branch.

    Args:
        cwd: Path to the GitMap repository directory.
        name: Branch name to create or delete (omit to list branches).
        delete: If True, delete the named branch.

    Returns:
        dict: ok, output (branch list or confirmation).
    """
    args = ["branch"]
    if delete and name:
        args += ["--delete", name]
    elif name:
        args.append(name)
    return _run(args, cwd=cwd)


def gitmap_diff(
        cwd: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
) -> dict:
    """
    Show changes between the working tree and a branch or commit.

    Args:
        cwd: Path to the GitMap repository directory.
        branch: Compare with this branch name.
        commit: Compare with this commit hash.

    Returns:
        dict: ok, output (diff text from CLI).
    """
    args = ["diff"]
    if branch:
        args += ["--branch", branch]
    if commit:
        args += ["--commit", commit]
    return _run(args, cwd=cwd)


def gitmap_push(
        cwd: str,
        branch: Optional[str] = None,
        portal_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
) -> dict:
    """
    Push committed changes to ArcGIS Portal.

    Args:
        cwd: Path to the GitMap repository directory.
        branch: Branch to push (defaults to current branch).
        portal_url: Portal URL override.
        username: Portal username override.
        password: Portal password override.

    Returns:
        dict: ok, output (push result from CLI).
    """
    args = ["push"]
    if branch:
        args += ["--branch", branch]
    args += _portal_flags(portal_url, username, password)
    return _run(args, cwd=cwd, timeout=120)


def gitmap_pull(
        cwd: str,
        branch: Optional[str] = None,
        portal_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
) -> dict:
    """
    Pull the latest map state from ArcGIS Portal.

    Args:
        cwd: Path to the GitMap repository directory.
        branch: Branch to pull (defaults to current branch).
        portal_url: Portal URL override.
        username: Portal username override.
        password: Portal password override.

    Returns:
        dict: ok, output (pull result from CLI).
    """
    args = ["pull"]
    if branch:
        args += ["--branch", branch]
    args += _portal_flags(portal_url, username, password)
    return _run(args, cwd=cwd, timeout=120)


def gitmap_log(
        cwd: str,
        branch: Optional[str] = None,
        limit: Optional[int] = None,
) -> dict:
    """
    View commit history for a GitMap repository.

    Uses the Python API directly for better performance and structured output.

    Args:
        cwd: Path to the GitMap repository directory.
        branch: Show log for this branch (defaults to current).
        limit: Maximum number of commits to show.

    Returns:
        dict: ok, output (commit log from CLI).
    """
    import sys

    # Add Git-Map packages to path
    gitmap_dir = os.path.expanduser("~/Desktop/Git-Map")
    sys.path.insert(0, os.path.join(gitmap_dir, "packages"))
    sys.path.insert(0, os.path.join(gitmap_dir, "apps", "cli"))

    try:
        from gitmap_core.repository import find_repository

        # Find the repository
        repo = find_repository(cwd)
        if not repo:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"No GitMap repository found at {cwd}",
                "output": f"No GitMap repository found at {cwd}",
            }

        # Get commit history
        commits = repo.get_commit_history(branch=branch, limit=limit or 50)

        # Format output
        commit_list = []
        for c in commits:
            commit_list.append({
                "id": getattr(c, "id", None),
                "message": getattr(c, "message", None),
                "author": getattr(c, "author", None),
                "timestamp": str(getattr(c, "timestamp", None)),
                "branch": getattr(c, "branch", None),
            })

        return {
            "ok": True,
            "returncode": 0,
            "stdout": str(commit_list),
            "stderr": "",
            "output": str(commit_list),
            "commits": commit_list,
        }
    except ImportError as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Failed to import gitmap_core: {e}",
            "output": f"Failed to import gitmap_core: {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "output": str(e),
        }
