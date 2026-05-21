"""Tests for the gitmap doctor command.

Verifies that the doctor command:
- Exits cleanly with --help
- Runs without crashing in an empty directory
- Reports Python version info
- Handles --fix flag

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - click.testing: CLI test runner
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

# Register gitmap_cli as a package alias for the CLI directory
_cli_dir = Path(__file__).parent.parent.parent.parent / "apps" / "cli" / "gitmap"
_cli_commands_dir = _cli_dir / "commands"

if "gitmap_cli" not in sys.modules:
    _pkg = types.ModuleType("gitmap_cli")
    _pkg.__path__ = [str(_cli_dir)]
    _pkg.__package__ = "gitmap_cli"
    sys.modules["gitmap_cli"] = _pkg

    _cmds = types.ModuleType("gitmap_cli.commands")
    _cmds.__path__ = [str(_cli_commands_dir)]
    _cmds.__package__ = "gitmap_cli.commands"
    sys.modules["gitmap_cli.commands"] = _cmds

if str(_cli_dir) not in sys.path:
    sys.path.insert(0, str(_cli_dir))

from main import cli  # noqa: E402


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestDoctorCommand:
    """Tests for 'gitmap doctor'."""

    def test_doctor_help(self, runner: CliRunner) -> None:
        """doctor --help should exit cleanly."""
        result = runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0, f"doctor --help failed:\n{result.output}"
        assert "environment" in result.output.lower() or "check" in result.output.lower()

    def test_doctor_runs_in_empty_dir(self, runner: CliRunner, tmp_path) -> None:
        """doctor should complete without unhandled exceptions in a non-repo dir."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor"])
        # Exit 0 (all ok) or 1 (issues found) — both are fine, just no crash
        assert result.exit_code in (0, 1), f"Unexpected exit code {result.exit_code}:\n{result.output}"

    def test_doctor_shows_python_version(self, runner: CliRunner, tmp_path) -> None:
        """doctor output should mention the Python version."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor"])
        assert "Python" in result.output, f"Expected 'Python' in doctor output:\n{result.output}"

    def test_doctor_shows_packages(self, runner: CliRunner, tmp_path) -> None:
        """doctor output should list package check results."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor"])
        # Should at least mention click and rich
        assert "click" in result.output
        assert "rich" in result.output

    def test_doctor_fix_flag(self, runner: CliRunner, tmp_path) -> None:
        """doctor --fix should run without error."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor", "--fix"])
        assert result.exit_code in (0, 1)

    def test_doctor_registered_in_help(self, runner: CliRunner) -> None:
        """doctor must appear in top-level --help output."""
        result = runner.invoke(cli, ["--help"])
        assert "doctor" in result.output, f"'doctor' not found in CLI help:\n{result.output}"


def test_first_user_docs_include_doctor_preflight() -> None:
    """First-user docs should keep the diagnostic preflight visible."""
    repo_root = Path(__file__).resolve().parents[3]
    docs_to_check = [
        repo_root / "README.md",
        repo_root / "docs/getting-started/quickstart.md",
        repo_root / "docs/validation/first-user-test.md",
    ]

    for doc_path in docs_to_check:
        text = doc_path.read_text(encoding="utf-8")
        assert "gitmap doctor" in text, f"{doc_path} should mention gitmap doctor"
        assert "gitmap doctor --portal" in text, f"{doc_path} should mention the Portal preflight"


def test_first_user_validation_diff_order_matches_staged_workflow() -> None:
    """The first-user flow should diff staged changes before branch comparison."""
    repo_root = Path(__file__).resolve().parents[3]
    doc_path = repo_root / "docs/validation/first-user-test.md"
    text = doc_path.read_text(encoding="utf-8")

    pull_index = text.index("gitmap pull")
    status_index = text.index("gitmap status")
    staged_diff_index = text.index("gitmap diff --format visual")
    commit_index = text.index('gitmap commit -m "Validate GitMap workflow"')
    branch_diff_index = text.index("gitmap diff main feature/validation-change --format visual")

    assert pull_index < status_index < staged_diff_index < commit_index < branch_diff_index
