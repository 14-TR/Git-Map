"""Send ArcGIS notifications to group members.

The notify command connects to ArcGIS Online/Enterprise using the
existing GitMap authentication helpers, gathers usernames for all
members of the specified group, and dispatches a message via the ArcGIS
`Group.notify` API (no SMTP configuration required).

Execution Context:
    CLI command - invoked via `gitmap notify`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Portal connection and communication helpers

Metadata:
    Version: 0.2.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from gitmap_core.communication import get_group_member_usernames
from gitmap_core.communication import list_groups
from gitmap_core.communication import send_group_notification
from gitmap_core.connection import get_connection

from .utils import get_portal_url

console = Console()


# ---- Notify Command -------------------------------------------------------------------------------------------


@click.command()
@click.option(
    "--group",
    "-g",
    default="",
    help="Group ID or title to target for notifications.",
)
@click.option(
    "--user",
    multiple=True,
    help="Specific username(s) to notify (can be used multiple times). If omitted, all group members are notified.",
)
@click.option(
    "--subject",
    "-s",
    default="",
    help="Notification subject line.",
)
@click.option(
    "--list-groups",
    "-l",
    "list_groups_flag",
    is_flag=True,
    help="List all available groups and exit.",
)
@click.option(
    "--message",
    "-m",
    default="",
    help="Notification body text (use --message-file to load from a file).",
)
@click.option(
    "--message-file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="Path to a file containing the notification body.",
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Portal URL (or use PORTAL_URL env var, which is required).",
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
def notify(
        group: str,
        user: tuple[str, ...],
        subject: str,
        message: str,
        message_file: Optional[Path],
        url: str,
        username: str,
        password: str,
        list_groups_flag: bool,
) -> None:
    """Send a notification to group members using ArcGIS APIs.
    
    By default, notifies all members of the specified group. Use --user
    to target specific users (useful for testing).
    
    Use --list-groups to query and display all available groups.
    """
    # Handle list groups mode
    if list_groups_flag:
        try:
            # Get Portal URL from parameter or environment variable
            portal_url = get_portal_url(url if url else None)
            
            # Connect to Portal/AGOL
            console.print(f"[dim]Connecting to {portal_url}...[/dim]")
            connection = get_connection(
                url=portal_url,
                username=username if username else None,
                password=password if password else None,
            )
            if connection.username:
                console.print(f"[dim]Authenticated as {connection.username}[/dim]")

            console.print("[dim]Querying available groups...[/dim]")
            groups = list_groups(connection.gis)

            if not groups:
                console.print("[dim]No groups found.[/dim]")
                return

            # Display groups in a table
            table = Table(title="Available Groups")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="green")
            table.add_column("Owner", style="yellow")

            for group_info in groups:
                table.add_row(
                    group_info.get("id", ""),
                    group_info.get("title", ""),
                    group_info.get("owner", ""),
                )

            console.print()
            console.print(table)
        except Exception as list_error:
            msg = f"Failed to list groups: {list_error}"
            raise click.ClickException(msg) from list_error
        return

    # Notification mode
    try:
        # Validate required parameters for notification mode
        if not group:
            raise click.ClickException("Group is required (use --group or --list-groups to see available groups).")
        if not subject:
            raise click.ClickException("Subject is required (use --subject).")

        body = _load_message_body(message, message_file)
        if not body:
            raise click.ClickException("Notification body is required (use --message or --message-file).")

        # Get Portal URL from parameter or environment variable
        portal_url = get_portal_url(url if url else None)
        
        # Connect to Portal/AGOL
        console.print(f"[dim]Connecting to {portal_url}...[/dim]")
        connection = get_connection(
            url=portal_url,
            username=username if username else None,
            password=password if password else None,
        )
        if connection.username:
            console.print(f"[dim]Authenticated as {connection.username}[/dim]")

        # Determine recipients
        if user:
            # Use specified users
            recipients = list(user)
            console.print(f"[dim]Targeting {len(recipients)} specified user(s): {', '.join(recipients)}[/dim]")
        else:
            # Get all group members
            recipients = get_group_member_usernames(connection.gis, group)
            console.print(f"[dim]Found {len(recipients)} member(s) in group '{group}'.[/dim]")

        notified_users = send_group_notification(
            gis=connection.gis,
            group_id_or_title=group,
            subject=subject,
            body=body,
            users=recipients,
        )

        console.print()
        console.print("[green]Notification sent successfully via ArcGIS.[/green]")
        console.print(f"  [bold]Group:[/bold] {group}")
        console.print(f"  [bold]Users:[/bold] {', '.join(notified_users)}")
    except Exception as notify_error:
        msg = f"Notification failed: {notify_error}"
        raise click.ClickException(msg) from notify_error


def _load_message_body(inline_message: str, message_file: Optional[Path]) -> str:
    """Resolve the notification body content from CLI parameters."""
    if message_file:
        return message_file.read_text(encoding="utf-8")
    return inline_message


