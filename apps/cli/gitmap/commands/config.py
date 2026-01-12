"""GitMap config command.

Manages repository configuration settings.

Execution Context:
    CLI command - invoked via `gitmap config`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import click
from rich.console import Console

from gitmap_core.repository import find_repository

console = Console()


# ---- Config Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--production-branch",
    "-p",
    default="",
    help="Set the production branch name (branch that triggers notifications on push).",
)
@click.option(
    "--unset-production",
    is_flag=True,
    help="Remove the production branch setting.",
)
@click.option(
    "--auto-visualize/--no-auto-visualize",
    "auto_visualize",
    default=None,
    help="Enable/disable automatic context graph regeneration after events.",
)
def config(
        production_branch: str,
        unset_production: bool,
        auto_visualize: bool | None,
) -> None:
    """Manage repository configuration settings.

    Examples:
        gitmap config --production-branch main
        gitmap config --production-branch release/1.0.0
        gitmap config --unset-production
        gitmap config --auto-visualize
        gitmap config --no-auto-visualize
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        config_obj = repo.get_config()
        changes_made = False

        # Remote-specific options require remote to be configured
        if (unset_production or production_branch) and not config_obj.remote:
            raise click.ClickException("No remote configured. Use 'gitmap clone' first.")

        if unset_production:
            if config_obj.remote:
                config_obj.remote.production_branch = None
                changes_made = True
                console.print("[green]Production branch setting removed[/green]")

        if production_branch:
            if config_obj.remote:
                config_obj.remote.production_branch = production_branch
                changes_made = True
                console.print(f"[green]Production branch set to '{production_branch}'[/green]")
                console.print("[dim]Pushes to this branch will trigger notifications to all users in map groups[/dim]")

        if auto_visualize is not None:
            config_obj.auto_visualize = auto_visualize
            changes_made = True
            if auto_visualize:
                console.print("[green]Auto-visualization enabled[/green]")
                console.print("[dim]Context graph will regenerate after commits and other events[/dim]")
            else:
                console.print("[green]Auto-visualization disabled[/green]")

        if changes_made:
            repo.update_config(config_obj)
        else:
            # Show current configuration
            console.print("[bold]Repository Configuration:[/bold]")
            console.print()
            console.print(f"  [bold]Project:[/bold] {config_obj.project_name}")
            if config_obj.remote:
                console.print(f"  [bold]Remote URL:[/bold] {config_obj.remote.url}")
                if config_obj.remote.production_branch:
                    console.print(f"  [bold]Production Branch:[/bold] {config_obj.remote.production_branch}")
                else:
                    console.print("  [bold]Production Branch:[/bold] [dim](not set)[/dim]")
            console.print(f"  [bold]Auto-Visualize:[/bold] {'enabled' if config_obj.auto_visualize else 'disabled'}")
            console.print()

    except Exception as config_error:
        msg = f"Config operation failed: {config_error}"
        raise click.ClickException(msg) from config_error

