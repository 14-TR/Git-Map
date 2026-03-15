# gitmap log

Show commit history for the current branch (or all branches with `--graph`).

## Usage

```bash
gitmap log [OPTIONS]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-n` | 10 | Maximum number of commits to show |
| `--oneline` | | false | Compact one-line format |
| `--graph` | | false | Visual ASCII commit graph with branch labels |
| `--branch` | `-b` | *(current)* | Show history for a specific branch |

## Examples

```bash
# Show last 10 commits on current branch
gitmap log

# Show last 5 commits
gitmap log -n 5

# One-line compact format
gitmap log --oneline

# Visual ASCII commit graph (all branches)
gitmap log --graph

# Graph in compact one-line format
gitmap log --graph --oneline

# Show history for a specific branch
gitmap log --branch feature/new-layer
gitmap log -b main --oneline
```

## Default output

```
commit a3f2c1b0e5f1d2c3b4a5960718293a4b5c6d7e8f (HEAD -> main)
Author: Jane Smith
Date:   2024-06-15 10:23:04
Parent: 9e1b4a22

    Added flood layer
    (3 layer(s))

commit 9e1b4a22d3f4e5b6c7a8091011121314151617181
Author: Jane Smith
Date:   2024-06-14 14:05:11

    Initial snapshot
    (2 layer(s))
```

## One-line output (`--oneline`)

```
* a3f2c1b0  Added flood layer
  9e1b4a22  Initial snapshot
```

The `*` marker indicates HEAD.

## Graph output (`--graph`)

```
* a3f2c1b0 (HEAD -> main) Merged feature/new-basemap
|\
| * d2e3f4a5 (feature/new-basemap) Add satellite basemap
| * c1b2a3d4 Update label style
* | b0a1c2d3 Fix symbology on Parcels
|/
* 9e1b4a22 Initial snapshot
```

The graph shows branches diverging (`|`) and merging (`/`, `\`). Branch labels appear in parentheses. `HEAD ->` highlights the current position.

## See also

- [`gitmap show`](show.md) — inspect a single commit in detail
- [`gitmap diff`](diff.md) — compare commits
- [`gitmap branch`](branch.md) — list or create branches
