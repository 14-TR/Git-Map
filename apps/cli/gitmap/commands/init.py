"""GitMap init command.

Initializes a new GitMap repository in the current directory,
creating the .gitmap directory structure.

Execution Context:
    CLI command - invoked via `gitmap init`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from gitmap_core.repository import Repository

console = Console()


# ---- Init Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--project-name",
    "-n",
    default="",
    help="Project name (defaults to directory name).",
)
@click.option(
    "--user-name",
    "-u",
    default="",
    help="Default author name for commits.",
)
@click.option(
    "--user-email",
    "-e",
    default="",
    help="Default author email for commits.",
)
@click.argument(
    "path",
    type=click.Path(),
    default=".",
    required=False,
)
def init(
        path: str,
        project_name: str,
        user_name: str,
        user_email: str,
) -> None:
    """Initialize a new GitMap repository.

    Creates a .gitmap directory structure in the specified PATH
    (defaults to current directory).

    Example:
        gitmap init
        gitmap init --project-name "My Project" --user-name "John Doe"
        gitmap init /path/to/project
    """
    try:
        repo_path = Path(path).resolve()
        repo = Repository(repo_path)

        if repo.exists():
            console.print(
                f"[yellow]GitMap repository already exists at {repo.gitmap_dir}[/yellow]"
            )
            return

        repo.init(
            project_name=project_name,
            user_name=user_name,
            user_email=user_email,
        )

        console.print(
            f"[green]Initialized empty GitMap repository in {repo.gitmap_dir}[/green]"
        )
        console.print()
        console.print("Repository structure created:")
        console.print(f"  [dim]{repo.gitmap_dir}/[/dim]")
        console.print(f"    [dim]├── config.json[/dim]")
        console.print(f"    [dim]├── HEAD[/dim]")
        console.print(f"    [dim]├── index.json[/dim]")
        console.print(f"    [dim]├── refs/heads/main[/dim]")
        console.print(f"    [dim]└── objects/commits/[/dim]")

    except Exception as init_error:
        msg = f"Failed to initialize repository: {init_error}"
        raise click.ClickException(msg) from init_error


