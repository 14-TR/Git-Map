# Git-Map OpenClaw Integration

OpenClaw plugin for Git-Map version control. Provides 9 tools for managing ArcGIS web maps using Git-like operations.

## Prerequisites

- **Git-Map installed** — this repository checkout, or another checkout pointed to by `GITMAP_ROOT`:
  ```bash
  export GITMAP_ROOT="/path/to/git-map"  # optional when running from this integration directory
  pip install -e "$GITMAP_ROOT/packages/gitmap_core"
  pip install -e "$GITMAP_ROOT/apps/cli/gitmap"
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
   cd /path/to/git-map/integrations/openclaw
   export GITMAP_ROOT="$(cd ../.. && pwd)"
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
| `gitmap_health` | Check local GitMap/OpenClaw integration readiness without contacting Portal |
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
| `GITMAP_ROOT` | GitMap source checkout used by local fallback imports; optional when the server runs from this repo |
| `PORTAL_URL` | ArcGIS Portal or AGOL URL (required) |
| `ARCGIS_USERNAME` | Portal username |
| `ARCGIS_PASSWORD` | Portal password |

The OpenClaw plugin schema also supports `serverUrl` for pointing the TypeScript
plugin at a non-default GitMap skill server URL. The default is
`http://localhost:7400`.

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

- **Server not starting**: Check Python dependencies are installed and `GITMAP_ROOT` points at a valid GitMap checkout if you are not running from this repository
- **Health check failing**: Run `curl http://localhost:7400/health` or call `gitmap_health`; both report the resolved GitMap root and local CLI/source-tree checks without contacting Portal
- **Wrong repo path**: OpenClaw sends `repo_path`; the Python server normalizes it to the CLI wrapper `cwd` parameter
- **Tools not working**: Ensure `PORTAL_URL` is set and credentials are valid
- **Plugin not loading**: Run `openclaw plugins list` to verify installation
