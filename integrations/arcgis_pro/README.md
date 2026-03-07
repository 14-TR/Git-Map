# GitMap — ArcGIS Pro Python Toolbox

Version-control your ArcGIS web maps directly from the ArcGIS Pro ribbon.

## What's included

| Tool | Category | Description |
|------|----------|-------------|
| Init Repository | Repository | Create a new `.gitmap` repo in a folder |
| Commit Map | Repository | Save a web map JSON snapshot as a commit |
| Status | Repository | Show current branch + HEAD info |
| Create Branch | Branches | Branch from current HEAD |
| Checkout Branch | Branches | Switch branches, optionally export map JSON |
| Log History | History | Browse commit history |
| Diff Maps | History | Compare two commits/branches |
| Push to Remote | Remote | Push branch to a GitMap server |
| Pull from Remote | Remote | Pull updates from a GitMap server |

## Installation

### 1. Install gitmap-core

```bash
# In ArcGIS Pro's Python environment (via Python Command Prompt):
pip install gitmap-core
```

### 2. Add the toolbox to ArcGIS Pro

1. Open **Catalog** pane → right-click **Toolboxes** → **Add Toolbox**
2. Navigate to this file: `GitMap.pyt`
3. The **GitMap** toolbox appears under your project toolboxes

### 3. (Optional) Pin to Favorites

Right-click any tool → **Add to Favorites** for quick access.

## Quick Start

```
Init Repository  →  [select your project folder]
Commit Map       →  [select your exported web map JSON, add a message]
Create Branch    →  "feature/add-flood-layer"
Commit Map       →  [after edits, commit on the new branch]
Diff Maps        →  main → feature/add-flood-layer
Checkout Branch  →  main   (revert to baseline)
```

## Exporting your web map JSON

In ArcGIS Pro, use **Share > Export Web Map** or the REST API to get a
`webmap.json` file. Commit that file with the **Commit Map** tool.

## Notes

- The toolbox is a pure Python `.pyt` file — no ArcGIS extension licences required.
- `arcpy` is only imported inside tool `execute()` methods, so the toolbox
  can be imported in non-ArcGIS environments for testing.
- Remote push/pull requires a running GitMap server (see `apps/server`).

## Troubleshooting

**"gitmap_core is not installed"** — Open the ArcGIS Pro Python Command Prompt
and run `pip install gitmap-core`.

**"No GitMap repository found"** — Run **Init Repository** on your project folder first.
