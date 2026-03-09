# I Built Git for ArcGIS Web Maps — Here's Why and How

If you've ever spent 20 minutes trying to remember why someone changed the basemap on a production web map, this post is for you.

I'm a GIS developer who got frustrated enough to build **GitMap** — an open-source command-line tool that brings Git-style version control to ArcGIS Online and Enterprise Portal web maps. After about a year of development, it's now at v0.6.0 with 660+ tests and real workflows. I want to share what I built, why, and what I learned.

---

## The Problem

ArcGIS web maps are collaborative by nature. Multiple team members edit them. Layers get added and removed. Symbology gets tweaked. Basemaps get swapped. And then something breaks.

The typical workflow looks like this:

1. Something looks wrong on a web map
2. Check the Last Modified date in Portal — no useful info
3. Ask the team — "did anyone change anything?"
4. Shrug and manually compare the current state to a screenshot from last week

There's no native audit trail. No branching. No "undo last 3 changes." No way to test a major rework in isolation before pushing it to production.

**Git solves all of this for code. Why not for maps?**

---

## What GitMap Does

GitMap gives you Git-like commands that operate on ArcGIS web map JSON under the hood:

```bash
# Initialize a repo for a map
gitmap init --item-id abc123def456

# Save the current state
gitmap commit -m "Added flood risk layer"

# Create an experimental branch
gitmap branch feature/new-symbology
gitmap checkout feature/new-symbology

# Make changes in Portal... then commit again
gitmap commit -m "Updated parcel layer symbology"

# See what changed
gitmap diff

# Merge back to main when satisfied
gitmap checkout main
gitmap merge feature/new-symbology

# See full history
gitmap log
```

The output looks like this:

```
$ gitmap diff
~ Layer: Parcels
  opacity: 0.8 → 1.0
  visible: false → true
  renderer.type: simple → classBreaks
  popupInfo.title: "Parcel" → "Parcel ID: {APN}"

$ gitmap log
a3f9c12  2026-03-05  Added flood risk layer          (main)
b7e2d44  2026-03-03  Updated basemap to Streets v2
c1a8f91  2026-03-01  Initial commit
```

---

## How It Works

GitMap stores everything locally in a `.gitmap/` directory alongside your project files:

```
.gitmap/
├── config.json       # Portal connection and item ID
├── HEAD              # Current branch ref
├── index.json        # Staging area
├── refs/heads/       # Branch pointers
└── objects/commits/  # Full map JSON snapshots per commit
```

When you `gitmap commit`, it:
1. Connects to Portal via the ArcGIS Python API
2. Pulls the current web map JSON
3. Stores a snapshot in `.gitmap/objects/commits/`
4. Updates the branch ref

When you `gitmap diff`, it uses **DeepDiff** to compare two snapshots and renders the changes in a human-readable table with color coding.

When you `gitmap merge`, it performs a 3-way merge (base → source → target) on the map JSON, detecting conflicts when both branches changed the same layer property.

---

## What v0.6.0 Includes

After 6 months of iteration, GitMap now has:

- **18 Git-like commands**: init, commit, log, diff, branch, checkout, merge, push, pull, clone, stash, cherry-pick, tag, revert, notify, auto-pull, auto-commit, and more
- **Branch-to-branch diff**: `gitmap diff main feature/new-symbology`
- **Stash**: Save WIP without committing — `gitmap stash push` / `gitmap stash pop`
- **Cherry-pick**: Apply a specific commit from another branch
- **Revert**: Undo a commit with an inverse changeset
- **Context visualization**: Mermaid flowcharts, git-graph, ASCII, HTML of your repo history
- **ArcGIS Pro toolbox**: 9 native tools if you work in Pro
- **MCP server**: Expose GitMap as tools for AI agents (Claude, etc.)
- **660+ tests** with >90% coverage
- **Docker support** for team deployments
- **CI via GitHub Actions** on Python 3.11, 3.12, 3.13

---

## Lessons Learned

**1. Web map JSON is messier than you think.**  
The ArcGIS web map JSON spec has evolved over a decade. Layers can have dozens of nested properties. Field aliases, pop-up templates, renderer definitions — all of it is fair game for a diff. Getting the diff output to be *readable* rather than just accurate took significant iteration.

**2. 3-way merge on JSON is hard but possible.**  
Code merges work line-by-line. JSON merges need to work property-by-property, understanding that a layer's `renderer` block is a semantic unit. I eventually settled on a strategy that detects conflicts at the property path level (`layers[2].renderer.type`) and surfaces them clearly rather than silently mangling the JSON.

**3. Auth is the hardest part for users.**  
Portal/ArcGIS Online authentication has multiple modes: username/password, OAuth, IWA, PKI. Getting the connection setup to be simple enough for non-developers while supporting all the enterprise edge cases is still a work in progress.

**4. Tests are your friend.**  
Because I can't run tests against a real Portal, everything is mocked. This forced me to think carefully about interfaces and made refactoring much safer. Going from 0 to 660+ tests over 6 months made a real difference in confidence.

---

## What's Next

- **`pip install gitmap`** — proper PyPI release under a clean package name
- **Demo video** — 90-second walkthrough of the core workflow
- **Documentation site** — [in progress at gitmap docs](https://github.com/14-TR/Git-Map/tree/main/documentation)
- **r/gis community launch** — getting real GIS users to try it

---

## Try It

```bash
# Install
pip install gitmap-core

# Set up a .env file with your Portal credentials
# PORTAL_URL=https://your-portal.com/portal
# PORTAL_USERNAME=your_username
# PORTAL_PASSWORD=your_password

# Initialize a repo
gitmap init --item-id YOUR_WEB_MAP_ITEM_ID
gitmap commit -m "Initial snapshot"
```

- **GitHub:** [14-TR/Git-Map](https://github.com/14-TR/Git-Map)
- **Issues / Feature requests:** Open an issue — I read everything
- **PyPI:** `pip install gitmap-core`

If you're a GIS professional dealing with this problem, I'd love feedback on what's missing or broken. The tool is open source and very much a community project.

---

*TR Ingram is a GIS developer and AI tools builder at ingramgeoai.com.*
