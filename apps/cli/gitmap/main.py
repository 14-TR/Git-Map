"""GitMap CLI entry point.

Orchestrator for the GitMap command-line interface. Registers all
command modules and provides the main entry point.

Execution Context:
    CLI application - run via `python main.py` or `gitmap` command

Dependencies:
    - click: CLI framework
    - gitmap_core: Core library

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import sys

import click

from gitmap_cli.commands.branch import branch
from gitmap_cli.commands.checkout import checkout
from gitmap_cli.commands.clone import clone
from gitmap_cli.commands.commit import commit
from gitmap_cli.commands.diff import diff
from gitmap_cli.commands.init import init
from gitmap_cli.commands.log import log
from gitmap_cli.commands.merge import merge
from gitmap_cli.commands.pull import pull
from gitmap_cli.commands.push import push
from gitmap_cli.commands.status import status


# ---- CLI Group ----------------------------------------------------------------------------------------------


@click.group()
@click.version_option(version="0.1.0", prog_name="gitmap")
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
cli.add_command(diff)
cli.add_command(log)
cli.add_command(merge)
cli.add_command(push)
cli.add_command(pull)


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


