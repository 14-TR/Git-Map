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

import argparse
import sys
from pathlib import Path

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, ListItem, ListView, Static

from gitmap_core.repository import Repository, find_repository

from gitmap_client.screens.commit_history import CommitHistoryScreen
from gitmap_client.screens.repo_picker import RepoPickerScreen
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

    .help-text {
        padding: 1;
        text-style: italic;
        color: $text-muted;
    }

    .hint {
        padding: 1;
        text-style: dim;
        color: $text-muted;
    }

    .button-container {
        layout: horizontal;
        align: center;
        padding: 2;
    }

    .button-container > Button {
        margin: 1;
        min-width: 12;
    }

    .label {
        padding: 1;
        text-style: bold;
        background: $panel;
    }

    .separator {
        padding: 1;
        text-align: center;
        color: $text-muted;
    }

    #repo-selector-container {
        height: 10;
        border: solid $primary;
        margin: 1;
    }

    #repo-status {
        padding: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("o", "open_repo", "Open Repo", key_display="O"),
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
        self.available_repos: list[Path] = []

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
                    yield Static("Repository:", classes="label")
                    with VerticalScroll(id="repo-selector-container"):
                        yield ListView(id="repo-selector")
                    yield Static("", id="repo-status", classes="hint")
                    yield Static("─" * 30, classes="separator")
                    yield StatusPanel()
                with Vertical(id="content"):
                    yield Static("Welcome to GitMap Client", id="content-area")
        yield Footer()

    def _find_repositories_in_dir(
            self,
            base_dir: Path,
    ) -> list[Path]:
        """Find all GitMap repositories in a directory.

        Args:
            base_dir: Directory to scan.

        Returns:
            List of repository root paths found.
        """
        repos = []
        if not base_dir.exists() or not base_dir.is_dir():
            return repos

        try:
            for item in base_dir.iterdir():
                if item.is_dir():
                    gitmap_dir = item / ".gitmap"
                    if gitmap_dir.exists() and gitmap_dir.is_dir():
                        try:
                            repo = Repository(item)
                            if repo.is_valid():
                                repos.append(item)
                        except Exception:
                            pass
        except Exception:
            pass

        return sorted(repos)

    def _scan_repositories_directory(
            self,
    ) -> None:
        """Automatically scan repositories directory and populate selector."""
        try:
            # Try to find repositories/ directory
            project_root = Path(__file__).parent.parent.parent.parent.parent  # Git-Map root
            repos_dir = project_root / "repositories"
            
            if not repos_dir.exists():
                # Try from current working directory
                cwd = Path.cwd()
                if "repositories" in str(cwd):
                    # We might be in a repository subdirectory
                    parts = Path(cwd).parts
                    for i, part in enumerate(parts):
                        if part == "repositories" and i < len(parts) - 1:
                            repos_dir = Path(*parts[:i+1])
                            break
            
            if repos_dir.exists():
                self.available_repos = self._find_repositories_in_dir(repos_dir)
                
                # Update UI
                list_view = self.query_one("#repo-selector", ListView)
                list_view.clear()
                
                if self.available_repos:
                    for repo_path in self.available_repos:
                        repo_name = repo_path.name
                        item = ListItem(Label(repo_name))
                        item.id = str(repo_path)
                        list_view.append(item)
                    
                    status = self.query_one("#repo-status", Static)
                    status.update(f"Found {len(self.available_repos)} repo(s)")
                    
                    # Auto-select first repository if no repo was provided
                    if not self.repo_path and self.available_repos:
                        self._load_repository(self.available_repos[0])
                else:
                    status = self.query_one("#repo-status", Static)
                    status.update(f"No repos in: {repos_dir}")
        except Exception as scan_error:
            status = self.query_one("#repo-status", Static)
            status.update(f"Scan error: {scan_error}")

    def _load_repository(
            self,
            repo_path: Path,
    ) -> None:
        """Load a repository and update UI.

        Args:
            repo_path: Path to repository to load.
        """
        try:
            repo = Repository(repo_path)
            if not repo.exists() or not repo.is_valid():
                self.notify(f"Invalid repository: {repo_path}", severity="error")
                return

            self.repo_path = repo_path
            self.repo = repo

            self.notify(
                f"Loaded repository: {self.repo.root}",
                severity="success",
                timeout=2,
            )
        except Exception as load_error:
            self.notify(f"Error loading repository: {load_error}", severity="error")

    def on_mount(
            self,
    ) -> None:
        """Handle application mount event.

        Initializes repository connection and validates GitMap directory.
        """
        # First, scan for repositories
        self._scan_repositories_directory()

        # Then try to load specified or found repository
        try:
            if self.repo_path:
                self._load_repository(Path(self.repo_path))
            elif not self.repo:
                # If no repo loaded yet, try searching from current directory
                search_dir = Path.cwd()
                self.repo = find_repository(search_dir)
                if self.repo:
                    self.repo_path = self.repo.root
                    self.notify(
                        f"Loaded repository: {self.repo.root}",
                        severity="information",
                        timeout=3,
                    )
                else:
                    # No repo found anywhere
                    status = self.query_one("#repo-status", Static)
                    if not self.available_repos:
                        status.update("No repositories found. Press O to browse.")
        except Exception as init_error:
            self.notify(
                f"Error initializing repository: {init_error}",
                severity="error",
                timeout=5,
            )

    def on_list_view_selected(
            self,
            event: ListView.Selected,
    ) -> None:
        """Handle repository selection from list.

        Args:
            event: Selection event.
        """
        if event.list_view.id == "repo-selector":
            selected_item = event.item
            if selected_item and hasattr(selected_item, 'id'):
                repo_path = Path(selected_item.id)
                self._load_repository(repo_path)

    def action_open_repo(
            self,
    ) -> None:
        """Open repository picker screen."""
        current_path = self.repo.root if self.repo else Path.cwd()
        # Default repositories directory: repositories/ in project root
        project_root = Path(__file__).parent.parent.parent.parent.parent  # Go up to Git-Map root
        default_repos_dir = project_root / "repositories"
        # If current repo is in repositories/, use that as the base
        if self.repo and "repositories" in str(self.repo.root):
            try:
                repos_path = Path(self.repo.root)
                # Find the repositories/ parent directory
                while repos_path.name != "repositories" and repos_path != repos_path.parent:
                    repos_path = repos_path.parent
                if repos_path.name == "repositories":
                    default_repos_dir = repos_path
            except Exception:
                pass
        
        self.push_screen(
            RepoPickerScreen(
                initial_path=current_path,
                repositories_dir=default_repos_dir if default_repos_dir.exists() else None,
            ),
            self._on_repo_selected,
        )

    async def _on_repo_selected(
            self,
            path: str | None,
    ) -> None:
        """Handle repository path selection.

        Args:
            path: Selected repository path, or None if cancelled.
        """
        if not path:
            return  # User cancelled

        try:
            from gitmap_core.repository import Repository
            
            repo_path = Path(path).resolve()
            new_repo = Repository(repo_path)

            if not new_repo.exists() or not new_repo.is_valid():
                self.notify(
                    f"Invalid GitMap repository at: {repo_path}",
                    severity="error",
                    timeout=5,
                )
                return

            # Update repository
            self.repo_path = repo_path
            self.repo = new_repo

            self.notify(
                f"Loaded repository: {self.repo.root}",
                severity="success",
                timeout=3,
            )

        except Exception as repo_error:
            self.notify(
                f"Error loading repository: {repo_error}",
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
    parser = argparse.ArgumentParser(
        description="GitMap TUI Client - Interactive visual interface for GitMap"
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        help="Path to GitMap repository (default: search from current directory)",
    )
    parser.add_argument(
        "--cwd",
        "-C",
        type=str,
        help="Change to this directory before searching for repository",
    )
    
    args = parser.parse_args()
    
    # Change directory if specified
    if args.cwd:
        try:
            import os
            os.chdir(args.cwd)
            console.print(f"[dim]Changed to directory: {args.cwd}[/dim]")
        except Exception as chdir_error:
            console.print(f"[red]Failed to change directory: {chdir_error}[/red]")
            return 1
    
    try:
        repo_path = Path(args.repo).resolve() if args.repo else None
        app = GitMapClient(repo_path=repo_path)
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
