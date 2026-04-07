"""GitMap CLI grouped help formatter.

Provides a custom Click Group that renders commands in logical workflow
sections rather than a single flat alphabetical list, and improves
command-discovery UX for the GitMap CLI.

Execution Context:
    CLI framework support — imported by main.py

Dependencies:
    - click: CLI framework

Metadata:
    Version: 1.1.0
    Author: GitMap Team
"""

from __future__ import annotations

import difflib

import click

# ---- Command Section Definitions ----------------------------------------------------------------------------

#: Ordered sections: (section_title, [command_names_in_display_order])
#: Commands not listed here fall into an "Other" catch-all section.
COMMAND_SECTIONS: list[tuple[str, list[str]]] = [
    (
        "Repository",
        ["init", "clone", "setup-repos"],
    ),
    (
        "Snapshot & History",
        ["status", "commit", "log", "show", "diff", "tag"],
    ),
    (
        "Branching",
        ["branch", "checkout", "merge", "cherry-pick", "merge-from", "stash", "revert"],
    ),
    (
        "Remote Sync",
        ["push", "pull", "auto-pull"],
    ),
    (
        "Portal Utilities",
        ["list", "lsm", "notify"],
    ),
    (
        "Tooling",
        ["config", "context", "daemon", "doctor", "completions"],
    ),
]

HELP_FOOTER = (
    "Getting started: gitmap init → gitmap status → gitmap commit -m \"Initial snapshot\"\n"
    "Need shell completions? Run: gitmap completions"
)


class GroupedHelpGroup(click.Group):
    """Click Group that groups --help commands into workflow sections."""

    suggestion_limit = 3
    suggestion_cutoff = 0.5

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Render commands in named sections instead of a flat list."""
        available: dict[str, click.BaseCommand | None] = {
            name: self.get_command(ctx, name) for name in self.list_commands(ctx)
        }

        placed: set[str] = set()

        for section_title, cmd_names in COMMAND_SECTIONS:
            rows: list[tuple[str, str]] = []
            for name in cmd_names:
                cmd = available.get(name)
                if cmd is None:
                    continue
                help_text = cmd.get_short_help_str(limit=60)
                rows.append((name, help_text))
                placed.add(name)

            if not rows:
                continue

            with formatter.section(section_title):
                formatter.write_dl(rows)

        remainder: list[tuple[str, str]] = []
        for name in sorted(available):
            if name not in placed:
                cmd = available[name]
                if cmd is not None:
                    remainder.append((name, cmd.get_short_help_str(limit=60)))

        if remainder:
            with formatter.section("Other"):
                formatter.write_dl(remainder)

    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Append a short getting-started footer to top-level help."""
        if HELP_FOOTER:
            formatter.write_paragraph()
            formatter.write_text(HELP_FOOTER)

    def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[str, click.Command, list[str]]:
        """Add suggestions when the user mistypes a command name."""
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError as exc:
            if not args:
                raise

            unknown = args[0]
            suggestions = difflib.get_close_matches(
                unknown,
                self.list_commands(ctx),
                n=self.suggestion_limit,
                cutoff=self.suggestion_cutoff,
            )
            if not suggestions:
                raise

            suggestion_text = ", ".join(f"'{name}'" for name in suggestions)
            raise click.UsageError(
                (
                    f"No such command '{unknown}'.\n"
                    f"Did you mean: {suggestion_text}?\n"
                    "Run 'gitmap --help' to see the full command list."
                ),
                ctx=ctx,
            ) from exc
