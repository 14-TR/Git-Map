# Core Concepts

Git-Map adapts Git's mental model to web maps. If you know Git, you already know most of this.

## Repository

A **repository** (`.gitmap/` directory) is the version-control database for a project. It stores every commit, branch pointer, and config value. One repository typically tracks one logical map project.

```
my-maps/
└── .gitmap/
    ├── config.json      # Project settings
    ├── HEAD             # Points to current branch
    ├── index.json       # Staged map data (working area)
    ├── refs/heads/      # Branch pointers
    └── objects/commits/ # Commit snapshots
```

## Commit

A **commit** is a snapshot of the map's JSON at a point in time. Each commit stores:

- The full `operationalLayers` and map settings
- Author, timestamp, and message
- A reference to the parent commit (forming a chain)

Commits are immutable. You can always return to any commit with `gitmap revert` or `gitmap checkout`.

## Branch

A **branch** is just a named pointer to a commit. Branches let you maintain parallel versions of a map — for example:

- `main` → production map
- `feature/new-symbology` → experimental changes
- `staging` → QA-ready version

Branches are cheap and fast. Create them freely.

## Index (Staging Area)

The **index** (`index.json`) holds the current map data pulled from Portal or manually staged. Running `gitmap commit` snapshots the index into a new commit.

## Remote

The **remote** is an ArcGIS Online or Portal organization. `gitmap push` writes the current branch to Portal as a web map item; `gitmap pull` reads it back.

## HEAD

`HEAD` points to the current branch (or a specific commit in detached-HEAD mode). Most commands operate on HEAD.

---

Next: [CLI Reference →](../commands/index.md)
