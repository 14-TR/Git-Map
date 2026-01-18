"""GitMap Client TUI Application.

Main application entry point for the GitMap terminal user interface.
Provides an interactive visual interface for GitMap operations.

Execution Context:
    TUI application - run via `gitmap-client` command

Dependencies:
    - textual: TUI framework
    - gitmap_core: Core library
    - rich: Terminal formatting

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from gitmap_core.repository import find_repository

from gitmap_client.screens.commit_history import CommitHistoryScreen
from gitmap_client.screens.status_view import StatusViewScreen
from gitmap_client.widgets.status_panel import StatusPanel

console = Console()


# ---- Main Application ---------------------------------------------------------------------------------------


class GitMapClient(App):
    """GitMap TUI Client Application.

    Interactive terminal interface for GitMap version control.
    Provides visual navigation of commits, branches, and Portal operations.
    """

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
    }

    #content {
        width: 1fr;
    }

    .title {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("s", "show_status", "Status", key_display="S"),
        Binding("l", "show_log", "Log", key_display="L"),
        Binding("b", "show_branches", "Branches", key_display="B"),
        Binding("?", "show_help", "Help", key_display="?"),
    ]

    TITLE = "GitMap Client"
    SUB_TITLE = "Version Control for ArcGIS Web Maps"

    def __init__(
            self,
            repo_path: Path | None = None,
    ) -> None:
        """Initialize GitMap Client.

        Args:
            repo_path: Path to GitMap repository (optional, will search current directory).
        """
        super().__init__()
        self.repo_path = repo_path
        self.repo = None

    def compose(
            self,
    ) -> ComposeResult:
        """Compose the UI layout.

        Yields:
            UI widgets in layout order.
        """
        yield Header()
        with Container(id="main-container"):
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Static("GitMap Client", classes="title")
                    yield StatusPanel()
                with Vertical(id="content"):
                    yield Static("Welcome to GitMap Client", id="content-area")
        yield Footer()

    def on_mount(
            self,
    ) -> None:
        """Handle application mount event.

        Initializes repository connection and validates GitMap directory.
        """
        try:
            # Find repository
            if self.repo_path:
                from gitmap_core.repository import Repository
                self.repo = Repository(self.repo_path)
            else:
                self.repo = find_repository()

            if not self.repo:
                self.notify(
                    "No GitMap repository found. Run 'gitmap init' first.",
                    severity="error",
                    timeout=5,
                )
                return

            self.notify(
                f"Loaded repository: {self.repo.path}",
                severity="information",
                timeout=3,
            )

        except Exception as init_error:
            self.notify(
                f"Error initializing repository: {init_error}",
                severity="error",
                timeout=5,
            )

    def action_show_status(
            self,
    ) -> None:
        """Show status screen."""
        if not self.repo:
            self.notify("No repository loaded", severity="warning")
            return
        self.push_screen(StatusViewScreen(self.repo))

    def action_show_log(
            self,
    ) -> None:
        """Show commit log screen."""
        if not self.repo:
            self.notify("No repository loaded", severity="warning")
            return
        self.push_screen(CommitHistoryScreen(self.repo))

    def action_show_branches(
            self,
    ) -> None:
        """Show branches screen."""
        if not self.repo:
            self.notify("No repository loaded", severity="warning")
            return
        self.notify("Branches view coming soon!", severity="information")

    def action_show_help(
            self,
    ) -> None:
        """Show help screen."""
        self.notify(
            "Use keyboard shortcuts: Q=Quit, S=Status, L=Log, B=Branches",
            severity="information",
            timeout=5,
        )


# ---- Main Function ------------------------------------------------------------------------------------------


def main() -> int:
    """Main entry point for GitMap Client TUI.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        app = GitMapClient()
        app.run()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Exited by user[/yellow]")
        return 0
    except Exception as app_error:
        console.print(f"[red]Error: {app_error}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
