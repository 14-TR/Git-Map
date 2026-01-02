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
def config(
        production_branch: str,
        unset_production: bool,
) -> None:
    """Manage repository configuration settings.

    Examples:
        gitmap config --production-branch main
        gitmap config --production-branch release/1.0.0
        gitmap config --unset-production
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        config_obj = repo.get_config()

        if not config_obj.remote:
            raise click.ClickException("No remote configured. Use 'gitmap clone' first.")

        if unset_production:
            config_obj.remote.production_branch = None
            repo.update_config(config_obj)
            console.print("[green]Production branch setting removed[/green]")
        elif production_branch:
            config_obj.remote.production_branch = production_branch
            repo.update_config(config_obj)
            console.print(f"[green]Production branch set to '{production_branch}'[/green]")
            console.print("[dim]Pushes to this branch will trigger notifications to all users in map groups[/dim]")
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
            console.print()

    except Exception as config_error:
        msg = f"Config operation failed: {config_error}"
        raise click.ClickException(msg) from config_error

