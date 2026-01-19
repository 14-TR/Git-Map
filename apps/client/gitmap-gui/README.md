# GitMap GUI - Web-based Graphical Interface

A beautiful web-based GUI for GitMap version control operations.

## Features

- 🏠 **Repository Overview** - See current branch, commits, branches, and pending changes
- 📋 **Commit History** - Browse commits with visual graph from all branches
- 🌿 **Branches** - View and manage branches
- 📝 **Changes** - See detailed pending modifications with layer-level diff
- 📁 **Repository Browser** - Browse all repositories in `/app/repositories`
- 🔄 **Portal Integration** - Connect to Portal, clone, pull, and push maps
- 🔀 **Merge Operations** - Preview and execute branch merges with conflict resolution

## Architecture

The GUI is built with a modular architecture for maintainability:

```
gitmap_gui/
├── app.py              # Main Flask application entry point
├── config.py           # Global state management (repo, portal connection)
├── utils.py            # Helper functions (get_repo, scan_repositories)
├── routes/             # Route blueprints organized by feature
│   ├── __init__.py     # Blueprint registration
│   ├── main.py         # Main route (/)
│   ├── repository.py   # Repository operations (/api/status, /api/repositories, etc.)
│   ├── branch.py       # Branch operations (/api/branches, /api/branch/*)
│   ├── commit.py       # Commit operations (/api/commits, /api/commit)
│   ├── merge.py        # Merge operations (/api/merge/*)
│   ├── diff.py         # Diff operations (/api/diff)
│   ├── portal.py       # Portal connection (/api/portal/*)
│   └── remote.py       # Remote operations (/api/clone, /api/pull, /api/push)
├── static/
│   ├── css/
│   │   └── style.css   # All CSS styles
│   └── js/
│       └── app.js      # All JavaScript functionality
└── templates/
    └── base.html       # Main HTML template
```

## Installation

The GUI is installed automatically when building the Docker image:

```bash
# From the Git-Map root directory
docker-compose build gui
```

## Usage

### Via Docker Compose (Recommended)

Start the GUI service:

```bash
docker-compose up gui
```

Or in detached mode:

```bash
docker-compose up -d gui
```

Access at: http://localhost:5000

### Direct Command Line

```bash
# Default: scans /app/repositories
gitmap-gui

# Specify repositories directory
gitmap-gui --repositories-dir /path/to/repositories

# Specify port
gitmap-gui --port 8080

# Specify a single repository
gitmap-gui --repo /path/to/specific/repo
```

## Repository Directory

The GUI scans `/app/repositories` (or the directory specified with `--repositories-dir`) for GitMap repositories.

Each subdirectory containing a `.gitmap` folder will be detected as a repository.

## Docker Configuration

The GUI service is configured in `docker-compose.yml`:

```yaml
gui:
  build:
    context: .
    dockerfile: docker/Dockerfile
  ports:
    - "5000:5000"
  volumes:
    - ./repositories:/app/repositories
  command: gitmap-gui --repositories-dir /app/repositories --port 5000 --host 0.0.0.0
```

## Troubleshooting

### Repositories not showing up

1. Make sure repositories are in `/app/repositories` (or your configured directory)
2. Each repository must have a `.gitmap` folder
3. Check the browser console for API errors
4. Verify the API works: `curl http://localhost:5000/api/repositories`

### GUI not starting

1. Rebuild the Docker image: `docker-compose build gui`
2. Check logs: `docker-compose logs gui`
3. Make sure port 5000 is not in use

## API Endpoints

### Repository
- `GET /api/status` - Get repository status (current branch, HEAD commit, pending changes)
- `GET /api/repositories` - List all repositories in the repositories directory
- `POST /api/repo/switch` - Switch to a different repository
- `POST /api/repo/reload` - Force reload repository from disk

### Commits
- `GET /api/commits` - Get commit history from all branches
- `POST /api/commit` - Create a new commit

### Branches
- `GET /api/branches` - Get list of all branches
- `POST /api/branch/create` - Create a new branch
- `POST /api/branch/checkout` - Checkout a branch
- `DELETE /api/branch/<name>` - Delete a branch

### Diff & Changes
- `GET /api/diff` - Get current diff (index vs HEAD) with detailed layer changes

### Merge
- `POST /api/merge/preview` - Preview a merge and detect conflicts
- `POST /api/merge/execute` - Execute merge with conflict resolutions
- `POST /api/merge/abort` - Abort the current merge

### Portal
- `POST /api/portal/connect` - Connect to ArcGIS Portal
- `GET /api/portal/status` - Get portal connection status
- `GET /api/portal/webmaps` - List available web maps from Portal

### Remote Operations
- `POST /api/clone` - Clone a web map from Portal
- `POST /api/pull` - Pull changes from Portal
- `POST /api/push` - Push changes to Portal

## Development

### Project Structure

The application is organized into modular components:

- **Routes**: Each feature has its own blueprint module in `routes/` directory
- **Static Files**: CSS and JavaScript are separated from HTML for better maintainability
- **Templates**: HTML structure in `templates/base.html`
- **Configuration**: Global state managed in `config.py`

### Setting Up Development Environment

```bash
cd apps/client/gitmap-gui
pip install -e ".[dev]"
gitmap-gui --repositories-dir /path/to/repos
```

### Making Changes

1. **Adding a new route**: Create a new blueprint in `routes/` and register it in `routes/__init__.py`
2. **Styling**: Modify `static/css/style.css`
3. **Frontend logic**: Modify `static/js/app.js`
4. **HTML structure**: Modify `templates/base.html`
