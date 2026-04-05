from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from click.testing import CliRunner


def _pyproject_version(pyproject_path: Path) -> str:
    version_line = next(
        line for line in pyproject_path.read_text().splitlines() if line.startswith("version = ")
    )
    return version_line.split('"')[1]


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_core_package_version_matches_pyproject() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root / "packages"))

    import gitmap_core

    pyproject_version = _pyproject_version(repo_root / "packages/gitmap_core/pyproject.toml")
    assert gitmap_core.__version__ == pyproject_version


def test_cli_package_version_matches_pyproject() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    cli_module = _load_module("gitmap_cli", repo_root / "apps/cli/gitmap/__init__.py")

    pyproject_version = _pyproject_version(repo_root / "apps/cli/gitmap/pyproject.toml")
    assert cli_module.__version__ == pyproject_version


def test_cli_version_command_reports_pyproject_version() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root / "apps/cli/gitmap"))
    sys.path.insert(0, str(repo_root / "packages"))

    from main import cli

    expected_version = _pyproject_version(repo_root / "apps/cli/gitmap/pyproject.toml")
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert expected_version in result.output
