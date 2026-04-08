# Git-Map

**Version control for ArcGIS web maps.**

[![CI](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml/badge.svg)](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gitmap.svg)](https://pypi.org/project/gitmap/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-734%2B-brightgreen)](https://github.com/14-TR/Git-Map/actions)

Git-Map brings familiar Git workflows to ArcGIS Online and Portal for ArcGIS. Clone a web map, make changes in a branch, inspect diffs, merge safely, and push the approved version back to Portal.

```bash
$ gitmap clone a1b2c3d4e5f6
Cloned "County Flood Risk" into county-flood-risk

$ gitmap branch feature/new-basemap
Created branch feature/new-basemap

$ gitmap diff --branch main
~ operationalLayers[2].visibility: false -> true
+ operationalLayers[5]: "Hydrants"

$ gitmap commit -m "Add hydrants layer and enable parcels"
[feature/new-basemap 8f2a1d9] Add hydrants layer and enable parcels

$ gitmap push --branch feature/new-basemap
Pushed feature/new-basemap to Portal
```

## Why Git-Map?

ArcGIS web maps are JSON documents with real history, but most teams still manage them like opaque portal items. That creates a few recurring problems:

- changes land without a clear audit trail
- experimentation is risky because production maps are easy to overwrite
- it is hard to answer simple questions like “what changed?” or “who changed it?”
- moving fixes between environments is mostly manual

Git-Map solves that with version-control primitives GIS teams already understand:

- **commit history** for every saved map state
- **branches** for safe experiments and parallel work
- **diffs** that show exactly what changed in the map JSON
- **merge + revert** workflows for safer releases and rollbacks
- **push/pull sync** between your local repo and ArcGIS Portal or ArcGIS Online

## What you can do with it

- track a single critical map with commits and rollback points
- compare production vs staging before publishing
- branch a map for cartography or popup experiments
- bulk-clone many maps with `setup-repos`
- keep repositories synced with Portal using `auto-pull`
- visualize history with the context graph tools
- expose Git-Map operations to other tooling through its integrations

## Install

### Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- ArcGIS Online or Portal for ArcGIS access

### Install from PyPI

```bash
pip install gitmap
```

Verify:

```bash
gitmap --version
```

### Install from source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
pip install -e "packages/gitmap_core[dev]"
pip install -e apps/cli/gitmap
```

## 5-minute quickstart

### 1. Configure credentials

Copy the example environment file:

```bash
cp configs/env.example .env
```

Then set your portal details:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

`.env` is ignored by Git and should never be committed.

### 2. Clone an existing web map

```bash
gitmap clone abc123def456
cd MyWebMap
```

If you want to start a repo from scratch instead:

```bash
gitmap init --project-name "Flood Risk Map"
```

### 3. Create a branch for your change

```bash
gitmap branch feature/hydrology-update
gitmap checkout feature/hydrology-update
```

### 4. Make edits and review the diff

After editing the tracked map files:

```bash
gitmap status
gitmap diff --branch main
```

### 5. Commit and push

```bash
gitmap commit -m "Add hydrology layer"
gitmap push --branch feature/hydrology-update
```

### 6. Merge when approved

```bash
gitmap checkout main
gitmap merge feature/hydrology-update
gitmap push
```

That is the core Git-Map loop: **clone or init -> branch -> change -> diff -> commit -> push -> merge**.

## Typical workflows

### Safe experimentation on production maps

```bash
gitmap checkout main
gitmap branch feature/try-new-basemap
gitmap checkout feature/try-new-basemap

# edit the map

gitmap diff --branch main
gitmap commit -m "Try imagery basemap"
```

### Review what changed before a release

```bash
gitmap diff --branch main
gitmap log --limit 10
gitmap show HEAD
```

### Roll back a bad change

```bash
gitmap log --limit 20
gitmap revert <commit-id>
gitmap push
```

### Manage many maps at once

```bash
gitmap setup-repos --owner myusername --directory repositories
gitmap auto-pull --directory repositories --auto-commit
```

## Command groups

### Repository setup

- `gitmap init` — initialize a new repository
- `gitmap clone` — clone a web map from Portal
- `gitmap setup-repos` — bulk clone maps into a directory

### Snapshot and history

- `gitmap status` — inspect working tree state
- `gitmap commit -m "message"` — record a snapshot
- `gitmap log` — show commit history
- `gitmap show` — inspect a commit in detail
- `gitmap diff` — compare working tree, branch, or commit state
- `gitmap tag` — create or manage tags
- `gitmap revert` — reverse a previous commit
- `gitmap stash` — save or restore in-progress changes
- `gitmap cherry-pick` — apply a commit onto the current branch

### Branching and merges

- `gitmap branch` — list or create branches
- `gitmap checkout` — switch branches
- `gitmap merge` — merge into the current branch
- `gitmap merge-from` — merge from another repository

### Remote sync

- `gitmap push` — push a branch to ArcGIS Portal
- `gitmap pull` — pull the latest remote changes
- `gitmap auto-pull` — sync many repositories automatically

### Portal utilities

- `gitmap list` — search available web maps
- `gitmap lsm` — transfer popup and form settings between maps
- `gitmap notify` — notify Portal group members through ArcGIS APIs

### Tooling

- `gitmap config` — manage repository settings
- `gitmap context` — visualize event history and relationships
- `gitmap daemon` — manage scheduled auto-pull updates
- `gitmap doctor` — check your environment for common issues
- `gitmap completions` — generate shell completion scripts

Run `gitmap COMMAND --help` for command-specific options and examples.

## Key features

- **Git-style workflows for GIS** — familiar commands for branching, commits, history, and merges
- **Property-level diffs** — inspect what changed in a web map instead of guessing
- **Context graph** — visualize events and relationships over time
- **Bulk operations** — onboard or sync many maps efficiently
- **Portal-aware utilities** — manage notifications and layer setting transfers
- **Minimal runtime requirements** — standard Python CLI, no heavyweight platform needed

## Configuration

Git-Map supports several ways to provide credentials and repository settings.

### Environment variables

| Variable | Description |
|---|---|
| `PORTAL_URL` | Portal or ArcGIS Online URL |
| `PORTAL_USER` | Portal username |
| `PORTAL_PASSWORD` | Portal password |
| `ARCGIS_USERNAME` | Alternate username variable |
| `ARCGIS_PASSWORD` | Alternate password variable |

### Repository config

Each repository stores Git-Map metadata in `.gitmap/config.json`.

Example:

```json
{
  "version": "1.0",
  "user_name": "Jane Smith",
  "user_email": "jane@example.com",
  "project_name": "FloodRisk",
  "remote": {
    "name": "origin",
    "url": "https://www.arcgis.com",
    "folder_id": "abc123",
    "item_id": "def456"
  }
}
```

## Development

### Project layout

```text
Git-Map/
├── apps/
│   └── cli/gitmap/                # CLI package
├── packages/
│   ├── gitmap_core/               # Core library
│   └── gitmap_core/tests/         # Core test suite
├── configs/                       # Example configuration
├── docs/                          # Documentation site content
├── documentation/                 # Internal design/spec material
└── integrations/openclaw/tests/   # Integration tests
```

### Local dev install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/gitmap_core[dev]"
pip install -e apps/cli/gitmap
```

### Run tests

```bash
python -m pytest packages/gitmap_core/tests integrations/openclaw/tests -x -q
```

## Documentation and support

- Documentation site: <https://14-tr.github.io/Git-Map/>
- Technical paper: <https://14-tr.github.io/Git-Map/technical-paper/>
- Issues: <https://github.com/14-TR/Git-Map/issues>
- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## Contributing

Contributions are welcome. If you are fixing a bug or adding a feature:

1. create a branch
2. add or update tests
3. keep the CLI behavior stable unless the change is intentional
4. open a PR with a clear explanation of what changed and why

## License

MIT — see [LICENSE](LICENSE).
