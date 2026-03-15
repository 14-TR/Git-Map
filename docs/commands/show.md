# gitmap show

Show details of a specific commit — metadata, layer summary, and diff against its parent.

## Usage

```bash
gitmap show [OPTIONS] [REF]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `REF` | Commit ID (full or partial), or branch name. Defaults to HEAD. |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--verbose` | `-v` | false | Show property-level change details |
| `--no-diff` | | false | Show only metadata and layer summary (skip diff) |
| `--format` | | `text` | Diff output format: `text` (plain lines) or `visual` (Rich table) |

## Examples

```bash
# Show HEAD commit
gitmap show

# Show a specific commit by short hash
gitmap show abc123

# Show the tip of a branch
gitmap show feature/new-layer

# Show with a visual diff table
gitmap show --format visual

# Show with field-level diff details
gitmap show -v

# Show metadata and layers only (no diff)
gitmap show --no-diff

# Combine: visual format with verbose details
gitmap show abc123 --format visual -v
```

## Output

```
╭─ gitmap show HEAD ──────────────────────────────╮
│ Showing commit a3f2c1b0                         │
╰─────────────────────────────────────────────────╯

commit a3f2c1b0e5f1d2c3b4a5960718293a4b5c6d7e8f
Author:    Jane Smith
Date:      2024-06-15 10:23:04
Parent:    9e1b4a22

    Added flood risk layer

─── Layer Summary ────────────────────────────────
 Type    Title                         Visible
 layer   Flood Zones                   yes
 layer   Parcels                       yes
 layer   City Boundaries               yes
  3 layer(s), 0 table(s)

─── Changes vs Parent ────────────────────────────
  +1 added  ~1 modified

  + Flood Zones
  ~ Parcels  (2 field(s) changed)
```

## Visual format (`--format visual`)

The visual format renders changes as a Rich table with colored symbols:

| Symbol | Color | Meaning |
|--------|-------|---------|
| `+` | Green | Layer or table added |
| `-` | Red | Layer or table removed |
| `~` | Yellow | Layer or table modified |
| `*` | Cyan | Map-level property changed |

## Verbose mode (`-v`)

With `--verbose`, modified layers show field-level JSON diffs:

```
commit a3f2c1b0 (HEAD -> main)
...

─── Changes vs Parent ────────────────────────────
  ~1 modified

  ~ Parcels  (2 field(s) changed)

  Parcels:
  {
    "opacity": [0.8, 1.0],
    "visible": [false, true]
  }
```

## See also

- [`gitmap log`](log.md) — list commits to find a REF
- [`gitmap diff`](diff.md) — compare commits or working tree
- [`gitmap commit`](commit.md) — create a commit
