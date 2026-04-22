"""GitMap CLI grouped help formatter.

Provides a custom Click Group that renders commands in logical workflow
sections rather than a single flat alphabetical list, and improves
command-discovery UX for the GitMap CLI.

Execution Context:
    CLI framework support — imported by main.py

Dependencies:
    - click: CLI framework

Metadata:
    Version: 1.2.0
    Author: GitMap Team
"""

from __future__ import annotations

import difflib
import inspect

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

HELP_FOOTER_LINES = [
    'Getting started: gitmap init → gitmap status → gitmap commit -m "Initial snapshot"',
    "Need shell completions? Run: gitmap completions",
]

_EXAMPLE_HEADINGS = {"Examples:"}
_CALLOUT_PREFIXES = ("Tip:", "Tips:", "Note:", "Notes:")
_ORIGINAL_FORMAT_HELP_TEXT = click.Command.format_help_text


def _flush_paragraph(formatter: click.HelpFormatter, lines: list[str]) -> None:
    """Write buffered prose lines as a normal wrapped paragraph."""
    if not lines:
        return
    formatter.write_text("\n".join(lines))
    lines.clear()


def _write_examples_block(formatter: click.HelpFormatter, heading: str, example_lines: list[str]) -> None:
    """Render examples as one-per-line entries instead of one flattened paragraph."""
    formatter.write_text(heading)
    with formatter.indentation():
        for line in example_lines:
            formatter.write_text(line)


def _format_structured_help_text(formatter: click.HelpFormatter, text: str) -> None:
    """Render help text while preserving example blocks and callout lines."""
    paragraph_lines: list[str] = []
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()

        if not stripped:
            _flush_paragraph(formatter, paragraph_lines)
            index += 1
            continue

        if stripped in _EXAMPLE_HEADINGS:
            _flush_paragraph(formatter, paragraph_lines)
            index += 1
            example_lines: list[str] = []

            while index < len(lines):
                candidate = lines[index].strip()
                if not candidate:
                    break
                if candidate in _EXAMPLE_HEADINGS or candidate.startswith(_CALLOUT_PREFIXES):
                    break
                example_lines.append(candidate)
                index += 1

            if example_lines:
                _write_examples_block(formatter, stripped, example_lines)
            else:
                formatter.write_text(stripped)
            continue

        if stripped.startswith(_CALLOUT_PREFIXES):
            _flush_paragraph(formatter, paragraph_lines)
            formatter.write_text(stripped)
            index += 1
            continue

        paragraph_lines.append(stripped)
        index += 1

    _flush_paragraph(formatter, paragraph_lines)


def _format_help_text_preserving_examples(self: click.Command, ctx: click.Context, formatter: click.HelpFormatter) -> None:
    """Override Click's help formatter so GitMap examples stay readable."""
    if self.help is not None:
        text = inspect.cleandoc(self.help).partition("\f")[0]
    else:
        text = ""

    if self.deprecated:
        deprecated_message = (
            f"(DEPRECATED: {self.deprecated})"
            if isinstance(self.deprecated, str)
            else "(DEPRECATED)"
        )
        text = f"{text} {deprecated_message}" if text else deprecated_message

    if not text:
        return

    formatter.write_paragraph()
    with formatter.indentation():
        _format_structured_help_text(formatter, text)


if click.Command.format_help_text is not _format_help_text_preserving_examples:
    click.Command.format_help_text = _format_help_text_preserving_examples
    click.Group.format_help_text = _format_help_text_preserving_examples


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
        if HELP_FOOTER_LINES:
            formatter.write_paragraph()
            for line in HELP_FOOTER_LINES:
                formatter.write_text(line)

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
