# gitmap push

Push the current branch to ArcGIS Online or Portal as a web map item.

## Usage

```bash
gitmap push [OPTIONS]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--branch` | `-b` | Branch to push (defaults to current branch) |
| `--url` | `-u` | Portal URL (falls back to config, then `PORTAL_URL` env var) |
| `--username` | | Portal username (or `ARCGIS_USERNAME` env var) |
| `--no-notify` | | Skip sending notifications even if pushing to the production branch |
| `--rationale` | `-r` | Reason for this push (stored in audit log) |

## Examples

```bash
# Push current branch
gitmap push

# Push a specific branch
gitmap push --branch staging

# Push to a custom Portal
gitmap push --url https://portal.example.com

# Skip notifications
gitmap push --no-notify

# With rationale
gitmap push -r "Deploying accessibility improvements for sprint 4"
```

## Output

```
Connecting to https://www.arcgis.com...
Authenticated as jsmith
Pushing branch 'main'...

Pushed 'main' to Portal

  Item ID:  abc123def456
  Title:    Downtown Parcels [main]
  URL:      https://www.arcgis.com/home/item.html?id=abc123def456

✓ Notifications sent to 3 user(s)
```

## Notes

- Git-Map creates a folder called `GitMap` in your Portal to organize branch items.
- If the production branch is configured and `--no-notify` is not passed, portal group members are notified.
- Credentials can be stored in `config.json` via `gitmap config` to avoid typing them each time.
