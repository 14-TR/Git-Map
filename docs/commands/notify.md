# notify

Send ArcGIS notifications to Portal group members.

## Synopsis

```bash
gitmap notify [OPTIONS]
```

## Description

`notify` sends in-platform notifications to ArcGIS Online or Portal group members using the ArcGIS API. No SMTP configuration is required — messages are delivered through the same notification system as Portal itself.

Use this to announce map updates, request reviews, or coordinate with collaborators.

## Options

| Option | Description |
|---|---|
| `--group, -g TEXT` | Group ID or title to notify (required unless `--list-groups`) |
| `--user TEXT` | Notify a specific user (repeatable; defaults to all group members) |
| `--subject, -s TEXT` | Notification subject line (required) |
| `--message, -m TEXT` | Notification body text |
| `--message-file PATH` | Load notification body from a file |
| `--list-groups, -l` | List available groups and exit |
| `--url, -u TEXT` | Portal URL (or set `PORTAL_URL` env var) |
| `--username TEXT` | Portal username (or use `ARCGIS_USERNAME` env var) |
| `--password TEXT` | Portal password (or use `ARCGIS_PASSWORD` env var) |
| `--help` | Show help and exit |

## Examples

```bash
# Notify all members of the "editors" group
gitmap notify \
  --group editors \
  --subject "Basemap updated" \
  --message "The dark basemap is now live on the flood risk map."

# Notify a specific user for testing
gitmap notify \
  --group editors \
  --user testuser \
  --subject "Test notification" \
  --message "This is a test."

# Load message body from a file
gitmap notify \
  --group "Field Crew" \
  --subject "Release notes" \
  --message-file release-notes.txt

# List available groups first
gitmap notify --list-groups

# Notify multiple specific users
gitmap notify \
  --group "GIS Team" \
  --user alice \
  --user bob \
  --subject "Map review" \
  --message "Please review the changes on feature/new-layers."
```

## List Groups

Use `--list-groups` to discover group IDs and titles before sending:

```bash
gitmap notify --list-groups
```

Output:

```
Available Groups
┌──────────────────────┬─────────────────┬────────────┐
│ ID                   │ Title           │ Owner      │
├──────────────────────┼─────────────────┼────────────┤
│ abc123def456         │ GIS Editors     │ jsmith     │
│ 789xyz000aaa         │ Field Crew      │ jdoe       │
└──────────────────────┴─────────────────┴────────────┘
```

## Integration with Push

`notify` is automatically triggered by `gitmap push` when pushing to the configured production branch. Use `--no-notify` on push to skip automatic notifications:

```bash
gitmap push                # Notifies if pushing to production branch
gitmap push --no-notify    # Skip notifications
```

## Authentication

Requires Portal authentication. Set environment variables in `.env`:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

## See Also

- [`gitmap push`](push.md) — push to Portal (auto-notifies on production branch)
- [`gitmap config`](config.md) — configure production branch
