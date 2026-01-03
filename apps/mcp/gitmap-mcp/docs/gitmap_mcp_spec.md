# GitMap MCP Server Specification

## Overview

**Purpose**: MCP server that exposes GitMap functionality as tools for Cursor agents, enabling natural language interaction with GitMap operations.

**Scope**: MCP server application providing GitMap version control operations via Model Context Protocol.

**Version**: 0.1.0

## Architecture

The GitMap MCP server is implemented as a FastMCP server that exposes GitMap operations as MCP tools. It integrates directly with the `gitmap_core` library, providing programmatic access to all GitMap functionality.

### Server Structure

```
apps/mcp/gitmap-mcp/
├── docs/
│   └── gitmap_mcp_spec.md
├── configs/
│   └── gitmap_mcp_config.json.example
├── scripts/
│   ├── __init__.py
│   └── tools/
│       ├── __init__.py
│       ├── repository_tools.py
│       ├── branch_tools.py
│       ├── commit_tools.py
│       ├── remote_tools.py
│       ├── layer_tools.py
│       └── portal_tools.py
├── main.py
└── pyproject.toml
```

## Available Tools

### Repository Tools

#### `gitmap_init`

Initialize a new GitMap repository.

**Parameters**:
- `path` (str, optional): Directory path to initialize (defaults to current directory)
- `project_name` (str, optional): Project name (defaults to directory name)
- `user_name` (str, optional): Default author name for commits
- `user_email` (str, optional): Default author email for commits

**Returns**: Dictionary with success status and repository path

**Example**:
```json
{
  "success": true,
  "repository_path": "/path/to/repo",
  "gitmap_dir": "/path/to/repo/.gitmap",
  "message": "Initialized empty GitMap repository"
}
```

#### `gitmap_clone`

Clone a web map from Portal.

**Parameters**:
- `item_id` (str, required): Portal item ID to clone
- `directory` (str, optional): Directory to clone into (defaults to map title)
- `url` (str, optional): Portal URL (defaults to ArcGIS Online)
- `username` (str, optional): Portal username (uses env vars if not provided)

**Returns**: Dictionary with success status and clone details

#### `gitmap_status`

Show the working tree status.

**Parameters**: None

**Returns**: Dictionary with current branch, commit info, and change status

### Branch Tools

#### `gitmap_branch_list`

List all branches in the repository.

**Parameters**: None

**Returns**: Dictionary with list of branches and current branch

#### `gitmap_branch_create`

Create a new branch.

**Parameters**:
- `name` (str, required): Branch name to create

**Returns**: Dictionary with success status and branch details

#### `gitmap_branch_delete`

Delete a branch.

**Parameters**:
- `name` (str, required): Branch name to delete

**Returns**: Dictionary with success status

#### `gitmap_checkout`

Switch to a different branch.

**Parameters**:
- `branch` (str, required): Branch name to checkout
- `create` (bool, optional): Create branch if it doesn't exist (default: false)

**Returns**: Dictionary with success status and branch info

### Commit Tools

#### `gitmap_commit`

Create a new commit.

**Parameters**:
- `message` (str, required): Commit message describing the changes
- `author` (str, optional): Override commit author

**Returns**: Dictionary with success status and commit details

#### `gitmap_log`

Show commit history.

**Parameters**:
- `limit` (int, optional): Maximum number of commits to show (default: 10)
- `oneline` (bool, optional): Show compact one-line format (default: false)

**Returns**: Dictionary with commit history

#### `gitmap_diff`

Show changes between states.

**Parameters**:
- `target` (str, optional): Branch name or commit ID to compare with (defaults to HEAD)
- `verbose` (bool, optional): Show detailed property-level changes (default: false)

**Returns**: Dictionary with diff results

### Remote Tools

#### `gitmap_push`

Push branch to ArcGIS Portal.

**Parameters**:
- `branch` (str, optional): Branch to push (defaults to current branch)
- `url` (str, optional): Portal URL (uses configured remote if not specified)
- `username` (str, optional): Portal username (uses env vars if not provided)
- `no_notify` (bool, optional): Skip sending notifications (default: false)

**Returns**: Dictionary with success status and push details

#### `gitmap_pull`

Pull latest changes from Portal.

**Parameters**:
- `branch` (str, optional): Branch to pull (defaults to current branch)
- `url` (str, optional): Portal URL (uses configured remote if not specified)
- `username` (str, optional): Portal username (uses env vars if not provided)

**Returns**: Dictionary with success status and pull details

### Layer Tools

#### `gitmap_layer_settings_merge`

Transfer popup and form settings between maps.

**Parameters**:
- `source` (str, required): Source map (item ID, branch name, commit ID, or file path)
- `target` (str, optional): Target map (defaults to current index)
- `dry_run` (bool, optional): Preview changes without applying them (default: false)

**Returns**: Dictionary with success status and transfer details

### Portal Tools

#### `gitmap_notify`

Send a notification to group members using ArcGIS APIs.

**Parameters**:
- `group` (str, required): Group ID or title to target for notifications
- `subject` (str, required): Notification subject line
- `message` (str, optional): Notification body text (or use message_file)
- `message_file` (str, optional): Path to file containing notification body
- `users` (list[str], optional): Specific usernames to notify (defaults to all group members)
- `url` (str, optional): Portal URL (uses env var or defaults to ArcGIS Online)
- `username` (str, optional): Portal username (uses env vars if not provided)
- `password` (str, optional): Portal password (uses env vars if not provided)

**Returns**: Dictionary with success status and notification details

#### `gitmap_list_maps`

List all available web maps from Portal.

**Parameters**:
- `query` (str, optional): Search query to filter web maps
- `owner` (str, optional): Filter web maps by owner username
- `tag` (str, optional): Filter web maps by tag
- `max_results` (int, optional): Maximum number of web maps to return (default: 100)
- `url` (str, optional): Portal URL (uses env var or defaults to ArcGIS Online)
- `username` (str, optional): Portal username (uses env vars if not provided)
- `password` (str, optional): Portal password (uses env vars if not provided)

**Returns**: Dictionary with list of web maps

**Output Format**:
The tool returns a `table` field containing pre-formatted markdown output. When displaying results to users, agents MUST use this `table` format directly without reformatting. The format displays each map title as a bold header followed by the item ID in a code block.

**Example Output Format**:
```
**Map Title**:
```
item_id
```
```

#### `gitmap_list_groups`

List all available groups from Portal.

**Parameters**:
- `url` (str, optional): Portal URL (uses env var or defaults to ArcGIS Online)
- `username` (str, optional): Portal username (uses env vars if not provided)
- `password` (str, optional): Portal password (uses env vars if not provided)

**Returns**: Dictionary with list of groups

## Configuration

### Environment Variables

All Portal credentials come from environment variables (no hardcoded values):

- `PORTAL_URL` - Portal URL (defaults to `https://www.arcgis.com` for ArcGIS Online)
- `PORTAL_USER` - Portal username
- `PORTAL_PASSWORD` - Portal password
- `ARCGIS_USERNAME` - Alternative username variable
- `ARCGIS_PASSWORD` - Alternative password variable

**Automatic `.env` File Loading**: The MCP server automatically loads the `.env` file from:
1. Current working directory (where Cursor runs the MCP server)
2. Parent directories (searches up to 3 levels)

This means you don't need to configure environment variables in the MCP config JSON - just create a `.env` file in your project root with your credentials, and the MCP server will find and load it automatically.

Example `.env` file:
```
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

### Cursor Configuration

To use the GitMap MCP server in Cursor, add it to your Cursor settings. The configuration template is provided in `configs/gitmap_mcp_config.json.example`.

#### Running Inside a Container (Dev Container / Docker)

**If you're running Cursor inside a Docker container** (like a dev container), use the simple Python command since the package is already installed:

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "python",
      "args": ["-m", "gitmap_mcp.main"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

This is the recommended configuration when using Cursor with a dev container, as shown in `.devcontainer/devcontainer.json`.

#### Local Development (Non-Docker)

For local development (non-Docker), use the direct script path (recommended - works without package installation):

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "python",
      "args": ["${workspaceFolder}/apps/mcp/gitmap-mcp/main.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

**Note**: 
- The `env` section is not required. The MCP server automatically loads your `.env` file from the workspace directory.
- Just ensure your `.env` file exists in the project root with your Portal credentials.
- Using the direct script path works without needing to install the package.

**Alternative** (if package is installed):

If you've installed the package via `pip install -e apps/mcp/gitmap-mcp`, you can use:

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "python",
      "args": ["-m", "gitmap_mcp.main"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

**Optional**: If you prefer to explicitly pass environment variables through the MCP config (instead of using `.env` file), you can add an `env` section, but this is not necessary since the `.env` file is automatically loaded.

#### Running from Host Machine into Docker Container

**Only use this if Cursor is running on your host machine** and you want to execute the MCP server inside a Docker container. If you're already in a dev container, use the configuration above instead.

For Docker environments, the MCP server is pre-installed after `docker compose build`. Configure Cursor to run it inside Docker:

**Note**: Modern Docker uses `docker compose` (as a subcommand) instead of `docker-compose` (legacy standalone binary). Use the following configuration:

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "docker",
      "args": [
        "compose", "exec", "-T", "dev",
        "python", "-m", "gitmap_mcp.main"
      ]
    }
  }
}
```

**Legacy Docker Compose V1** (if you still have `docker-compose` installed):

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "docker-compose",
      "args": [
        "exec", "-T", "dev",
        "python", "-m", "gitmap_mcp.main"
      ]
    }
  }
}
```

**Important**: If you see an error like `spawn docker-compose ENOENT`, it means:
1. You're trying to use `docker-compose` but it's not installed, OR
2. You're already inside a container and should use the simple `python -m gitmap_mcp.main` configuration instead

Or using docker exec:

```json
{
  "mcpServers": {
    "gitmap": {
      "command": "docker",
      "args": [
        "exec", "-i",
        "gitmap-dev",
        "python", "-m", "gitmap_mcp.main"
      ]
    }
  }
}
```

## Installation

### From Source

1. Install the MCP server package:
```bash
pip install -e apps/mcp/gitmap-mcp
```

2. Ensure dependencies are installed:
```bash
pip install -e packages/gitmap_core
```

### Docker Build

The MCP server is automatically installed during Docker build:

```bash
docker compose build
```

**Note**: If you're using legacy Docker Compose V1, use `docker-compose build` instead.

After build, the MCP server is available in all Docker containers.

## Usage Examples

### Initialize Repository

```python
# Via MCP tool call
result = gitmap_init(
    path=".",
    project_name="MyProject",
    user_name="John Doe",
    user_email="john@example.com"
)
```

### Clone a Map

```python
result = gitmap_clone(
    item_id="abc123def456",
    directory="my-project",
    url="https://www.arcgis.com"
)
```

### Create and Commit Changes

```python
# Create branch
gitmap_branch_create("feature/new-layer")

# Checkout branch
gitmap_checkout("feature/new-layer")

# Make changes to map JSON...

# Commit changes
gitmap_commit(message="Added new operational layer")
```

### Push to Portal

```python
result = gitmap_push(
    branch="feature/new-layer",
    url="https://www.arcgis.com"
)
```

## Error Handling

All tools return a consistent response format:

```json
{
  "success": true|false,
  "error": "Error message (if success is false)",
  // ... additional fields based on tool
}
```

Tools handle errors gracefully and provide clear error messages. Common error scenarios:

- Repository not found: Tools return error indicating repository needs to be initialized
- Authentication failures: Clear messages about missing credentials
- Portal connection issues: Detailed error messages about connection problems

## Portability Requirements

1. **No User-Specific Data**: All credentials come from environment variables
2. **Works from Any Directory**: Repository discovery uses `find_repository()` which searches from CWD upward
3. **Installation Independence**: Package installable via `pip install -e .`
4. **Configuration Templates Only**: Only example configs provided, no user-specific data

## Dependencies

- `gitmap_core>=0.1.0` - Core GitMap library
- `mcp>=1.0.0` - Model Context Protocol SDK

## References

- [GitMap CLI Documentation](../../../README.md)
- [GitMap Core Library](../../../packages/gitmap_core/README.md)
- [Apps Folder Specification](../../../documentation/project_specs/30-apps/apps_folder_spec.md)
- [MCP Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)
