# GitMap

**Version control for ArcGIS web maps.**

[![CI](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml/badge.svg)](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gitmap.svg)](https://pypi.org/project/gitmap/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-734%2B-brightgreen)](https://github.com/14-TR/Git-Map/actions)

GitMap brings Git-style branching, history, diffs, merges, and rollbacks to ArcGIS Online and Portal web maps.

```bash
$ gitmap clone abc123def456 FloodRiskMap
$ cd FloodRiskMap
$ gitmap branch feature/dark-basemap
$ gitmap checkout feature/dark-basemap
$ gitmap pull
$ gitmap diff main feature/dark-basemap --format visual
$ gitmap commit -m "Switch to dark basemap"
$ gitmap checkout main && gitmap merge feature/dark-basemap && gitmap push
```

## Why teams use GitMap

- **Track every map change** with commit history instead of guessing who changed what.
- **Experiment safely** on branches before touching production maps.
- **Review diffs clearly** at the layer and property level.
- **Roll back fast** when a bad basemap, renderer, popup, or visibility change slips through.
- **Scale beyond one map** with bulk repo setup, auto-pull, and Portal-aware workflows.

## What GitMap gives you

- **Git-like CLI for GIS** — `init`, `clone`, `status`, `commit`, `branch`, `checkout`, `diff`, `log`, `merge`, `push`, `pull`, `revert`, and more
- **ArcGIS-aware diffing** — layer/table additions, removals, and field-level JSON changes
- **Three-way merge support** — branch and merge map changes without manual JSON surgery
- **Shareable outputs** — terminal, visual, JSON, and HTML diff/report formats
- **Automation hooks** — bulk repo setup, auto-pull, context graph exports, and MCP support for AI workflows
- **Cross-platform Python package** — macOS, Linux, and Windows on Python 3.11-3.14

## Install in one step

### Recommended: PyPI

```bash
pip install gitmap
```

Verify it worked:

```bash
gitmap --version
```

### From source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
pip install -e packages/gitmap_core
pip install -e apps/cli/gitmap
```

## Quickstart: first successful workflow

### 1. Set ArcGIS credentials

```bash
export PORTAL_URL=https://your-org.maps.arcgis.com
export ARCGIS_USERNAME=your_username
export ARCGIS_PASSWORD=your_password
```

Or copy the example environment file and edit it:

```bash
cp configs/env.example .env
```

### 2. Clone a web map from ArcGIS

```bash
gitmap clone abc123def456
cd YourMapTitle
```

`abc123def456` is the web map item ID from ArcGIS Online or Portal.

### 3. Confirm the repo is clean

```bash
gitmap status
```

Typical output:

```text
╭─ GitMap Status ─╮
│ On branch: main │
╰─────────────────╯
Nothing to commit, working tree clean
```

### 4. Create a feature branch

```bash
gitmap branch feature/new-basemap
gitmap checkout feature/new-basemap
```

### 5. Make a change and pull it locally

Edit the map in ArcGIS, then sync the latest state into your branch:

```bash
gitmap pull
gitmap status
```

### 6. Review exactly what changed

```bash
gitmap diff main feature/new-basemap --format visual
```

For a shareable stakeholder report:

```bash
gitmap diff main feature/new-basemap --format html --output basemap-review.html
```

### 7. Commit the branch

```bash
gitmap commit -m "Switch to dark basemap"
```

### 8. Merge and deploy

```bash
gitmap checkout main
gitmap merge feature/new-basemap
gitmap push
```

That is the core GitMap loop: **clone → branch → pull → diff → commit → merge → push**.

## Demo workflows

### Branch and compare map changes

```bash
gitmap branch feature/parcel-popup
gitmap checkout feature/parcel-popup
gitmap pull
gitmap diff main feature/parcel-popup --verbose
```

### Inspect history like Git

```bash
gitmap log --graph --oneline
gitmap show HEAD
```

### Revert a bad deployment safely

```bash
gitmap log --oneline
gitmap revert a3f2c1b0
gitmap push
```

### Manage many maps at once

```bash
gitmap setup-repos --owner myusername --directory repositories
gitmap auto-pull --directory repositories --auto-commit
```

## Common commands

| Command | What it does |
|---|---|
| `gitmap clone <ITEM_ID> [PATH]` | Create a local repo from an ArcGIS web map |
| `gitmap status` | Show branch and working tree state |
| `gitmap branch <NAME>` | Create a branch |
| `gitmap checkout <NAME>` | Switch branches |
| `gitmap diff [SOURCE] [TARGET]` | Compare staged state, branches, or commits |
| `gitmap commit -m "message"` | Save the current map state as a commit |
| `gitmap log --graph --oneline` | View history with branch context |
| `gitmap merge <BRANCH>` | Merge a feature branch |
| `gitmap push` | Publish the current state back to ArcGIS |
| `gitmap pull` | Fetch the latest ArcGIS state into the repo |
| `gitmap revert <COMMIT>` | Restore a previous commit without rewriting history |
| `gitmap setup-repos` | Bulk-clone many maps |
| `gitmap auto-pull` | Sync many repos on a schedule |
| `gitmap context show` | Visualize repo event history |

## Configuration

GitMap looks for credentials in environment variables when repository config is not set.

| Variable | Description |
|---|---|
| `PORTAL_URL` | ArcGIS Online or Portal URL |
| `ARCGIS_USERNAME` | ArcGIS username |
| `ARCGIS_PASSWORD` | ArcGIS password |
| `PORTAL_USER` | Alternate username variable |
| `PORTAL_PASSWORD` | Alternate password variable |

Authentication priority:

1. Command-line options
2. `.env` file
3. ArcGIS Pro session
4. Anonymous access where supported

## Docs and references

- [Installation guide](docs/getting-started/installation.md)
- [Quickstart](docs/getting-started/quickstart.md)
- [Core concepts](docs/getting-started/concepts.md)
- [CLI command reference](docs/commands/index.md)
- [Portal guide](docs/guides/portals.md)
- [Workflow guide](docs/guides/workflow.md)
- [Contributing](docs/contributing.md)
- [Technical paper](docs/technical-paper.md)

## Development

```bash
cd /Users/tr-mini/Projects/git-map
python -m pytest tests/ -x -q
```

Project layout:

```text
Git-Map/
├── apps/cli/gitmap/      # CLI package
├── packages/gitmap_core/ # Core library
├── docs/                 # MkDocs site and command docs
├── configs/              # Example environment/config files
└── tests/                # Test suite
```

## Troubleshooting

**Authentication failed**
- Confirm `PORTAL_URL`, `ARCGIS_USERNAME`, and `ARCGIS_PASSWORD`
- Verify the Portal URL is reachable
- Try passing credentials directly on the command line

**Repository already exists**
- Work inside the existing GitMap repo, or remove `.gitmap/` if you truly want a fresh start

**Need to see what changed before pushing**
- Run `gitmap diff --format visual`
- Use `--verbose` for property-level changes
- Export HTML when you need a shareable review artifact

## Contributing

1. Fork the repo
2. Create a `jig/*` or feature branch
3. Add tests for behavior changes
4. Run the test suite before opening a PR
5. Open a PR with a clear summary and screenshots or sample output when useful

## License

MIT — see [LICENSE](LICENSE).

**GitMap** — the git for GIS.
