"""GitMap completions command.

Generates shell completion scripts for bash, zsh, and fish.

Execution Context:
    CLI command - invoked via `gitmap completions <shell>`

Dependencies:
    - click: CLI framework
    - rich: Terminal output

Metadata:
    Version: 1.0.0
    Author: GitMap Team
"""

from __future__ import annotations

import os
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# Shell-specific environment variable names (Click convention)
_COMPLETE_VAR = {
    "bash": "_GITMAP_COMPLETE",
    "zsh": "_GITMAP_COMPLETE",
    "fish": "_GITMAP_COMPLETE",
}

# Install instructions per shell
_INSTALL_INSTRUCTIONS: dict[str, str] = {
    "bash": """\
# Add to ~/.bashrc or ~/.bash_profile:
eval "$(_GITMAP_COMPLETE=bash_source gitmap)"

# Then reload your shell:
source ~/.bashrc""",
    "zsh": """\
# Add to ~/.zshrc:
eval "$(_GITMAP_COMPLETE=zsh_source gitmap)"

# Then reload your shell:
source ~/.zshrc""",
    "fish": """\
# Add to ~/.config/fish/completions/gitmap.fish:
_GITMAP_COMPLETE=fish_source gitmap | source

# Or run once to install permanently:
_GITMAP_COMPLETE=fish_source gitmap > ~/.config/fish/completions/gitmap.fish""",
}


# ---- Completions Command ------------------------------------------------------------------------------------


@click.command(epilog="Tip: run 'gitmap completions --install bash' to auto-install into ~/.bashrc.")
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    required=False,
)
@click.option(
    "--install",
    "install_shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    default=None,
    help="Auto-install completion into the appropriate shell config file.",
)
@click.option(
    "--print",
    "print_script",
    is_flag=True,
    default=False,
    help="Print the raw completion script to stdout (useful for piping).",
)
def completions(
    shell: str | None,
    install_shell: str | None,
    print_script: bool,
) -> None:
    """Generate shell completion scripts.

    Enables tab-completion for gitmap commands and options in your
    terminal. Supports bash, zsh, and fish.

    Examples:
        gitmap completions bash                  # Show bash setup instructions
        gitmap completions zsh                   # Show zsh setup instructions
        gitmap completions fish                  # Show fish setup instructions
        gitmap completions --install bash        # Auto-install into ~/.bashrc
        gitmap completions --install zsh         # Auto-install into ~/.zshrc
        gitmap completions --print bash          # Print script to stdout
    """
    target_shell = install_shell or shell

    if not target_shell:
        # Detect current shell
        detected = _detect_shell()
        console.print()
        console.print("[bold]GitMap Shell Completions[/bold]")
        console.print()
        console.print("Enable tab-completion so pressing [cyan]<Tab>[/cyan] auto-completes commands and options.")
        console.print()
        if detected:
            console.print(f"Detected shell: [cyan]{detected}[/cyan]")
            console.print()
        console.print("Usage:")
        console.print("  [dim]gitmap completions bash[/dim]       — show bash setup instructions")
        console.print("  [dim]gitmap completions zsh[/dim]        — show zsh  setup instructions")
        console.print("  [dim]gitmap completions fish[/dim]       — show fish setup instructions")
        console.print("  [dim]gitmap completions --install zsh[/dim]  — auto-install into ~/.zshrc")
        console.print()
        return

    target_shell = target_shell.lower()

    if print_script:
        # Emit the raw script so the user can pipe it
        import subprocess

        env = os.environ.copy()
        env[_COMPLETE_VAR[target_shell]] = f"{target_shell}_source"
        result = subprocess.run(
            [sys.executable, "-m", "gitmap_cli.main"],
            env=env,
            capture_output=True,
            text=True,
        )
        click.echo(result.stdout, nl=False)
        return

    if install_shell:
        _auto_install(install_shell)
        return

    # Print instructions
    instructions = _INSTALL_INSTRUCTIONS[target_shell]
    console.print()
    console.print(
        Panel(
            Syntax(instructions, "bash", theme="monokai", background_color="default"),
            title=f"[bold]Completion setup for {target_shell}[/bold]",
            border_style="cyan",
        )
    )
    console.print()
    console.print(f"Or run [cyan]gitmap completions --install {target_shell}[/cyan] to add this automatically.")
    console.print()


def _detect_shell() -> str | None:
    """Detect the current shell from environment.

    Returns:
        Shell name ('bash', 'zsh', 'fish') or None if not detected.
    """
    shell_path = os.environ.get("SHELL", "")
    if shell_path.endswith("zsh"):
        return "zsh"
    if shell_path.endswith("bash"):
        return "bash"
    if shell_path.endswith("fish"):
        return "fish"
    return None


def _get_rc_file(shell: str) -> str:
    """Get the appropriate RC file for the given shell.

    Args:
        shell: Shell name.

    Returns:
        Absolute path to the shell RC file.
    """
    home = os.path.expanduser("~")
    mapping = {
        "bash": os.path.join(home, ".bashrc"),
        "zsh": os.path.join(home, ".zshrc"),
        "fish": os.path.join(home, ".config", "fish", "completions", "gitmap.fish"),
    }
    return mapping[shell]


def _auto_install(shell: str) -> None:
    """Auto-install completion configuration into the shell RC file.

    Args:
        shell: Shell name to install for.
    """
    rc_file = _get_rc_file(shell)
    marker = "# gitmap shell completion"

    if shell == "fish":
        # Fish uses a separate file, write the full source command
        rc_dir = os.path.dirname(rc_file)
        os.makedirs(rc_dir, exist_ok=True)
        line = "_GITMAP_COMPLETE=fish_source gitmap | source\n"
        try:
            with open(rc_file, "w") as fh:
                fh.write(f"{marker}\n{line}")
            console.print(f"[green]✓[/green] Installed fish completion to [cyan]{rc_file}[/cyan]")
            console.print("[dim]No shell reload needed — fish auto-sources completions/[/dim]")
        except OSError as err:
            raise click.ClickException(f"Failed to write {rc_file}: {err}") from err
        return

    # bash / zsh — append eval line to RC file
    eval_line = f'eval "$(_GITMAP_COMPLETE={shell}_source gitmap)"\n'

    # Check if already installed
    try:
        if os.path.exists(rc_file):
            with open(rc_file) as fh:
                existing = fh.read()
            if marker in existing or "_GITMAP_COMPLETE" in existing:
                console.print(
                    f"[yellow]⚠[/yellow] Completion already present in [cyan]{rc_file}[/cyan] — no changes made."
                )
                return
    except OSError:
        pass

    try:
        with open(rc_file, "a") as fh:
            fh.write(f"\n{marker}\n{eval_line}")
        console.print(f"[green]✓[/green] Installed {shell} completion to [cyan]{rc_file}[/cyan]")
        console.print(f"[dim]Run [bold]source {rc_file}[/bold] to enable in the current session.[/dim]")
    except OSError as err:
        raise click.ClickException(f"Failed to write {rc_file}: {err}") from err
