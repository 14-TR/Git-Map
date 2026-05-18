# Quickstart

Get from zero to your first committed map version in under 5 minutes.

For the first run, use a non-production test web map that you own or can safely modify. Most GitMap commands are local-only, but `gitmap push` can update ArcGIS content.

## First-Run Safety Checklist

Before running the workflow for the first time:

- Use a non-production web map that you own or can safely modify.
- Confirm you copied the web map item ID from the ArcGIS item URL, not the map title or a layer ID.
- Remember that `clone`, `status`, `diff`, `log`, and `commit` are local/review operations.
- Treat `pull` as a read from ArcGIS and `push` as the step that can update ArcGIS-managed content.
- Review `gitmap diff` before any `gitmap push`.

## Prerequisites

Make sure you have gitmap installed:

```bash
pip install gitmap-cli
gitmap --version
```

You also need an ArcGIS Online or Portal web map item ID. Open the web map item page and copy the `id` value from the URL, such as `...?id=abc123def456`.

## 1. Set Up Credentials

Before connecting to Portal, export your credentials:

```bash
export PORTAL_URL=https://your-org.maps.arcgis.com
export ARCGIS_USERNAME=your_username
export ARCGIS_PASSWORD=your_password
```

Or copy the example env file and edit it:

```bash
cp configs/env.example .env
# edit .env with your credentials
```

## 2. Clone an Existing Map

The quickest way to start is cloning a map directly from Portal:

```bash
gitmap clone abc123def456
cd YourMapTitle
```

Replace `abc123def456` with your web map's item ID (visible in the Portal URL).

This creates a local repository with the map's current state as the initial commit. The local folder contains GitMap metadata and tracked web map JSON. Cloning reads from Portal; it does not change the Portal item.

## 3. Check Status

```bash
gitmap status
```

Expected output:

```
╭─ GitMap Status ─╮
│ On branch: main │
╰─────────────────╯
Nothing to commit, working tree clean
```

If you see an error here, check that you are inside the folder created by `gitmap clone` and that the clone completed successfully.

## 4. Create a Branch and Experiment

```bash
gitmap branch feature/new-basemap
gitmap checkout feature/new-basemap
```

Edit the map in Portal, then pull the changes down:

```bash
gitmap pull
gitmap status
```

## 5. Commit Your Changes

```bash
gitmap commit -m "Switched to dark basemap"
```

Output:

```
Created commit a3f2c1b0

  Message: Switched to dark basemap
  Author:  Your Name
  Layers:  4

Branch 'feature/new-basemap' updated to a3f2c1b0
```

## 6. Review What Changed

```bash
gitmap diff main feature/new-basemap --format visual
```

Shows a layer-by-layer comparison between your feature branch and `main`.

## 7. View History

```bash
gitmap log --oneline
```

## 8. Merge and Deploy

When the feature looks good, merge it back to `main` and push:

```bash
gitmap checkout main
gitmap merge feature/new-basemap
gitmap push
```

`gitmap push` is the step that can update ArcGIS content. Review the diff before pushing, and keep using a test map until the workflow is familiar.

## First-Run Troubleshooting

- Missing credentials: set `ARCGIS_USERNAME`, `ARCGIS_PASSWORD`, and `PORTAL_URL`, or create a local `.env` file.
- Missing command: install with `pip install gitmap-cli`, then run `gitmap --version`.
- Wrong item ID: copy the web map item ID from the ArcGIS item page URL, not the map title or layer ID.
- Wrong directory: run GitMap commands from the folder created by `gitmap clone`.
- Permission denied: confirm your ArcGIS account can read the map and can edit it before trying `gitmap push`.

---

Next: [Core Concepts →](concepts.md)
