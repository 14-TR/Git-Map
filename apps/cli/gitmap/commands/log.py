"""GitMap log command.

Shows commit history for the repository.

Execution Context:
    CLI command - invoked via `gitmap log`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository management

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""

from __future__ import annotations

import json

import click
from rich.console import Console

from gitmap_core.graph import build_graph
from gitmap_core.repository import find_repository

console = Console()


# ---- Graph Rendering ----------------------------------------------------------------------------------------


def _format_labels(labels: list[str]) -> str:
    """Format branch/ref labels for inline display.

    Args:
        labels: List of label strings (e.g. ``["HEAD -> main", "v1.0"]``).

    Returns:
        Parenthesised, comma-separated label string, or empty string.
    """
    if not labels:
        return ""
    styled: list[str] = []
    for label in labels:
        if label.startswith("HEAD ->"):
            styled.append(f"[yellow]{label}[/yellow]")
        else:
            styled.append(f"[green]{label}[/green]")
    return "(" + ", ".join(styled) + ")"


def _print_graph(limit: int, oneline: bool, repo) -> None:
    """Render the graph log output.

    Args:
        limit: Maximum number of commits to display.
        oneline: If True, use compact single-line format.
        repo: Initialised Repository object.
    """
    nodes = build_graph(repo, limit=limit)

    if not nodes:
        console.print("[dim]No commits yet[/dim]")
        return

    for node in nodes:
        commit = node.commit
        label_str = _format_labels(node.labels)
        prefix = node.prefix_line

        if oneline:
            # Compact: prefix  hash  (labels)  message
            short_id = f"[cyan]{commit.id[:8]}[/cyan]"
            sep = " " if label_str else ""
            console.print(f"{prefix} {short_id}{sep}{label_str} {commit.message}")
        else:
            # Full format
            head_label = f" {label_str}" if label_str else ""
            console.print(f"{prefix} [bold cyan]commit {commit.id}[/bold cyan]{head_label}")
            console.print(f"{'|' if node.lane >= 0 else ' '} Author: {commit.author}")
            console.print(f"{'|' if node.lane >= 0 else ' '} Date:   {commit.timestamp}")
            layers = commit.map_data.get("operationalLayers", [])
            console.print(f"{'|' if node.lane >= 0 else ' '}")
            console.print(f"{'|' if node.lane >= 0 else ' '}     {commit.message}")
            console.print(f"{'|' if node.lane >= 0 else ' '} [dim]({len(layers)} layer(s))[/dim]")

        # Draw connector lines (e.g. for merge commits)
        for connector in node.connector_lines:
            console.print(connector)


# ---- Log Command --------------------------------------------------------------------------------------------


@click.command(epilog="Tip: use 'gitmap show <commit>' to inspect a commit in detail.")
@click.option(
    "--limit",
    "-n",
    default=10,
    help="Maximum number of commits to show.",
)
@click.option(
    "--oneline",
    is_flag=True,
    help="Show compact one-line format.",
)
@click.option(
    "--graph",
    "show_graph",
    is_flag=True,
    help="Show a visual ASCII commit graph with branch labels.",
)
@click.option(
    "--branch",
    "-b",
    default=None,
    help="Show history for a specific branch (defaults to current branch).",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format: 'text' for human-readable, 'json' for machine-readable.",
)
def log(
    limit: int,
    oneline: bool,
    show_graph: bool,
    branch: str | None,
    fmt: str,
) -> None:
    """Show commit history.

    Displays the commit log starting from HEAD, walking back through
    parent commits. Use --graph to see a visual representation of
    branches and their ancestry.

    Examples:
        gitmap log
        gitmap log -n 5
        gitmap log --oneline
        gitmap log --graph
        gitmap log --graph --oneline
        gitmap log --branch feature/my-layer
        gitmap log -b main --oneline
        gitmap log --format json
        gitmap log -n 5 --format json
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository. Run 'gitmap init' to create one.")

        # Graph mode: walk all branches
        if show_graph:
            if branch:
                # Restrict to a single branch's history for --graph --branch
                branch_commit = repo.get_branch_commit(branch)
                if not branch_commit:
                    raise click.ClickException(f"Branch not found: '{branch}'")
            _print_graph(limit, oneline, repo)
            return

        # ---- Original non-graph log ----
        current_branch = repo.get_current_branch()

        # Resolve which branch to walk
        if branch and branch != current_branch:
            branch_commit = repo.get_branch_commit(branch)
            if not branch_commit:
                raise click.ClickException(f"Branch not found: '{branch}'")
            commits = repo.get_commit_history(start_commit=branch_commit, limit=limit)
            head_commit = branch_commit
        else:
            commits = repo.get_commit_history(limit=limit)
            head_commit = repo.get_head_commit()

        if not commits:
            if fmt == "json":
                click.echo("[]")
            else:
                console.print("[dim]No commits yet[/dim]")
            return

        # ---- JSON output ----
        if fmt == "json":
            entries = []
            for commit in commits:
                layers = commit.map_data.get("operationalLayers", [])
                entries.append(
                    {
                        "id": commit.id,
                        "short_id": commit.id[:8],
                        "message": commit.message,
                        "author": commit.author,
                        "timestamp": commit.timestamp,
                        "parent": commit.parent,
                        "layers": len(layers),
                        "is_head": commit.id == head_commit,
                    }
                )
            click.echo(json.dumps(entries, indent=2))
            return

        if oneline:
            # Compact format
            for commit in commits:
                marker = "[yellow]*[/yellow] " if commit.id == head_commit else "  "
                console.print(f"{marker}[cyan]{commit.id[:8]}[/cyan] {commit.message}")
        else:
            # Full format
            for i, commit in enumerate(commits):
                if i > 0:
                    console.print()

                # Header with commit ID
                is_head = commit.id == head_commit
                head_marker = f" [yellow](HEAD -> {current_branch})[/yellow]" if is_head else ""

                console.print(f"[bold cyan]commit {commit.id}[/bold cyan]{head_marker}")
                console.print(f"Author: {commit.author}")
                console.print(f"Date:   {commit.timestamp}")

                if commit.parent:
                    console.print(f"Parent: {commit.parent[:8]}")

                console.print()
                console.print(f"    {commit.message}")

                # Layer summary
                layers = commit.map_data.get("operationalLayers", [])
                console.print(f"    [dim]({len(layers)} layer(s))[/dim]")

    except Exception as log_error:
        msg = f"Log failed: {log_error}"
        raise click.ClickException(msg) from log_error
