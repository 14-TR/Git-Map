"""Repository Picker Screen.

Allows user to select or enter a GitMap repository path.

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from gitmap_core.repository import Repository


class RepoPickerScreen(ModalScreen[str | None]):
    """Modal screen for selecting a GitMap repository path.

    Allows user to type a path or navigate directories.
    Returns the selected repository path or None if cancelled.
    """

    CSS = """
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

    #repo-path-input {
        margin: 1;
        padding: 1;
    }

    #scan-dir-input {
        margin: 1;
        padding: 1;
        width: 1fr;
    }

    #scan-btn {
        margin: 1;
        min-width: 8;
    }

    #repo-list-panel {
        width: 1fr;
        border-right: solid $primary;
        padding: 1;
    }

    #manual-panel {
        width: 1fr;
        padding: 1;
    }

    .section-title {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }

    #repo-list-container {
        height: 15;
        border: solid $primary;
        margin: 1;
    }

    #repo-list-status {
        padding: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", key_display="ESC"),
        Binding("enter", "confirm", "Confirm", key_display="ENTER"),
    ]

    def __init__(
            self,
            initial_path: Path | str | None = None,
            repositories_dir: Path | str | None = None,
    ) -> None:
        """Initialize repository picker.

        Args:
            initial_path: Initial path to show (defaults to current directory).
            repositories_dir: Directory containing multiple repositories (optional).
        """
        super().__init__()
        self.initial_path = Path(initial_path) if initial_path else Path.cwd()
        self.repositories_dir = Path(repositories_dir) if repositories_dir else None
        self.found_repos: list[Path] = []

    def compose(
            self,
    ) -> ComposeResult:
        """Compose repository picker widgets."""
        yield Header()
        with Container():
            with Horizontal():
                # Left side: Repository list
                with Vertical(id="repo-list-panel"):
                    yield Label("Found Repositories", classes="section-title")
                    yield Static(
                        "Scan a directory to find all GitMap repositories:",
                        classes="help-text",
                    )
                    with Horizontal():
                        yield Input(
                            value=str(self.repositories_dir or self.initial_path.parent),
                            placeholder="/path/to/repositories/dir",
                            id="scan-dir-input",
                        )
                        yield Button("Scan", variant="primary", id="scan-btn")
                    with VerticalScroll(id="repo-list-container"):
                        yield ListView(id="repo-list")
                    yield Static("", id="repo-list-status", classes="hint")
                
                # Right side: Manual path input
                with Vertical(id="manual-panel"):
                    yield Label("Manual Path Entry", classes="section-title")
                    yield Static(
                        "Or enter the path directly:",
                        classes="help-text",
                    )
                    yield Input(
                        value=str(self.initial_path),
                        placeholder="/path/to/repository",
                        id="repo-path-input",
                    )
                    yield Static(
                        "Tip: You can type a path or use Tab to auto-complete",
                        classes="hint",
                    )
            
            with Container(classes="button-container"):
                yield Button("Open", variant="primary", id="open-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
        yield Footer()

    def on_mount(
            self,
    ) -> None:
        """Focus input when screen mounts."""
        self.query_one("#repo-path-input", Input).focus()
        # Auto-scan if repositories_dir was provided
        if self.repositories_dir and self.repositories_dir.exists():
            self._scan_directory(self.repositories_dir)

    def _find_repositories(
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
            # Scan immediate subdirectories for .gitmap folders
            for item in base_dir.iterdir():
                if item.is_dir():
                    gitmap_dir = item / ".gitmap"
                    if gitmap_dir.exists() and gitmap_dir.is_dir():
                        # Validate it's a proper GitMap repo
                        try:
                            repo = Repository(item)
                            if repo.is_valid():
                                repos.append(item)
                        except Exception:
                            pass
        except Exception:
            pass

        return sorted(repos)

    def _scan_directory(
            self,
            scan_dir: Path,
    ) -> None:
        """Scan directory for repositories and update list.

        Args:
            scan_dir: Directory to scan.
        """
        try:
            resolved_dir = scan_dir.expanduser().resolve()
            self.found_repos = self._find_repositories(resolved_dir)
            
            list_view = self.query_one("#repo-list", ListView)
            list_view.clear()
            
            if self.found_repos:
                for repo_path in self.found_repos:
                    item = ListItem(Label(str(repo_path)))
                    item.id = str(repo_path)
                    list_view.append(item)
                
                status = self.query_one("#repo-list-status", Static)
                status.update(f"Found {len(self.found_repos)} repository/repositories")
            else:
                status = self.query_one("#repo-list-status", Static)
                status.update(f"No GitMap repositories found in: {resolved_dir}")
                
        except Exception as scan_error:
            status = self.query_one("#repo-list-status", Static)
            status.update(f"Error scanning: {scan_error}")

    def on_button_pressed(
            self,
            event: Button.Pressed,
    ) -> None:
        """Handle button presses."""
        if event.button.id == "scan-btn":
            scan_input = self.query_one("#scan-dir-input", Input)
            scan_path = Path(scan_input.value.strip()).expanduser()
            self._scan_directory(scan_path)
        elif event.button.id == "open-btn":
            self.action_confirm()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def on_list_view_selected(
            self,
            event: ListView.Selected,
    ) -> None:
        """Handle repository selection from list.

        Args:
            event: Selection event.
        """
        selected_item = event.item
        if selected_item and hasattr(selected_item, 'id'):
            # Update manual input with selected path
            input_widget = self.query_one("#repo-path-input", Input)
            input_widget.value = selected_item.id

    def on_input_changed(
            self,
            event: Input.Changed,
    ) -> None:
        """Validate path as user types."""
        if event.control.id == "repo-path-input":
            path_str = event.value.strip()
            if not path_str:
                return

            try:
                path = Path(path_str).expanduser().resolve()
                
                # Check if it's a valid GitMap repository
                gitmap_dir = path / ".gitmap"
                if gitmap_dir.exists() and gitmap_dir.is_dir():
                    # Valid repository
                    self.query_one("#open-btn", Button).variant = "success"
                    self.query_one("#open-btn", Button).label = "Open ✓"
                elif path.exists() and path.is_dir():
                    # Valid directory, but check parent directories
                    current = path
                    found = False
                    for _ in range(5):  # Check up to 5 levels up
                        if (current / ".gitmap").exists():
                            found = True
                            break
                        if current == current.parent:
                            break
                        current = current.parent
                    
                    if found:
                        self.query_one("#open-btn", Button).variant = "primary"
                        self.query_one("#open-btn", Button).label = f"Open (use: {current})"
                    else:
                        self.query_one("#open-btn", Button).variant = "warning"
                        self.query_one("#open-btn", Button).label = "Open (no .gitmap found)"
                elif not path.exists():
                    # Path doesn't exist
                    self.query_one("#open-btn", Button).variant = "default"
                    self.query_one("#open-btn", Button).label = "Open (path not found)"
                else:
                    self.query_one("#open-btn", Button).variant = "default"
                    self.query_one("#open-btn", Button).label = "Open"
            except Exception:
                self.query_one("#open-btn", Button).variant = "default"
                self.query_one("#open-btn", Button).label = "Open"

    def on_button_pressed(
            self,
            event: Button.Pressed,
    ) -> None:
        """Handle button presses."""
        if event.button.id == "open-btn":
            self.action_confirm()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_confirm(
            self,
    ) -> None:
        """Confirm and return selected path."""
        input_widget = self.query_one("#repo-path-input", Input)
        path_str = input_widget.value.strip()

        if not path_str:
            self.notify("Please enter a path", severity="warning")
            return

        try:
            path = Path(path_str).expanduser().resolve()
            
            # Check if it's a GitMap repository
            gitmap_dir = path / ".gitmap"
            if gitmap_dir.exists() and gitmap_dir.is_dir():
                self.dismiss(str(path))
                return
            
            # Check parent directories for .gitmap
            current = path
            for _ in range(10):  # Check up to 10 levels up
                if (current / ".gitmap").exists() and (current / ".gitmap").is_dir():
                    self.dismiss(str(current))
                    return
                if current == current.parent:
                    break
                current = current.parent

            # No .gitmap found, but return the path anyway (validation will happen in main app)
            self.dismiss(str(path))

        except Exception as path_error:
            self.notify(f"Invalid path: {path_error}", severity="error")

    def action_cancel(
            self,
    ) -> None:
        """Cancel and return None."""
        self.dismiss(None)
