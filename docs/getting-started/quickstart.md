# Quickstart

Get from zero to your first committed map version in under 5 minutes.

## 1. Initialize a Repository

Navigate to a working directory and initialize Git-Map:

```bash
mkdir my-maps
cd my-maps
gitmap init --project-name "My Maps" --user-name "Your Name"
```

This creates a `.gitmap/` directory that tracks all your map versions.

## 2. Pull a Map from Portal

Authenticate and pull a web map from ArcGIS Online or Portal:

```bash
gitmap pull --url https://www.arcgis.com --branch main
```

Git-Map fetches the map JSON and stages it locally. Nothing is committed yet.

## 3. Check Status

```bash
gitmap status
```

You'll see something like:

```
╭─ GitMap Status ─╮
│ On branch: main │
╰─────────────────╯
Changes not committed:
  Staged map with 4 layer(s)
Use "gitmap commit -m <message>" to commit changes
```

## 4. Commit

```bash
gitmap commit -m "Initial snapshot of production map"
```

Output:

```
Created commit a3f2c1b0

  Message:   Initial snapshot of production map
  Author:    Your Name
  Layers:    4

Branch 'main' updated to a3f2c1b0
```

## 5. Create a Branch and Experiment

```bash
gitmap branch feature/new-basemap
gitmap checkout feature/new-basemap
```

Make your changes (edit the map in Portal), then pull and commit again:

```bash
gitmap pull
gitmap commit -m "Switched to dark basemap"
```

## 6. View History

```bash
gitmap log
```

## 7. Diff Two Versions

```bash
gitmap diff
```

## 8. Merge and Push

When the feature is ready, merge it back and push to Portal:

```bash
gitmap checkout main
gitmap merge feature/new-basemap
gitmap push
```

---

Next: [Core Concepts →](concepts.md)
