# Working with Portals

Git-Map supports both **ArcGIS Online** and **Portal for ArcGIS** (10.8+).

## Authentication

### Environment Variables (recommended for CI/CD)

```bash
export ARCGIS_USERNAME=jsmith
export ARCGIS_PASSWORD=mypassword
export PORTAL_URL=https://myorg.maps.arcgis.com
```

### Per-Repo Config

Store the remote URL in the repo config so you don't have to pass `--url` every time:

```bash
gitmap config --remote-url https://myorg.maps.arcgis.com
gitmap config --username jsmith
```

This writes to `.gitmap/config.json`. **Do not commit credentials to source control.**

## ArcGIS Online

The default Portal URL is `https://www.arcgis.com`. Named-user authentication is used.

```bash
gitmap pull --url https://www.arcgis.com
```

## Portal for ArcGIS

Replace with your organization's Portal URL:

```bash
gitmap pull --url https://portal.myorg.com/portal
```

## Item Organization

When you `push`, Git-Map creates a `GitMap` folder in your Portal content and names items using the pattern:

```
{project-name} [{branch}]
```

This keeps branches organized and easy to find.

## Notifications

When pushing to the configured production branch, Git-Map can send Portal notifications to all users in groups that have access to the map. Use `--no-notify` to suppress this.

```bash
gitmap push              # notifies group members
gitmap push --no-notify  # silent push
```
