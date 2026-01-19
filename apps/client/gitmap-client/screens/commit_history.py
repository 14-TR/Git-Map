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
            # Collect commits from all branches (always read fresh from disk)
            all_branches = self.repo.list_branches()
            if not all_branches:
                self.notify("No branches found", severity="warning")
                return

            current_branch = self.repo.get_current_branch()
            
            # Debug: Show what we found
            branch_info = []
            for b in all_branches:
                commit_id = self.repo.get_branch_commit(b)
                branch_info.append(f"{b}->{commit_id[:8] if commit_id else 'none'}")
            
            # Track commits and which branches they belong to
            commit_to_branches: dict[str, list[str]] = {}
            all_commits: dict[str, "Commit"] = {}
            
            # Collect commits from all branches
            for branch_name in all_branches:
                # Always read fresh commit ID for this branch from disk
                commit_id = self.repo.get_branch_commit(branch_name)
                if not commit_id:
                    # Branch exists but has no commits yet
                    continue
                
                # Traverse commit history for this branch starting from HEAD
                visited = set()
                current_commit_id = commit_id
                max_depth = 50
                depth = 0
                
                while current_commit_id and depth < max_depth:
                    if current_commit_id in visited:
                        # Cycle detected or already processed
                        break
                    visited.add(current_commit_id)
                    
                    # Always read commit fresh from disk
                    commit = self.repo.get_commit(current_commit_id)
                    if not commit:
                        # Commit file doesn't exist - might be corrupted or missing
                        break
                    
                    # Track this commit
                    if current_commit_id not in commit_to_branches:
                        commit_to_branches[current_commit_id] = []
                        all_commits[current_commit_id] = commit
                    
                    # Add branch to commit if not already there
                    if branch_name not in commit_to_branches[current_commit_id]:
                        commit_to_branches[current_commit_id].append(branch_name)
                    
                    # Move to parent commit
                    current_commit_id = commit.parent
                    depth += 1

            if not all_commits:
                self.notify("No commits found in any branch", severity="information")
                return

            # Sort commits by timestamp (newest first)
            sorted_commits = sorted(
                all_commits.values(),
                key=lambda c: c.timestamp,
                reverse=True
            )

            # Build visual commit log
            log_lines = [
                f"[bold cyan]Branches:[/bold cyan] {', '.join(all_branches)}",
                f"[dim]Current: {current_branch or '(none)'}[/dim]",
                f"[dim]Repository: {self.repo.root}[/dim]",
                f"[dim]Showing {len(sorted_commits)} commits across {len(all_branches)} branch(es)[/dim]",
                f"[dim]Branch info: {'; '.join(branch_info)}[/dim]",
                "",
            ]
            
            # Debug: Show first few commit IDs for verification
            if sorted_commits:
                recent_commits = sorted_commits[:3]
                commit_ids = [f"{c.id[:8]}: {c.message[:30]}" for c in recent_commits]
                log_lines.insert(-1, f"[dim]Recent commits: {'; '.join(commit_ids)}[/dim]\n")

            for idx, commit in enumerate(sorted_commits):
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

                # Get branches this commit belongs to
                branches = commit_to_branches.get(commit.id, [])
                branch_labels = []
                for branch in branches:
                    if branch == current_branch:
                        branch_labels.append(f"[yellow]*{branch}[/yellow]")
                    else:
                        branch_labels.append(f"[dim]{branch}[/dim]")
                
                branch_str = " ".join(branch_labels) if branch_labels else "[dim](no branch)[/dim]"

                # Build commit line
                log_lines.append(
                    f"[yellow]{graph}[/yellow] [bold cyan]{short_id}[/bold cyan] "
                    f"[green]{short_msg}[/green]"
                )
                log_lines.append(
                    f"  [dim]{author_short} • {time_str} • Branches: {branch_str}[/dim]"
                )
                log_lines.append("")

            # Update display
            try:
                content = self.query_one("#commit-list", Static)
                content_text = "\n".join(log_lines)
                content.update(content_text)
                
                # Verify update worked
                if not content_text or len(sorted_commits) == 0:
                    self.notify(
                        f"No commits to display (found {len(all_commits)} commits, {len(all_branches)} branches)",
                        severity="warning",
                        timeout=3,
                    )
                else:
                    self.notify(
                        f"Commit history refreshed: {len(sorted_commits)} commits from {len(all_branches)} branch(es)",
                        severity="information",
                        timeout=2,
                    )
            except Exception as update_error:
                self.notify(
                    f"Error updating display: {update_error}",
                    severity="error",
                    timeout=5,
                )
                # Try to show error in the content area
                try:
                    content = self.query_one("#commit-list", Static)
                    content.update(f"[red]Error: {update_error}[/red]")
                except Exception:
                    pass

        except Exception as log_error:
            import traceback
            error_details = f"{log_error}\n{traceback.format_exc()}"
            self.notify(
                f"Error loading commits: {log_error}",
                severity="error",
                timeout=10,
            )
            # Try to show error details
            try:
                content = self.query_one("#commit-list", Static)
                content.update(f"[red]Error loading commits:[/red]\n{log_error}")
            except Exception:
                pass

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
