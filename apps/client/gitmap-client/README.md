# GitMap Client - Terminal UI

Interactive terminal user interface (TUI) for GitMap version control operations.

## Overview

GitMap Client provides a visual, keyboard-driven interface for managing GitMap repositories. Like `lazygit` but designed specifically for ArcGIS web map version control.

## Features

- **Visual Commit History**: Browse commit log with graph visualization
- **Repository Status**: View current branch, HEAD, and staged changes
- **Branch Navigation**: Switch between branches and view branch information
- **Keyboard-Driven**: Fast, efficient navigation without touching the mouse
- **Real-time Updates**: Status panel auto-refreshes to show repository state

## Installation

```bash
# From the Git-Map root directory
pip install -e apps/client/gitmap-client
```

## Usage

Navigate to any GitMap repository and run:

```bash
gitmap-client
```

Or specify a repository path:

```bash
gitmap-client --repo /path/to/repository
```

### Keyboard Shortcuts

Global shortcuts available everywhere:

- `Q` - Quit application
- `S` - Show repository status
- `L` - Show commit log/history
- `B` - Show branches (coming soon)
- `?` - Show help

Screen-specific shortcuts:

- `ESC` - Return to previous screen
- `R` - Refresh current view
- `J/K` - Navigate up/down (vim-style, in applicable screens)

## Screens

### Status View (Press `S`)

Displays comprehensive repository information:
- Current branch and HEAD commit
- List of all branches
- Staged changes in index
- Remote configuration (if configured)

### Commit History (Press `L`)

Shows visual commit log:
- Commit graph with branch connectors
- Commit IDs (shortened)
- Commit messages
- Author and timestamp information
- Up to 50 recent commits

### Welcome Screen (Default)

- Repository overview in sidebar
- Quick status information
- Help reminders

## Architecture

```
gitmap-client/
├── pyproject.toml          # Package configuration
├── __init__.py             # Package initialization
├── app.py                  # Main TUI application
├── widgets/                # Reusable UI components
│   └── status_panel.py     # Sidebar status widget
└── screens/                # Full-screen views
    ├── status_view.py      # Repository status screen
    └── commit_history.py   # Commit log screen
```

## Development

### Running in Dev Mode

```bash
cd apps/client/gitmap-client
pip install -e ".[dev]"
```

### Creating Test Data

```bash
# Create a test repository
mkdir /tmp/test-repo
cd /tmp/test-repo
gitmap init --user-name "Test User" --project-name "Test"

# Use Python to create test commits
python <<EOF
from gitmap_core.repository import Repository
from pathlib import Path

repo = Repository(Path("."))
repo.update_index({"operationalLayers": [{"title": "Layer 1"}]})
repo.create_commit("First commit")
EOF

# Run the client
gitmap-client
```

## Technology Stack

- **Textual** - Modern TUI framework with rich widgets
- **Rich** - Terminal formatting and styling
- **gitmap_core** - Core GitMap functionality

## Future Enhancements

- [ ] Interactive diff viewer for map changes
- [ ] Branch creation and switching from TUI
- [ ] Portal push/pull operations
- [ ] Merge conflict resolution interface
- [ ] Search and filter commits
- [ ] Visual merge graph
- [ ] Configuration editor
- [ ] Context timeline visualization

## Related Projects

- **GitMap CLI** - Command-line interface for GitMap
- **GitMap Core** - Core library for GitMap operations
- **GitMap MCP** - Model Context Protocol server for IDE integration

## License

MIT
