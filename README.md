# GitMap

**Version control for ArcGIS web maps**

GitMap provides Git-like version control for ArcGIS Online and Enterprise Portal web maps. Branch, commit, diff, merge, push, and pull maps using familiar workflows.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Usage Examples](#usage-examples)
- [Docker Setup](#docker-setup)
- [Development](#development)
- [Architecture](#architecture)

## Features

- **Version Control**: Track changes to ArcGIS web maps with commits and branches
- **Branching**: Create feature branches for parallel development
- **Diffing**: Compare map versions and see layer-level changes
- **Merging**: Merge branches with conflict resolution
- **Portal Integration**: Push and pull maps to/from ArcGIS Portal or ArcGIS Online
- **Map Discovery**: List and search available web maps from Portal with the `list` command
- **Layer Settings Transfer**: Transfer popup and form settings between maps with the `lsm` command
- **Bulk Repository Setup**: Automate cloning multiple maps with owner filtering
- **Auto-Pull**: Automatically sync all repositories with Portal to keep them up to date (with optional auto-commit)
- **Context Visualization**: Visualize event history and relationships in multiple formats (Mermaid, ASCII, HTML)
- **CLI Interface**: Familiar Git-like command-line interface
- **Rich Output**: Beautiful terminal output with colors and formatting

## Installation

### Prerequisites

- Python 3.11 or higher
- ArcGIS Portal or ArcGIS Online account
- pip (Python package manager)

### Install from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd gitmap
```

2. Install the core library:
```bash
pip install -e packages/gitmap_core
```

3. Install the CLI:
```bash
pip install -e apps/cli/gitmap
```

### Verify Installation

```bash
gitmap --version
```

You should see: `gitmap, version 0.5.0`

## Quick Start

### 1. Configure Authentication

Create a `.env` file in the project root (or copy from `configs/env.example`):

```bash
cp configs/env.example .env
```

Edit `.env` with your credentials:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

**Note**: The `.env` file is git-ignored and should never be committed.

### 2. Initialize a Repository

Start a new GitMap repository:

```bash
gitmap init
```

Or initialize with project details:

```bash
gitmap init --project-name "My Web Map" --user-name "John Doe" --user-email "john@example.com"
```

### 3. Clone an Existing Map

Clone a web map from Portal:

```bash
gitmap clone <item_id>
```

Example:
```bash
gitmap clone abc123def456 --directory my-project
```

### 4. Make Changes and Commit

After modifying your map JSON:

```bash
# Check status
gitmap status

# Commit changes
gitmap commit -m "Added new operational layer"
```

### 5. Push to Portal

Push your changes to Portal:

```bash
gitmap push
```

## Configuration

### Repository Configuration

GitMap stores configuration in `.gitmap/config.json`:

```json
{
    "version": "1.0",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "project_name": "MyProject",
    "remote": {
        "name": "origin",
        "url": "https://www.arcgis.com",
        "folder_id": "abc123",
        "item_id": "def456"
    }
}
```

### Environment Variables

GitMap supports the following environment variables (set in `.env` or your shell):

- `PORTAL_URL` - Portal URL (defaults to `https://www.arcgis.com` for ArcGIS Online)
- `PORTAL_USER` - Portal username
- `PORTAL_PASSWORD` - Portal password
- `ARCGIS_USERNAME` - Alternative username variable
- `ARCGIS_PASSWORD` - Alternative password variable

### Authentication Methods

GitMap attempts authentication in this order:

1. Username/password provided via command-line options
2. Environment variables from `.env` file
3. ArcGIS Pro authentication (if running in ArcGIS Pro)
4. Anonymous access (limited functionality)

## CLI Commands

### `gitmap init`

Initialize a new GitMap repository.

```bash
gitmap init [PATH] [OPTIONS]
```

**Options:**
- `--project-name, -n` - Project name (defaults to directory name)
- `--user-name, -u` - Default author name for commits
- `--user-email, -e` - Default author email for commits

**Examples:**
```bash
gitmap init
gitmap init --project-name "My Project"
gitmap init /path/to/project --user-name "John Doe"
```

### `gitmap clone`

Clone a web map from Portal.

```bash
gitmap clone <ITEM_ID> [OPTIONS]
```

**Options:**
- `--directory, -d` - Directory to clone into (defaults to map title)
- `--url, -u` - Portal URL (defaults to ArcGIS Online)
- `--username` - Portal username (or use env var)

**Examples:**
```bash
gitmap clone abc123def456
gitmap clone abc123def456 --directory my-project
gitmap clone abc123def456 --url https://portal.example.com
```

### `gitmap setup-repos`

Bulk clone web maps into a repositories directory.

```bash
gitmap setup-repos [OPTIONS]
```

**Description:**
Automates the setup of a repositories directory by cloning multiple web maps at once. Each map is cloned into its own subdirectory with a `.gitmap` folder. Useful for setting up local copies of multiple maps owned by a specific user or matching specific criteria.

**Options:**
- `--directory, -d` - Directory to clone repositories into (defaults to 'repositories')
- `--owner, -o` - Filter web maps by owner username
- `--query, -q` - Search query to filter web maps (e.g., 'title:MyMap')
- `--tag, -t` - Filter web maps by tag
- `--max-results, -m` - Maximum number of web maps to clone (default: 100)
- `--url, -u` - Portal URL (or use PORTAL_URL env var)
- `--username` - Portal username (or use env var)
- `--password` - Portal password (or use env var)
- `--skip-existing` - Skip maps that already have directories (instead of failing)

**Examples:**
```bash
# Clone all maps owned by a specific user
gitmap setup-repos --owner myusername

# Clone to a custom directory
gitmap setup-repos --owner myusername --directory my-repos

# Clone maps with a specific tag
gitmap setup-repos --tag production --skip-existing

# Clone maps matching a search query
gitmap setup-repos --query "title:Project*" --owner myusername

# Combine filters
gitmap setup-repos --owner myusername --tag production --max-results 50
```

### `gitmap auto-pull`

Automatically pull updates for all GitMap repositories in a directory.

```bash
gitmap auto-pull [OPTIONS]
```

**Description:**
Scans a directory for GitMap repositories and pulls the latest changes from Portal for each one. Useful for keeping multiple local repositories in sync with their Portal counterparts. Can be run manually or scheduled via cron/systemd timer for automated synchronization.

**Options:**
- `--directory, -d` - Directory containing GitMap repositories (defaults to 'repositories')
- `--branch, -b` - Branch to pull for each repository (defaults to 'main')
- `--url, -u` - Portal URL (or use PORTAL_URL env var)
- `--username` - Portal username (or use env var)
- `--password` - Portal password (or use env var)
- `--skip-errors` - Continue pulling other repos if one fails (default: True)
- `--auto-commit` - Automatically commit changes after successful pull (default: False)
- `--commit-message, -m` - Custom commit message template (use {repo} for repository name, {date} for timestamp)

**Examples:**
```bash
# Pull updates for all repositories in the default 'repositories' directory
gitmap auto-pull

# Pull from a custom directory
gitmap auto-pull --directory my-repos

# Pull a specific branch from all repositories
gitmap auto-pull --branch production

# Pull with custom Portal URL
gitmap auto-pull --url https://portal.example.com

# Automatically commit changes after pulling
gitmap auto-pull --auto-commit

# Use a custom commit message template
gitmap auto-pull --auto-commit --commit-message "Auto-pull from Portal on {date}"

# Schedule with cron (every hour)
0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit
```

### `gitmap list`

List all available web maps from Portal or ArcGIS Online.

```bash
gitmap list [OPTIONS]
```

**Description:**
Queries Portal/ArcGIS Online and displays all available web maps in a table format. Useful for discovering web map item IDs before cloning or browsing available maps in your organization.

**Options:**
- `--query, -q` - Search query to filter web maps (e.g., 'title:MyMap')
- `--owner, -o` - Filter web maps by owner username
- `--tag, -t` - Filter web maps by tag
- `--max-results, -m` - Maximum number of web maps to return (default: 100)
- `--url, -u` - Portal URL (or use PORTAL_URL env var)
- `--username` - Portal username (or use env var)
- `--password` - Portal password (or use env var)

**Examples:**
```bash
# List all web maps
gitmap list

# List web maps owned by a specific user
gitmap list --owner myusername

# List web maps with a specific tag
gitmap list --tag production

# Combine filters
gitmap list --owner myusername --tag production

# Search by title
gitmap list --query "title:MyMap"

# Limit results
gitmap list --max-results 50
```

### `gitmap status`

Show the working tree status.

```bash
gitmap status
```

Displays:
- Current branch
- Staged changes
- Unstaged changes
- Untracked files

### `gitmap branch`

List, create, or delete branches.

```bash
gitmap branch [BRANCH_NAME] [OPTIONS]
```

**Options:**
- `--delete, -d` - Delete a branch
- `--list, -l` - List all branches

**Examples:**
```bash
gitmap branch                    # List branches
gitmap branch feature/new-layer  # Create new branch
gitmap branch -d feature/old     # Delete branch
```

### `gitmap checkout`

Switch branches or restore working tree files.

```bash
gitmap checkout <BRANCH_NAME>
```

**Examples:**
```bash
gitmap checkout feature/new-layer
gitmap checkout main
```

### `gitmap commit`

Record changes to the repository.

```bash
gitmap commit [OPTIONS]
```

**Options:**
- `--message, -m` - Commit message (required)
- `--author` - Override commit author

**Examples:**
```bash
gitmap commit -m "Added new layer"
gitmap commit -m "Fixed layer visibility" --author "Jane Doe"
```

### `gitmap diff`

Show changes between commits, branches, or working tree.

```bash
gitmap diff [OPTIONS]
```

**Options:**
- `--branch, -b` - Compare with branch
- `--commit, -c` - Compare with commit

**Examples:**
```bash
gitmap diff                    # Show working tree changes
gitmap diff --branch main      # Compare with main branch
gitmap diff --commit abc123    # Compare with specific commit
```

### `gitmap log`

Show commit history.

```bash
gitmap log [OPTIONS]
```

**Options:**
- `--branch, -b` - Show log for specific branch
- `--limit, -n` - Limit number of commits

**Examples:**
```bash
gitmap log
gitmap log --branch feature/new-layer
gitmap log --limit 10
```

### `gitmap merge`

Merge branches.

```bash
gitmap merge <BRANCH_NAME>
```

**Examples:**
```bash
gitmap merge feature/new-layer
```

### `gitmap push`

Push changes to Portal.

```bash
gitmap push [OPTIONS]
```

**Options:**
- `--branch, -b` - Branch to push (defaults to current)
- `--url, -u` - Portal URL
- `--username` - Portal username

**Examples:**
```bash
gitmap push
gitmap push --branch feature/new-layer
gitmap push --url https://portal.example.com
```

### `gitmap pull`

Pull changes from Portal.

```bash
gitmap pull [OPTIONS]
```

**Options:**
- `--branch, -b` - Branch to pull (defaults to current)
- `--url, -u` - Portal URL
- `--username` - Portal username

**Examples:**
```bash
gitmap pull
gitmap pull --branch main
```

### `gitmap lsm`

Transfer popup and form settings between maps.

```bash
gitmap lsm <SOURCE> [TARGET] [OPTIONS]
```

**Description:**
Transfers `popupInfo` and `formInfo` from layers and tables in a source map to matching layers and tables in a target map. Works with item IDs, branch names, commit IDs, or file paths. Automatically handles nested layers within GroupLayers.

**Options:**
- `--dry-run` - Preview changes without applying them

**Arguments:**
- `SOURCE` - Source map (item ID, branch name, commit ID, or file path)
- `TARGET` - Target map (optional, defaults to current index)

**Examples:**
```bash
# Transfer settings between branches
gitmap lsm main feature/new-layer

# Transfer from Portal item ID to current index
gitmap lsm abc123def456

# Transfer from file to file with dry-run
gitmap lsm source.json target.json --dry-run

# Transfer from another repository directory
gitmap lsm ../other-repo
```

### `gitmap notify`

Send a notification to members of a Portal/AGOL group using the
ArcGIS API for Python `Group.notify` method (leveraging your Portal/AGOL
authentication; no SMTP settings required). Notifications go to users in
the target group according to their ArcGIS notification preferences.

By default, all group members are notified. Use `--user` to target specific
users (useful for testing).

```bash
gitmap notify --group <GROUP_ID_OR_TITLE> --subject "Subject" --message "Body"
```

**Options:**
- `--group, -g` - Group ID or title to target for notifications (required)
- `--user` - Specific username(s) to notify (can be used multiple times). If omitted, all group members are notified.
- `--subject, -s` - Notification subject line
- `--message, -m` - Notification body (or use `--message-file`)
- `--message-file` - Load the notification body from a text file
- `--url, -u` - Portal URL (defaults to ArcGIS Online)
- `--username` / `--password` - Portal credentials (or use env vars)

**Examples:**
```bash
# Notify all members of the editors group
gitmap notify --group editors --subject "Release planned" \
  --message "New basemap will be published on Friday."

# Test by sending to a single user
gitmap notify --group editors --user testuser --subject "Test notification" \
  --message "This is a test message."

# Notify multiple specific users
gitmap notify --group editors --user user1 --user user2 --subject "Update" \
  --message "Please review the changes."

# Load a longer message from a file
gitmap notify --group "Field Crew" --subject "Inspection prep" --message-file notes.txt
```

### `gitmap context`

Visualize and manage the context graph showing events, relationships, and annotations.

```bash
gitmap context <SUBCOMMAND> [OPTIONS]
```

**Description:**
The context command provides tools for visualizing the event history and relationships in your GitMap repository. It tracks all operations (commits, pushes, pulls, merges, branches, diffs) and displays them in various formats suitable for terminal viewing or export to IDEs.

**Subcommands:**
- `show` - Display context graph in terminal (ASCII, Mermaid, or Mermaid Timeline formats)
- `export` - Export context graph to file (Mermaid, ASCII, or HTML)
- `timeline` - Show ASCII timeline of context events
- `graph` - Show ASCII graph of event relationships

**Options (for `show` and `timeline`):**
- `--format, -f` - Output format: `ascii`, `mermaid`, or `mermaid-timeline` (default: ascii)
- `--limit, -n` - Maximum events to display (default: 20)
- `--type, -t` - Filter by event types (can be used multiple times): `commit`, `push`, `pull`, `merge`, `branch`, `diff`
- `--no-unicode` - Use simple ASCII characters (no Unicode)

**Options (for `export`):**
- `--format, -f` - Output format: `mermaid`, `mermaid-timeline`, `mermaid-git`, `ascii`, `ascii-graph`, or `html` (default: mermaid)
- `--output, -o` - Output file path (defaults to context.<ext>)
- `--limit, -n` - Maximum events to include (default: 50)
- `--type, -t` - Filter by event types
- `--title` - Title for the visualization
- `--theme` - Color theme for HTML output: `light` or `dark` (default: light)
- `--direction` - Graph direction for Mermaid flowcharts: `TB`, `BT`, `LR`, or `RL` (default: TB)
- `--no-annotations` - Exclude annotations from visualization

**Examples:**
```bash
# Display context graph in terminal
gitmap context show

# Display as Mermaid diagram
gitmap context show --format mermaid

# Show only commits and pushes
gitmap context show --type commit --type push

# Export to Mermaid file for IDE viewing
gitmap context export

# Export to HTML with dark theme
gitmap context export --format html --theme dark -o context.html

# Export with custom title and direction
gitmap context export --format mermaid --direction LR --title "My Project Timeline"

# Show timeline of recent events
gitmap context timeline

# Show event relationship graph
gitmap context graph -n 15
```

### `gitmap config`

Manage repository configuration settings.

```bash
gitmap config [OPTIONS]
```

**Description:**
Configure repository settings such as the production branch (which triggers notifications on push) and auto-visualization (automatically regenerates context graph after events).

**Options:**
- `--production-branch, -p` - Set the production branch name (branch that triggers notifications on push)
- `--unset-production` - Remove the production branch setting
- `--auto-visualize` - Enable automatic context graph regeneration after events
- `--no-auto-visualize` - Disable automatic context graph regeneration

**Examples:**
```bash
# View current configuration
gitmap config

# Set production branch
gitmap config --production-branch main

# Set production branch to a release branch
gitmap config --production-branch release/1.0.0

# Remove production branch setting
gitmap config --unset-production

# Enable auto-visualization
gitmap config --auto-visualize

# Disable auto-visualization
gitmap config --no-auto-visualize
```

## Usage Examples

### Workflow: Bulk Repository Setup

```bash
# Set up a repositories directory with all maps owned by a user
gitmap setup-repos --owner myusername --directory my-maps

# Navigate into one of the cloned repositories
cd my-maps/MyWebMap

# Check the status
gitmap status

# Make changes and commit
gitmap commit -m "Updated layer symbology"

# Push back to Portal
gitmap push
```

### Workflow: Keeping Repositories in Sync

```bash
# Pull updates for all repositories at once
gitmap auto-pull

# Pull from a specific directory
gitmap auto-pull --directory my-maps

# Set up automated synchronization with cron (runs every hour)
# Add this to your crontab (crontab -e):
0 * * * * cd /path/to/project && /path/to/gitmap auto-pull --directory repositories

# Or use systemd timer for more control
# Create /etc/systemd/system/gitmap-sync.service and gitmap-sync.timer
```

### Workflow: Creating a New Feature

```bash
# 1. Start from main branch
gitmap checkout main

# 2. Create feature branch
gitmap branch feature/add-basemap

# 3. Switch to feature branch
gitmap checkout feature/add-basemap

# 4. Make changes to your map (edit JSON files)

# 5. Check what changed
gitmap status
gitmap diff

# 6. Commit changes
gitmap commit -m "Added new basemap layer"

# 7. Push to Portal
gitmap push --branch feature/add-basemap

# 8. Merge back to main
gitmap checkout main
gitmap merge feature/add-basemap
gitmap push
```

### Workflow: Collaborating with Others

```bash
# 1. Pull latest changes from Portal
gitmap pull

# 2. Check for conflicts
gitmap status

# 3. If conflicts exist, resolve them manually
# Then commit the resolution
gitmap commit -m "Resolved merge conflicts"

# 4. Push resolved changes
gitmap push
```

### Workflow: Comparing Versions

```bash
# Compare current working tree with main branch
gitmap diff --branch main

# Compare two specific commits
gitmap diff --commit abc123 --commit def456

# View commit history
gitmap log --limit 20
```

### Workflow: Transferring Layer Settings

```bash
# Transfer popup and form settings from one branch to another
gitmap checkout feature/new-layer
gitmap lsm main

# Preview what would be transferred (dry-run)
gitmap lsm main feature/new-layer --dry-run

# Transfer settings from a Portal item ID
gitmap lsm abc123def456

# Transfer settings between different repositories
gitmap lsm ../source-repo
```

## Docker Setup

GitMap includes Docker support for consistent development environments.

### Development Shell

Start an interactive development shell:

```bash
docker-compose up dev
```

This provides:
- Python 3.11 environment
- All dependencies installed
- Volume mounts for live code editing
- ArcGIS cache persistence

### Running Apps

Run a specific app:

```bash
APP_GROUP=cli APP_NAME=gitmap docker-compose up app
```

## Development

### Project Structure

```
gitmap/
├── apps/                    # Runnable applications
│   └── cli/
│       └── gitmap/          # CLI application
├── packages/                # First-party libraries
│   └── gitmap_core/        # Core library
├── configs/                 # Configuration templates
├── docker/                  # Docker configuration
└── documentation/          # Specifications and docs
```

### Installing for Development

```bash
# Install core library in editable mode
pip install -e packages/gitmap_core

# Install CLI in editable mode
pip install -e apps/cli/gitmap
```

### Running Tests

```bash
# From project root
pytest
```

### Code Standards

- Python 3.11+
- PEP 8 style guide
- Type hints required
- PEP 257 docstrings
- Uses `pathlib.Path` for file operations

## Architecture

### Core Components

- **`gitmap_core`**: Core library providing:
  - Repository management (`.gitmap` directory structure)
  - Portal authentication and connection
  - Web map JSON operations
  - Diff and merge algorithms
  - Remote push/pull operations

- **`gitmap-cli`**: Command-line interface providing:
  - 18 Git-like commands (including `list`, `lsm`, `setup-repos`, `auto-pull`, `notify`, `context`, and `config`)
  - Rich terminal output
  - User-friendly error messages

### Repository Structure

GitMap stores version control data in a `.gitmap` directory:

```
.gitmap/
├── config.json          # Repository configuration
├── HEAD                 # Current branch reference
├── index.json           # Staging area
├── refs/
│   └── heads/          # Branch references
└── objects/
    └── commits/        # Commit objects
```

### Data Model

- **Commit**: Snapshot of map state with metadata
- **Branch**: Named pointer to a commit
- **Remote**: Portal connection configuration
- **Config**: Repository settings and defaults

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

1. Verify your `.env` file exists and contains correct credentials
2. Check that environment variables are set:
   ```bash
   echo $PORTAL_USER
   echo $PORTAL_PASSWORD
   ```
3. Try providing credentials via command-line options
4. Verify Portal URL is correct

### Common Errors

**"Not connected. Call connect() first"**
- Ensure you've authenticated with Portal
- Check your `.env` file configuration

**"Repository already exists"**
- Remove existing `.gitmap` directory if starting fresh
- Or work within the existing repository

**"Failed to connect to Portal"**
- Verify Portal URL is accessible
- Check network connectivity
- Confirm credentials are correct

## Contributing

Contributions are welcome! Please:

1. Follow the code standards outlined in `documentation/project_specs/`
2. Add tests for new features
3. Update documentation as needed
4. Submit pull requests with clear descriptions

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- Open an issue on the repository
- Review documentation in `documentation/`
- Check specifications in `documentation/project_specs/`

---

**GitMap** - Version control for ArcGIS web maps

