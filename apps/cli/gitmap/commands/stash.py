"""GitMap stash command.

Save and restore work-in-progress changes.

Execution Context:
    CLI command - invoked via `gitmap stash`

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
from rich.table import Table

from gitmap_core.repository import find_repository

console = Console()


# ---- Stash Command Group ------------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option(
    "--message", "-m",
    default=None,
    help="Message describing the stash (for push).",
)
@click.pass_context
def stash(
        ctx: click.Context,
        message: str | None,
) -> None:
    """Save and restore work-in-progress changes.

    Without subcommand, defaults to 'push' (save current changes).

    Examples:
        gitmap stash                   # Push current changes
        gitmap stash -m "WIP feature"  # Push with message
        gitmap stash pop               # Apply and remove top stash
        gitmap stash list              # List all stashes
        gitmap stash drop              # Remove top stash without applying
        gitmap stash clear             # Remove all stashes
    """
    if ctx.invoked_subcommand is None:
        # Default to push
        ctx.invoke(stash_push, message=message)


@stash.command(name="push")
@click.option(
    "--message", "-m",
    default=None,
    help="Message describing the stash.",
)
def stash_push(
        message: str | None,
) -> None:
    """Save current index state to the stash stack.

    Saves uncommitted changes and restores the index to HEAD state.

    Examples:
        gitmap stash push
        gitmap stash push -m "Work in progress on feature X"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        stash_entry = repo.stash_push(message=message)

        console.print(f"[green]Saved working directory and index state[/green]")
        console.print(f"  [bold]Stash:[/bold] {stash_entry['id']}")
        console.print(f"  [bold]Message:[/bold] {stash_entry['message']}")

        if stash_entry.get("branch"):
            console.print(f"  [bold]Branch:[/bold] {stash_entry['branch']}")

    except Exception as stash_error:
        msg = f"Stash failed: {stash_error}"
        raise click.ClickException(msg) from stash_error


@stash.command(name="pop")
@click.argument(
    "index",
    type=int,
    default=0,
    required=False,
)
def stash_pop(
        index: int,
) -> None:
    """Apply and remove a stash entry.

    INDEX is the stash index (0 = most recent, default).

    Examples:
        gitmap stash pop        # Apply most recent stash
        gitmap stash pop 1      # Apply second most recent
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        stash_entry = repo.stash_pop(index=index)

        console.print(f"[green]Applied stash and removed from list[/green]")
        console.print(f"  [bold]Stash:[/bold] {stash_entry.get('id', 'unknown')}")
        console.print(f"  [bold]Message:[/bold] {stash_entry['message']}")

        # Show what was restored
        layers = stash_entry.get("index_data", {}).get("operationalLayers", [])
        console.print(f"  [bold]Layers:[/bold] {len(layers)}")

    except Exception as stash_error:
        msg = f"Stash pop failed: {stash_error}"
        raise click.ClickException(msg) from stash_error


@stash.command(name="list")
def stash_list() -> None:
    """List all stash entries.

    Shows all saved stashes with their index, ID, and message.

    Examples:
        gitmap stash list
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        stashes = repo.stash_list()

        if not stashes:
            console.print("[dim]No stash entries.[/dim]")
            return

        table = Table(title="Stash List")
        table.add_column("Index", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Branch", style="yellow")
        table.add_column("Message", style="dim")

        for i, stash_ref in enumerate(stashes):
            table.add_row(
                str(i),
                stash_ref.get("id", "unknown"),
                stash_ref.get("branch", ""),
                stash_ref.get("message", "")[:50],
            )

        console.print(table)

    except Exception as stash_error:
        msg = f"Stash list failed: {stash_error}"
        raise click.ClickException(msg) from stash_error


@stash.command(name="drop")
@click.argument(
    "index",
    type=int,
    default=0,
    required=False,
)
def stash_drop(
        index: int,
) -> None:
    """Remove a stash entry without applying.

    INDEX is the stash index (0 = most recent, default).

    Examples:
        gitmap stash drop       # Drop most recent stash
        gitmap stash drop 1     # Drop second most recent
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        stash_ref = repo.stash_drop(index=index)

        console.print(f"[green]Dropped stash[/green]")
        console.print(f"  [bold]Stash:[/bold] {stash_ref.get('id', 'unknown')}")
        console.print(f"  [bold]Message:[/bold] {stash_ref.get('message', '')}")

    except Exception as stash_error:
        msg = f"Stash drop failed: {stash_error}"
        raise click.ClickException(msg) from stash_error


@stash.command(name="clear")
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Skip confirmation prompt.",
)
def stash_clear(
        force: bool,
) -> None:
    """Remove all stash entries.

    Permanently deletes all saved stashes.

    Examples:
        gitmap stash clear
        gitmap stash clear --force
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        stashes = repo.stash_list()
        if not stashes:
            console.print("[dim]No stash entries to clear.[/dim]")
            return

        if not force:
            console.print(f"[yellow]This will remove {len(stashes)} stash entry(ies).[/yellow]")
            if not click.confirm("Continue?", default=False):
                console.print("[dim]Clear cancelled.[/dim]")
                return

        count = repo.stash_clear()

        console.print(f"[green]Cleared {count} stash entry(ies)[/green]")

    except Exception as stash_error:
        msg = f"Stash clear failed: {stash_error}"
        raise click.ClickException(msg) from stash_error
