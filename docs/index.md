# Git-Map

**Version control for ArcGIS web maps.**

Git-Map brings familiar Git-style workflows to ArcGIS Online and Portal for ArcGIS. Branch your maps, commit changes, diff versions, merge branches, and push/pull from your portal — all from the command line.

---

## Why Git-Map?

| Problem | Git-Map Solution |
|---------|-----------------|
| Web maps change without history | Every state is a commit you can revisit |
| No way to experiment safely | Branches let you iterate without breaking production |
| Collaboration is overwrite-prone | Merge branches, review diffs before applying |
| Deployments are manual and fragile | `gitmap push` syncs the right version to Portal |
| Rollbacks require memory | `gitmap revert` restores any previous commit |

## Quick Install

```bash
pip install gitmap
```

Then see the [Quickstart](getting-started/quickstart.md) to run your first commit in under 5 minutes.

## Core Workflow

```bash
gitmap init          # Start tracking a directory
gitmap pull          # Fetch current map from Portal
gitmap commit -m "My change"
gitmap push          # Deploy to Portal
```

## Feature Highlights

- **18+ CLI commands** — init, clone, commit, branch, checkout, diff, log, merge, push, pull, revert, stash, tag, cherry-pick, and more
- **Three-way merge** — layer-atomic merge algorithm adapted for ArcGIS web map JSON
- **Rich diff engine** — property-level diffs powered by DeepDiff, showing exactly what changed
- **Context graph** — SQLite-backed event history with timeline visualization
- **MCP server** — expose all operations to AI coding agents (Cursor, Claude, etc.)
- **ArcGIS Pro toolbox** — native Python Toolbox with 9 tools for the Pro ribbon UI
- **Bulk operations** — `setup-repos` and `auto-pull` for managing dozens of maps at once

## Compatibility

- **ArcGIS Online** — fully supported
- **Portal for ArcGIS** (10.8+) — supported
- **Python** 3.11 · 3.12 · 3.13 · 3.14
- **OS** — macOS, Linux, Windows

---

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[CLI Reference →](commands/index.md){ .md-button }
