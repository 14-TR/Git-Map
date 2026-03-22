"""GitMap CLI grouped help formatter.

Provides a custom Click Group that renders commands in logical workflow
sections rather than a single flat alphabetical list.

Execution Context:
    CLI framework support — imported by main.py

Dependencies:
    - click: CLI framework

Metadata:
    Version: 1.0.0
    Author: GitMap Team
"""
from __future__ import annotations

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
        ["config", "context", "daemon"],
    ),
]


class GroupedHelpGroup(click.Group):
    """Click Group that groups --help commands into workflow sections."""

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Render commands in named sections instead of a flat list."""
        available: dict[str, click.BaseCommand | None] = {
            name: self.get_command(ctx, name)
            for name in self.list_commands(ctx)
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

        # Emit anything that wasn't placed in a section
        remainder: list[tuple[str, str]] = []
        for name in sorted(available):
            if name not in placed:
                cmd = available[name]
                if cmd is not None:
                    remainder.append((name, cmd.get_short_help_str(limit=60)))

        if remainder:
            with formatter.section("Other"):
                formatter.write_dl(remainder)
