"""GitMap auto-pull command.

Automatically pulls updates for all bitmap repositories in a directory.
Scans for .gitmap repositories and updates them from Portal.

Execution Context:
    CLI command - invoked via `gitmap auto-pull`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository and connection management

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import Repository

from .utils import get_portal_url

console = Console()


# ---- Auto-Pull Command --------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--directory",
    "-d",
    default="repositories",
    help="Directory containing bitmap repositories (defaults to 'repositories').",
)
@click.option(
    "--branch",
    "-b",
    default="main",
    help="Branch to pull for each repository (defaults to 'main').",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (or use PORTAL_URL env var).",
)
@click.option(
    "--username",
    default="",
    help="Portal username (or use ARCGIS_USERNAME env var).",
)
@click.option(
    "--password",
    default="",
    help="Portal password (or use ARCGIS_PASSWORD env var).",
)
@click.option(
    "--skip-errors",
    is_flag=True,
    default=True,
    help="Continue pulling other repos if one fails (default: True).",
)
@click.option(
    "--auto-commit",
    is_flag=True,
    default=False,
    help="Automatically commit changes after successful pull (default: False).",
)
@click.option(
    "--commit-message",
    "-m",
    default="",
    help="Custom commit message template (use {repo} for repository name, {date} for timestamp).",
)
def auto_pull(
        directory: str,
        branch: str,
        url: str,
        username: str,
        password: str,
        skip_errors: bool,
        auto_commit: bool,
        commit_message: str,
) -> None:
    """Automatically pull updates for all bitmap repositories.

    Scans a directory for GitMap repositories and pulls the latest changes
    from Portal for each one. Useful for keeping multiple local repositories
    in sync with their Portal counterparts.

    Optionally auto-commits changes after successful pulls using the --auto-commit flag.

    Examples:
        gitmap auto-pull
        gitmap auto-pull --directory my-repos
        gitmap auto-pull --branch main --skip-errors
        gitmap auto-pull --directory repositories --url https://portal.example.com
        gitmap auto-pull --auto-commit
        gitmap auto-pull --auto-commit --commit-message "Auto-pull from Portal on {date}"
    """
    try:
        # Resolve base directory
        base_dir = Path(directory).resolve()

        if not base_dir.exists():
            raise click.ClickException(
                f"Directory '{base_dir}' does not exist. "
                f"Create it with 'gitmap setup-repos' or specify a different directory."
            )

        if not base_dir.is_dir():
            raise click.ClickException(f"'{base_dir}' is not a directory")

        console.print(f"[dim]Scanning for GitMap repositories in {base_dir}...[/dim]")

        # Find all GitMap repositories
        repos_to_pull = []
        for item in base_dir.iterdir():
            if item.is_dir():
                gitmap_dir = item / ".gitmap"
                if gitmap_dir.exists() and gitmap_dir.is_dir():
                    repos_to_pull.append(item)

        if not repos_to_pull:
            console.print(f"[yellow]No GitMap repositories found in '{base_dir}'[/yellow]")
            console.print()
            console.print("[dim]Tip: Use 'gitmap setup-repos' to clone multiple repositories[/dim]")
            return

        console.print(f"[bold]Found {len(repos_to_pull)} repository/repositories[/bold]")
        console.print()

        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url if url else None)

        # Connect to Portal once (reuse connection for all pulls)
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
            password=password if password else None,
        )

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        console.print()

        # Pull each repository
        success_count = 0
        skipped_count = 0
        failed_repos = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for idx, repo_path in enumerate(repos_to_pull, 1):
                repo_name = repo_path.name

                task = progress.add_task(
                    f"[{idx}/{len(repos_to_pull)}] Pulling '{repo_name}'...",
                    total=None
                )

                try:
                    # Load repository
                    repo = Repository(repo_path)

                    # Get the target branch (use specified branch or current branch)
                    current_branch = repo.get_current_branch()

                    # Check if we should use the specified branch or current branch
                    branches = repo.list_branches()
                    if branch in branches:
                        target_branch = branch
                    elif current_branch:
                        target_branch = current_branch
                    else:
                        # No valid branch found
                        progress.update(
                            task,
                            description=f"[{idx}/{len(repos_to_pull)}] ⊘ Skipped '{repo_name}' (no branches found)"
                        )
                        skipped_count += 1
                        continue

                    # Perform pull
                    remote_ops = RemoteOperations(repo, connection)
                    map_data = remote_ops.pull(target_branch)

                    # Get layer count for summary
                    layers = map_data.get("operationalLayers", [])
                    layer_count = len(layers)

                    # Auto-commit if enabled
                    commit_id = None
                    if auto_commit:
                        # Check if there are changes to commit
                        if repo.has_uncommitted_changes():
                            # Generate commit message
                            if commit_message:
                                # Replace template variables
                                msg = commit_message.replace("{repo}", repo_name)
                                msg = msg.replace("{date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            else:
                                # Default commit message
                                msg = f"Auto-pull from Portal ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                            
                            # Create commit
                            new_commit = repo.create_commit(
                                message=msg,
                                author=None,
                                rationale=None,
                            )
                            commit_id = new_commit.id[:8]

                    # Update progress display
                    if commit_id:
                        progress.update(
                            task,
                            description=f"[{idx}/{len(repos_to_pull)}] ✓ Pulled & Committed '{repo_name}' ({layer_count} layers, {commit_id})"
                        )
                    else:
                        progress.update(
                            task,
                            description=f"[{idx}/{len(repos_to_pull)}] ✓ Pulled '{repo_name}' ({layer_count} layers)"
                        )
                    success_count += 1

                except Exception as pull_error:
                    if skip_errors:
                        progress.update(
                            task,
                            description=f"[{idx}/{len(repos_to_pull)}] ✗ Failed '{repo_name}'"
                        )
                        failed_repos.append({
                            "name": repo_name,
                            "path": str(repo_path),
                            "error": str(pull_error),
                        })
                    else:
                        raise click.ClickException(
                            f"Pull failed for '{repo_name}': {pull_error}"
                        ) from pull_error

        # Display summary
        console.print()
        console.print("[bold]═" * 60 + "[/bold]")
        console.print("[bold]Summary[/bold]")
        console.print("[bold]═" * 60 + "[/bold]")
        console.print(f"  [green]✓ Successfully pulled:[/green] {success_count}")

        if skipped_count > 0:
            console.print(f"  [yellow]⊘ Skipped (no '{branch}' branch):[/yellow] {skipped_count}")

        if failed_repos:
            console.print(f"  [red]✗ Failed:[/red] {len(failed_repos)}")
            console.print()
            console.print("[bold red]Failed Repositories:[/bold red]")
            for failed in failed_repos:
                console.print(f"  • {failed['name']}")
                console.print(f"    [dim]Path: {failed['path']}[/dim]")
                console.print(f"    [dim]Error: {failed['error']}[/dim]")

        console.print()
        if success_count > 0:
            console.print("[dim]All repositories updated successfully![/dim]")
            console.print()
            if auto_commit:
                console.print("[dim]Changes have been automatically committed.[/dim]")
                console.print("[dim]Use 'gitmap log' in each repo to review commits.[/dim]")
            else:
                console.print("[dim]Note: Changes are staged but not committed.[/dim]")
                console.print("[dim]Use 'gitmap diff' and 'gitmap commit' in each repo to review and save changes.[/dim]")
                console.print("[dim]Tip: Use '--auto-commit' flag to automatically commit changes.[/dim]")

    except Exception as auto_pull_error:
        msg = f"Auto-pull failed: {auto_pull_error}"
        raise click.ClickException(msg) from auto_pull_error
