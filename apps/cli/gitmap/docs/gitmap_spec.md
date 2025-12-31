# GitMap CLI Application Specification

## Overview

**Purpose**: Provide a command-line interface for Git-like version control of ArcGIS web maps.

**Scope**: CLI commands for initializing repositories, managing branches, committing changes, and synchronizing with ArcGIS Portal.

**Version**: 0.2.0

## Orchestration Flow

```mermaid
flowchart TD
    User[User Input] --> CLI[CLI Parser]
    CLI --> Cmd[Command Module]
    Cmd --> Core[gitmap_core Package]
    Core --> Repo[.gitmap Repository]
    Core --> Portal[ArcGIS Portal]
```

## Inputs/Outputs

### Inputs
- Command-line arguments and options
- User credentials (environment variables or prompts)
- Local `.gitmap` repository

### Outputs
- Terminal output (status, logs, diffs)
- Modified `.gitmap` repository
- Web map items in ArcGIS Portal

## Configuration

Configuration is stored in `.gitmap/config.json`:

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

Environment variables:
- `ARCGIS_USERNAME`: Portal username
- `ARCGIS_PASSWORD`: Portal password

## Error Handling

All commands follow exception handling patterns from `repo_spec.md`:
- Wrap operations in try/except blocks
- Construct descriptive error messages
- Raise RuntimeError with context

## Dependencies

### Internal
- `packages/gitmap_core`: Core library

### External
- `click>=8.1.0`: CLI framework
- `rich>=13.0.0`: Terminal formatting
- `arcgis>=2.3.0`: Portal interaction

## Runbook

### Installation

```bash
pip install -e packages/gitmap_core
pip install -e apps/cli/gitmap
```

### Basic Usage

```bash
# Initialize new repository
gitmap init

# Check status
gitmap status

# Create and switch branches
gitmap branch feature/new-layer
gitmap checkout feature/new-layer

# Commit changes
gitmap commit -m "Added new layer"

# View history
gitmap log

# Push to Portal
gitmap push

# Transfer layer settings between maps
gitmap lsm source-branch target-branch
gitmap lsm abc123def456 --dry-run
```

## Features

### Layer Settings Merge

The `lsm` command transfers popup settings (`popupInfo`) and form settings (`formInfo`) from layers in a source map to matching layers in a target map. Features:

- **Multiple Source Types**: Supports item IDs, branch names, commit IDs, or file paths
- **Auto-Detection**: Automatically detects if a map (by item ID) has an existing `.gitmap` repository
- **Branch Selection**: If a repository exists, prompts user to select which branch to use
- **Auto-Clone**: If no repository exists for an item ID, automatically clones the map from Portal
- **Dry-Run Mode**: Preview changes without applying them using `--dry-run` flag
- **Smart Matching**: Matches layers by exact name (title or ID)
- **Graceful Skipping**: Skips layers that don't exist in target with informative messages

**Usage Examples**:
```bash
# Transfer settings between branches
gitmap lsm main feature/new-layer

# Transfer from Portal item ID to current index
gitmap lsm abc123def456

# Preview changes without applying
gitmap lsm source.json target.json --dry-run
```

## Acceptance Criteria

- [ ] All commands implemented and functional
- [ ] Rich terminal output for status, log, diff
- [ ] Portal authentication via environment variables
- [ ] Clear error messages for all failure modes
- [ ] Comprehensive --help for all commands
- [ ] Layer settings merge supports item IDs, branches, commits, and files


