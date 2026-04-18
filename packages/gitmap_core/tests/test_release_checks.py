from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


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


def test_ci_package_validation_smoke_tests_dist_installs() -> None:
    release_checks = _load_release_checks_module()
    ci_workflow_text = release_checks.CI_WORKFLOW.read_text()

    for expected_command in (
        "python scripts/verify_dist_install.py core",
        "python scripts/verify_dist_install.py cli",
        "python scripts/verify_dist_install.py meta",
    ):
        assert expected_command in ci_workflow_text


def test_release_metadata_requires_existing_readmes_and_typed_markers() -> None:
    release_checks = _load_release_checks_module()

    release_checks._validate_package_metadata(release_checks.ROOT_PYPROJECT)
    release_checks._validate_package_metadata(release_checks.CORE_PYPROJECT)
    release_checks._validate_package_metadata(release_checks.CLI_PYPROJECT)


@pytest.mark.parametrize(
    ("ref_name", "expected_version"),
    [
        ("refs/tags/core-v1.2.3", "1.2.3"),
        ("cli-v1.2.3", "1.2.3"),
        ("v1.2.3", "1.2.3"),
    ],
)
def test_validate_release_tag_accepts_matching_tags(ref_name: str, expected_version: str) -> None:
    release_checks = _load_release_checks_module()

    release_checks.validate_release_tag(
        ref_name,
        state={
            "root_version": expected_version,
            "core_version": expected_version,
            "cli_version": expected_version,
        },
    )


@pytest.mark.parametrize(
    ("ref_name", "state", "message"),
    [
        (
            "refs/tags/core-v9.9.9",
            {"root_version": "1.2.3", "core_version": "1.2.3", "cli_version": "1.2.3"},
            "expected version 1.2.3",
        ),
        (
            "cli-v2.0.0",
            {"root_version": "1.2.3", "core_version": "1.2.3", "cli_version": "1.2.3"},
            "expected version 1.2.3",
        ),
        (
            "v0.0.1",
            {"root_version": "1.2.3", "core_version": "1.2.3", "cli_version": "1.2.3"},
            "expected version 1.2.3",
        ),
        (
            "refs/heads/main",
            {"root_version": "1.2.3", "core_version": "1.2.3", "cli_version": "1.2.3"},
            "Release tag must be one of",
        ),
    ],
)
def test_validate_release_tag_rejects_mismatched_or_invalid_tags(
    ref_name: str,
    state: dict[str, str],
    message: str,
) -> None:
    release_checks = _load_release_checks_module()

    with pytest.raises(AssertionError, match=message):
        release_checks.validate_release_tag(ref_name, state=state)
