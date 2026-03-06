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
pip install gitmap-core
```

Then see the [Quickstart](getting-started/quickstart.md) to run your first commit in under 5 minutes.

## Core Workflow

```
gitmap init          # Start tracking a directory
gitmap pull          # Fetch current map from Portal
gitmap commit -m "My change"
gitmap push          # Deploy to Portal
```

## Compatibility

- **ArcGIS Online** — fully supported
- **Portal for ArcGIS** (10.8+) — supported
- **Python** 3.11 · 3.12 · 3.13
- **OS** — macOS, Linux, Windows

---

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[CLI Reference →](commands/index.md){ .md-button }
