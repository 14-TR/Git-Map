from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
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


def test_public_validation_evidence_matches_collected_core_tests() -> None:
    """Public proof claims should stay in sync with pytest collection."""
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(REPO_ROOT / "packages"), str(REPO_ROOT)]),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "packages/gitmap_core/tests",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    match = re.search(r"(\d+) tests collected", result.stdout)
    assert match, result.stdout
    collected_count = int(match.group(1))

    public_claims = {
        "README.md": f"tests-{collected_count}%2B",
        "docs/contributing.md": f"{collected_count}+ tests",
        "docs/technical-paper.md": f"{collected_count} collected core tests",
        "marketing/blog-post.md": f"{collected_count}+ tests",
        "marketing/launch-strategy.md": f"{collected_count}+ tests",
        "marketing/reddit-rgis-post.md": f"{collected_count}+ tests",
    }
    for relative_path, expected_text in public_claims.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert expected_text in text, f"{relative_path} missing {expected_text!r}"


@pytest.mark.parametrize(
    ("ref_name", "expected_version"),
    [
        ("refs/tags/core-v1.2.3", "1.2.3"),
        ("cli-v1.2.3", "1.2.3"),
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
            "Root release tags are not published",
        ),
        (
            "refs/tags/v1.2.3",
            {"root_version": "1.2.3", "core_version": "1.2.3", "cli_version": "1.2.3"},
            "Use core-v<version> or cli-v<version>",
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
