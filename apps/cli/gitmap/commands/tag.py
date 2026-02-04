"""GitMap tag command.

Create, list, and delete tags for version marking.

Execution Context:
    CLI command - invoked via `gitmap tag`

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


# ---- Tag Command --------------------------------------------------------------------------------------------


@click.command()
@click.argument(
    "name",
    required=False,
)
@click.argument(
    "commit",
    required=False,
)
@click.option(
    "--list", "-l",
    "list_tags",
    is_flag=True,
    help="List all tags.",
)
@click.option(
    "--delete", "-d",
    "delete_tag",
    is_flag=True,
    help="Delete a tag.",
)
def tag(
        name: str | None,
        commit: str | None,
        list_tags: bool,
        delete_tag: bool,
) -> None:
    """Create, list, or delete tags.

    Tags are named references to specific commits, typically used
    for marking releases (e.g., v1.0.0, v2.0.0).

    Examples:
        gitmap tag v1.0.0              # Tag HEAD as v1.0.0
        gitmap tag v1.0.0 abc12345     # Tag specific commit
        gitmap tag --list              # List all tags
        gitmap tag -l                  # List all tags (short)
        gitmap tag --delete v1.0.0     # Delete tag
        gitmap tag -d v1.0.0           # Delete tag (short)
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # List tags
        if list_tags:
            tags = repo.list_tags()
            if not tags:
                console.print("[dim]No tags found.[/dim]")
                return

            table = Table(title="Tags")
            table.add_column("Tag", style="cyan")
            table.add_column("Commit", style="green")
            table.add_column("Message", style="dim")

            for tag_name in tags:
                commit_id = repo.get_tag(tag_name)
                if commit_id:
                    commit_obj = repo.get_commit(commit_id)
                    message = commit_obj.message.split("\n")[0][:50] if commit_obj else ""
                    table.add_row(tag_name, commit_id[:8], message)
                else:
                    table.add_row(tag_name, "???", "")

            console.print(table)
            return

        # Delete tag
        if delete_tag:
            if not name:
                raise click.ClickException("Tag name required for delete")

            repo.delete_tag(name)
            console.print(f"[green]Deleted tag '{name}'[/green]")
            return

        # Create tag
        if not name:
            # No name and no flags - show usage
            raise click.ClickException(
                "Usage: gitmap tag <name> [commit] or gitmap tag --list"
            )

        commit_id = repo.create_tag(name, commit)
        commit_obj = repo.get_commit(commit_id)

        console.print(f"[green]Created tag '{name}'[/green]")
        console.print(f"  [bold]Commit:[/bold] {commit_id[:8]}")
        if commit_obj:
            console.print(f"  [bold]Message:[/bold] {commit_obj.message.split(chr(10))[0]}")

    except Exception as tag_error:
        msg = f"Tag operation failed: {tag_error}"
        raise click.ClickException(msg) from tag_error
