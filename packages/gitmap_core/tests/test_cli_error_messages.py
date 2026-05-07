from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

_repo_root = Path(__file__).resolve().parents[3]
_cli_dir = _repo_root / "apps" / "cli" / "gitmap"
_cli_commands_dir = _cli_dir / "commands"

if "gitmap_cli" not in sys.modules:
    _pkg = types.ModuleType("gitmap_cli")
    _pkg.__path__ = [str(_cli_dir)]
    _pkg.__package__ = "gitmap_cli"
    sys.modules["gitmap_cli"] = _pkg

if "gitmap_cli.commands" not in sys.modules:
    _cmds = types.ModuleType("gitmap_cli.commands")
    _cmds.__path__ = [str(_cli_commands_dir)]
    _cmds.__package__ = "gitmap_cli.commands"
    sys.modules["gitmap_cli.commands"] = _cmds

if str(_cli_dir) not in sys.path:
    sys.path.insert(0, str(_cli_dir))

import gitmap_cli.commands.branch as branch_module  # noqa: E402
import gitmap_cli.commands.commit as commit_module  # noqa: E402
import gitmap_cli.commands.diff as diff_module  # noqa: E402
import gitmap_cli.commands.status as status_module  # noqa: E402
import gitmap_cli.commands.tag as tag_module  # noqa: E402

branch = branch_module.branch
commit = commit_module.commit
diff = diff_module.diff
status = status_module.status
tag = tag_module.tag


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_branch_delete_without_name_surfaces_actionable_click_error(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    repo = Mock()
    repo.get_current_branch.return_value = "main"
    monkeypatch.setattr(branch_module, "find_repository", lambda: repo)

    result = runner.invoke(branch, ["--delete"])

    assert result.exit_code != 0
    assert "Branch name required." in result.output
    assert "Usage: gitmap branch <name>" in result.output
    assert "Branch operation failed:" not in result.output


def test_tag_without_name_surfaces_usage_instead_of_generic_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
) -> None:
    repo = Mock()
    monkeypatch.setattr(tag_module, "find_repository", lambda: repo)

    result = runner.invoke(tag, [])

    assert result.exit_code != 0
    assert "Usage: gitmap tag <name> [commit] or gitmap tag --list" in result.output
    assert "Tag operation failed:" not in result.output


def test_status_outside_repository_surfaces_actionable_click_error(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
) -> None:
    monkeypatch.setattr(status_module, "find_repository", lambda: None)

    result = runner.invoke(status, [])

    assert result.exit_code != 0
    assert "Not a GitMap repository. Run 'gitmap init' to create one." in result.output
    assert "Failed to get status:" not in result.output


def test_commit_outside_repository_surfaces_actionable_click_error(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
) -> None:
    monkeypatch.setattr(commit_module, "find_repository", lambda: None)

    result = runner.invoke(commit, ["-m", "test commit"])

    assert result.exit_code != 0
    assert "Not a GitMap repository. Run 'gitmap init' to create one." in result.output
    assert "Commit failed:" not in result.output


def test_diff_missing_ref_surfaces_actionable_click_error(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
) -> None:
    repo = Mock()
    repo.get_index.return_value = {"operationalLayers": []}
    repo.list_branches.return_value = []
    repo.get_commit.return_value = None
    monkeypatch.setattr(diff_module, "find_repository", lambda: repo)

    result = runner.invoke(diff, ["missing-branch"])

    assert result.exit_code != 0
    assert "Branch or commit not found: 'missing-branch'" in result.output
    assert "Diff failed:" not in result.output
