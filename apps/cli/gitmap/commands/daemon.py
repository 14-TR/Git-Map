"""GitMap daemon command.

Runs auto-pull on a scheduled interval in the background as a daemon process.
Provides start, stop, status, and logs subcommands for daemon management.

Execution Context:
    CLI command - invoked via `gitmap daemon <subcommand>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - apscheduler: Job scheduling
    - gitmap_core: Repository and connection management

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import atexit
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from apscheduler.schedulers.background import BackgroundScheduler
from rich.console import Console
from rich.table import Table

from gitmap_core.connection import get_connection
from gitmap_core.remote import RemoteOperations
from gitmap_core.repository import Repository

from .utils import get_portal_url

console = Console()

# Daemon state directory
DAEMON_DIR = Path.home() / ".gitmap-daemon"
PID_FILE = DAEMON_DIR / "daemon.pid"
CONFIG_FILE = DAEMON_DIR / "config.json"
LOG_FILE = DAEMON_DIR / "daemon.log"


# ---- Daemon State Management --------------------------------------------------------------------------------


def ensure_daemon_dir() -> None:
    """Ensure daemon state directory exists."""
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)


def is_daemon_running() -> bool:
    """Check if daemon is currently running."""
    if not PID_FILE.exists():
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        # Check if process exists
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, ProcessLookupError):
        # Process doesn't exist, clean up stale PID file
        if PID_FILE.exists():
            PID_FILE.unlink()
        return False


def get_daemon_pid() -> int | None:
    """Get the PID of the running daemon."""
    if not PID_FILE.exists():
        return None

    try:
        with open(PID_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None


def write_pid_file() -> None:
    """Write current process PID to file."""
    ensure_daemon_dir()
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file() -> None:
    """Remove PID file."""
    if PID_FILE.exists():
        PID_FILE.unlink()


def save_config(config: dict[str, Any]) -> None:
    """Save daemon configuration."""
    ensure_daemon_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_config() -> dict[str, Any] | None:
    """Load daemon configuration."""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# ---- Auto-Pull Core Logic -----------------------------------------------------------------------------------


def execute_auto_pull(config: dict[str, Any], logger: logging.Logger) -> None:
    """Execute auto-pull operation with given configuration.

    Args:
        config: Configuration dictionary containing auto-pull settings
        logger: Logger instance for recording activity
    """
    try:
        logger.info("=" * 80)
        logger.info(f"Starting auto-pull at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        # Extract configuration
        directory = config.get("directory", "repositories")
        branch = config.get("branch", "main")
        portal_url = config.get("portal_url", "")
        username = config.get("username", "")
        password = config.get("password", "")
        skip_errors = config.get("skip_errors", True)
        auto_commit = config.get("auto_commit", False)
        commit_message = config.get("commit_message", "")

        # Resolve base directory
        base_dir = Path(directory).resolve()

        if not base_dir.exists():
            logger.error(f"Directory '{base_dir}' does not exist")
            return

        if not base_dir.is_dir():
            logger.error(f"'{base_dir}' is not a directory")
            return

        logger.info(f"Scanning for GitMap repositories in {base_dir}")

        # Find all GitMap repositories
        repos_to_pull = []
        for item in base_dir.iterdir():
            if item.is_dir():
                gitmap_dir = item / ".gitmap"
                if gitmap_dir.exists() and gitmap_dir.is_dir():
                    repos_to_pull.append(item)

        if not repos_to_pull:
            logger.warning(f"No GitMap repositories found in '{base_dir}'")
            return

        logger.info(f"Found {len(repos_to_pull)} repository/repositories")

        # Get Portal URL
        url = get_portal_url(portal_url if portal_url else None)

        # Connect to Portal once (reuse connection for all pulls)
        logger.info(f"Connecting to {url}")
        connection = get_connection(
            url=url,
            username=username if username else None,
            password=password if password else None,
        )

        if connection.username:
            logger.info(f"Authenticated as {connection.username}")

        # Pull each repository
        success_count = 0
        skipped_count = 0
        failed_repos = []

        for idx, repo_path in enumerate(repos_to_pull, 1):
            repo_name = repo_path.name
            logger.info(f"[{idx}/{len(repos_to_pull)}] Processing '{repo_name}'...")

            try:
                # Load repository
                repo = Repository(repo_path)

                # Get the target branch
                current_branch = repo.get_current_branch()
                branches = repo.list_branches()

                if branch in branches:
                    target_branch = branch
                elif current_branch:
                    target_branch = current_branch
                else:
                    logger.warning(f"[{idx}/{len(repos_to_pull)}] Skipped '{repo_name}' (no branches found)")
                    skipped_count += 1
                    continue

                # Perform pull
                remote_ops = RemoteOperations(repo, connection)
                map_data = remote_ops.pull(target_branch)

                # Get layer count
                layers = map_data.get("operationalLayers", [])
                layer_count = len(layers)

                # Auto-commit if enabled
                commit_id = None
                if auto_commit:
                    if repo.has_uncommitted_changes():
                        # Generate commit message
                        if commit_message:
                            msg = commit_message.replace("{repo}", repo_name)
                            msg = msg.replace("{date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            msg = f"Auto-pull from Portal ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

                        # Create commit
                        new_commit = repo.create_commit(
                            message=msg,
                            author=None,
                            rationale=None,
                        )
                        commit_id = new_commit.id[:8]

                # Log success
                if commit_id:
                    logger.info(f"[{idx}/{len(repos_to_pull)}] ✓ Pulled & Committed '{repo_name}' ({layer_count} layers, {commit_id})")
                else:
                    logger.info(f"[{idx}/{len(repos_to_pull)}] ✓ Pulled '{repo_name}' ({layer_count} layers)")

                success_count += 1

            except Exception as pull_error:
                logger.error(f"[{idx}/{len(repos_to_pull)}] ✗ Failed '{repo_name}': {pull_error}")
                if skip_errors:
                    failed_repos.append({
                        "name": repo_name,
                        "path": str(repo_path),
                        "error": str(pull_error),
                    })
                else:
                    raise

        # Log summary
        logger.info("-" * 80)
        logger.info("Summary:")
        logger.info(f"  ✓ Successfully pulled: {success_count}")

        if skipped_count > 0:
            logger.info(f"  ⊘ Skipped (no '{branch}' branch): {skipped_count}")

        if failed_repos:
            logger.info(f"  ✗ Failed: {len(failed_repos)}")
            for failed in failed_repos:
                logger.error(f"    • {failed['name']}: {failed['error']}")

        logger.info(f"Auto-pull completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

    except Exception as auto_pull_error:
        logger.error(f"Auto-pull failed: {auto_pull_error}", exc_info=True)


# ---- Daemon Process -----------------------------------------------------------------------------------------


def run_daemon(config: dict[str, Any]) -> None:
    """Run the daemon process with scheduled auto-pull.

    Args:
        config: Configuration dictionary containing interval and auto-pull settings
    """
    # Setup logging
    ensure_daemon_dir()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
        ]
    )
    logger = logging.getLogger("gitmap-daemon")

    # Write PID file
    write_pid_file()

    # Setup cleanup on exit
    atexit.register(remove_pid_file)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        remove_pid_file()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Get interval from config
    interval_minutes = config.get("interval_minutes", 60)

    logger.info("=" * 80)
    logger.info("GitMap Auto-Pull Daemon Started")
    logger.info("=" * 80)
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Interval: {interval_minutes} minutes")
    logger.info(f"Directory: {config.get('directory', 'repositories')}")
    logger.info(f"Branch: {config.get('branch', 'main')}")
    logger.info(f"Auto-commit: {config.get('auto_commit', False)}")
    logger.info("=" * 80)

    # Create scheduler
    scheduler = BackgroundScheduler()

    # Schedule auto-pull job
    scheduler.add_job(
        func=execute_auto_pull,
        trigger='interval',
        minutes=interval_minutes,
        args=[config, logger],
        id='auto_pull_job',
        name='Auto-pull repositories',
        max_instances=1,  # Prevent overlapping executions
    )

    # Start scheduler
    scheduler.start()
    logger.info(f"Scheduler started. Next run at: {scheduler.get_job('auto_pull_job').next_run_time}")

    # Run first execution immediately
    logger.info("Running initial auto-pull...")
    execute_auto_pull(config, logger)

    try:
        # Keep the daemon running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    finally:
        scheduler.shutdown()
        logger.info("Daemon stopped")


# ---- CLI Commands -------------------------------------------------------------------------------------------


@click.group()
def daemon() -> None:
    """Manage auto-pull daemon for scheduled repository updates.

    The daemon runs auto-pull on a user-defined interval in the background.
    Use subcommands to start, stop, check status, or view logs.
    """
    pass


@daemon.command()
@click.option(
    "--interval",
    "-i",
    type=int,
    default=60,
    help="Auto-pull interval in minutes (default: 60).",
)
@click.option(
    "--directory",
    "-d",
    default="repositories",
    help="Directory containing gitmap repositories (default: 'repositories').",
)
@click.option(
    "--branch",
    "-b",
    default="main",
    help="Branch to pull for each repository (default: 'main').",
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
def start(
    interval: int,
    directory: str,
    branch: str,
    url: str,
    username: str,
    password: str,
    skip_errors: bool,
    auto_commit: bool,
    commit_message: str,
) -> None:
    """Start the auto-pull daemon.

    Starts a background daemon process that runs auto-pull at the specified
    interval. The daemon will continue running until stopped.

    Examples:
        gitmap daemon start --interval 30
        gitmap daemon start --interval 60 --auto-commit
        gitmap daemon start --interval 120 --directory my-repos --branch main
    """
    # Check if daemon is already running
    if is_daemon_running():
        console.print("[red]✗ Daemon is already running[/red]")
        pid = get_daemon_pid()
        if pid:
            console.print(f"[dim]PID: {pid}[/dim]")
        console.print()
        console.print("[dim]Use 'gitmap daemon status' to check status[/dim]")
        console.print("[dim]Use 'gitmap daemon stop' to stop the daemon[/dim]")
        raise click.Abort()

    # Validate interval
    if interval <= 0:
        raise click.BadParameter("Interval must be greater than 0")

    # Build configuration
    config = {
        "interval_minutes": interval,
        "directory": directory,
        "branch": branch,
        "portal_url": url,
        "username": username,
        "password": password,
        "skip_errors": skip_errors,
        "auto_commit": auto_commit,
        "commit_message": commit_message,
    }

    # Save configuration
    save_config(config)

    console.print("[bold]Starting GitMap auto-pull daemon...[/bold]")
    console.print()
    console.print(f"[dim]Interval: {interval} minutes[/dim]")
    console.print(f"[dim]Directory: {directory}[/dim]")
    console.print(f"[dim]Branch: {branch}[/dim]")
    console.print(f"[dim]Auto-commit: {auto_commit}[/dim]")
    console.print()

    # Fork to background
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process
            # Wait briefly to ensure child started successfully
            time.sleep(1)

            if is_daemon_running():
                console.print(f"[green]✓ Daemon started successfully[/green]")
                console.print(f"[dim]PID: {pid}[/dim]")
                console.print()
                console.print("[dim]Use 'gitmap daemon status' to check status[/dim]")
                console.print("[dim]Use 'gitmap daemon logs' to view logs[/dim]")
                console.print("[dim]Use 'gitmap daemon stop' to stop the daemon[/dim]")
            else:
                console.print("[red]✗ Failed to start daemon[/red]")
                console.print("[dim]Check logs for details: gitmap daemon logs[/dim]")

            sys.exit(0)
    except OSError as fork_error:
        raise click.ClickException(f"Failed to fork daemon: {fork_error}")

    # Child process continues here
    # Detach from parent
    os.setsid()

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    with open(os.devnull, 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())

    # Run daemon
    run_daemon(config)


@daemon.command()
def stop() -> None:
    """Stop the auto-pull daemon.

    Gracefully stops the running daemon process.

    Examples:
        gitmap daemon stop
    """
    if not is_daemon_running():
        console.print("[yellow]⊘ Daemon is not running[/yellow]")
        return

    pid = get_daemon_pid()
    if not pid:
        console.print("[red]✗ Could not determine daemon PID[/red]")
        return

    console.print(f"[dim]Stopping daemon (PID: {pid})...[/dim]")

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Wait for process to exit (up to 10 seconds)
        for _ in range(10):
            time.sleep(1)
            if not is_daemon_running():
                break

        if is_daemon_running():
            # Force kill if still running
            console.print("[yellow]Daemon did not stop gracefully, forcing shutdown...[/yellow]")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            remove_pid_file()

        console.print("[green]✓ Daemon stopped[/green]")

    except ProcessLookupError:
        console.print("[yellow]⊘ Daemon process not found (may have already stopped)[/yellow]")
        remove_pid_file()
    except PermissionError:
        console.print("[red]✗ Permission denied to stop daemon[/red]")
    except Exception as stop_error:
        console.print(f"[red]✗ Error stopping daemon: {stop_error}[/red]")


@daemon.command()
def status() -> None:
    """Check the status of the auto-pull daemon.

    Shows whether the daemon is running and displays configuration.

    Examples:
        gitmap daemon status
    """
    # Check if daemon is running
    running = is_daemon_running()
    pid = get_daemon_pid()

    # Load configuration
    config = load_config()

    # Create status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="dim")
    table.add_column("Value")

    # Status
    if running:
        table.add_row("Status", "[green]✓ Running[/green]")
        if pid:
            table.add_row("PID", str(pid))
    else:
        table.add_row("Status", "[red]✗ Not running[/red]")

    # Configuration
    if config:
        table.add_row("Interval", f"{config.get('interval_minutes', 'N/A')} minutes")
        table.add_row("Directory", config.get('directory', 'N/A'))
        table.add_row("Branch", config.get('branch', 'N/A'))
        table.add_row("Auto-commit", str(config.get('auto_commit', False)))

        if config.get('commit_message'):
            table.add_row("Commit Message", config.get('commit_message'))

    # Log file
    if LOG_FILE.exists():
        log_size = LOG_FILE.stat().st_size
        log_size_kb = log_size / 1024
        table.add_row("Log File", f"{LOG_FILE} ({log_size_kb:.1f} KB)")

    console.print()
    console.print("[bold]GitMap Auto-Pull Daemon Status[/bold]")
    console.print()
    console.print(table)
    console.print()

    if running:
        console.print("[dim]Use 'gitmap daemon logs' to view logs[/dim]")
        console.print("[dim]Use 'gitmap daemon stop' to stop the daemon[/dim]")
    else:
        console.print("[dim]Use 'gitmap daemon start' to start the daemon[/dim]")


@daemon.command()
@click.option(
    "--lines",
    "-n",
    type=int,
    default=50,
    help="Number of lines to display (default: 50).",
)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    default=False,
    help="Follow log output (like tail -f).",
)
def logs(lines: int, follow: bool) -> None:
    """View daemon logs.

    Displays recent log entries from the daemon log file.

    Examples:
        gitmap daemon logs
        gitmap daemon logs --lines 100
        gitmap daemon logs --follow
    """
    if not LOG_FILE.exists():
        console.print("[yellow]⊘ No log file found[/yellow]")
        console.print()
        console.print("[dim]The daemon has not been started yet or logs have been cleared[/dim]")
        return

    console.print(f"[bold]Daemon Logs[/bold] [dim]({LOG_FILE})[/dim]")
    console.print()

    if follow:
        # Follow mode - continuously display new log entries
        console.print("[dim]Following logs (press Ctrl+C to stop)...[/dim]")
        console.print()

        try:
            # Display last N lines first
            with open(LOG_FILE, "r") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                for line in recent_lines:
                    console.print(line.rstrip())

            # Follow new lines
            with open(LOG_FILE, "r") as f:
                # Seek to end
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(0.5)

        except KeyboardInterrupt:
            console.print()
            console.print("[dim]Stopped following logs[/dim]")

    else:
        # Display last N lines
        with open(LOG_FILE, "r") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            for line in recent_lines:
                console.print(line.rstrip())

        console.print()
        console.print(f"[dim]Showing last {len(recent_lines)} lines[/dim]")
        console.print("[dim]Use --lines N to show more, or --follow to tail logs[/dim]")
