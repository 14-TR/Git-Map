# config

View or update repository configuration.

## Synopsis

```bash
gitmap config [OPTIONS]
```

## Description

`config` manages the settings stored in `.gitmap/config.json`. With no options, it prints the current configuration. With options, it updates specific settings.

## Options

| Option | Description |
|---|---|
| `--production-branch, -p TEXT` | Set the branch that triggers notifications on push |
| `--unset-production` | Clear the production branch setting |
| `--auto-visualize` | Enable automatic context graph regeneration |
| `--no-auto-visualize` | Disable automatic context graph regeneration |
| `--help` | Show help and exit |

## Examples

```bash
# View current configuration
gitmap config

# Set the production branch (pushes to this branch notify group members)
gitmap config --production-branch main

# Change production branch to a release branch
gitmap config --production-branch release/v2.0

# Remove the production branch setting
gitmap config --unset-production

# Enable auto-visualization (context graph regenerates after events)
gitmap config --auto-visualize

# Disable auto-visualization
gitmap config --no-auto-visualize
```

## Configuration File

Settings are stored at `.gitmap/config.json`:

```json
{
  "version": "1.0",
  "user_name": "Jane Smith",
  "user_email": "jane@example.com",
  "project_name": "FloodRisk",
  "auto_visualize": false,
  "remote": {
    "name": "origin",
    "url": "https://www.arcgis.com",
    "folder_id": "abc123",
    "item_id": "def456",
    "production_branch": "main"
  }
}
```

## Production Branch

When a production branch is set, pushing to that branch will automatically notify all members of Portal groups that have access to the map.

```bash
# Set up notifications for the main branch
gitmap config --production-branch main

# Now pushes to main trigger notifications
gitmap push --branch main
```

Use `--no-notify` on `gitmap push` to skip notifications for a specific push.

## See Also

- [`gitmap push`](push.md) — push to Portal (uses production branch setting)
- [`gitmap notify`](notify.md) — send notifications manually
- [`gitmap context`](context.md) — visualize event history
