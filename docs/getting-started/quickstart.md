# Quickstart

Get from zero to your first committed map version in under 5 minutes.

## Prerequisites

Make sure you have gitmap installed:

```bash
pip install gitmap
gitmap --version
```

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

This creates a local repository with the map's current state as the initial commit.

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
gitmap diff --branch main
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

The map is now live in Portal.

---

Next: [Core Concepts →](concepts.md)
