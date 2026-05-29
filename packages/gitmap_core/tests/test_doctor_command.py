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

import gitmap_cli.commands.doctor as doctor_module  # noqa: E402
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

    def test_doctor_portal_fails_closed_on_anonymous_connection(
        self,
        monkeypatch: pytest.MonkeyPatch,
        runner: CliRunner,
        tmp_path,
    ) -> None:
        """doctor --portal should not treat anonymous access as verified credentials."""

        class AnonymousConnection:
            username = None

        monkeypatch.setattr(doctor_module, "_pkg_installed", lambda import_name: True)
        monkeypatch.setattr(
            doctor_module,
            "_portal_credential_state",
            lambda: {
                "username_var": None,
                "username": None,
                "password_var": None,
                "password": None,
                "has_username": False,
                "has_password": False,
            },
        )

        import gitmap_core.connection as connection_module

        monkeypatch.setattr(connection_module, "get_connection", lambda **_: AnonymousConnection())

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor", "--portal"])

        assert result.exit_code == 1, result.output
        assert "Connected anonymously" in result.output
        assert "credential verification not proven" in result.output

    def test_doctor_portal_flags_incomplete_credentials(
        self,
        monkeypatch: pytest.MonkeyPatch,
        runner: CliRunner,
        tmp_path,
    ) -> None:
        """doctor --portal should surface partial env credentials before first-user testing."""
        monkeypatch.setattr(doctor_module, "_pkg_installed", lambda import_name: True)
        monkeypatch.setattr(
            doctor_module,
            "_portal_credential_state",
            lambda: {
                "username_var": "ARCGIS_USERNAME",
                "username": "test-user",
                "password_var": None,
                "password": None,
                "has_username": True,
                "has_password": False,
            },
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor", "--portal"])

        assert result.exit_code == 1, result.output
        assert "Incomplete Portal credentials" in result.output
        assert "username/password variables are incomplete" in result.output

    def test_doctor_portal_accepts_named_user_connection(
        self,
        monkeypatch: pytest.MonkeyPatch,
        runner: CliRunner,
        tmp_path,
    ) -> None:
        """doctor --portal should pass when Portal connectivity resolves to a named user."""

        class NamedConnection:
            username = "portal-user"

        monkeypatch.setattr(doctor_module, "_pkg_installed", lambda import_name: True)
        monkeypatch.setattr(
            doctor_module,
            "_portal_credential_state",
            lambda: {
                "username_var": "ARCGIS_USERNAME",
                "username": "portal-user",
                "password_var": "ARCGIS_PASSWORD",
                "password": "secret",
                "has_username": True,
                "has_password": True,
            },
        )

        import gitmap_core.connection as connection_module

        monkeypatch.setattr(connection_module, "get_connection", lambda **_: NamedConnection())

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor", "--portal"])

        assert result.exit_code in (0, 1), result.output
        assert "Connected as" in result.output
