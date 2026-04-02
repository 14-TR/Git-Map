# gitmap diff

Show changes between map states — index vs HEAD, branch vs branch, or commit vs commit.

## Usage

```bash
gitmap diff [SOURCE] [TARGET] [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Branch name or commit ID (optional) |
| `TARGET` | Branch name or commit ID (optional) |

When called with no arguments, compares the staging area (index) to HEAD.

## Options

| Option | Description |
|--------|-------------|
| `--verbose, -v` | Show detailed property-level changes |
| `--format [text\|visual\|html]` | Output format (default: `text`) |
| `--output, -o PATH` | Write output to file (used with `--format html`; default: `diff-report.html`) |

## Examples

```bash
# Index vs HEAD (default)
gitmap diff

# Index vs a specific branch
gitmap diff main

# Index vs a specific commit
gitmap diff abc123

# Branch vs branch
gitmap diff main feature/new-layer

# Rich table view in terminal
gitmap diff main feature --format visual

# Export shareable HTML report
gitmap diff main feature --format html
gitmap diff main feature --format html --output /tmp/my-diff.html

# Verbose: show per-field changes
gitmap diff --verbose
```

## Output Formats

### `text` (default)

Plain summary listing added, removed, and modified layers.

```
Added layers (1):
  + Flood Zones (layer-001)
Modified layers (1):
  ~ Parcels (layer-002)
Removed layers (1):
  - Old Boundaries (layer-003)
```

### `visual`

Rich table with color-coded rows in the terminal.

```
╭─ GitMap Diff ──────────────────────────────────────╮
│ index → HEAD (a3f9c12)                              │
│ +1 added  ~1 modified  -1 removed                  │
╰────────────────────────────────────────────────────╯
  + Flood Zones       Added in index
  ~ Parcels           1 field(s) changed
  - Old Boundaries    Removed in index (present in HEAD)
```

### `html`

Self-contained dark-themed HTML report with:
- Stats badges (added / removed / modified counts)
- Color-coded diff table
- Expanded JSON detail block for modified layers
- Footer with generation timestamp

Useful for sharing diffs with stakeholders who don't have GitMap installed.

```bash
gitmap diff main staging --format html --output staging-diff.html
# ✓ HTML report written to /path/to/staging-diff.html
```

## See Also

- [`gitmap log`](log.md) — view commit history
- [`gitmap context`](context.md) — visualize event history
