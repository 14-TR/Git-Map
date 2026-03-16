# setup-repos

Bulk clone web maps from Portal into a local repositories directory.

## Synopsis

```bash
gitmap setup-repos [OPTIONS]
```

## Description

`setup-repos` queries Portal for web maps, then clones each one into its own subdirectory under a base `repositories/` folder. Each cloned map gets a `.gitmap/` repository initialized with the current map state as the first commit.

Use this command to quickly bootstrap a local working copy of your organization's web maps.

## Options

| Option | Description |
|---|---|
| `--directory, -d TEXT` | Output directory (default: `repositories`) |
| `--owner, -o TEXT` | Filter by owner username |
| `--query, -q TEXT` | ArcGIS search query (e.g., `title:FloodRisk`) |
| `--tag, -t TEXT` | Filter by tag |
| `--max-results, -m INT` | Maximum maps to clone (default: 100) |
| `--url, -u TEXT` | Portal URL (or set `PORTAL_URL` env var) |
| `--username TEXT` | Portal username (or use `ARCGIS_USERNAME` env var) |
| `--password TEXT` | Portal password (or use `ARCGIS_PASSWORD` env var) |
| `--skip-existing` | Skip maps whose directory already exists |
| `--help` | Show help and exit |

## Examples

```bash
# Clone all maps owned by a specific user
gitmap setup-repos --owner jsmith

# Clone into a custom directory
gitmap setup-repos --owner jsmith --directory ~/gis-projects

# Filter by tag
gitmap setup-repos --tag production --skip-existing

# Search by title pattern
gitmap setup-repos --query "title:FloodRisk*" --max-results 20

# Clone only specific maps matching title and owner
gitmap setup-repos --query "title:Project*" --owner myusername
```

## Directory Structure

After running, your output directory will look like:

```
repositories/
├── FloodRiskMap/
│   ├── .gitmap/
│   │   ├── config.json
│   │   ├── HEAD
│   │   ├── index.json
│   │   └── objects/commits/
│   └── (working directory)
├── ParcelMap/
│   └── .gitmap/
└── UtilityNetwork/
    └── .gitmap/
```

Each directory is a fully initialized GitMap repository with:
- Remote configured to point back to the Portal item
- First commit containing the current map state

## Subsequent Syncs

After initial setup, use `auto-pull` to keep all repositories in sync:

```bash
# Pull latest changes from Portal
gitmap auto-pull

# Pull and commit changes
gitmap auto-pull --auto-commit

# Run on a schedule
0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit
```

## See Also

- [`gitmap auto-pull`](auto-pull.md) — sync all repos with Portal
- [`gitmap daemon`](daemon.md) — background scheduler
- [`gitmap clone`](clone.md) — clone a single map by item ID
