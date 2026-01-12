"""GitMap push command.

Pushes local branch to ArcGIS Portal.

Execution Context:
    CLI command - invoked via `gitmap push`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Remote operations

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os

import click
from rich.console import Console

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import find_repository

console = Console()


# ---- Push Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--branch",
    "-b",
    default="",
    help="Branch to push (defaults to current branch).",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (uses configured remote if not specified).",
)
@click.option(
    "--username",
    default="",
    help="Portal username (or use ARCGIS_USERNAME env var).",
)
@click.option(
    "--no-notify",
    is_flag=True,
    help="Skip sending notifications even if pushing to production branch.",
)
@click.option(
    "--rationale",
    "-r",
    default="",
    help="Optional rationale explaining why this push is being made.",
)
def push(
        branch: str,
        url: str,
        username: str,
        no_notify: bool,
        rationale: str,
) -> None:
    """Push branch to ArcGIS Portal.

    Uploads the current branch as a web map item in Portal. Creates
    a GitMap folder to organize branch items.

    If the branch is configured as the production branch, notifications
    will be sent to all users in groups that have access to the map.
    Use --no-notify to skip notifications for this push.

    Examples:
        gitmap push
        gitmap push --branch feature/new-layer
        gitmap push --url https://portal.example.com
        gitmap push --no-notify  # Skip notifications even for production branch
        gitmap push -r "Deploying accessibility improvements"
    """
    try:
        repo = find_repository()

        if not repo:
            raise click.ClickException("Not a GitMap repository")

        # Determine Portal URL
        config = repo.get_config()
        portal_url = url or (config.remote.url if config.remote else os.environ.get("PORTAL_URL", "https://www.arcgis.com"))

        # Connect to Portal
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
        )

        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # Perform push
        target_branch = branch or repo.get_current_branch()
        console.print(f"[dim]Pushing branch '{target_branch}'...[/dim]")

        remote_ops = RemoteOperations(repo, connection)
        item, notification_status = remote_ops.push(target_branch, skip_notifications=no_notify)

        # Display result
        console.print()
        console.print(f"[green]Pushed '{target_branch}' to Portal[/green]")
        console.print()
        console.print(f"  [bold]Item ID:[/bold] {item.id}")
        console.print(f"  [bold]Title:[/bold] {item.title}")
        console.print(f"  [bold]URL:[/bold] {item.homepage}")
        
        # Display notification status
        if notification_status["attempted"]:
            console.print()
            if notification_status["sent"]:
                users_count = len(notification_status["users_notified"])
                console.print(f"[green]✓ Notifications sent to {users_count} user(s)[/green]")
                if users_count <= 10:  # Show usernames if not too many
                    console.print(f"  [dim]Users: {', '.join(notification_status['users_notified'])}[/dim]")
            else:
                console.print(f"[yellow]⚠ Notifications not sent[/yellow]")
                if notification_status["reason"]:
                    console.print(f"  [dim]Reason: {notification_status['reason']}[/dim]")
                console.print(f"  [dim]Tip: Share the map with groups that have members to receive notifications[/dim]")

        # Record event in context store (non-blocking)
        try:
            with repo.get_context_store() as store:
                store.record_event(
                    event_type="push",
                    repo=str(repo.root),
                    ref=target_branch,
                    actor=connection.username,
                    payload={
                        "item_id": item.id,
                        "item_title": item.title,
                        "portal_url": portal_url,
                        "branch": target_branch,  # Track which branch was pushed
                    },
                    rationale=rationale if rationale else None,
                )
            
            # Auto-regenerate context graph if enabled
            config = repo.get_config()
            if config.auto_visualize:
                repo.regenerate_context_graph()
            
            if rationale:
                console.print()
                console.print(f"  [bold]Rationale:[/bold] {rationale}")
        except Exception:
            pass  # Don't fail push if context recording fails

    except Exception as push_error:
        msg = f"Push failed: {push_error}"
        raise click.ClickException(msg) from push_error


