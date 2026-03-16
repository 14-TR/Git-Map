# auto-pull

Sync all GitMap repositories in a directory with Portal.

## Synopsis

```bash
gitmap auto-pull [OPTIONS]
```

## Description

`auto-pull` scans a directory for GitMap repositories (subdirectories containing a `.gitmap/` folder), connects to Portal once, and pulls the latest map state for each one. Optionally auto-commits changes after each pull.

This is designed for teams managing many maps or for scheduled sync workflows (e.g., cron jobs).

## Options

| Option | Description |
|---|---|
| `--directory, -d TEXT` | Directory containing GitMap repos (default: `repositories`) |
| `--branch, -b TEXT` | Branch to pull for each repo (default: `main`) |
| `--url, -u TEXT` | Portal URL (or set `PORTAL_URL` env var) |
| `--username TEXT` | Portal username (or use `ARCGIS_USERNAME` env var) |
| `--auto-commit` | Commit changes automatically after each pull |
| `--commit-message, -m TEXT` | Commit message template (use `{repo}` and `{date}`) |
| `--skip-errors` | Continue to next repo if one fails |
| `--help` | Show help and exit |

## Examples

```bash
# Sync all repos in the default "repositories/" directory
gitmap auto-pull

# Sync and auto-commit each pulled change
gitmap auto-pull --auto-commit

# Custom directory and branch
gitmap auto-pull --directory my-maps --branch production

# Custom commit message template
gitmap auto-pull \
  --auto-commit \
  --commit-message "Portal sync: {repo} on {date}"

# Skip failed repos and keep going
gitmap auto-pull --skip-errors
```

## Automated Sync with Cron

Keep all repositories in sync without manual intervention:

```bash
# Every hour, sync and commit
0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit

# Every 15 minutes, pull only (no commit)
*/15 * * * * cd /path/to/project && gitmap auto-pull
```

Or use the built-in [`gitmap daemon`](daemon.md) for managed background scheduling:

```bash
gitmap daemon start --interval 60 --auto-commit
```

## Directory Structure

`auto-pull` expects repos laid out like:

```
repositories/
├── FloodRiskMap/
│   └── .gitmap/
├── ParcelMap/
│   └── .gitmap/
└── UtilityNetwork/
    └── .gitmap/
```

Use [`gitmap setup-repos`](setup-repos.md) to bulk-clone Portal maps into this structure.

## See Also

- [`gitmap daemon`](daemon.md) — background scheduler for auto-pull
- [`gitmap setup-repos`](setup-repos.md) — bulk clone Portal maps
- [`gitmap pull`](pull.md) — pull a single repository
