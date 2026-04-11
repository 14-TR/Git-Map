from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"

PACKAGE_CHECKS = {
    "core": {
        "package_name": "gitmap-core",
        "required_prefixes": ["gitmap_core-"],
        "commands": [
            ["python", "-c", "import gitmap_core; print(gitmap_core.__version__)"],
        ],
    },
    "cli": {
        "package_name": "gitmap-cli",
        "required_prefixes": ["gitmap_core-", "gitmap_cli-"],
        "commands": [
            ["python", "-c", "import gitmap_cli; print(gitmap_cli.__version__)"],
            ["gitmap", "--version"],
        ],
    },
    "meta": {
        "package_name": "gitmap",
        "required_prefixes": ["gitmap_core-", "gitmap_cli-", "gitmap-"],
        "commands": [
            ["python", "-c", "import gitmap_core, gitmap_cli; print(gitmap_core.__version__, gitmap_cli.__version__)"],
            ["gitmap", "--version"],
        ],
    },
}


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def _pick_artifact(prefix: str) -> Path:
    matches = sorted(
        path for path in DIST_DIR.iterdir()
        if path.is_file() and path.name.startswith(prefix)
    )
    if not matches:
        raise FileNotFoundError(f"No dist artifacts found for prefix {prefix!r} in {DIST_DIR}")

    wheels = [path for path in matches if path.suffix == ".whl"]
    return wheels[0] if wheels else matches[0]


def verify(kind: str) -> None:
    artifacts = [_pick_artifact(prefix) for prefix in PACKAGE_CHECKS[kind]["required_prefixes"]]
    with tempfile.TemporaryDirectory(prefix=f"gitmap-{kind}-smoke-") as tmpdir:
        venv_dir = Path(tmpdir) / "venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)])

        bin_dir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
        python_bin = bin_dir / "python"
        pip_bin = bin_dir / "pip"
        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

        _run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"], env=env)
        _run([str(pip_bin), "install", *[str(path) for path in artifacts]], env=env)

        for command in PACKAGE_CHECKS[kind]["commands"]:
            _run(command, env=env)

    print(f"Verified installable dist artifacts for {PACKAGE_CHECKS[kind]['package_name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke-test built GitMap distributions in a clean virtualenv")
    parser.add_argument("kind", choices=sorted(PACKAGE_CHECKS), help="Distribution set to verify")
    args = parser.parse_args()
    verify(args.kind)
