# GitMap GUI - Web-based Graphical Interface

A beautiful web-based GUI for GitMap version control operations.

## Features

- 🏠 **Repository Overview** - See current branch, commits, branches, and pending changes
- 📋 **Commit History** - Browse commits with visual graph
- 🌿 **Branches** - View and manage branches
- 📝 **Changes** - See pending modifications
- 📁 **Repository Browser** - Browse all repositories in `/app/repositories`

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

- `GET /` - Main GUI page
- `GET /api/status` - Repository status
- `GET /api/commits` - Commit history
- `GET /api/branches` - Branch list
- `GET /api/repositories` - List all repositories
- `POST /api/repo/switch` - Switch active repository

## Development

```bash
cd apps/client/gitmap-gui
pip install -e ".[dev]"
gitmap-gui --repositories-dir /path/to/repos
```
