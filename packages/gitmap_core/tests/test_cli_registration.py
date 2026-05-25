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
import os
import re
import subprocess
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

    def test_help_shows_getting_started_footer(self, runner: CliRunner) -> None:
        """Top-level help should guide new users toward the main workflow."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Getting started:" in result.output
        assert "gitmap init" in result.output
        assert "gitmap clone <item-id> --url <portal-url>" in result.output
        assert "gitmap completions" in result.output

        footer = result.output.split("Getting started:", maxsplit=1)[1]
        expected_new_repo = 'New repository: gitmap init -> gitmap status -> gitmap commit -m "Initial snapshot"'
        assert expected_new_repo in footer
        assert "Existing web map: gitmap clone <item-id> --url <portal-url>" in footer
        assert "Need shell completions? Run: gitmap completions" in footer
        assert 'snapshot" Need shell completions?' not in footer

    def test_help_uses_gitmap_prog_name(self, runner: CliRunner) -> None:
        """Help output should show the installed command name, not the internal function name."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage: gitmap [OPTIONS] COMMAND [ARGS]..." in result.output
        assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." not in result.output

    def test_direct_script_help_uses_gitmap_prog_name(self) -> None:
        """Running the source script directly should still present the public gitmap command name."""
        repo_root = Path(__file__).resolve().parents[3]
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(repo_root / "packages"),
                    str(repo_root / "apps" / "cli" / "gitmap"),
                ]
            ),
        }

        result = subprocess.run(
            [sys.executable, str(repo_root / "apps" / "cli" / "gitmap" / "main.py"), "--help"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        assert result.returncode == 0
        assert "Usage: gitmap [OPTIONS] COMMAND [ARGS]..." in result.stdout
        assert "Usage: main.py [OPTIONS] COMMAND [ARGS]..." not in result.stdout

    def test_direct_script_unknown_command_points_to_gitmap_help(self) -> None:
        """Source-script errors should point users at gitmap help, not main.py help."""
        repo_root = Path(__file__).resolve().parents[3]
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(repo_root / "packages"),
                    str(repo_root / "apps" / "cli" / "gitmap"),
                ]
            ),
        }

        result = subprocess.run(
            [sys.executable, str(repo_root / "apps" / "cli" / "gitmap" / "main.py"), "mergefrom"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        assert result.returncode != 0
        combined_output = result.stdout + result.stderr
        assert "Try 'gitmap --help' for help." in combined_output
        assert "Run 'gitmap --help' to see the full command list." in combined_output
        assert "Try 'main.py --help' for help." not in combined_output

    def test_documented_diff_options_exist_in_cli_help(self, runner: CliRunner) -> None:
        """Documented gitmap diff examples should not mention stale options."""
        repo_root = Path(__file__).resolve().parents[3]
        diff_help = runner.invoke(cli, ["diff", "--help"])
        assert diff_help.exit_code == 0, f"diff --help failed:\n{diff_help.output}"

        documented_options: set[str] = set()
        for doc_path in (repo_root / "docs").rglob("*.md"):
            for line in doc_path.read_text(encoding="utf-8").splitlines():
                if not line.strip().startswith("gitmap diff"):
                    continue
                documented_options.update(re.findall(r"(?<!\\w)--[a-z][a-z-]*", line))

        missing = sorted(option for option in documented_options if option not in diff_help.output)
        assert not missing, f"Documented gitmap diff options missing from CLI help: {missing}"

    @pytest.mark.parametrize(
        ("command", "examples"),
        [
            (
                "clone",
                [
                    "gitmap clone abc123def456",
                    "gitmap clone abc123def456 --directory my-project",
                    "gitmap clone abc123def456 --url https://portal.example.com",
                ],
            ),
            (
                "pull",
                [
                    "gitmap pull",
                    "gitmap pull --branch main",
                    "gitmap pull --url https://portal.example.com",
                    'gitmap pull -r "Syncing production changes"',
                ],
            ),
            (
                "diff",
                [
                    "gitmap diff                               # Index vs HEAD",
                    "gitmap diff main                          # Index vs main",
                    "gitmap diff abc123                        # Index vs commit abc123",
                    "gitmap diff main feature/new-layer        # Branch vs branch",
                    "gitmap diff main feature --format visual  # Visual table view",
                    "gitmap diff main feature --format json    # Machine-readable JSON",
                    "gitmap diff abc123 def456                 # Commit vs commit",
                ],
            ),
        ],
    )
    def test_first_user_command_examples_render_on_separate_lines(
        self,
        runner: CliRunner,
        command: str,
        examples: list[str],
    ) -> None:
        """First-user command help examples should remain readable command blocks."""
        result = runner.invoke(cli, [command, "--help"], terminal_width=100)
        assert result.exit_code == 0, f"{command} --help failed:\n{result.output}"

        for example in examples:
            assert f"  {example}" in result.output

        examples_block = result.output.split("Examples:", maxsplit=1)[1].split("Options:", maxsplit=1)[0]
        assert " ".join(examples) not in examples_block

    @pytest.mark.parametrize(
        ("mistyped", "expected"),
        [
            ("statsu", "status"),
            ("stats", "stash"),
            ("chekout", "checkout"),
        ],
    )
    def test_unknown_command_suggests_similar_commands(self, runner: CliRunner, mistyped: str, expected: str) -> None:
        """Mistyped commands should include actionable suggestions."""
        result = runner.invoke(cli, [mistyped])
        assert result.exit_code != 0
        assert "No such command" in result.output
        assert "Try 'gitmap --help' for help." in result.output
        assert "Did you mean:" in result.output
        assert expected in result.output
        assert "gitmap --help" in result.output
        assert "Try 'cli --help' for help." not in result.output
