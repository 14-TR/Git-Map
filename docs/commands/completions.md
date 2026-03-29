# gitmap completions

Generate and install shell completion scripts for tab-completion support.

## Usage

```bash
gitmap completions [SHELL] [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `SHELL` | Shell to generate completions for: `bash`, `zsh`, or `fish` (optional — auto-detected if omitted) |

## Options

| Option | Description |
|--------|-------------|
| `--install SHELL` | Auto-install the completion snippet into the appropriate shell config file |
| `--print` | Print the raw completion script to stdout (useful for piping) |
| `--help` | Show help and exit |

## Description

`gitmap completions` enables tab-completion in your terminal so pressing `<Tab>` after typing `gitmap` auto-completes command names and options.

It uses Click's built-in completion mechanism. Completions are available for:

- **bash** — adds `eval` line to `~/.bashrc`
- **zsh** — adds `eval` line to `~/.zshrc`
- **fish** — writes completion file to `~/.config/fish/completions/gitmap.fish`

When called with no arguments, `gitmap completions` detects your current shell and shows the appropriate setup instructions.

## Examples

```bash
# Show instructions for your detected shell
gitmap completions

# Show setup instructions for a specific shell
gitmap completions bash
gitmap completions zsh
gitmap completions fish

# Auto-install into ~/.zshrc (then reload your shell)
gitmap completions --install zsh

# Auto-install for bash
gitmap completions --install bash

# Print the raw script (for manual inspection or piping)
gitmap completions --print bash > /tmp/gitmap-completions.bash
```

## Example Output

```
GitMap Shell Completions

Enable tab-completion so pressing <Tab> auto-completes commands and options.

Detected shell: zsh

Usage:
  gitmap completions bash       — show bash setup instructions
  gitmap completions zsh        — show zsh  setup instructions
  gitmap completions fish       — show fish setup instructions
  gitmap completions --install zsh  — auto-install into ~/.zshrc
```

## Auto-Install

The `--install` flag modifies your shell config file directly, appending the eval hook after a `# gitmap shell completion` marker. It checks for an existing installation and skips if already present — safe to run multiple times.

```bash
$ gitmap completions --install zsh
✓ Installed zsh completion to /Users/you/.zshrc
Run source ~/.zshrc to enable in the current session.
```

## Manual Setup

If you prefer to manage your shell config manually:

**bash** — add to `~/.bashrc` or `~/.bash_profile`:

```bash
eval "$(_GITMAP_COMPLETE=bash_source gitmap)"
```

**zsh** — add to `~/.zshrc`:

```bash
eval "$(_GITMAP_COMPLETE=zsh_source gitmap)"
```

**fish** — add to `~/.config/fish/completions/gitmap.fish`:

```fish
_GITMAP_COMPLETE=fish_source gitmap | source
```

## See Also

- [`gitmap doctor`](doctor.md) — verify your GitMap environment
- [`gitmap --help`](index.md) — list all available commands
