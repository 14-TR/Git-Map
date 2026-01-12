"""GitMap context visualization command.

Provides commands for visualizing and exporting the context graph
in various formats (Mermaid, ASCII, HTML).

Execution Context:
    CLI command - invoked via `gitmap context`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository and visualization

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from gitmap_core.repository import find_repository
from gitmap_core.visualize import visualize_context

console = Console()


# ---- Context Command Group -----------------------------------------------------------------------------------


@click.group()
def context() -> None:
    """Context graph visualization and management.

    View and export the context graph showing events, relationships,
    and annotations. Supports multiple output formats for IDE viewing.

    Examples:
        gitmap context show
        gitmap context export --format mermaid -o graph.md
        gitmap context timeline
    """
    pass


# ---- Show Command --------------------------------------------------------------------------------------------


@context.command()
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["ascii", "mermaid", "mermaid-timeline"]),
    default="ascii",
    help="Output format for visualization.",
)
@click.option(
    "--limit",
    "-n",
    default=20,
    help="Maximum events to display.",
)
@click.option(
    "--type",
    "-t",
    "event_types",
    multiple=True,
    type=click.Choice(["commit", "push", "pull", "merge", "branch", "diff"]),
    help="Filter by event types.",
)
@click.option(
    "--no-unicode",
    is_flag=True,
    help="Use simple ASCII characters (no Unicode).",
)
def show(
    output_format: str,
    limit: int,
    event_types: tuple[str, ...],
    no_unicode: bool,
) -> None:
    """Display context graph in terminal.

    Shows the context graph visualization directly in the terminal.
    Best for quick viewing of recent events.

    Examples:
        gitmap context show
        gitmap context show --format mermaid
        gitmap context show -n 10 --type commit
    """
    try:
        repo = find_repository()
        if not repo:
            raise click.ClickException("Not a GitMap repository")

        with repo.get_context_store() as store:
            viz = visualize_context(
                store,
                output_format=output_format,
                limit=limit,
                event_types=list(event_types) if event_types else None,
                use_unicode=not no_unicode,
            )

        if output_format == "ascii":
            console.print(Panel(viz, title="Context Timeline", border_style="blue"))
        elif output_format.startswith("mermaid"):
            console.print(Panel(
                Syntax(viz, "text", theme="monokai"),
                title="Mermaid Diagram",
                subtitle="Copy to .md file for IDE preview",
                border_style="green",
            ))

    except ValueError as format_error:
        raise click.ClickException(str(format_error)) from format_error
    except Exception as show_error:
        msg = f"Show failed: {show_error}"
        raise click.ClickException(msg) from show_error


# ---- Export Command ------------------------------------------------------------------------------------------


@context.command()
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["mermaid", "mermaid-timeline", "mermaid-git", "ascii", "ascii-graph", "html"]),
    default="mermaid",
    help="Output format for export.",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file path. Defaults to context.<ext>",
)
@click.option(
    "--limit",
    "-n",
    default=50,
    help="Maximum events to include.",
)
@click.option(
    "--type",
    "-t",
    "event_types",
    multiple=True,
    type=click.Choice(["commit", "push", "pull", "merge", "branch", "diff"]),
    help="Filter by event types.",
)
@click.option(
    "--title",
    default=None,
    help="Title for the visualization.",
)
@click.option(
    "--theme",
    type=click.Choice(["light", "dark"]),
    default="light",
    help="Color theme (for HTML output).",
)
@click.option(
    "--direction",
    type=click.Choice(["TB", "BT", "LR", "RL"]),
    default="TB",
    help="Graph direction for Mermaid flowcharts.",
)
@click.option(
    "--no-annotations",
    is_flag=True,
    help="Exclude annotations from visualization.",
)
def export(
    output_format: str,
    output_file: str | None,
    limit: int,
    event_types: tuple[str, ...],
    title: str | None,
    theme: str,
    direction: str,
    no_annotations: bool,
) -> None:
    """Export context graph to file.

    Generates visualization files that can be viewed directly in IDEs.
    Mermaid files (.md) work with VS Code, JetBrains, and GitHub.
    HTML files include interactive features.

    Examples:
        gitmap context export
        gitmap context export -f html -o context.html
        gitmap context export -f mermaid --direction LR
        gitmap context export --type commit --type push
    """
    try:
        repo = find_repository()
        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Determine output file extension
        ext_map = {
            "mermaid": ".md",
            "mermaid-timeline": ".md",
            "mermaid-git": ".md",
            "ascii": ".txt",
            "ascii-graph": ".txt",
            "html": ".html",
        }

        if output_file is None:
            ext = ext_map.get(output_format, ".txt")
            output_file = f"context-graph{ext}"

        output_path = Path(output_file)

        # Generate title if not provided
        if title is None:
            config = repo.get_config()
            title = f"{config.project_name} Context Graph" if config.project_name else "Context Graph"

        with repo.get_context_store() as store:
            viz = visualize_context(
                store,
                output_format=output_format,
                limit=limit,
                event_types=list(event_types) if event_types else None,
                title=title,
                theme=theme,
                direction=direction,
                show_annotations=not no_annotations,
            )

        # Wrap Mermaid in markdown code block
        if output_format.startswith("mermaid") and output_path.suffix == ".md":
            content = f"# {title}\n\n```mermaid\n{viz}\n```\n"
        else:
            content = viz

        # Write file
        output_path.write_text(content, encoding="utf-8")

        console.print(f"[green]✓[/green] Exported to [cyan]{output_path}[/cyan]")

        # Provide viewing hints
        if output_format.startswith("mermaid"):
            console.print("[dim]View in VS Code with Mermaid preview extension[/dim]")
        elif output_format == "html":
            console.print("[dim]Open in browser or IDE HTML preview[/dim]")

    except ValueError as format_error:
        raise click.ClickException(str(format_error)) from format_error
    except Exception as export_error:
        msg = f"Export failed: {export_error}"
        raise click.ClickException(msg) from export_error


# ---- Timeline Command ----------------------------------------------------------------------------------------


@context.command()
@click.option(
    "--limit",
    "-n",
    default=20,
    help="Maximum events to display.",
)
@click.option(
    "--type",
    "-t",
    "event_types",
    multiple=True,
    type=click.Choice(["commit", "push", "pull", "merge", "branch", "diff"]),
    help="Filter by event types.",
)
def timeline(
    limit: int,
    event_types: tuple[str, ...],
) -> None:
    """Show ASCII timeline of context events.

    Displays a chronological timeline of events with annotations.
    Quick way to see recent activity history.

    Examples:
        gitmap context timeline
        gitmap context timeline -n 10
        gitmap context timeline --type commit
    """
    try:
        repo = find_repository()
        if not repo:
            raise click.ClickException("Not a GitMap repository")

        with repo.get_context_store() as store:
            viz = visualize_context(
                store,
                output_format="ascii",
                limit=limit,
                event_types=list(event_types) if event_types else None,
            )

        console.print(Panel(viz, title="Context Timeline", border_style="blue"))

    except Exception as timeline_error:
        msg = f"Timeline failed: {timeline_error}"
        raise click.ClickException(msg) from timeline_error


# ---- Graph Command -------------------------------------------------------------------------------------------


@context.command()
@click.option(
    "--limit",
    "-n",
    default=30,
    help="Maximum events to display.",
)
@click.option(
    "--type",
    "-t",
    "event_types",
    multiple=True,
    type=click.Choice(["commit", "push", "pull", "merge", "branch", "diff"]),
    help="Filter by event types.",
)
def graph(
    limit: int,
    event_types: tuple[str, ...],
) -> None:
    """Show ASCII graph of event relationships.

    Displays events with their relationships in ASCII format.
    Shows how events are connected.

    Examples:
        gitmap context graph
        gitmap context graph -n 15
    """
    try:
        repo = find_repository()
        if not repo:
            raise click.ClickException("Not a GitMap repository")

        with repo.get_context_store() as store:
            viz = visualize_context(
                store,
                output_format="ascii-graph",
                limit=limit,
                event_types=list(event_types) if event_types else None,
            )

        console.print(Panel(viz, title="Context Graph", border_style="green"))

    except Exception as graph_error:
        msg = f"Graph failed: {graph_error}"
        raise click.ClickException(msg) from graph_error
