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

# Ensure the CLI package is importable as 'gitmap_cli'
# The package dir is named 'gitmap' but the package name is 'gitmap_cli' (via pyproject.toml mapping)
# When not pip-installed, we register it manually as a module alias
import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

_cli_dir = Path(__file__).parent.parent.parent.parent / "apps" / "cli" / "gitmap"
_cli_commands_dir = _cli_dir / "commands"

if "gitmap_cli" not in sys.modules:
    # Register gitmap_cli as a package pointing to the gitmap directory
    _pkg = types.ModuleType("gitmap_cli")
    _pkg.__path__ = [str(_cli_dir)]
    _pkg.__package__ = "gitmap_cli"
    sys.modules["gitmap_cli"] = _pkg

    # Register gitmap_cli.commands subpackage
    _cmds = types.ModuleType("gitmap_cli.commands")
    _cmds.__path__ = [str(_cli_commands_dir)]
    _cmds.__package__ = "gitmap_cli.commands"
    sys.modules["gitmap_cli.commands"] = _cmds

if str(_cli_dir) not in sys.path:
    sys.path.insert(0, str(_cli_dir))

from main import cli  # noqa: E402

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
        "doctor",
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
        "completions",
    ]

    def test_help_exits_cleanly(self, runner: CliRunner) -> None:
        """CLI --help should exit with code 0."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0, f"--help failed:\n{result.output}"

    def test_all_expected_commands_registered(self, runner: CliRunner) -> None:
        """Every command in EXPECTED_COMMANDS must appear in help output."""
        result = runner.invoke(cli, ["--help"])
        missing = [cmd for cmd in self.EXPECTED_COMMANDS if cmd not in result.output]
        assert not missing, f"Commands missing from CLI registration: {missing}\n\nFull help output:\n{result.output}"

    def test_show_command_registered(self, runner: CliRunner) -> None:
        """Regression: 'show' command must be registered (was missing in v0.6.0)."""
        result = runner.invoke(cli, ["--help"])
        assert "show" in result.output, (
            "'show' command not found in CLI help. Ensure it is imported and registered in main.py."
        )

    def test_show_command_help(self, runner: CliRunner) -> None:
        """'gitmap show --help' should exit cleanly and describe the command."""
        result = runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0, f"show --help failed:\n{result.output}"
        assert "commit" in result.output.lower(), "Expected 'commit' in show help text"

    def test_completions_command_registered(self, runner: CliRunner) -> None:
        """'gitmap completions' must be registered and exit cleanly."""
        result = runner.invoke(cli, ["completions", "--help"])
        assert result.exit_code == 0, f"completions --help failed:\n{result.output}"
        assert "bash" in result.output.lower() or "shell" in result.output.lower()

    def test_version_flag(self, runner: CliRunner) -> None:
        """--version should report a version string."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "gitmap" in result.output.lower() or "version" in result.output.lower()
