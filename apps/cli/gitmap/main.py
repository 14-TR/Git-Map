"""GitMap CLI entry point.

Orchestrator for the GitMap command-line interface. Registers all
command modules and provides the main entry point.

Execution Context:
    CLI application - run via `python main.py` or `gitmap` command

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Core library

Metadata:
    Version: 0.6.0
    Author: GitMap Team
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gitmap_cli.commands.auto_pull import auto_pull
from gitmap_cli.commands.branch import branch
from gitmap_cli.commands.checkout import checkout
from gitmap_cli.commands.cherry_pick import cherry_pick
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
from gitmap_cli.commands.revert import revert
from gitmap_cli.commands.setup_repos import setup_repos
from gitmap_cli.commands.stash import stash
from gitmap_cli.commands.show import show
from gitmap_cli.commands.status import status
from gitmap_cli.commands.tag import tag

console = Console()

# Import hyphenated modules using importlib.util (kebab-case filenames)
_layer_settings_merge_path = Path(__file__).parent / "commands" / "layer-settings-merge.py"
_layer_settings_merge_spec = importlib.util.spec_from_file_location(
    "layer_settings_merge",
    _layer_settings_merge_path,
)
_layer_settings_merge_module = importlib.util.module_from_spec(_layer_settings_merge_spec)
_layer_settings_merge_spec.loader.exec_module(_layer_settings_merge_module)
layer_settings_merge = _layer_settings_merge_module.layer_settings_merge

_merge_from_path = Path(__file__).parent / "commands" / "merge-from.py"
_merge_from_spec = importlib.util.spec_from_file_location(
    "merge_from",
    _merge_from_path,
)
_merge_from_module = importlib.util.module_from_spec(_merge_from_spec)
_merge_from_spec.loader.exec_module(_merge_from_module)
merge_from = _merge_from_module.merge_from


# ---- Grouped Help Formatter ---------------------------------------------------------------------------------


class SectionedGroup(click.Group):
    """Click Group that renders help with commands organized into logical sections."""

    #: Ordered sections and the command names that belong to each.
    SECTIONS: list[tuple[str, list[str]]] = [
        ("Setup", ["init", "clone", "config", "setup-repos"]),
        ("Track Changes", ["list", "status", "commit", "diff", "show"]),
        ("Branching", ["branch", "checkout", "cherry-pick", "merge", "merge-from"]),
        ("History", ["log", "revert", "stash", "tag"]),
        ("Portal Sync", ["push", "pull", "auto-pull"]),
        ("Advanced", ["context", "daemon", "notify", "layer-settings-merge"]),
    ]

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write grouped help to *formatter*."""
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self._format_sections(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def _format_sections(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write command sections, then a catch-all for any unlisted commands."""
        seen: set[str] = set()

        for section_title, cmd_names in self.SECTIONS:
            rows: list[tuple[str, str]] = []
            for name in cmd_names:
                cmd = self.get_command(ctx, name)
                if cmd is None or cmd.hidden:
                    continue
                seen.add(name)
                help_str = cmd.get_short_help_str(limit=formatter.width)
                rows.append((name, help_str))

            if rows:
                with formatter.section(section_title):
                    formatter.write_dl(rows)

        # Emit any commands that weren't placed in a section
        other_rows: list[tuple[str, str]] = []
        for name, cmd in sorted(self.commands.items()):
            if name in seen or cmd.hidden:
                continue
            help_str = cmd.get_short_help_str(limit=formatter.width)
            other_rows.append((name, help_str))

        if other_rows:
            with formatter.section("Other"):
                formatter.write_dl(other_rows)

        formatter.write_paragraph()
        formatter.write_text('Run "gitmap COMMAND --help" for detailed help on any command.')

    def invoke(self, ctx: click.Context) -> None:
        """Show a welcome banner when gitmap is invoked with no subcommand."""
        if ctx.invoked_subcommand is None and not ctx.args:
            _print_welcome_banner()
            click.echo(ctx.get_help())
            ctx.exit()
        else:
            super().invoke(ctx)


# ---- Welcome Banner -----------------------------------------------------------------------------------------


def _print_welcome_banner() -> None:
    """Print a brief welcome banner above the help text."""
    banner = Text()
    banner.append("gitmap", style="bold cyan")
    banner.append(" — version control for ArcGIS web maps\n", style="dim")
    banner.append("\nQuick start:\n", style="bold")
    banner.append("  gitmap init              ", style="green")
    banner.append("# create a repo\n", style="dim")
    banner.append("  gitmap list              ", style="green")
    banner.append("# discover your portal maps\n", style="dim")
    banner.append("  gitmap commit -m 'msg'   ", style="green")
    banner.append("# snapshot current state\n", style="dim")
    banner.append("  gitmap log               ", style="green")
    banner.append("# view history\n", style="dim")
    banner.append("  gitmap diff main feature ", style="green")
    banner.append("# compare branches", style="dim")

    console.print(Panel(banner, border_style="blue", padding=(0, 1)))
    console.print()


# ---- CLI Group ----------------------------------------------------------------------------------------------


@click.group(cls=SectionedGroup, invoke_without_command=True)
@click.version_option(version="0.6.0", prog_name="gitmap")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """GitMap — version control for ArcGIS web maps.

    Provides Git-like workflows for ArcGIS Online and Enterprise Portal
    web maps. Branch, commit, diff, merge, push, and pull maps using
    commands your team already knows.
    """
    pass


# ---- Register Commands --------------------------------------------------------------------------------------


cli.add_command(init)
cli.add_command(clone)
cli.add_command(cherry_pick, name="cherry-pick")
cli.add_command(show)
cli.add_command(status)
cli.add_command(branch)
cli.add_command(checkout)
cli.add_command(commit)
cli.add_command(config)
cli.add_command(context)
cli.add_command(daemon)
cli.add_command(diff)
cli.add_command(layer_settings_merge, name="layer-settings-merge")
cli.add_command(list_maps, name="list")
cli.add_command(log)
cli.add_command(merge)
cli.add_command(merge_from, name="merge-from")
cli.add_command(notify)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(revert)
cli.add_command(stash)
cli.add_command(tag)
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
