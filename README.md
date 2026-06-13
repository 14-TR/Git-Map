# GitMap

**Version control for ArcGIS web maps.**

[![CI](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml/badge.svg)](https://github.com/14-TR/Git-Map/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gitmap-cli.svg)](https://pypi.org/project/gitmap-cli/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-825%2B-brightgreen)](https://github.com/14-TR/Git-Map/actions)

GitMap brings familiar Git workflows to ArcGIS Online and Portal for ArcGIS. Clone a web map, make changes in a branch, inspect exactly what changed, merge safely, and push the approved version back to Portal.

```bash
$ gitmap clone abc123def456
Cloned "County Flood Risk" into county-flood-risk

$ cd county-flood-risk
$ gitmap branch feature/new-basemap
Created branch feature/new-basemap

$ gitmap checkout feature/new-basemap
Switched to branch feature/new-basemap

$ gitmap pull
Pulled latest web map JSON from Portal

$ gitmap diff --format visual
~ operationalLayers[2].visibility: false -> true
+ operationalLayers[5]: "Hydrants"

$ gitmap commit -m "Add hydrants layer and enable parcels"
[feature/new-basemap 8f2a1d9] Add hydrants layer and enable parcels

$ gitmap diff main feature/new-basemap --format visual

$ gitmap checkout main
$ gitmap merge feature/new-basemap
$ gitmap push
Pushed main to Portal
```

## Demo

A 60-90 second demo script is available at [`marketing/demo-script.md`](marketing/demo-script.md). The planned recording will show the safe test-map workflow: clone, branch, pull/edit, diff, commit, merge, and push.

Until the video or GIF is recorded, the script documents the exact commands, narration, and safety notes for the first public demo.

## Why GIS teams use GitMap

ArcGIS web maps are JSON documents with real history, but most teams still manage them like opaque Portal items. That creates familiar problems:

- production maps get overwritten without a clear audit trail
- cartography, popup, layer, and renderer experiments are risky
- reviewing “what changed?” usually means manual Portal inspection
- promoting fixes between staging and production is repetitive
- rolling back a bad map change is slower than it should be

GitMap adds version-control primitives GIS teams already understand:

- **commit history** for every saved map state
- **branches** for safe experiments and parallel work
- **ArcGIS-aware diffs** for layers, tables, renderers, popups, and JSON properties
- **merge and revert workflows** for safer releases and rollbacks
- **push/pull sync** between local repositories and ArcGIS Online or Portal
- **automation hooks** for bulk map repositories, scheduled pulls, and AI-assisted workflows

## Install

### Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- Access to ArcGIS Online or Portal for ArcGIS
- A web map item ID for the first repository you want to clone

### Current supported install path

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e apps/cli/gitmap
```

Use a Python 3.11+ interpreter when creating the virtual environment. On systems where `python3` still points to Python 3.9 or 3.10, use an explicit executable such as `python3.11`, `python3.12`, or `python3.13`.

This installs the `gitmap` console command from the current checkout. Verify the CLI is available:

```bash
gitmap --version
gitmap --help
gitmap doctor
```

The `gitmap-cli` PyPI package is not currently a supported first-user install path. Until published installs are verified for supported Python versions, use the source install flow above.

## Quickstart: first successful workflow

This walkthrough starts with an existing ArcGIS web map and finishes by pushing an approved main-branch state back to Portal. For your first run, use a non-production test web map that you own or can safely modify.

Before you start, verify that the item ID comes from the ArcGIS web map item URL and that the map is safe to test against. `gitmap clone` reads from Portal and creates a local repository; `gitmap push` is the step that can update ArcGIS-managed content.

### 1. Configure Portal credentials

GitMap can read credentials from environment variables or from a local `.env` file. The repo includes a template:

```bash
cp configs/env.example .env
```

Edit `.env` with your Portal details:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

GitMap also accepts the alternate username/password names used by several ArcGIS tools:

```env
ARCGIS_USERNAME=your_username
ARCGIS_PASSWORD=your_password
```

`.env` is ignored by Git and should never be committed.

### 2. Clone a web map

Copy the web map item ID from ArcGIS Online or Portal, then clone it:

- Open the web map item page in ArcGIS Online or Portal.
- Copy the `id` value from the URL, such as `...?id=abc123def456`.
- Use a test map first. `clone`, `status`, `diff`, `log`, and `commit` work locally, but `push` can update ArcGIS content.

```bash
gitmap clone abc123def456
cd YourMapTitle
```

To choose the local folder name yourself:

```bash
gitmap clone abc123def456 --directory flood-risk-map
cd flood-risk-map
```

The clone command creates a local GitMap repository containing the web map JSON, GitMap metadata, and an initial commit for the current Portal state. It does not modify the Portal item.

If install, package, credential, or current-directory checks are unclear before cloning, run:

```bash
gitmap doctor
gitmap doctor --portal
```

`gitmap doctor` checks the local environment without writing to Portal. The `--portal` option attempts a connectivity check against the configured ArcGIS organization.

### 3. Check the starting state

```bash
gitmap status
gitmap log --limit 5
```

You should be on `main` with a clean working tree after the initial clone.

### 4. Create a feature branch

```bash
gitmap branch feature/hydrology-update
gitmap checkout feature/hydrology-update
```

Make the map change in ArcGIS, or edit the tracked map JSON files locally if you are working at that level.

### 5. Pull and review changes

If the change was made in ArcGIS, pull the latest Portal state into your branch:

```bash
gitmap pull
```

Review the branch against `main`:

```bash
gitmap status
gitmap diff --format visual
```

For a shareable stakeholder review artifact:

```bash
gitmap diff --format html --output hydrology-review.html
```

### 6. Commit the approved change

```bash
gitmap commit -m "Update hydrology layers"
```

After committing the feature branch, you can compare the saved branch tip against
`main`:

```bash
gitmap diff main feature/hydrology-update --format visual
```

Optional rationale text can be saved with the commit:

```bash
gitmap commit -m "Update hydrology layers" -r "Matches the April field-data refresh"
```

### 7. Merge and push

```bash
gitmap checkout main
gitmap merge feature/hydrology-update
gitmap push
```

`gitmap push` publishes the current branch state back to the configured ArcGIS item or Portal-managed GitMap item, depending on repository configuration. Review diffs before pushing, and use a test web map until you are comfortable with the workflow.

That is the core GitMap loop: **clone → branch → pull or edit → diff → commit → merge → push**.

## Common workflows

### Safely experiment with a production map

```bash
gitmap checkout main
gitmap branch feature/try-imagery-basemap
gitmap checkout feature/try-imagery-basemap

# make the map change in ArcGIS, then sync it locally
gitmap pull
gitmap diff --format visual
gitmap commit -m "Try imagery basemap"
gitmap diff main feature/try-imagery-basemap --format visual
```

### Review changes before release

```bash
gitmap diff main feature/try-imagery-basemap --format html --output release-review.html
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

## Command reference at a glance

| Command | What it does |
|---|---|
| `gitmap clone <ITEM_ID>` | Create a local repository from an ArcGIS web map |
| `gitmap clone <ITEM_ID> --directory <PATH>` | Clone into a chosen local folder |
| `gitmap status` | Show current branch and working tree state |
| `gitmap branch <NAME>` | Create a branch |
| `gitmap checkout <NAME>` | Switch branches |
| `gitmap pull` | Fetch the latest Portal state into the current repo |
| `gitmap diff [SOURCE] [TARGET]` | Compare the index, branches, or commits |
| `gitmap diff main feature/x --format visual` | Show a Rich table branch comparison |
| `gitmap diff main feature/x --format html --output review.html` | Export a shareable diff report |
| `gitmap commit -m "message"` | Save the current map state as a commit |
| `gitmap log --limit 10` | View recent history |
| `gitmap show HEAD` | Inspect a commit |
| `gitmap merge <BRANCH>` | Merge a feature branch into the current branch |
| `gitmap push` | Publish the current branch back to ArcGIS |
| `gitmap revert <COMMIT>` | Restore a previous commit without rewriting history |
| `gitmap setup-repos` | Bulk-clone many maps |
| `gitmap auto-pull` | Sync many repositories on a schedule |
| `gitmap context show` | Visualize repository event history |

Run `gitmap COMMAND --help` for command-specific options and examples.

## Configuration

GitMap supports several ways to provide credentials and repository settings.

### Environment variables

| Variable | Description |
|---|---|
| `PORTAL_URL` | ArcGIS Online or Portal URL |
| `PORTAL_USER` | Portal username |
| `PORTAL_PASSWORD` | Portal password |
| `ARCGIS_USERNAME` | Alternate username variable |
| `ARCGIS_PASSWORD` | Alternate password variable |

Command-line options such as `--url` and `--username` take precedence when a command supports them.

### Repository config

Each repository stores GitMap metadata in `.gitmap/config.json`.

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

## Documentation and support

- Documentation site: <https://14-tr.github.io/Git-Map/>
- Installation guide: [docs/getting-started/installation.md](docs/getting-started/installation.md)
- Quickstart guide: [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- Core concepts: [docs/getting-started/concepts.md](docs/getting-started/concepts.md)
- CLI command reference: [docs/commands/index.md](docs/commands/index.md)
- Portal guide: [docs/guides/portals.md](docs/guides/portals.md)
- Workflow guide: [docs/guides/workflow.md](docs/guides/workflow.md)
- Technical paper: [docs/technical-paper.md](docs/technical-paper.md)
- Issues: <https://github.com/14-TR/Git-Map/issues>

## Development

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e apps/cli/gitmap
python -m pytest packages/gitmap_core/tests integrations/openclaw/tests -x -q
```

Project layout:

```text
Git-Map/
├── apps/                         # CLI, MCP, and client app packages
├── packages/gitmap_core/         # Core library and core tests
├── configs/                      # Example configuration
├── docs/                         # MkDocs documentation site content
├── documentation/                # Internal design/spec material
└── integrations/openclaw/tests/  # OpenClaw integration tests
```

## Contributing

Contributions are welcome. If you are fixing a bug or adding a feature:

1. create a branch
2. add or update tests for behavior changes
3. keep CLI behavior stable unless the change is intentional
4. run the test suite before opening a PR
5. open a PR with a clear explanation and sample output when useful

## License

MIT — see [LICENSE](LICENSE).

**GitMap** — the git for GIS.
