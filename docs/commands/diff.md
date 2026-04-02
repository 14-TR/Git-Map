# gitmap diff

Show changes between states — index vs HEAD, two branches, or two commits.

## Usage

```bash
gitmap diff [SOURCE] [TARGET] [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Branch name or commit ID to compare *from* (optional) |
| `TARGET` | Branch name or commit ID to compare *to* (optional; requires SOURCE) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--verbose` | `-v` | false | Show property-level field changes |
| `--format` | | `text` | Output format: `text`, `visual`, or `html` |
| `--output` | `-o` | `diff-report.html` | Output file path (used with `--format html`) |

## Modes

| Arguments provided | What is compared |
|--------------------|-----------------|
| *(none)* | Index (staging area) vs HEAD |
| `SOURCE` only | Index vs that branch or commit |
| `SOURCE TARGET` | SOURCE directly vs TARGET (index not involved) |

## Examples

```bash
# Compare staging area to HEAD
gitmap diff

# Compare staging area to another branch
gitmap diff main

# Compare two branches
gitmap diff main feature/new-basemap

# Compare two commits
gitmap diff abc123 def456

# Visual Rich table output
gitmap diff main feature/new-basemap --format visual

# Export shareable HTML report
gitmap diff main feature --format html
gitmap diff main feature --format html --output /tmp/my-diff.html

# Show field-level changes
gitmap diff --verbose

# Combine: visual + verbose
gitmap diff main feature/new-basemap --format visual -v
```

## Text output (default)

```
╭─ GitMap Diff ──────────────────────────────────╮
│ Comparing index → HEAD (a3f2c1b0)              │
╰─────────────────────────────────────────────────╯

+1 added  ~1 modified

  + Flood Zones
  ~ Parcels  (2 field(s) changed)
```

## Visual output (`--format visual`)

Renders a Rich table with colored diff symbols:

| Symbol | Color | Meaning |
|--------|-------|---------|
| `+` | Green | Layer or table added |
| `-` | Red | Layer or table removed |
| `~` | Yellow | Layer or table modified |
| `*` | Cyan | Map-level property changed |

```
╭─ GitMap Diff ─────────────────────────────────────╮
│ main → feature/new-basemap                        │
│ +1 added  ~1 modified                             │
╰───────────────────────────────────────────────────╯

     Layer / Table           Change
  +  Flood Zones             added
  ~  Parcels                 2 field(s) changed
```

## HTML output (`--format html`)

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

## Verbose mode (`-v`)

With `--verbose`, modified layers show field-level JSON diffs:

```
Detailed Changes:

Layer: Parcels
{
  "opacity": [0.8, 1.0],
  "visible": [false, true]
}
```

## See also

- [`gitmap show`](show.md) — inspect a single commit with its diff
- [`gitmap log`](log.md) — find commit IDs to compare
- [`gitmap commit`](commit.md) — save staged changes as a commit
- [`gitmap context`](context.md) — visualize event history
