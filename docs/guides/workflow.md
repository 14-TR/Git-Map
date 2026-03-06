# Day-to-Day Workflow

This guide walks through the standard Git-Map workflow for managing a production web map.

## The Golden Rule

**Never edit the production map directly.** Always work on a branch, review the diff, and merge when ready.

## Typical Session

### 1. Start on main, sync first

```bash
cd my-map-project
gitmap checkout main
gitmap pull
gitmap commit -m "Sync: latest production state"
```

### 2. Create a feature branch

```bash
gitmap branch feature/updated-symbology
gitmap checkout feature/updated-symbology
```

### 3. Make changes in Portal

Edit the map in ArcGIS Online or Portal as normal. When done:

```bash
gitmap pull --branch feature/updated-symbology
gitmap diff           # Review what changed
gitmap commit -m "Updated parcel symbology per client request"
```

### 4. Merge and deploy

```bash
gitmap checkout main
gitmap merge feature/updated-symbology
gitmap push
```

### 5. Tag releases (optional)

```bash
gitmap tag v2.3 -m "Q2 2024 symbology update"
```

## Rollback

If something goes wrong after a push:

```bash
gitmap log --oneline        # Find the last good commit
gitmap revert a3f2c1b0      # Restore that state
gitmap push                 # Deploy the fix
```
