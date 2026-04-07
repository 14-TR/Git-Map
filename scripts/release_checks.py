from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]

ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"
CORE_PYPROJECT = REPO_ROOT / "packages/gitmap_core/pyproject.toml"
CLI_PYPROJECT = REPO_ROOT / "apps/cli/gitmap/pyproject.toml"
CORE_INIT = REPO_ROOT / "packages/gitmap_core/__init__.py"
CLI_INIT = REPO_ROOT / "apps/cli/gitmap/__init__.py"
CLI_MAIN = REPO_ROOT / "apps/cli/gitmap/main.py"
PUBLISH_WORKFLOW = REPO_ROOT / ".github/workflows/publish.yml"


def _load_pyproject(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _extract_version(path: Path, pattern: str) -> str:
    text = path.read_text()
    match = re.search(pattern, text)
    if not match:
        raise AssertionError(f"Could not find version in {path}")
    return match.group(1)


def collect_release_state() -> dict[str, str | list[str]]:
    root_project = _load_pyproject(ROOT_PYPROJECT)["project"]
    core_project = _load_pyproject(CORE_PYPROJECT)["project"]
    cli_project = _load_pyproject(CLI_PYPROJECT)["project"]

    root_version = root_project["version"]
    core_version = core_project["version"]
    cli_version = cli_project["version"]
    core_init_version = _extract_version(CORE_INIT, r'__version__\s*=\s*"([^"]+)"')
    cli_init_version = _extract_version(CLI_INIT, r'__version__\s*=\s*"([^"]+)"')
    cli_main_version = _extract_version(CLI_MAIN, r'click\.version_option\(version="([^"]+)"')

    return {
        "root_version": root_version,
        "core_version": core_version,
        "cli_version": cli_version,
        "core_init_version": core_init_version,
        "cli_init_version": cli_init_version,
        "cli_main_version": cli_main_version,
        "root_dependencies": list(root_project.get("dependencies", [])),
        "core_dependencies": list(core_project.get("dependencies", [])),
        "cli_dependencies": list(cli_project.get("dependencies", [])),
        "root_urls": sorted(root_project.get("urls", {}).keys()),
        "core_urls": sorted(core_project.get("urls", {}).keys()),
        "cli_urls": sorted(cli_project.get("urls", {}).keys()),
    }


def validate_release_state() -> None:
    state = collect_release_state()
    versions = {
        state["root_version"],
        state["core_version"],
        state["cli_version"],
        state["core_init_version"],
        state["cli_init_version"],
        state["cli_main_version"],
    }
    assert len(versions) == 1, f"Release versions are out of sync: {state}"

    version = state["root_version"]
    assert f"gitmap-core>={version}" in state["root_dependencies"], state["root_dependencies"]
    assert f"gitmap-cli>={version}" in state["root_dependencies"], state["root_dependencies"]
    assert f"gitmap-core>={version}" in state["cli_dependencies"], state["cli_dependencies"]

    for pyproject in (ROOT_PYPROJECT, CORE_PYPROJECT, CLI_PYPROJECT):
        project = _load_pyproject(pyproject)["project"]
        assert project.get("readme") == "README.md", f"{pyproject} should publish README.md"
        assert project.get("license", {}).get("text") == "MIT", f"{pyproject} should declare MIT license"
        urls = project.get("urls", {})
        for required_url in ("Homepage", "Repository", "Bug Tracker"):
            assert required_url in urls, f"{pyproject} missing project.urls.{required_url}"

    workflow_text = PUBLISH_WORKFLOW.read_text()
    for tag_pattern in ('- "core-v*"', '- "cli-v*"', '- "v*"'):
        assert tag_pattern in workflow_text, f"Missing publish tag pattern: {tag_pattern}"
    for package_name in ("gitmap-core", "gitmap-cli", "gitmap"):
        assert f"https://pypi.org/p/{package_name}" in workflow_text, f"Missing PyPI environment URL for {package_name}"


if __name__ == "__main__":
    validate_release_state()
    state = collect_release_state()
    print(f"Release metadata OK for GitMap v{state['root_version']}")
