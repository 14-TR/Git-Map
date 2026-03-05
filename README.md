# GitMap

**Version control for ArcGIS web maps.**

[![CI](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml/badge.svg)](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-450%2B-brightgreen)](https://github.com/14-TR/Git-Map/actions)

GitMap brings Git-like version control to ArcGIS Online and Enterprise Portal web maps. Branch, commit, diff, merge, push, and pull maps using workflows your team already knows.

```
$ gitmap commit -m "Added flood risk layer"
[main a3f9c12] Added flood risk layer
 1 layer changed

$ gitmap diff --branch main
~ Layer: Parcels
  opacity: 0.8 → 1.0
  visible: false → true

$ gitmap merge feature/new-basemap
Merged feature/new-basemap into main
```

---

## Why GitMap?

| Problem | GitMap Solution |
|---|---|
| "Who changed the basemap last Tuesday?" | `gitmap log` — full commit history with author + timestamp |
| "Can I test this symbology without breaking prod?" | `gitmap branch feature/symbology` — isolated branches |
| "Revert to last week's version" | `gitmap checkout <commit-id>` |
| "What's different between staging and production?" | `gitmap diff --branch production` |
| "Keep 50 maps in sync with Portal" | `gitmap auto-pull` |

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Usage Examples](#usage-examples)
- [Docker Setup](#docker-setup)
- [Development](#development)
- [Architecture](#architecture)

---

## Installation

### Prerequisites

- Python 3.11, 3.12, or 3.13
- ArcGIS Portal or ArcGIS Online account
- pip

### Install from Source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map

# Install core library
pip install -e packages/gitmap_core

# Install CLI
pip install -e apps/cli/gitmap
```

### Verify Installation

```bash
gitmap --version
# gitmap, version 0.6.0
```

---

## Quick Start

### 1. Configure Authentication

```bash
cp configs/env.example .env
```

Edit `.env`:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

> **Note:** `.env` is git-ignored and never committed.

### 2. Initialize a Repository

```bash
gitmap init --project-name "Flood Risk Map"
```

### 3. Clone an Existing Map from Portal

```bash
gitmap clone abc123def456
```

### 4. Create a Branch, Edit, Commit

```bash
gitmap branch feature/new-layer
gitmap checkout feature/new-layer

# Edit your map JSON files...

gitmap status
gitmap commit -m "Added hydrology layer"
```

### 5. Push Back to Portal

```bash
gitmap push
```

### 6. Merge When Ready

```bash
gitmap checkout main
gitmap merge feature/new-layer
gitmap push
```

---

## Configuration

### Repository Config (`.gitmap/config.json`)

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

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PORTAL_URL` | Portal or AGOL URL | `https://www.arcgis.com` |
| `PORTAL_USER` | Username | — |
| `PORTAL_PASSWORD` | Password | — |
| `ARCGIS_USERNAME` | Alternative username var | — |
| `ARCGIS_PASSWORD` | Alternative password var | — |

### Authentication Priority

1. Command-line options (`--username`, `--password`)
2. `.env` file
3. ArcGIS Pro session (if running inside Pro)
4. Anonymous (limited)

---

## CLI Commands

| Command | Description |
|---|---|
| `gitmap init` | Initialize a new repository |
| `gitmap clone <item_id>` | Clone a web map from Portal |
| `gitmap status` | Show working tree status |
| `gitmap commit -m "msg"` | Record changes |
| `gitmap branch [name]` | List or create branches |
| `gitmap checkout <branch>` | Switch branches |
| `gitmap diff` | Show changes |
| `gitmap log` | Show commit history |
| `gitmap merge <branch>` | Merge branches |
| `gitmap push` | Push to Portal |
| `gitmap pull` | Pull from Portal |
| `gitmap list` | List Portal web maps |
| `gitmap setup-repos` | Bulk clone multiple maps |
| `gitmap auto-pull` | Sync all repos with Portal |
| `gitmap lsm` | Transfer layer popup/form settings |
| `gitmap notify` | Notify Portal group members |
| `gitmap context` | Visualize event history |
| `gitmap config` | Manage repo configuration |

---

### `gitmap init`

```bash
gitmap init [PATH] [OPTIONS]

Options:
  --project-name, -n TEXT   Project name (defaults to directory name)
  --user-name, -u TEXT      Default author name for commits
  --user-email, -e TEXT     Default author email for commits

Examples:
  gitmap init
  gitmap init --project-name "Flood Risk Map"
  gitmap init /path/to/project --user-name "Jane Smith"
```

### `gitmap clone`

```bash
gitmap clone <ITEM_ID> [OPTIONS]

Options:
  --directory, -d TEXT   Clone into this directory (defaults to map title)
  --url, -u TEXT         Portal URL (defaults to ArcGIS Online)
  --username TEXT        Portal username (or use env var)

Examples:
  gitmap clone abc123def456
  gitmap clone abc123def456 --directory my-project
  gitmap clone abc123def456 --url https://portal.example.com
```

### `gitmap setup-repos`

Bulk clone multiple web maps into a `repositories/` directory.

```bash
gitmap setup-repos [OPTIONS]

Options:
  --directory, -d TEXT     Output directory (default: repositories)
  --owner, -o TEXT         Filter by owner username
  --query, -q TEXT         Search query (e.g. 'title:MyMap')
  --tag, -t TEXT           Filter by tag
  --max-results, -m INT    Max maps to clone (default: 100)
  --skip-existing          Skip already-cloned maps

Examples:
  gitmap setup-repos --owner myusername
  gitmap setup-repos --tag production --skip-existing
  gitmap setup-repos --query "title:Project*" --max-results 50
```

### `gitmap auto-pull`

Sync all GitMap repositories in a directory with Portal.

```bash
gitmap auto-pull [OPTIONS]

Options:
  --directory, -d TEXT     Directory of repos (default: repositories)
  --branch, -b TEXT        Branch to pull (default: main)
  --auto-commit            Commit changes after pull
  --commit-message, -m TEXT  Template: use {repo} and {date}
  --skip-errors            Continue on failure

Examples:
  gitmap auto-pull
  gitmap auto-pull --auto-commit
  gitmap auto-pull --commit-message "Sync from Portal on {date}"

# Automate with cron (every hour):
  0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit
```

### `gitmap list`

```bash
gitmap list [OPTIONS]

Options:
  --query, -q TEXT      Search query
  --owner, -o TEXT      Filter by owner
  --tag, -t TEXT        Filter by tag
  --max-results, -m INT Max results (default: 100)

Examples:
  gitmap list
  gitmap list --owner myusername --tag production
  gitmap list --query "title:MyMap"
```

### `gitmap status`

Show the working tree status — current branch, staged/unstaged changes, untracked files.

```bash
gitmap status
```

### `gitmap branch`

```bash
gitmap branch [BRANCH_NAME] [OPTIONS]

Options:
  --delete, -d    Delete a branch
  --list, -l      List all branches

Examples:
  gitmap branch                    # List branches
  gitmap branch feature/new-layer  # Create branch
  gitmap branch -d feature/old     # Delete branch
```

### `gitmap checkout`

```bash
gitmap checkout <BRANCH_NAME>

Examples:
  gitmap checkout feature/new-layer
  gitmap checkout main
```

### `gitmap commit`

```bash
gitmap commit [OPTIONS]

Options:
  --message, -m TEXT   Commit message (required)
  --author TEXT        Override commit author

Examples:
  gitmap commit -m "Added hydrology layer"
  gitmap commit -m "Fixed visibility" --author "Jane Smith"
```

### `gitmap diff`

```bash
gitmap diff [OPTIONS]

Options:
  --branch, -b TEXT   Compare with branch
  --commit, -c TEXT   Compare with commit

Examples:
  gitmap diff                  # Working tree changes
  gitmap diff --branch main    # vs main branch
  gitmap diff --commit abc123  # vs specific commit
```

### `gitmap log`

```bash
gitmap log [OPTIONS]

Options:
  --branch, -b TEXT   Log for specific branch
  --limit, -n INT     Limit number of commits

Examples:
  gitmap log
  gitmap log --limit 10
```

### `gitmap merge`

```bash
gitmap merge <BRANCH_NAME>

Example:
  gitmap merge feature/new-layer
```

### `gitmap push` / `gitmap pull`

```bash
gitmap push [--branch BRANCH] [--url URL] [--username USER]
gitmap pull [--branch BRANCH] [--url URL] [--username USER]
```

### `gitmap lsm`

Transfer `popupInfo` and `formInfo` between maps.

```bash
gitmap lsm <SOURCE> [TARGET] [OPTIONS]

Options:
  --dry-run   Preview changes without applying

Arguments:
  SOURCE   item ID, branch name, commit ID, or file path
  TARGET   optional; defaults to current index

Examples:
  gitmap lsm main feature/new-layer
  gitmap lsm abc123def456
  gitmap lsm source.json target.json --dry-run
  gitmap lsm ../other-repo
```

### `gitmap notify`

Send notifications to Portal group members via ArcGIS API.

```bash
gitmap notify --group <GROUP_ID_OR_TITLE> --subject "Subject" --message "Body"

Options:
  --group, -g TEXT       Group ID or title (required)
  --user TEXT            Specific username (repeatable; omit for all members)
  --subject, -s TEXT     Subject line
  --message, -m TEXT     Message body
  --message-file TEXT    Load message from file

Examples:
  gitmap notify --group editors --subject "New release" --message "Basemap updated."
  gitmap notify --group editors --user testuser --subject "Test" --message "Hello"
  gitmap notify --group "Field Crew" --subject "Prep" --message-file notes.txt
```

### `gitmap context`

Visualize event history and relationships.

```bash
gitmap context <show|export|timeline|graph> [OPTIONS]

show / timeline options:
  --format, -f TEXT   ascii | mermaid | mermaid-timeline (default: ascii)
  --limit, -n INT     Max events (default: 20)
  --type, -t TEXT     Filter: commit|push|pull|merge|branch|diff

export options:
  --format, -f TEXT   mermaid | mermaid-timeline | mermaid-git | ascii | ascii-graph | html
  --output, -o TEXT   Output file
  --theme TEXT        light | dark (HTML only)
  --title TEXT        Visualization title

Examples:
  gitmap context show
  gitmap context show --format mermaid --type commit --type push
  gitmap context export --format html --theme dark -o history.html
  gitmap context timeline
```

### `gitmap config`

```bash
gitmap config [OPTIONS]

Options:
  --production-branch, -p TEXT   Set production branch
  --unset-production             Remove production branch
  --auto-visualize               Enable auto context graph
  --no-auto-visualize            Disable auto context graph

Examples:
  gitmap config                              # View config
  gitmap config --production-branch main
  gitmap config --auto-visualize
```

---

## Usage Examples

### Bulk Repository Setup

```bash
gitmap setup-repos --owner myusername --directory my-maps
cd my-maps/MyWebMap
gitmap status
gitmap commit -m "Updated symbology"
gitmap push
```

### Keep Repositories in Sync

```bash
# Manual sync
gitmap auto-pull

# Automated (cron, every hour)
0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit
```

### Feature Branch Workflow

```bash
gitmap checkout main
gitmap branch feature/add-basemap
gitmap checkout feature/add-basemap

# Edit map JSON files...

gitmap diff
gitmap commit -m "Added satellite basemap option"
gitmap push --branch feature/add-basemap

gitmap checkout main
gitmap merge feature/add-basemap
gitmap push
```

### Compare Versions

```bash
gitmap diff --branch main
gitmap diff --commit abc123
gitmap log --limit 20
```

### Transfer Layer Settings

```bash
# Preview
gitmap lsm main feature/new-layer --dry-run

# Apply
gitmap lsm main feature/new-layer

# From Portal item ID
gitmap lsm abc123def456
```

---

## Docker Setup

```bash
# Interactive dev shell
docker-compose up dev

# Run specific app
APP_GROUP=cli APP_NAME=gitmap docker-compose up app
```

---

## Development

### Project Structure

```
Git-Map/
├── apps/
│   └── cli/gitmap/          # CLI application (gitmap-cli 0.6.0)
├── packages/
│   └── gitmap_core/         # Core library (gitmap_core 0.6.0)
├── configs/                 # Config templates (.env.example)
├── docker/                  # Docker config
└── documentation/           # Specs and design docs
```

### Install for Development

```bash
pip install -e "packages/gitmap_core[dev]"
pip install -e apps/cli/gitmap
```

### Run Tests

```bash
# All tests
cd Git-Map && python -m pytest tests/ -x -q

# With coverage
python -m pytest packages/gitmap_core/tests --cov=packages/gitmap_core --cov-report=term-missing
```

### Code Standards

- Python 3.11+
- PEP 8, PEP 257
- Type hints required
- `pathlib.Path` for file operations

### CI

Tests run automatically on every push and PR via [GitHub Actions](https://github.com/14-TR/Git-Map/actions) across Python 3.11, 3.12, and 3.13.

---

## Architecture

### Core Components

**`gitmap_core`** — Core library:
- Repository management (`.gitmap/` structure)
- Portal authentication and connection
- Web map JSON diffing and merging
- Remote push/pull operations
- Context graph visualization

**`gitmap-cli`** — CLI layer:
- 18 Git-like commands
- Rich terminal output with colors
- User-friendly error messages

### Repository Layout

```
.gitmap/
├── config.json      # Repo settings
├── HEAD             # Current branch ref
├── index.json       # Staging area
├── refs/
│   └── heads/       # Branch refs
└── objects/
    └── commits/     # Commit snapshots
```

### Data Model

| Concept | Description |
|---|---|
| **Commit** | Snapshot of a map's JSON state + metadata |
| **Branch** | Named pointer to a commit |
| **Remote** | Portal connection config |
| **Index** | Staging area (like `git add`) |

---

## Troubleshooting

**Authentication errors**
- Check `.env` exists and credentials are correct
- Verify `PORTAL_URL` points to the right instance
- Try passing `--username` / `--password` directly

**"Not connected. Call connect() first"**
- Portal authentication failed — check `.env` config

**"Repository already exists"**
- Remove `.gitmap/` directory to start fresh, or work within the existing repo

**"Failed to connect to Portal"**
- Verify Portal URL is reachable from your network
- Check firewall / VPN settings

---

## Contributing

1. Fork the repo and create a `jig/*` branch
2. Follow code standards (PEP 8, type hints, docstrings)
3. Add tests for new features — keep coverage above 90%
4. Open a PR with a clear description of what changed and why

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Support & Community

- [Open an issue](https://github.com/14-TR/Git-Map/issues)
- [View documentation](documentation/)
- [Changelog](CHANGELOG.md)

---

**GitMap** — The git for GIS.
