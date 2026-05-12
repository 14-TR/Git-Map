# GitMap Demo Script

Purpose: a 60-90 second demo showing how GitMap gives ArcGIS web maps a Git-like review workflow.

Audience: GIS analysts, GIS managers, and developers who manage shared ArcGIS web maps.

Safety note: record this with a non-production test web map. Do not use a customer, production, or sensitive map.

## Core Message

GitMap lets teams clone an ArcGIS web map, make changes on a branch, review exactly what changed, commit the approved state, merge it, and push the chosen version back to ArcGIS.

## Recording Setup

- Use a test ArcGIS web map that you own and can safely modify.
- Have the web map item ID ready before recording.
- Use a clean terminal with GitMap installed.
- Keep credentials out of the recording.
- If using environment variables, set them before recording begins.

```bash
export PORTAL_URL=https://your-org.maps.arcgis.com
export ARCGIS_USERNAME=your_username
export ARCGIS_PASSWORD='[hidden]'
```

## 60-90 Second Flow

### 0-10 sec: State the problem

Narration:

> ArcGIS web maps change all the time, but teams usually do not get clean version history, branch workflow, or readable diff. GitMap brings Git-style review to ArcGIS web maps.

### 10-25 sec: Clone a safe test map

```bash
gitmap clone <TEST_WEB_MAP_ITEM_ID> --directory county-flood-risk
cd county-flood-risk
gitmap status
```

Show:

- the local GitMap repo was created
- the starting branch is `main`
- the working tree is clean

Narration:

> Clone reads the current web map from ArcGIS and creates a local GitMap repository. It does not modify the Portal item.

### 25-40 sec: Create a branch for a map change

```bash
gitmap branch feature/hydrants-layer
gitmap checkout feature/hydrants-layer
```

Narration:

> Branches let a GIS analyst try a map change without treating the production state as the draft.

### 40-55 sec: Pull and review the changed map state

After making a safe test change in ArcGIS, run:

```bash
gitmap pull
gitmap diff main feature/hydrants-layer --format visual
```

Show one simple, low-risk change:

- layer visibility
- popup text
- renderer style
- basemap selection
- a test-only operational layer

Narration:

> Pull refreshes the local branch from Portal. The visual diff turns opaque web map JSON into a reviewable change summary.

### 55-70 sec: Commit the approved change

```bash
gitmap commit -m "Add hydrants layer for review"
gitmap log --limit 3
```

Narration:

> Once the change is approved, commit it with a clear message. The map now has a local history.

### 70-85 sec: Merge and push intentionally

```bash
gitmap checkout main
gitmap merge feature/hydrants-layer
gitmap push
```

Narration:

> Push is the intentional write step. Review the diff first, then publish the approved branch state back to ArcGIS.

### 85-90 sec: Close

Narration:

> That is GitMap: clone, branch, pull, diff, commit, merge, and push for ArcGIS web maps.

## What This Proves

For GIS analysts:

> You can experiment with map changes and see exactly what changed before release.

For GIS managers:

> You get a safer approval path, rollback story, and audit trail for shared web maps.

For developers:

> You can automate ArcGIS web map versioning using familiar Git-like primitives.

## Safety Captions

- `clone`, `status`, `branch`, `checkout`, `diff`, `commit`, `log`, and `merge` are local or read/review operations in this flow.
- `pull` reads the latest web map state from Portal into the local branch.
- `push` is the Portal write step. Use it only after reviewing the diff and only against a safe test map during the demo.

## Future Recording Notes

- Keep the first recording terminal-only.
- Add captions for local-only, Portal-read, and Portal-write commands.
- Consider a second version that shows the ArcGIS web map before and after in browser tabs.
