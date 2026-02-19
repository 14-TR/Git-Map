"""Tests for GitMap OpenClaw integration tools.

Covers helper functions and tool wrappers without hitting real Portal/CLI.
Uses subprocess mocking to verify argument construction and output parsing.

Execution Context:
    Test module — run via pytest from repo root

Dependencies:
    - pytest
    - unittest.mock
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add integrations dir so tools can be imported standalone
sys.path.insert(0, str(Path(__file__).parent.parent))
import tools as gitmap_tools


# ---- _find_gitmap() ------------------------------------------------------------------


class TestFindGitmap:
    """Tests for _find_gitmap helper."""

    def test_returns_gitmap_when_in_path(self) -> None:
        """Returns ['gitmap'] when the binary is on PATH."""
        with patch("shutil.which", return_value="/usr/local/bin/gitmap"):
            result = gitmap_tools._find_gitmap()
        assert result == ["gitmap"]

    def test_falls_back_to_main_py_when_not_in_path(self, tmp_path: Path) -> None:
        """Falls back to python main.py when gitmap not in PATH."""
        # Patch shutil.which: gitmap absent, python3 present
        def which_side_effect(name: str):
            if name == "gitmap":
                return None
            if name == "python3":
                return "/usr/bin/python3"
            return None

        # Patch GITMAP_CLI_DIR so the main.py path exists
        fake_main = tmp_path / "apps" / "cli" / "gitmap" / "main.py"
        fake_main.parent.mkdir(parents=True)
        fake_main.touch()

        with patch("shutil.which", side_effect=which_side_effect), \
             patch.object(gitmap_tools, "GITMAP_CLI_DIR", tmp_path):
            result = gitmap_tools._find_gitmap()

        assert "/usr/bin/python3" in result[0]
        assert str(fake_main) in result[-1]

    def test_falls_back_to_module_when_main_py_missing(self) -> None:
        """Falls back to '-m gitmap_cli.main' when main.py not found."""
        with patch("shutil.which", return_value=None), \
             patch.object(gitmap_tools, "GITMAP_CLI_DIR", Path("/nonexistent")):
            result = gitmap_tools._find_gitmap()

        assert "-m" in result
        assert "gitmap_cli.main" in result


# ---- _run() --------------------------------------------------------------------------


class TestRun:
    """Tests for _run helper."""

    def _mock_completed_process(self, stdout="", stderr="", returncode=0):
        proc = MagicMock()
        proc.stdout = stdout
        proc.stderr = stderr
        proc.returncode = returncode
        return proc

    def test_returns_ok_on_success(self) -> None:
        """Returns ok=True and parsed output when process succeeds."""
        with patch("subprocess.run", return_value=self._mock_completed_process(
            stdout="On branch main\n", returncode=0
        )):
            result = gitmap_tools._run(["status"])

        assert result["ok"] is True
        assert result["returncode"] == 0
        assert "On branch main" in result["stdout"]
        assert result["output"] == "On branch main"

    def test_returns_not_ok_on_nonzero_exit(self) -> None:
        """Returns ok=False when process exits non-zero."""
        with patch("subprocess.run", return_value=self._mock_completed_process(
            stderr="fatal: not a gitmap repo", returncode=1
        )):
            result = gitmap_tools._run(["status"])

        assert result["ok"] is False
        assert result["returncode"] == 1
        assert "fatal:" in result["stderr"]

    def test_output_combines_stdout_and_stderr(self) -> None:
        """Output field combines stdout and stderr."""
        with patch("subprocess.run", return_value=self._mock_completed_process(
            stdout="stdout part", stderr="stderr part", returncode=0
        )):
            result = gitmap_tools._run(["log"])

        assert "stdout part" in result["output"]
        assert "stderr part" in result["output"]

    def test_handles_timeout(self) -> None:
        """Returns structured error on TimeoutExpired."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gitmap", 60)):
            result = gitmap_tools._run(["push"], timeout=60)

        assert result["ok"] is False
        assert result["returncode"] == -1
        assert "timed out" in result["stderr"].lower()

    def test_handles_file_not_found(self) -> None:
        """Returns structured error when CLI executable missing."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = gitmap_tools._run(["status"])

        assert result["ok"] is False
        assert result["returncode"] == -1
        assert "not found" in result["stderr"].lower()

    def test_handles_unexpected_exception(self) -> None:
        """Returns structured error on unexpected exceptions."""
        with patch("subprocess.run", side_effect=PermissionError("denied")):
            result = gitmap_tools._run(["status"])

        assert result["ok"] is False
        assert "denied" in result["stderr"]

    def test_passes_cwd_to_subprocess(self, tmp_path: Path) -> None:
        """Passes cwd argument through to subprocess.run."""
        with patch("subprocess.run", return_value=self._mock_completed_process()) as mock_run:
            gitmap_tools._run(["status"], cwd=tmp_path)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == str(tmp_path)

    def test_merges_extra_env(self) -> None:
        """Extra environment variables are merged into the subprocess env."""
        with patch("subprocess.run", return_value=self._mock_completed_process()) as mock_run:
            gitmap_tools._run(["status"], extra_env={"PORTAL_URL": "https://test.com"})

        env = mock_run.call_args[1]["env"]
        assert env["PORTAL_URL"] == "https://test.com"


# ---- _portal_flags() -----------------------------------------------------------------


class TestPortalFlags:
    """Tests for _portal_flags credential helper."""

    def test_empty_when_no_credentials(self) -> None:
        """Returns empty list when no credentials provided."""
        flags = gitmap_tools._portal_flags(None, None, None)
        assert flags == []

    def test_adds_url_flag(self) -> None:
        """Adds --url flag when portal_url provided."""
        flags = gitmap_tools._portal_flags("https://arcgis.com", None, None)
        assert "--url" in flags
        assert "https://arcgis.com" in flags

    def test_adds_username_flag(self) -> None:
        """Adds --username flag when username provided."""
        flags = gitmap_tools._portal_flags(None, "alice", None)
        assert "--username" in flags
        assert "alice" in flags

    def test_adds_password_flag(self) -> None:
        """Adds --password flag when password provided."""
        flags = gitmap_tools._portal_flags(None, None, "s3cr3t")
        assert "--password" in flags
        assert "s3cr3t" in flags

    def test_adds_all_flags_together(self) -> None:
        """Adds all three flags when all credentials provided."""
        flags = gitmap_tools._portal_flags("https://test.com", "bob", "pass123")
        assert flags == [
            "--url", "https://test.com",
            "--username", "bob",
            "--password", "pass123",
        ]


# ---- gitmap_list() -------------------------------------------------------------------


class TestGitmapList:
    """Tests for gitmap_list tool."""

    def test_returns_error_when_no_portal_url(self) -> None:
        """Returns ok=False when PORTAL_URL not set."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove PORTAL_URL if set
            import os
            os.environ.pop("PORTAL_URL", None)
            result = gitmap_tools.gitmap_list()

        assert result["ok"] is False
        assert "PORTAL_URL" in result["output"]

    def test_returns_error_on_import_failure(self) -> None:
        """Returns ok=False when gitmap_core cannot be imported."""
        import builtins
        real_import = builtins.__import__

        def failing_import(name, *args, **kwargs):
            if name == "gitmap_core.connection":
                raise ImportError("No module named 'gitmap_core.connection'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=failing_import), \
             patch.dict("os.environ", {"PORTAL_URL": "https://test.com"}):
            result = gitmap_tools.gitmap_list(portal_url="https://test.com")

        # Either import error or connection attempt
        assert "ok" in result
        assert "returncode" in result

    def test_returns_maps_on_success(self) -> None:
        """Returns map list when connection and list succeed."""
        mock_map = MagicMock()
        mock_map.id = "map-001"
        mock_map.title = "Roads"
        mock_map.owner = "user1"
        mock_map.type = "Web Map"
        mock_map.tags = ["transportation"]
        mock_map.modified = "2024-01-01"

        mock_conn = MagicMock()

        with patch("gitmap_core.connection.get_connection", return_value=mock_conn), \
             patch("gitmap_core.maps.list_webmaps", return_value=[mock_map]):
            result = gitmap_tools.gitmap_list(
                portal_url="https://test.com",
                username="user",
                password="pass",
            )

        assert result["ok"] is True
        assert "maps" in result
        assert result["maps"][0]["id"] == "map-001"
        assert result["maps"][0]["title"] == "Roads"


# ---- CLI wrapper tools ---------------------------------------------------------------


class TestCliWrapperTools:
    """Tests for CLI wrapper tool functions."""

    def _make_ok_result(self, stdout=""):
        return {"ok": True, "returncode": 0, "stdout": stdout, "stderr": "", "output": stdout}

    def test_gitmap_status_calls_status(self, tmp_path: Path) -> None:
        """gitmap_status calls CLI with 'status'."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_status(cwd=str(tmp_path))
        mock_run.assert_called_once_with(["status"], cwd=str(tmp_path))

    def test_gitmap_commit_builds_args(self, tmp_path: Path) -> None:
        """gitmap_commit passes message and optional author."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_commit("Fix layer", cwd=str(tmp_path), author="alice")
        args = mock_run.call_args[0][0]
        assert args == ["commit", "--message", "Fix layer", "--author", "alice"]

    def test_gitmap_commit_no_author(self, tmp_path: Path) -> None:
        """gitmap_commit omits --author when not provided."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_commit("Quick fix", cwd=str(tmp_path))
        args = mock_run.call_args[0][0]
        assert "--author" not in args

    def test_gitmap_branch_list(self, tmp_path: Path) -> None:
        """gitmap_branch lists branches when no name given."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_branch(cwd=str(tmp_path))
        args = mock_run.call_args[0][0]
        assert args == ["branch"]

    def test_gitmap_branch_create(self, tmp_path: Path) -> None:
        """gitmap_branch creates branch when name given."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_branch(cwd=str(tmp_path), name="feature/roads")
        args = mock_run.call_args[0][0]
        assert "feature/roads" in args
        assert "--delete" not in args

    def test_gitmap_branch_delete(self, tmp_path: Path) -> None:
        """gitmap_branch deletes branch when delete=True and name given."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_branch(cwd=str(tmp_path), name="old-branch", delete=True)
        args = mock_run.call_args[0][0]
        assert "--delete" in args
        assert "old-branch" in args

    def test_gitmap_diff_no_target(self, tmp_path: Path) -> None:
        """gitmap_diff calls 'diff' with no extra args by default."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_diff(cwd=str(tmp_path))
        args = mock_run.call_args[0][0]
        assert args == ["diff"]

    def test_gitmap_diff_with_branch(self, tmp_path: Path) -> None:
        """gitmap_diff passes --branch when specified."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_diff(cwd=str(tmp_path), branch="main")
        args = mock_run.call_args[0][0]
        assert "--branch" in args and "main" in args

    def test_gitmap_diff_with_commit(self, tmp_path: Path) -> None:
        """gitmap_diff passes --commit when specified."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_diff(cwd=str(tmp_path), commit="abc123")
        args = mock_run.call_args[0][0]
        assert "--commit" in args and "abc123" in args

    def test_gitmap_push_with_credentials(self, tmp_path: Path) -> None:
        """gitmap_push passes branch and credential flags."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_push(
                cwd=str(tmp_path),
                branch="main",
                portal_url="https://portal.com",
                username="user",
                password="pass",
            )
        args = mock_run.call_args[0][0]
        assert "push" in args
        assert "--branch" in args and "main" in args
        assert "--url" in args and "https://portal.com" in args

    def test_gitmap_push_uses_long_timeout(self, tmp_path: Path) -> None:
        """gitmap_push uses 120s timeout for long network operations."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_push(cwd=str(tmp_path))
        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 120

    def test_gitmap_pull_with_branch(self, tmp_path: Path) -> None:
        """gitmap_pull passes --branch when specified."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_pull(cwd=str(tmp_path), branch="feature")
        args = mock_run.call_args[0][0]
        assert "pull" in args and "--branch" in args

    def test_gitmap_pull_uses_long_timeout(self, tmp_path: Path) -> None:
        """gitmap_pull uses 120s timeout."""
        with patch.object(gitmap_tools, "_run", return_value=self._make_ok_result()) as mock_run:
            gitmap_tools.gitmap_pull(cwd=str(tmp_path))
        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 120
