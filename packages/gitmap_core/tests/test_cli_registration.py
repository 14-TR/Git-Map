"""Tests for CLI command registration in main.py.

Verifies that all expected CLI commands are registered and appear
in the help output. Guards against commands being implemented but
accidentally omitted from main.py (regression: 'show' was missing).

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - click.testing: CLI test runner
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Ensure the CLI package is importable as 'gitmap_cli'
_cli_parent_dir = Path(__file__).parent.parent.parent.parent / "apps" / "cli"
if str(_cli_parent_dir) not in sys.path:
    sys.path.insert(0, str(_cli_parent_dir))

from gitmap_cli.main import cli  # noqa: E402


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    """Click test runner."""
    return CliRunner()


# ---- Registration Tests --------------------------------------------------------------------------------------


class TestCommandRegistration:
    """Verify all expected commands appear in the CLI help output."""

    EXPECTED_COMMANDS = [
        "auto-pull",
        "branch",
        "checkout",
        "cherry-pick",
        "clone",
        "commit",
        "config",
        "context",
        "daemon",
        "diff",
        "init",
        "list",
        "log",
        "lsm",
        "merge",
        "merge-from",
        "notify",
        "pull",
        "push",
        "revert",
        "setup-repos",
        "show",
        "stash",
        "status",
        "tag",
    ]

    def test_help_exits_cleanly(self, runner: CliRunner) -> None:
        """CLI --help should exit with code 0."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0, f"--help failed:\n{result.output}"

    def test_all_expected_commands_registered(self, runner: CliRunner) -> None:
        """Every command in EXPECTED_COMMANDS must appear in help output."""
        result = runner.invoke(cli, ["--help"])
        missing = [cmd for cmd in self.EXPECTED_COMMANDS if cmd not in result.output]
        assert not missing, (
            f"Commands missing from CLI registration: {missing}\n\n"
            f"Full help output:\n{result.output}"
        )

    def test_show_command_registered(self, runner: CliRunner) -> None:
        """Regression: 'show' command must be registered (was missing in v0.6.0)."""
        result = runner.invoke(cli, ["--help"])
        assert "show" in result.output, (
            "'show' command not found in CLI help. "
            "Ensure it is imported and registered in main.py."
        )

    def test_show_command_help(self, runner: CliRunner) -> None:
        """'gitmap show --help' should exit cleanly and describe the command."""
        result = runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0, f"show --help failed:\n{result.output}"
        assert "commit" in result.output.lower(), (
            "Expected 'commit' in show help text"
        )

    def test_version_flag(self, runner: CliRunner) -> None:
        """--version should report a version string."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "gitmap" in result.output.lower() or "version" in result.output.lower()
