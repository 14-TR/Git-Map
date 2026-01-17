"""GitMap CLI entry point.

Orchestrator for the GitMap command-line interface. Registers all
command modules and provides the main entry point.

Execution Context:
    CLI application - run via `python main.py` or `gitmap` command

Dependencies:
    - click: CLI framework
    - gitmap_core: Core library

Metadata:
    Version: 0.5.0
    Author: GitMap Team
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import click

from gitmap_cli.commands.auto_pull import auto_pull
from gitmap_cli.commands.branch import branch
from gitmap_cli.commands.checkout import checkout
from gitmap_cli.commands.clone import clone
from gitmap_cli.commands.commit import commit
from gitmap_cli.commands.config import config
from gitmap_cli.commands.context import context
from gitmap_cli.commands.daemon import daemon
from gitmap_cli.commands.diff import diff
from gitmap_cli.commands.init import init
from gitmap_cli.commands.list import list_maps
from gitmap_cli.commands.log import log
from gitmap_cli.commands.merge import merge
from gitmap_cli.commands.notify import notify
from gitmap_cli.commands.pull import pull
from gitmap_cli.commands.push import push
from gitmap_cli.commands.setup_repos import setup_repos
from gitmap_cli.commands.status import status

# Import hyphenated module using importlib.util (kebab-case filename)
_layer_settings_merge_path = Path(__file__).parent / "commands" / "layer-settings-merge.py"
_layer_settings_merge_spec = importlib.util.spec_from_file_location(
    "layer_settings_merge",
    _layer_settings_merge_path,
)
_layer_settings_merge_module = importlib.util.module_from_spec(_layer_settings_merge_spec)
_layer_settings_merge_spec.loader.exec_module(_layer_settings_merge_module)
layer_settings_merge = _layer_settings_merge_module.layer_settings_merge


# ---- CLI Group ----------------------------------------------------------------------------------------------


@click.group()
@click.version_option(version="0.5.0", prog_name="gitmap")
def cli() -> None:
    """GitMap - Version control for ArcGIS web maps.

    Provides Git-like version control for ArcGIS Online and Enterprise
    Portal web maps. Branch, commit, diff, merge, push, and pull maps
    using familiar workflows.
    """
    pass


# ---- Register Commands --------------------------------------------------------------------------------------


cli.add_command(init)
cli.add_command(clone)
cli.add_command(status)
cli.add_command(branch)
cli.add_command(checkout)
cli.add_command(commit)
cli.add_command(config)
cli.add_command(context)
cli.add_command(daemon)
cli.add_command(diff)
cli.add_command(layer_settings_merge)
cli.add_command(list_maps, name="list")
cli.add_command(log)
cli.add_command(merge)
cli.add_command(notify)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(auto_pull, name="auto-pull")
cli.add_command(setup_repos, name="setup-repos")


# ---- Main Function ------------------------------------------------------------------------------------------


def main() -> int:
    """Main entry point for GitMap CLI.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        cli()
        return 0
    except Exception as cli_error:
        click.echo(f"Error: {cli_error}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())


