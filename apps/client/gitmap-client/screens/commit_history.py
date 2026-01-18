"""Commit History Screen.

Displays visual commit history with branch graph.
Shows commit details, author, timestamp, and relationships.

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from gitmap_core.repository import Repository


class CommitHistoryScreen(Screen):
    """Commit history screen showing log of commits.

    Displays:
    - Visual commit graph
    - Commit messages
    - Author information
    - Timestamps
    - Branch markers
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", key_display="ESC"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("j", "cursor_down", "Down", key_display="J"),
        Binding("k", "cursor_up", "Up", key_display="K"),
    ]

    def __init__(
            self,
            repo: Repository,
    ) -> None:
        """Initialize commit history view.

        Args:
            repo: GitMap repository instance.
        """
        super().__init__()
        self.repo = repo
        self.commits = []

    def compose(
            self,
    ) -> ComposeResult:
        """Compose commit history widgets.

        Yields:
            UI widgets for commit history display.
        """
        yield Header()
        with Container():
            with Vertical():
                yield Static("Commit History", classes="title")
                with VerticalScroll(id="commit-container"):
                    yield Static("", id="commit-list")
        yield Footer()

    def on_mount(
            self,
    ) -> None:
        """Load commits when screen mounts."""
        self.action_refresh()

    def action_refresh(
            self,
    ) -> None:
        """Refresh commit history display."""
        try:
            # Get current branch
            current_branch = self.repo.current_branch()
            if not current_branch:
                self.notify("No branch checked out", severity="warning")
                return

            # Get branch reference
            branch_ref = self.repo.get_branch(current_branch)
            if not branch_ref or not branch_ref.commit_id:
                self.notify("No commits in current branch", severity="information")
                return

            # Get commit history
            self.commits = []
            commit_id = branch_ref.commit_id

            # Traverse commit history (up to 50 commits)
            max_commits = 50
            while commit_id and len(self.commits) < max_commits:
                commit = self.repo.get_commit(commit_id)
                if not commit:
                    break
                self.commits.append(commit)
                commit_id = commit.parent

            # Build visual commit log
            log_lines = [
                f"[bold cyan]Branch:[/bold cyan] {current_branch}",
                f"[dim]Showing {len(self.commits)} commits[/dim]",
                "",
            ]

            for idx, commit in enumerate(self.commits):
                # Visual graph connector
                if idx == 0:
                    graph = "●"
                else:
                    graph = "│"

                # Commit info
                short_id = commit.id[:8]
                short_msg = commit.message[:60] + "..." if len(commit.message) > 60 else commit.message
                author_short = commit.author.split()[0] if commit.author else "Unknown"

                # Format timestamp
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(commit.timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    time_str = commit.timestamp[:16]

                # Build commit line
                log_lines.append(
                    f"[yellow]{graph}[/yellow] [bold cyan]{short_id}[/bold cyan] "
                    f"[green]{short_msg}[/green]"
                )
                log_lines.append(
                    f"  [dim]{author_short} • {time_str}[/dim]"
                )
                log_lines.append("")

            # Update display
            content = self.query_one("#commit-list", Static)
            content.update("\n".join(log_lines))

            self.notify("Commit history refreshed", severity="information", timeout=2)

        except Exception as log_error:
            self.notify(
                f"Error loading commits: {log_error}",
                severity="error",
                timeout=5,
            )

    def action_cursor_down(
            self,
    ) -> None:
        """Move selection down (future enhancement)."""
        pass

    def action_cursor_up(
            self,
    ) -> None:
        """Move selection up (future enhancement)."""
        pass
