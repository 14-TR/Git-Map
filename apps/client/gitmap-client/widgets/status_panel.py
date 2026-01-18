"""Status Panel Widget.

Displays current repository status in the sidebar.
Shows current branch, HEAD commit, and recent activity.

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from gitmap_core.repository import Repository


class StatusPanel(Vertical):
    """Status panel widget showing repository information.

    Displays:
        - Current branch
        - HEAD commit
        - Modified files count
        - Quick navigation links
    """

    def compose(
            self,
    ) -> ComposeResult:
        """Compose status panel widgets.

        Yields:
            Static text widgets with repository status.
        """
        yield Static("Repository Status", classes="panel-title")
        yield Static("No repository loaded", id="repo-info")

    def on_mount(
            self,
    ) -> None:
        """Initialize panel on mount."""
        self.set_interval(2.0, self.refresh_status)

    def refresh_status(
            self,
    ) -> None:
        """Refresh repository status display."""
        try:
            # Get repository from app
            repo = self.app.repo
            if not repo:
                return

            # Get current branch
            current_branch = repo.current_branch()
            if not current_branch:
                current_branch = "No branch"

            # Get HEAD commit
            head_commit = repo.get_commit(repo.head())
            commit_short = head_commit.id[:8] if head_commit else "No commits"

            # Build status text
            status_lines = [
                f"[bold cyan]Branch:[/bold cyan] {current_branch}",
                f"[bold yellow]HEAD:[/bold yellow] {commit_short}",
                "",
                "[dim]Press ? for help[/dim]",
            ]

            # Update widget
            info_widget = self.query_one("#repo-info", Static)
            info_widget.update("\n".join(status_lines))

        except Exception:
            # Silently fail if repo not available
            pass
