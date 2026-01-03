# Cursor MCP Configuration for GitMap

## Quick Fix for "docker-compose ENOENT" Error

If you're seeing the error `spawn docker-compose ENOENT` in your MCP logs, you're likely running Cursor **inside a Docker container** (dev container), but the MCP configuration is trying to use `docker-compose` to execute commands.

## Solution: Use Direct Python Command

Since you're already inside the container, update your Cursor MCP configuration to use Python directly:

### Configuration for Dev Container / Inside Container

Add this to your Cursor MCP settings (usually in `~/.cursor/mcp.json` or Cursor settings):

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

### Alternative: Direct Script Path

If the package isn't installed, use the direct script path:

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

## How to Update Cursor MCP Settings

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP" or "Model Context Protocol"
3. Find the MCP servers configuration
4. Update the `gitmap` server configuration with one of the above JSON snippets
5. Restart Cursor or reload the MCP server

## Verification

After updating the configuration, the MCP server should start without the `docker-compose` error. You should see successful connection logs instead of the ENOENT error.

## When to Use Docker Compose Configuration

**Only use `docker compose exec` if:**
- Cursor is running on your **host machine** (not in a container)
- You want to execute the MCP server inside a separate Docker container
- You have Docker Compose installed on your host

If you're using Cursor's dev container feature (`.devcontainer/devcontainer.json`), you're already inside the container and should use the direct Python command configuration above.
