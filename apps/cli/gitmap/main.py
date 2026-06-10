"""GitMap CLI entry point.

Orchestrator for the GitMap command-line interface. Registers all
command modules and provides the main entry point.

Execution Context:
    CLI application - run via `python main.py` or `gitmap` command

Dependencies:
    - click: CLI framework
    - gitmap_core: Core library

Metadata:
    Version: 0.7.0
    Author: GitMap Team
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_CLI_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CLI_DIR.parents[2]
_PACKAGES_DIR = _REPO_ROOT / "packages"

if str(_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_DIR))

# Support direct source execution (`python apps/cli/gitmap/main.py`) in CI
# before the CLI package itself is installed.
if "gitmap_cli" not in sys.modules:
    _pkg = types.ModuleType("gitmap_cli")
    _pkg.__path__ = [str(_CLI_DIR)]
    _pkg.__package__ = "gitmap_cli"
    sys.modules["gitmap_cli"] = _pkg

import click  # noqa: E402
from gitmap_cli.help_formatter import GroupedHelpGroup  # noqa: E402

COMMAND_SPECS: dict[str, dict[str, str]] = {
    "init": {
        "module": "gitmap_cli.commands.init",
        "attr": "init",
        "short_help": "Initialize a new GitMap repository.",
    },
    "clone": {
        "module": "gitmap_cli.commands.clone",
        "attr": "clone",
        "short_help": "Clone a web map from ArcGIS Portal.",
    },
    "cherry-pick": {
        "module": "gitmap_cli.commands.cherry_pick",
        "attr": "cherry_pick",
        "short_help": "Apply a specific commit onto the current branch.",
    },
    "status": {
        "module": "gitmap_cli.commands.status",
        "attr": "status",
        "short_help": "Show working tree and branch status.",
    },
    "branch": {
        "module": "gitmap_cli.commands.branch",
        "attr": "branch",
        "short_help": "Create or list branches.",
    },
    "checkout": {
        "module": "gitmap_cli.commands.checkout",
        "attr": "checkout",
        "short_help": "Switch branches or restore commits.",
    },
    "commit": {
        "module": "gitmap_cli.commands.commit",
        "attr": "commit",
        "short_help": "Commit the staged map state.",
    },
    "config": {
        "module": "gitmap_cli.commands.config",
        "attr": "config",
        "short_help": "View or set GitMap configuration.",
    },
    "context": {
        "module": "gitmap_cli.commands.context",
        "attr": "context",
        "short_help": "Inspect or manage map context annotations.",
    },
    "daemon": {
        "module": "gitmap_cli.commands.daemon",
        "attr": "daemon",
        "short_help": "Run the GitMap automation daemon.",
    },
    "diff": {
        "module": "gitmap_cli.commands.diff",
        "attr": "diff",
        "short_help": "Show ArcGIS-aware diffs between map states.",
    },
    "doctor": {
        "module": "gitmap_cli.commands.doctor",
        "attr": "doctor",
        "short_help": "Check environment, config, and auth readiness.",
    },
    "lsm": {
        "path": str(_CLI_DIR / "commands" / "layer-settings-merge.py"),
        "module_name": "gitmap_cli.commands.layer_settings_merge",
        "attr": "layer_settings_merge",
        "short_help": "Merge layer settings between web maps.",
    },
    "list": {
        "module": "gitmap_cli.commands.list",
        "attr": "list_maps",
        "short_help": "List available web maps from Portal.",
    },
    "log": {
        "module": "gitmap_cli.commands.log",
        "attr": "log",
        "short_help": "Show commit history.",
    },
    "show": {
        "module": "gitmap_cli.commands.show",
        "attr": "show",
        "short_help": "Display a commit or map snapshot.",
    },
    "completions": {
        "module": "gitmap_cli.commands.completions",
        "attr": "completions",
        "short_help": "Generate shell completion scripts.",
    },
    "merge": {
        "module": "gitmap_cli.commands.merge",
        "attr": "merge",
        "short_help": "Merge another branch into the current branch.",
    },
    "merge-from": {
        "path": str(_CLI_DIR / "commands" / "merge-from.py"),
        "module_name": "gitmap_cli.commands.merge_from",
        "attr": "merge_from",
        "short_help": "Merge commits from one ref into another.",
    },
    "notify": {
        "module": "gitmap_cli.commands.notify",
        "attr": "notify",
        "short_help": "Send Portal notifications for a map item.",
    },
    "push": {
        "module": "gitmap_cli.commands.push",
        "attr": "push",
        "short_help": "Push the current branch state to Portal.",
    },
    "pull": {
        "module": "gitmap_cli.commands.pull",
        "attr": "pull",
        "short_help": "Pull the latest Portal state into the index.",
    },
    "revert": {
        "module": "gitmap_cli.commands.revert",
        "attr": "revert",
        "short_help": "Revert a commit by creating an inverse commit.",
    },
    "stash": {
        "module": "gitmap_cli.commands.stash",
        "attr": "stash",
        "short_help": "Temporarily stash working changes.",
    },
    "tag": {
        "module": "gitmap_cli.commands.tag",
        "attr": "tag",
        "short_help": "Create or list tags.",
    },
    "auto-pull": {
        "module": "gitmap_cli.commands.auto_pull",
        "attr": "auto_pull",
        "short_help": "Bulk-pull multiple repositories from Portal.",
    },
    "setup-repos": {
        "module": "gitmap_cli.commands.setup_repos",
        "attr": "setup_repos",
        "short_help": "Create multiple GitMap repos from a manifest.",
    },
}


def _load_command(spec: dict[str, str]) -> click.Command:
    if "module" in spec:
        module = __import__(spec["module"], fromlist=[spec["attr"]])
        return getattr(module, spec["attr"])

    module_name = spec["module_name"]
    loaded = sys.modules.get(module_name)
    if loaded is None:
        module_path = spec["path"]
        module_spec = importlib.util.spec_from_file_location(module_name, module_path)
        if module_spec is None or module_spec.loader is None:
            raise ImportError(f"Unable to load command module from {module_path}")
        loaded = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = loaded
        module_spec.loader.exec_module(loaded)
    return getattr(loaded, spec["attr"])


class LazyCommandGroup(GroupedHelpGroup):
    """Grouped help plus on-demand command imports for lightweight top-level CLI startup."""

    lazy_command_summaries = {name: spec["short_help"] for name, spec in COMMAND_SPECS.items()}

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(COMMAND_SPECS)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        spec = COMMAND_SPECS.get(cmd_name)
        if spec is None:
            return None
        return _load_command(spec)


# ---- CLI Group ----------------------------------------------------------------------------------------------

# ---- Grouped Help ------------------------------------------------------------------------------------------


@click.group(name="gitmap", cls=LazyCommandGroup)
@click.version_option(version="0.7.0", prog_name="gitmap")
def cli() -> None:
    """GitMap - Version control for ArcGIS web maps.

    Provides Git-like version control for ArcGIS Online and Enterprise
    Portal web maps. Branch, commit, diff, merge, push, and pull maps
    using familiar workflows.
    """
    pass


# ---- Main Function ------------------------------------------------------------------------------------------


def main() -> int:
    """Main entry point for GitMap CLI.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        cli(prog_name="gitmap")
        return 0
    except Exception as cli_error:
        click.echo(f"Error: {cli_error}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
