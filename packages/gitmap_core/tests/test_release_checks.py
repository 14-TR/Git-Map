from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_CHECKS_PATH = REPO_ROOT / "scripts/release_checks.py"


def _load_release_checks_module():
    spec = importlib.util.spec_from_file_location("release_checks", RELEASE_CHECKS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_release_versions_and_dependencies_are_synced() -> None:
    release_checks = _load_release_checks_module()
    state = release_checks.collect_release_state()

    expected_version = state["root_version"]
    assert state["core_version"] == expected_version
    assert state["cli_version"] == expected_version
    assert state["core_init_version"] == expected_version
    assert state["cli_init_version"] == expected_version
    assert state["cli_main_version"] == expected_version
    assert f"gitmap-core>={expected_version}" in state["root_dependencies"]
    assert f"gitmap-cli>={expected_version}" in state["root_dependencies"]
    assert f"gitmap-core>={expected_version}" in state["cli_dependencies"]


def test_release_metadata_and_publish_workflow_are_valid() -> None:
    release_checks = _load_release_checks_module()
    release_checks.validate_release_state()


def test_release_metadata_requires_existing_readmes_and_typed_markers() -> None:
    release_checks = _load_release_checks_module()

    release_checks._validate_package_metadata(release_checks.ROOT_PYPROJECT)
    release_checks._validate_package_metadata(release_checks.CORE_PYPROJECT)
    release_checks._validate_package_metadata(release_checks.CLI_PYPROJECT)
