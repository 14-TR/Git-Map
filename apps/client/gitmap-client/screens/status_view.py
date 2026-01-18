"""Status View Screen.

Displays detailed repository status including branch info,
modified files, and staging area.

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from gitmap_core.repository import Repository


class StatusViewScreen(Screen):
    """Status view screen showing repository state.

    Displays comprehensive repository status information:
    - Current branch and HEAD
    - Modified files in working directory
    - Staged changes in index
    - Remote synchronization status
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", key_display="ESC"),
        Binding("r", "refresh", "Refresh", key_display="R"),
    ]

    def __init__(
            self,
            repo: Repository,
    ) -> None:
        """Initialize status view.

        Args:
            repo: GitMap repository instance.
        """
        super().__init__()
        self.repo = repo

    def compose(
            self,
    ) -> ComposeResult:
        """Compose status view widgets.

        Yields:
            UI widgets for status display.
        """
        yield Header()
        with Container():
            with Vertical():
                yield Static("Repository Status", classes="title")
                yield Static("", id="status-content")
        yield Footer()

    def on_mount(
            self,
    ) -> None:
        """Refresh status when screen mounts."""
        self.action_refresh()

    def action_refresh(
            self,
    ) -> None:
        """Refresh status display."""
        try:
            # Get current branch
            current_branch = self.repo.current_branch()
            if not current_branch:
                current_branch = "No branch (detached HEAD)"

            # Get HEAD commit
            head_ref = self.repo.head()
            head_commit = self.repo.get_commit(head_ref) if head_ref else None

            # Get branches
            branches = self.repo.list_branches()

            # Get index status
            index_data = self.repo.get_index()

            # Build status output
            status_lines = [
                f"[bold cyan]On branch:[/bold cyan] {current_branch}",
                "",
            ]

            if head_commit:
                status_lines.extend([
                    f"[bold yellow]Latest commit:[/bold yellow]",
                    f"  ID: {head_commit.id[:12]}",
                    f"  Message: {head_commit.message}",
                    f"  Author: {head_commit.author}",
                    f"  Date: {head_commit.timestamp}",
                    "",
                ])
            else:
                status_lines.extend([
                    "[dim]No commits yet[/dim]",
                    "",
                ])

            # Show branches
            status_lines.extend([
                f"[bold green]Branches:[/bold green] ({len(branches)})",
            ])
            for branch_name in branches[:10]:  # Show first 10
                marker = "*" if branch_name == current_branch else " "
                status_lines.append(f"  {marker} {branch_name}")
            if len(branches) > 10:
                status_lines.append(f"  ... and {len(branches) - 10} more")
            status_lines.append("")

            # Show index status
            if index_data:
                status_lines.extend([
                    "[bold magenta]Staged changes:[/bold magenta]",
                    "  Map data is staged for commit",
                    "",
                ])
            else:
                status_lines.extend([
                    "[dim]No staged changes[/dim]",
                    "",
                ])

            # Show remote configuration
            config = self.repo.get_config()
            if config.remote:
                status_lines.extend([
                    "[bold blue]Remote:[/bold blue]",
                    f"  Name: {config.remote.name}",
                    f"  URL: {config.remote.url}",
                    "",
                ])

            # Update display
            content = self.query_one("#status-content", Static)
            content.update("\n".join(status_lines))

            self.notify("Status refreshed", severity="information", timeout=2)

        except Exception as status_error:
            self.notify(
                f"Error loading status: {status_error}",
                severity="error",
                timeout=5,
            )
