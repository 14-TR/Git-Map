# Git-Map OpenClaw Integration

OpenClaw plugin for Git-Map version control. Provides 8 tools for managing ArcGIS web maps using Git-like operations.

## Prerequisites

- **Git-Map installed** — `~/Desktop/Git-Map` with packages installed:
  ```bash
  pip install -e ~/Desktop/Git-Map/packages/gitmap_core
  pip install -e ~/Desktop/Git-Map/apps/cli/gitmap
  ```

- **OpenClaw installed** — Gateway running with plugin support

- **Environment variables** for ArcGIS authentication:
  ```bash
  export PORTAL_URL="https://arcgis.com"  # or your Portal URL
  export ARCGIS_USERNAME="your_username"
  export ARCGIS_PASSWORD="your_password"
  ```

## Installation

1. **Start the GitMap skill server:**
   ```bash
   cd ~/Desktop/Git-Map/integrations/openclaw
   python3 server.py
   ```
   Or use the installer script:
   ```bash
   ./install.sh
   ```

2. **Install the OpenClaw plugin:**
   ```bash
   openclaw plugins install -l ./integrations/openclaw
   ```

3. **Restart the OpenClaw gateway:**
   ```bash
   openclaw gateway restart
   ```

## Available Tools

| Tool | Description |
|------|-------------|
| `gitmap_list` | List available web maps from ArcGIS Portal/AGOL |
| `gitmap_status` | Show working tree status for a GitMap repository |
| `gitmap_commit` | Commit the current map state |
| `gitmap_branch` | List, create, or delete branches |
| `gitmap_diff` | Show differences between working tree and branch/commit |
| `gitmap_push` | Push committed changes to ArcGIS Portal |
| `gitmap_pull` | Pull latest map from ArcGIS Portal |
| `gitmap_log` | View commit history |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORTAL_URL` | ArcGIS Portal or AGOL URL (required) |
| `ARCGIS_USERNAME` | Portal username |
| `ARCGIS_PASSWORD` | Portal password |

Alternatively, pass credentials directly to tools as parameters.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  OpenClaw       │────▶│  index.ts        │────▶│  server.py      │
│  Gateway        │     │  (Plugin)        │     │  (Port 7400)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                 ┌─────────────────┐
                                                 │  tools.py       │
                                                 │  (GitMap CLI)   │
                                                 └─────────────────┘
```

- **index.ts**: OpenClaw plugin that proxies HTTP requests to the Python server
- **server.py**: HTTP server exposing GitMap CLI as REST endpoints
- **tools.py**: Tool implementations wrapping the GitMap CLI

## Troubleshooting

- **Server not starting**: Check Python dependencies are installed
- **Tools not working**: Ensure `PORTAL_URL` is set and credentials are valid
- **Plugin not loading**: Run `openclaw plugins list` to verify installation
