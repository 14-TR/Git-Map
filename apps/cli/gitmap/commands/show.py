"""GitMap show command.

Displays details of a specific commit: metadata, layer summary,
and the diff against its parent commit.

Execution Context:
    CLI command - invoked via `gitmap show [<commit>]`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository management, diff operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from gitmap_core.diff import diff_maps
from gitmap_core.diff import format_diff_stats
from gitmap_core.repository import find_repository

console = Console()


# ---- Helpers ------------------------------------------------------------------------------------------------


def _resolve_ref(repo, ref: str) -> str | None:
    """Resolve a branch name or commit ID to a commit ID."""
    branches = repo.list_branches()
    if ref in branches:
        return repo.get_branch_commit(ref)
    return ref if repo.get_commit(ref) else None


def _print_commit_header(commit, current_branch: str | None, is_head: bool) -> None:
    """Print the commit header block (hash, author, date, message)."""
    head_label = f" [yellow](HEAD -> {current_branch})[/yellow]" if is_head else ""
    console.print(f"[bold cyan]commit {commit.id}[/bold cyan]{head_label}")
    console.print(f"[bold]Author:[/bold]    {commit.author}")
    console.print(f"[bold]Date:[/bold]      {commit.timestamp}")

    if commit.parent:
        console.print(f"[bold]Parent:[/bold]    {commit.parent[:8]}")

    if hasattr(commit, "rationale") and commit.rationale:
        console.print(f"[bold]Rationale:[/bold] {commit.rationale}")

    console.print()
    console.print(f"    {commit.message}")


def _print_layer_summary(commit) -> None:
    """Print a summary table of layers in the commit."""
    layers = commit.map_data.get("operationalLayers", [])
    tables = commit.map_data.get("tables", [])

    console.print()
    console.print(Rule("[dim]Layer Summary[/dim]", style="dim"))

    if not layers and not tables:
        console.print("[dim]  (no layers or tables)[/dim]")
        return

    table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
    table.add_column("Type", style="dim", width=8)
    table.add_column("Title", min_width=30)
    table.add_column("Visible", width=8)

    for layer in layers:
        title = layer.get("title", layer.get("id", "(unnamed)"))
        visible = "[green]yes[/green]" if layer.get("visibility", True) else "[dim]no[/dim]"
        table.add_row("layer", title, visible)

    for tbl in tables:
        title = tbl.get("title", tbl.get("id", "(unnamed)"))
        table.add_row("[dim]table[/dim]", title, "[dim]—[/dim]")

    console.print(table)
    console.print(f"  [dim]{len(layers)} layer(s), {len(tables)} table(s)[/dim]")


def _print_diff_section(commit, parent_commit, verbose: bool, fmt: str) -> None:
    """Print the diff between commit and its parent."""
    console.print()
    console.print(Rule("[dim]Changes vs Parent[/dim]", style="dim"))

    map_diff = diff_maps(commit.map_data, parent_commit.map_data)

    if not map_diff.has_changes:
        console.print("[green]  ✓ No layer changes from parent[/green]")
        return

    stats = format_diff_stats(map_diff)
    stat_parts = []
    if stats["added"]:
        stat_parts.append(f"[green]+{stats['added']} added[/green]")
    if stats["removed"]:
        stat_parts.append(f"[red]-{stats['removed']} removed[/red]")
    if stats["modified"]:
        stat_parts.append(f"[yellow]~{stats['modified']} modified[/yellow]")
    console.print("  " + "  ".join(stat_parts))

    if fmt == "visual":
        _print_diff_table(map_diff, verbose)
    else:
        _print_diff_text(map_diff, verbose)


def _print_diff_table(map_diff, verbose: bool) -> None:
    """Render diff as a Rich table."""
    table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
    table.add_column("", width=3, no_wrap=True)
    table.add_column("Layer / Table", min_width=24)
    table.add_column("Detail", style="dim")

    symbol_styles = {"+": "green", "-": "red", "~": "yellow", "*": "cyan"}

    rows = []
    for change in map_diff.added_layers:
        rows.append(("+", change.layer_title, "added"))
    for change in map_diff.removed_layers:
        rows.append(("-", change.layer_title, "removed"))
    for change in map_diff.modified_layers:
        n = len(change.details) if change.details else 1
        rows.append(("~", change.layer_title, f"{n} field(s) changed"))
    for change in map_diff.added_tables:
        rows.append(("+", f"[table] {change.layer_title}", "added"))
    for change in map_diff.removed_tables:
        rows.append(("-", f"[table] {change.layer_title}", "removed"))
    for change in map_diff.modified_tables:
        n = len(change.details) if change.details else 1
        rows.append(("~", f"[table] {change.layer_title}", f"{n} field(s) changed"))
    if map_diff.property_changes:
        rows.append(("*", "Map properties", f"{len(map_diff.property_changes)} field(s) changed"))

    for symbol, name, detail in rows:
        style = symbol_styles.get(symbol, "white")
        table.add_row(Text(symbol, style=style), name, detail)

    console.print(table)

    if verbose:
        for change in map_diff.modified_layers:
            if change.details:
                console.print()
                console.print(f"  [cyan]{change.layer_title}:[/cyan]")
                details_json = json.dumps(change.details, indent=2)
                syntax = Syntax(details_json, "json", theme="monokai", indent_guides=True)
                console.print(syntax)


def _print_diff_text(map_diff, verbose: bool) -> None:
    """Render diff as plain text lines."""
    for change in map_diff.added_layers:
        console.print(f"  [green]+ {change.layer_title}[/green]")
    for change in map_diff.removed_layers:
        console.print(f"  [red]- {change.layer_title}[/red]")
    for change in map_diff.modified_layers:
        n = len(change.details) if change.details else 1
        console.print(f"  [yellow]~ {change.layer_title}[/yellow] [dim]({n} field(s) changed)[/dim]")
        if verbose and change.details:
            details_json = json.dumps(change.details, indent=2)
            syntax = Syntax(details_json, "json", theme="monokai", indent_guides=True)
            console.print(syntax)
    for change in map_diff.added_tables:
        console.print(f"  [green]+ [table] {change.layer_title}[/green]")
    for change in map_diff.removed_tables:
        console.print(f"  [red]- [table] {change.layer_title}[/red]")
    for change in map_diff.modified_tables:
        n = len(change.details) if change.details else 1
        console.print(f"  [yellow]~ [table] {change.layer_title}[/yellow] [dim]({n} field(s) changed)[/dim]")
    if map_diff.property_changes:
        console.print(f"  [cyan]* Map properties[/cyan] [dim]({len(map_diff.property_changes)} field(s) changed)[/dim]")
        if verbose:
            for key, (old_val, new_val) in map_diff.property_changes.items():
                console.print(f"    [dim]{key}:[/dim] {old_val!r} → {new_val!r}")


# ---- Show Command -------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "ref",
    required=False,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show property-level change details.",
)
@click.option(
    "--no-diff",
    "no_diff",
    is_flag=True,
    help="Show only commit metadata and layer summary, skip the diff.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "visual"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Diff output format: 'text' for plain lines, 'visual' for Rich table.",
)
def show(
        ref: str | None,
        verbose: bool,
        no_diff: bool,
        fmt: str,
) -> None:
    """Show details of a commit.

    Displays the commit metadata (author, date, message), a layer
    summary, and a diff against the parent commit.

    Without a REF argument, shows the current HEAD commit.
    REF can be a full or partial commit ID, or a branch name.

    Examples:
        gitmap show                         # Show HEAD
        gitmap show abc123                  # Show specific commit
        gitmap show feature/new-layer       # Show tip of a branch
        gitmap show --format visual         # Visual diff table
        gitmap show -v                      # Show field-level details
        gitmap show --no-diff               # Metadata + layers only
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException(
                "Not a GitMap repository. Run 'gitmap init' to create one."
            )

        current_branch = repo.get_current_branch()
        head_commit_id = repo.get_head_commit()

        # Resolve the target commit
        if ref:
            commit_id = _resolve_ref(repo, ref)
            if not commit_id:
                raise click.ClickException(
                    f"Unknown commit or branch: '{ref}'\n"
                    "Hint: use 'gitmap log --oneline' to list available commits."
                )
        else:
            commit_id = head_commit_id
            if not commit_id:
                raise click.ClickException(
                    "No commits yet. Make a commit first with:\n"
                    "  gitmap commit -m 'Initial commit'"
                )

        commit = repo.get_commit(commit_id)
        if not commit:
            raise click.ClickException(f"Could not load commit '{commit_id}'")

        is_head = commit_id == head_commit_id

        # ---- Header panel -------------------------------------------
        label = ref or "HEAD"
        console.print(Panel(
            f"[bold]Showing commit[/bold] [cyan]{commit_id[:8]}[/cyan]",
            title=f"gitmap show {label}",
            border_style="blue",
        ))
        console.print()

        # ---- Commit metadata ----------------------------------------
        _print_commit_header(commit, current_branch, is_head)

        # ---- Layer summary ------------------------------------------
        _print_layer_summary(commit)

        # ---- Diff section -------------------------------------------
        if not no_diff:
            if commit.parent:
                parent_commit = repo.get_commit(commit.parent)
                if parent_commit:
                    _print_diff_section(commit, parent_commit, verbose, fmt)
                else:
                    console.print()
                    console.print(
                        f"[dim]Parent commit {commit.parent[:8]} not found — "
                        "cannot compute diff[/dim]"
                    )
            else:
                console.print()
                console.print(
                    "[dim]Root commit — no parent to diff against[/dim]"
                )

        console.print()

    except click.ClickException:
        raise
    except Exception as show_error:
        msg = f"Show failed: {show_error}"
        raise click.ClickException(msg) from show_error
