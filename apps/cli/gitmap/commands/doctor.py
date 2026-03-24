"""GitMap doctor command.

Diagnoses the local GitMap environment: checks Python version, required
packages, environment variables, and (optionally) Portal connectivity.

Execution Context:
    CLI command - invoked via `gitmap doctor`

Dependencies:
    - click: CLI framework
    - rich: Terminal output
    - gitmap_core: Repository detection

Metadata:
    Version: 1.0.0
    Author: GitMap Team
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# Minimum Python version required
MIN_PYTHON = (3, 11)

# Required packages (package_name, import_name, install_hint)
REQUIRED_PACKAGES: list[tuple[str, str, str]] = [
    ("click", "click", "pip install click"),
    ("rich", "rich", "pip install rich"),
    ("deepdiff", "deepdiff", "pip install deepdiff"),
]

OPTIONAL_PACKAGES: list[tuple[str, str, str]] = [
    ("apscheduler", "apscheduler", "pip install apscheduler  # needed for 'gitmap daemon'"),
    ("arcgis", "arcgis", "pip install arcgis           # needed for Portal sync"),
]

# Environment variables
ENV_VARS: list[tuple[str, str, bool]] = [
    ("PORTAL_URL", "ArcGIS Portal / ArcGIS Online URL", False),
    ("ARCGIS_USERNAME", "Portal username", False),
    ("ARCGIS_PASSWORD", "Portal password (or use keyring)", False),
]


def _check(ok: bool) -> str:
    return "[green]✓[/green]" if ok else "[red]✗[/red]"


def _warn(value: bool) -> str:
    return "[yellow]⚠[/yellow]" if not value else "[green]✓[/green]"


def _pkg_installed(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


# ---- Doctor Command -----------------------------------------------------------------------------------------


@click.command(epilog="Tip: run 'gitmap doctor --portal' to also test Portal connectivity.")
@click.option(
    "--portal",
    "check_portal",
    is_flag=True,
    default=False,
    help="Attempt to connect to Portal and verify credentials.",
)
@click.option(
    "--fix",
    "show_fixes",
    is_flag=True,
    default=False,
    help="Show install commands for any missing packages.",
)
def doctor(check_portal: bool, show_fixes: bool) -> None:
    """Check your GitMap environment for common issues.

    Verifies Python version, required packages, environment variables,
    and optionally tests Portal connectivity.

    Examples:
        gitmap doctor
        gitmap doctor --portal
        gitmap doctor --fix
    """
    console.print()
    console.print("[bold]GitMap Doctor[/bold] — environment diagnostics")
    console.print()

    issues: list[str] = []
    fixes: list[str] = []
    all_ok = True

    # ---- Python version ---------------------------------------------------------------------------------
    console.print("[bold dim]─── Python ───[/bold dim]")
    py_ver = sys.version_info[:2]
    py_ok = py_ver >= MIN_PYTHON
    py_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"  {_check(py_ok)} Python {py_str}", end="")
    if not py_ok:
        console.print(f"  [red](requires {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+)[/red]")
        issues.append(f"Python {py_str} is below the minimum required version {MIN_PYTHON[0]}.{MIN_PYTHON[1]}")
        all_ok = False
    else:
        console.print()
    console.print()

    # ---- Required packages ------------------------------------------------------------------------------
    console.print("[bold dim]─── Required Packages ───[/bold dim]")
    for pkg_name, import_name, hint in REQUIRED_PACKAGES:
        installed = _pkg_installed(import_name)
        console.print(f"  {_check(installed)} {pkg_name}")
        if not installed:
            issues.append(f"Required package '{pkg_name}' is not installed")
            fixes.append(hint)
            all_ok = False
    console.print()

    # ---- Optional packages ------------------------------------------------------------------------------
    console.print("[bold dim]─── Optional Packages ───[/bold dim]")
    for pkg_name, import_name, hint in OPTIONAL_PACKAGES:
        installed = _pkg_installed(import_name)
        icon = "[green]✓[/green]" if installed else "[yellow]⊘[/yellow]"
        console.print(f"  {icon} {pkg_name}", end="")
        if not installed:
            console.print("  [dim](optional)[/dim]")
            if show_fixes:
                fixes.append(hint)
        else:
            console.print()
    console.print()

    # ---- Environment variables --------------------------------------------------------------------------
    console.print("[bold dim]─── Environment Variables ───[/bold dim]")
    for var_name, description, required in ENV_VARS:
        value = os.environ.get(var_name)
        is_set = bool(value)
        if required and not is_set:
            console.print(f"  {_check(False)} {var_name}  [dim]{description}[/dim]  [red](required)[/red]")
            issues.append(f"Required env var {var_name} is not set")
            all_ok = False
        elif is_set:
            # Mask password values
            display = "***" if "PASSWORD" in var_name or "TOKEN" in var_name else value
            console.print(f"  {_check(True)} {var_name}={display}  [dim]{description}[/dim]")
        else:
            console.print(f"  [yellow]⊘[/yellow] {var_name}  [dim]{description} (not set)[/dim]")
    console.print()

    # ---- Repository check -------------------------------------------------------------------------------
    console.print("[bold dim]─── Current Directory ───[/bold dim]")
    cwd = Path.cwd()
    gitmap_dir = cwd / ".gitmap"
    in_repo = gitmap_dir.exists() and gitmap_dir.is_dir()
    if in_repo:
        console.print(f"  {_check(True)} In a GitMap repository  [dim]({cwd})[/dim]")
        # Try to detect branch
        try:
            from gitmap_core.repository import Repository
            repo = Repository(cwd)
            branch = repo.get_current_branch()
            commits = repo.list_commits()
            console.print(f"  [green]✓[/green] Branch: [cyan]{branch or '(unknown)'}[/cyan]")
            console.print(f"  [green]✓[/green] Commits: {len(commits)}")
        except Exception as repo_err:
            console.print(f"  [yellow]⚠[/yellow] Could not read repo state: {repo_err}")
    else:
        console.print(f"  [yellow]⊘[/yellow] Not in a GitMap repository  [dim](run 'gitmap init' to start one)[/dim]")
    console.print()

    # ---- Portal connectivity check (optional) -----------------------------------------------------------
    if check_portal:
        console.print("[bold dim]─── Portal Connectivity ───[/bold dim]")
        portal_url = os.environ.get("PORTAL_URL", "https://www.arcgis.com")
        username = os.environ.get("ARCGIS_USERNAME", "")
        password = os.environ.get("ARCGIS_PASSWORD", "")

        if not _pkg_installed("arcgis"):
            console.print("  [yellow]⊘[/yellow] arcgis package not installed — cannot test connectivity")
            console.print("  [dim]Install with: pip install arcgis[/dim]")
        else:
            try:
                from gitmap_core.connection import get_connection
                console.print(f"  [dim]Connecting to {portal_url} ...[/dim]")
                conn = get_connection(
                    url=portal_url,
                    username=username or None,
                    password=password or None,
                )
                if conn.username:
                    console.print(f"  {_check(True)} Connected as [cyan]{conn.username}[/cyan]")
                else:
                    console.print(f"  {_check(True)} Connected (anonymous)")
            except Exception as conn_err:
                console.print(f"  {_check(False)} Connection failed: {conn_err}")
                issues.append(f"Portal connectivity check failed: {conn_err}")
                all_ok = False
        console.print()

    # ---- Summary ----------------------------------------------------------------------------------------
    if all_ok:
        console.print("[green bold]✓ No issues found.[/green bold] GitMap is ready to use.")
    else:
        console.print(f"[red bold]✗ Found {len(issues)} issue(s):[/red bold]")
        for i, issue in enumerate(issues, 1):
            console.print(f"  {i}. {issue}")

    if fixes:
        console.print()
        console.print("[bold]Suggested fixes:[/bold]")
        for fix in fixes:
            console.print(f"  [dim]$[/dim] {fix}")

    console.print()
    raise SystemExit(0 if all_ok else 1)
