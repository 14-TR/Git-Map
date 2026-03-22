# Git-Map: A Version Control System for ArcGIS Web Maps

**TR Ingram**  
*Independent Researcher / GIS Software Engineer*  
*Wyoming, USA*

**Date:** March 22, 2026  
**Version:** 3.0

---

## Abstract

Web maps published through ArcGIS Online (AGOL) and ArcGIS Enterprise Portal are stateful, JSON-encoded GIS artifacts whose operational layer configurations, symbology, popups, and cartographic properties evolve continuously. Despite this complexity, Esri's platform offers no native mechanism to snapshot, branch, or revert a web map's JSON definition—leaving GIS professionals dependent on ad hoc strategies such as item cloning, manual change logs, or informal naming conventions ("Map_v3_FINAL_2"). This paper presents **Git-Map** (v0.6.0+), a Python-based version control system that applies Git's conceptual model—commits, branches, merges, cherry-picks, stashes, reverts, and tags—to ArcGIS web map items. The system stores content-addressed snapshots of a map's operational layer JSON at each commit, implements a three-way merge algorithm at layer granularity, provides a `DeepDiff`-backed property-level diff engine, exposes operations through a Model Context Protocol (MCP) server for AI-agent workflows, wraps nine operations as a native ArcGIS Pro Python Toolbox, maintains an SQLite-backed event graph (`ContextStore`) for episodic memory and context awareness, and ships as a pip-installable monorepo with 660+ tests achieving ~96% coverage. The architecture is publicly documented and distributed under the MIT license, targeting community adoption among the GIS professional community.

---

## 1. Introduction

### 1.1 Problem Statement

A web map in ArcGIS Online or Portal for ArcGIS is fundamentally a JSON document—a structured payload conforming to the Esri web map specification—stored as a `Web Map` content item in the Portal content system. This document encodes the full operational state of a map: which feature layers are included (`operationalLayers`), their visibility, rendering rules, popup configurations, drawing info, spatial reference, extent, and basemap definition. Changes to any of these properties are reflected immediately in the item's data with no history retained at the platform level.

The implications for professional GIS workflows are significant:

- **No rollback**: A GIS analyst who inadvertently removes a critical layer from a shared operational map cannot restore the previous state without manual reconstruction.
- **No parallelism**: A team working on a shared web map has no branching mechanism; parallel edits overwrite each other.
- **No auditability**: There is no native record of when a layer was added, who changed a symbology rule, or why a particular configuration decision was made.
- **No promotion workflow**: Promoting maps from development to production environments requires manual comparison and institutional memory rather than deterministic diff output.

Esri's platform does provide *versioned geodatabases* for feature class editing—a mature branch-and-reconcile workflow for vector data—but this mechanism operates at the geodatabase layer and does not extend to the web map item itself. Portal's built-in item revision history tracks ownership and sharing metadata changes but does not snapshot the full JSON payload.

Git-Map addresses this gap by treating the web map JSON as the primary artifact under version control, applying concepts from distributed version control systems (DVCS) to the GIS domain.

### 1.2 Contributions

This paper documents the following technical contributions:

1. A formal architecture for a content-addressable, commit-based version control system operating on ArcGIS web map JSON stored in a `.gitmap` directory (§2).
2. A layer-atomic three-way merge algorithm adapted from standard VCS merge strategies to GIS-specific layer data structures (§3.4).
3. A `DeepDiff`-backed property-level diff engine producing structured `MapDiff` objects with per-layer change classification (§3.3).
4. An SQLite-backed event graph (`ContextStore`) enabling episodic memory and AI-agent context awareness across version control operations (§3.6).
5. A Model Context Protocol (MCP) server exposing all GitMap operations to AI coding agents (Cursor, Claude, etc.) via 26+ registered tools (§3.7).
6. A native ArcGIS Pro Python Toolbox wrapping nine core operations for direct integration with the Pro ribbon/Catalog UI (§3.8).
7. An OpenClaw integration providing subprocess-based tool wrappers for agent-driven map management (§3.9).
8. A complete monorepo publishing strategy with three PyPI packages (`gitmap-core`, `gitmap-cli`, `gitmap-mcp`) (§4.3).
9. An ASCII commit graph renderer with topological sort and lane-management for merge commit visualization (§3.5).

### 1.3 Scope

This paper covers Git-Map as of March 2026 (v0.6.0+). The system supports ArcGIS Online and Portal for ArcGIS ≥ 10.9, requires Python ≥ 3.10, and is distributed under the MIT license at `14-TR/Git-Map`. The scope includes the `gitmap_core` library, `gitmap` CLI (25+ commands), MCP server, ArcGIS Pro toolbox, and OpenClaw integration. Geodatabase versioning, feature editing workflows, and ArcGIS Server service management are explicitly out of scope.

---

## 2. System Architecture

### 2.1 High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Git-Map Monorepo                                 │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    packages/gitmap_core                             │ │
│  │                                                                    │ │
│  │  ┌────────────┐ ┌─────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ repository │ │  merge  │ │ diff │ │ context  │ │  graph   │  │ │
│  │  │    .py     │ │   .py   │ │  .py │ │    .py   │ │    .py   │  │ │
│  │  └─────┬──────┘ └─────────┘ └──────┘ └────┬─────┘ └──────────┘  │ │
│  │        │                                   │                      │ │
│  │  ┌─────┴──────┐  ┌──────────┐  ┌──────────┴──┐  ┌────────────┐  │ │
│  │  │   models   │  │connection│  │  visualize  │  │   remote   │  │ │
│  │  │    .py     │  │   .py    │  │    .py      │  │    .py     │  │ │
│  │  └────────────┘  └──────────┘  └─────────────┘  └────────────┘  │ │
│  │                                                                    │ │
│  │  ┌────────────────────────────────────────────────────────────┐   │ │
│  │  │  communication.py │ compat.py │ maps.py │ visualize.py    │   │ │
│  │  └────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              ▲                                           │
│            ┌─────────────────┼─────────────────┐                        │
│            │                 │                 │                        │
│  ┌─────────┴───┐  ┌──────────┴──────┐  ┌──────┴────────────────┐      │
│  │ apps/cli    │  │  apps/mcp       │  │ integrations/         │      │
│  │ gitmap CLI  │  │  gitmap-mcp     │  │ arcgis_pro/GitMap.pyt │      │
│  │ 25 commands │  │  26+ MCP tools  │  │ openclaw/tools.py     │      │
│  └─────────────┘  └─────────────────┘  └───────────────────────┘      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ apps/client/gitmap-client (Textual TUI) │ gitmap-gui (Flask UI) │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
              │                                    │
              ▼                                    ▼
   ┌──────────────────┐                 ┌───────────────────┐
   │  Local .gitmap/  │  push/pull      │  ArcGIS Portal /  │
   │  directory       │◄───────────────►│  AGOL Remote      │
   │  (filesystem)    │                 │                   │
   └──────────────────┘                 └───────────────────┘
```

### 2.2 Repository On-Disk Layout

The `.gitmap` directory mirrors Git's `.git` layout conceptually:

```
<project-root>/
└── .gitmap/
    ├── config.json          # RepoConfig: user info, remote, project_name
    ├── HEAD                 # "ref: refs/heads/main" or bare commit ID
    ├── index.json           # Staging area (current map JSON snapshot)
    ├── context.db           # SQLite event graph (ContextStore)
    ├── refs/
    │   ├── heads/
    │   │   ├── main         # Commit ID that main points to
    │   │   └── feature/x    # Supports nested branch names
    │   ├── remotes/
    │   │   └── origin/      # Remote tracking refs
    │   └── tags/
    │       └── v1.0.0       # Commit ID this tag points to
    ├── objects/
    │   └── commits/
    │       ├── <commit_id>.json   # Full commit snapshot
    │       └── <commit_id>.json
    └── stash/
        ├── stash_list.json  # Ordered stash stack manifest
        └── <hash>.json      # Individual stash payload
```

This flat-file layout makes the repository human-inspectable, trivially transportable (copy the directory), and requires no database beyond the optional `context.db`.

### 2.3 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Core library | Python 3.10+ / dataclasses | Type-safe, stdlib-first; no heavy ORM |
| Diff engine | `deepdiff` | Structured recursive diffing with semantic equality |
| Portal API | `arcgis` (ArcGIS API for Python) | Official Esri SDK; handles auth, items, groups |
| MCP server | `mcp` / FastMCP | Emerging standard for AI-tool interop |
| CLI | `click` | Composable command groups, familiar Git-style UX |
| TUI client | `textual` | Rich terminal UI, no Electron dependency |
| Web UI | Flask | Lightweight server-side rendering |
| Context store | SQLite (stdlib) | Zero-dependency, WAL-mode for concurrent access |
| Visualization | Mermaid / HTML | Portable, renders in GitHub and MkDocs |
| Documentation | MkDocs (Material theme) | Markdown-first, versioned, searchable |
| Packaging | pyproject.toml (hatchling) | PEP 517/518 compliant; three separate PyPI packages |

### 2.4 Monorepo Package Structure

The repository is organized as a Python monorepo under three logical namespaces:

- **`packages/gitmap_core`** — The shared library. Imported by all consumer applications. Published to PyPI as `gitmap-core`.
- **`apps/cli/gitmap`** — The `gitmap` CLI application. Depends on `gitmap_core`. Published as `gitmap-cli`.
- **`apps/mcp/gitmap-mcp`** — The MCP server. Depends on `gitmap_core` and `mcp`. Published as `gitmap-mcp`.
- **`apps/client/gitmap-client`** — Textual TUI client (in development).
- **`apps/client/gitmap-gui`** — Flask web GUI (in development).
- **`integrations/arcgis_pro`** — ArcGIS Pro Python Toolbox (`.pyt`).
- **`integrations/openclaw`** — OpenClaw plugin tools.

---

## 3. Implementation

### 3.1 Data Models (`packages/gitmap_core/models.py`)

Four core dataclasses form the type system for the repository:

#### 3.1.1 `Commit`

```python
@dataclass
class Commit:
    id: str          # 12-char SHA-256 prefix of content hash
    message: str
    author: str
    timestamp: str   # ISO 8601
    parent: str | None    # First parent (None = root commit)
    parent2: str | None   # Second parent (merge commits only)
    map_data: dict[str, Any]   # Full web map JSON snapshot
```

The `map_data` field stores the **complete** web map JSON at commit time—not a delta. This snapshot-based approach makes `checkout`, `revert`, and `cherry-pick` O(1) in terms of reconstruction: no chain traversal is needed to reconstruct the state at any commit. The trade-off is storage size linear in map complexity × commit count, but in practice ArcGIS web map JSON documents are typically 10–500 KB, making this tractable for the hundreds-of-commits lifecycle of a typical project.

Commit IDs are generated via SHA-256 of the JSON-serialized `{message, map_data, parent}` triple:

```python
def _generate_commit_id(self, message, map_data, parent):
    content = json.dumps({"message": message, "map_data": map_data, 
                           "parent": parent}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:12]
```

The 12-character truncation provides a collision probability of ~1/16^12 ≈ 4.7×10⁻¹⁵ per commit pair, acceptably low for single-project use. Collision handling is not implemented—a known limitation for extremely large repositories.

#### 3.1.2 `Branch`

```python
@dataclass
class Branch:
    name: str        # Supports hierarchical names: "feature/new-layer"
    commit_id: str   # The commit this branch points to
```

Branches are stored as flat files under `.gitmap/refs/heads/`. The branch name is used directly as the filename, with `/` separating subdirectories for hierarchical names (e.g., `refs/heads/feature/new-layer`). This mirrors Git's refspec behavior.

#### 3.1.3 `Remote`

```python
@dataclass
class Remote:
    name: str             # e.g., "origin"
    url: str              # Portal URL
    folder_id: str | None
    folder_name: str | None
    item_id: str | None   # Original web map item ID (for clone workflow)
    production_branch: str | None  # Triggers notifications on push
```

The `production_branch` field enables a push notification workflow: when the named branch is pushed, GitMap queries groups sharing the pushed item and sends Portal notifications to group members.

#### 3.1.4 `RepoConfig`

```python
@dataclass
class RepoConfig:
    version: str          # "1.0" — schema version for forward compat
    user_name: str
    user_email: str
    remote: Remote | None
    project_name: str
    auto_visualize: bool  # Regenerate context graph after each commit
```

The `auto_visualize` flag demonstrates the integration between the version control system and the AI-context layer: when enabled, each commit triggers a Mermaid graph regeneration written to `context-graph.md`, providing a continuously updated visual representation for IDE agents.

### 3.2 Repository Management (`packages/gitmap_core/repository.py`)

The `Repository` class is the central facade for all local operations. Its 1,300+ lines cover initialization, HEAD management, branch CRUD, index operations, commit creation, history traversal, tag operations, stash stack management, revert, cherry-pick, and common-ancestor search.

#### 3.2.1 Initialization

```python
def init(self, project_name="", user_name="", user_email=""):
    # Creates .gitmap/ directory tree
    # Initializes config.json with RepoConfig
    # Writes HEAD = "ref: refs/heads/main"
    # Creates empty index.json
    # Creates refs/heads/main (empty string = no commits yet)
    # Initializes SQLite context.db via ContextStore
```

The `ContextStore` is initialized with a `pass` context manager block to force schema creation (tables and indexes) before any events are recorded.

#### 3.2.2 HEAD State Machine

HEAD supports two states mirroring Git's behavior:

1. **Attached**: `HEAD` contains `ref: refs/heads/<branch>` — normal operation.
2. **Detached**: `HEAD` contains a raw commit ID — after `checkout <commit>`.

`get_current_branch()` returns `None` in detached state; `get_head_commit()` handles both cases.

#### 3.2.3 Index as Staging Area

The `index.json` file serves as the staging area. Unlike Git's byte-level staging area, GitMap's index holds the complete current map JSON. The workflow is:

1. `gitmap pull` → fetches map JSON from Portal → writes to `index.json`
2. User edits the map in Portal
3. `gitmap commit` → reads `index.json` → creates commit snapshot

The `has_uncommitted_changes()` method compares `index.json` against the HEAD commit's `map_data` using Python's `!=` operator on the deserialized JSON dicts. This is structurally correct but order-sensitive for list fields (layer ordering matters in web maps).

#### 3.2.4 Commit ID Generation Algorithm

The commit ID algorithm is:

```
sha256(sort_keys(json({message, map_data, parent})))[:12]
```

This creates a content-addressed identifier that is deterministic for identical content, making deduplication of redundant commits theoretically possible (though not currently implemented).

#### 3.2.5 Common Ancestor Search

The `find_common_ancestor(a, b)` method implements two-pass BFS:

1. **Phase 1**: Collect all ancestors of commit `a` into a set, following both `parent` and `parent2` pointers.
2. **Phase 2**: BFS from commit `b`, returning the first ancestor found in the Phase 1 set.

This correctly handles merge commits (diamond histories) and guarantees the *nearest* common ancestor because `b`'s ancestors are visited youngest-first. Time complexity: O(|ancestors(a)| + |ancestors(b)|); space: O(|ancestors(a)|).

### 3.3 Diff Engine (`packages/gitmap_core/diff.py`)

The diff module provides semantic comparison of web map JSON structures.

#### 3.3.1 `MapDiff` Data Structure

```python
@dataclass
class MapDiff:
    layer_changes: list[LayerChange]   # Per-layer delta
    table_changes: list[LayerChange]   # Per-table delta  
    property_changes: dict[str, Any]   # Map-level property delta (DeepDiff output)
```

`LayerChange` classifies each change as `"added"`, `"removed"`, or `"modified"`, with a `details` dict containing the raw `DeepDiff` output for modified layers.

#### 3.3.2 Layer Indexing Strategy

Layers are indexed by their `id` field (an integer or string assigned by Portal). This creates a stable identity for each layer across commits, enabling accurate add/remove/modify classification even when layer ordering changes:

```python
index1 = {layer.get("id"): layer for layer in layers1 if layer.get("id")}
```

Layers without an `id` field are not diffed individually—a known limitation for maps containing anonymous layers.

#### 3.3.3 Property-Level Diff

Map-level properties (everything except `operationalLayers` and `tables`) are compared using `DeepDiff`:

```python
deep_diff = DeepDiff(map2_props, map1_props, ignore_order=True)
result.property_changes = deep_diff.to_dict() if deep_diff else {}
```

`DeepDiff` produces a structured dictionary with keys like `type_changes`, `values_changed`, `dictionary_item_added`, enabling downstream code to interpret exactly what changed at any nesting level.

#### 3.3.4 Output Formatters

Three formatters support different consumers:

- `format_diff_summary(map_diff)` → human-readable text for CLI output.
- `format_diff_visual(map_diff, label_a, label_b)` → list of `(symbol, name, detail)` tuples for Rich table rendering.
- `format_diff_stats(map_diff)` → `{added, removed, modified, total}` counts for dashboard widgets.

### 3.4 Merge Engine (`packages/gitmap_core/merge.py`)

The merge algorithm treats each operational layer as an **atomic unit** for conflict detection, implementing a three-way merge when a common ancestor is available.

#### 3.4.1 Algorithm

For each layer ID encountered across the three versions (ours, theirs, base):

```
Case 1: Layer in both ours and theirs, unchanged → keep ours
Case 2: Layer in both, three-way context:
    - ours == base (we didn't change) → use theirs
    - theirs == base (they didn't change) → use ours
    - both changed → CONFLICT (keep ours, record conflict)
Case 3: Layer in both, no base → CONFLICT
Case 4: Layer only in ours:
    - was in base → they deleted it (keep ours)
    - not in base → we added it (keep)
Case 5: Layer only in theirs:
    - was in base and they modified it → CONFLICT (we deleted, they changed)
    - not in base → they added it (add to merged result)
```

The same logic applies symmetrically to `tables`.

#### 3.4.2 Conflict Representation

```python
@dataclass
class MergeConflict:
    layer_id: str
    layer_title: str
    ours: dict[str, Any]    # Our version
    theirs: dict[str, Any]  # Their version
    base: dict[str, Any] | None  # Common ancestor version
```

Conflict resolution is deferred to the user via `resolve_conflict(conflict, "ours"|"theirs"|"base")` and `apply_resolution(merge_result, layer_id, resolved_layer)`.

#### 3.4.3 Complexity Analysis

Let `n` = total unique layer IDs across all three versions. The algorithm makes O(n) passes through each of the three layer lists. Building ID index dictionaries is O(n). Total time complexity: O(n). Space complexity: O(n) for the ID indices plus O(merged output size).

In practice, web maps rarely contain more than 50–100 layers, making the absolute runtime negligible.

#### 3.4.4 Merge Command Flow

The CLI `gitmap merge <branch>` command orchestrates:
1. Resolves source branch tip commit → retrieves `map_data`.
2. Calls `find_common_ancestor()` to locate the merge base.
3. Invokes `merge_maps(ours, theirs, base)`.
4. If no conflicts: calls `create_commit()` with `parent2=source_commit_id` to record a true merge commit.
5. If conflicts: writes conflict state to a temporary file and prompts user.

### 3.5 Commit Graph Renderer (`packages/gitmap_core/graph.py`)

The graph module implements an ASCII commit graph renderer inspired by `git log --graph`.

#### 3.5.1 Algorithm Overview

1. **`_collect_commits(repo, limit)`**: Walks all branch tips via BFS following `parent` and `parent2` pointers, collecting all reachable commits into a dict.

2. **`_topological_sort(all_commits)`**: Implements a modified Kahn's algorithm to produce a topologically-ordered list (children before parents). Tie-breaking by `timestamp` (newest first) ensures recent commits appear at the top.

3. **Lane assignment**: A list `lanes: list[str | None]` tracks which commit ID each "lane" (column) is waiting for. When a commit is rendered:
   - Find the commit's lane (where `lanes[i] == cid`).
   - Render prefix: `"* | |"` with `*` at `my_lane`.
   - Update `lanes[my_lane]` to `commit.parent`.
   - If `commit.parent2`: assign it to a new lane, record as `merge_lane`.
   - Generate connector lines (e.g., `"| |\"`) for merge visualization.

4. **`GraphNode`** dataclass carries the commit, lane assignment, ref labels, prefix line, and connector lines for the rendering layer.

#### 3.5.2 Design Decisions

The graph renderer avoids storing the full adjacency matrix; instead it maintains a single `lanes` list that tracks "active" parent chains. This is memory-efficient but limited to forward-only rendering—the algorithm cannot backtrack to improve layout. For repositories with complex parallel histories, the lane assignment is first-come-first-served and may produce suboptimal layouts compared to Git's renderer.

### 3.6 Context Graph (`packages/gitmap_core/context.py`)

The `ContextStore` module implements an SQLite-backed episodic memory system for the version control workflow.

#### 3.6.1 Schema

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,     -- UUID
    timestamp TEXT NOT NULL, -- ISO 8601
    event_type TEXT NOT NULL, -- commit, push, pull, merge, branch, revert, stash, tag, cherry-pick
    actor TEXT,
    repo TEXT NOT NULL,      -- Repository root path
    ref TEXT,                -- Commit ID or branch name
    payload JSON NOT NULL    -- Event-specific structured data
);

CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(id),  -- NULL for standalone lessons
    annotation_type TEXT NOT NULL,  -- rationale, lesson, outcome, issue
    content TEXT NOT NULL,
    source TEXT,    -- user, agent, auto
    timestamp TEXT NOT NULL
);

CREATE TABLE edges (
    source_id TEXT REFERENCES events(id),
    target_id TEXT REFERENCES events(id),
    relationship TEXT NOT NULL,  -- caused_by, reverts, related_to, cherry_picked_from
    metadata JSON,
    PRIMARY KEY (source_id, target_id, relationship)
);
```

Indexes are created on `events(event_type)`, `events(ref)`, `events(timestamp)`, `annotations(event_id)`, and `annotations(annotation_type)`.

WAL (Write-Ahead Logging) journal mode is enabled at connection time for better concurrent read/write performance.

#### 3.6.2 Event Recording Pattern

Every mutation operation in `repository.py` records a context event in a `try/except` block after the primary operation completes:

```python
try:
    with self.get_context_store() as store:
        store.record_event(
            event_type="commit",
            repo=str(self.root),
            ref=commit_id,
            actor=author,
            payload={"message": message, "branch": branch, ...},
            rationale=rationale,  # Optional user-provided why
        )
except Exception:
    pass  # Context recording never blocks the primary operation
```

This defensive pattern ensures that `context.db` corruption or unavailability cannot prevent commits, pushes, or other critical operations.

#### 3.6.3 Graph Edges for Operation Lineage

The `add_edge()` method creates typed relationships between events:

- `revert` event → `reverts` → original commit event
- `cherry-pick` event → `cherry_picked_from` → source commit event
- `merge` event → `caused_by` → source branch events (planned)

These edges enable future tooling to reconstruct the full lineage of why a particular map state exists.

#### 3.6.4 Context-Aware Features

The `get_timeline()`, `search_events()`, and `get_related_events()` methods provide the foundation for:

- **`gitmap context`** CLI subcommand: Displays the operation timeline with annotations.
- **MCP context tools**: `context_explain_changes`, `context_get_timeline`, `context_search_history`, `context_record_lesson`.
- **`auto_visualize`** feature: Automatically generates a Mermaid diagram of the context graph after each commit (when `config.auto_visualize = True`).

### 3.7 Remote Operations (`packages/gitmap_core/remote.py`)

The `RemoteOperations` class bridges the local repository to ArcGIS Portal/AGOL.

#### 3.7.1 Push Strategy

Push is handled in two modes:

1. **Item-ID push** (clone workflow): When `config.remote.item_id` is set and `branch == "main"`, the original web map item is updated directly via `item.update(data=json.dumps(map_data))`. This preserves the item's Portal URL, sharing settings, and item page.

2. **Branch-as-item push**: For other branches or when item_id is absent, the branch is mapped to a Portal item titled `<project_name>_<branch_name>` (slashes replaced with underscores) with tags `["GitMap", "project:<name>", "branch:<name>", "commit:<id>"]`.

The tag-based identity scheme allows `_find_branch_item_in_root()` to locate existing items without requiring a folder ID—useful when the user has not yet configured a remote folder.

#### 3.7.2 Pull Strategy

Pull follows the inverse path: for `main` with `item_id` configured, `item.get_data()` is called on the original item. For other branches, the branch item is located by title/tag search.

**Known Issue**: Pull does not create a new commit automatically—it only updates `index.json`. Users must separately run `gitmap commit` after a pull to snapshot the fetched state. This two-step workflow differs from Git's fast-forward behavior and may surprise users. It is flagged as technical debt.

#### 3.7.3 Production Branch Notifications

When `config.remote.production_branch` matches the branch being pushed, the system:
1. Queries the item's sharing groups.
2. Calls `notify_item_group_users(gis, item, subject, body)` from `communication.py`.
3. Returns a `notification_status` dict indicating success, failure, or reason for skip.

The notification logic gracefully handles private items (not shared), items without groups, and Portal notification API failures—none of which fail the push operation.

#### 3.7.4 Portal API Compatibility (`compat.py`)

The `compat.py` module provides a `create_folder()` function that handles API differences between `arcgis` library versions:

- **v2.3.0+**: `gis.content.folders.create(name)` 
- **v2.2.x**: `gis.content.create_folder(name)` 
- **Legacy**: Direct manager call

This abstraction insulates the rest of the codebase from version-specific Portal SDK behavior.

### 3.8 CLI Application (`apps/cli/gitmap/`)

The CLI provides 25 commands organized into workflow-grouped help output.

#### 3.8.1 Command Groups

| Group | Commands |
|-------|----------|
| Repository | `init`, `clone`, `status` |
| Staging | `commit`, `diff`, `log`, `show` |
| Branches | `branch`, `checkout`, `merge`, `merge-from`, `cherry-pick` |
| Remote | `push`, `pull`, `notify` |
| History | `revert`, `tag`, `stash` |
| Portal | `list`, `config`, `setup-repos` |
| Context | `context` |
| Advanced | `layer-settings-merge`, `auto-pull`, `daemon` |

#### 3.8.2 Grouped Help Formatter

The `GroupedHelpGroup` class in `help_formatter.py` subclasses Click's `Group` to render commands in logical sections rather than a flat alphabetical list. This significantly improves discoverability for GIS professionals unfamiliar with CLI workflows.

#### 3.8.3 Key Command Implementations

**`gitmap log --graph`**: Invokes `build_graph(repo, limit)` from `graph.py`, then renders each `GraphNode`'s `prefix_line` and `connector_lines` using Rich's console output for colored terminal rendering.

**`gitmap show <commit>`**: Loads the commit by ID, retrieves the parent commit, calls `diff_maps()` to compute the delta, then renders both commit metadata and a Rich table of the diff.

**`gitmap layer-settings-merge`**: A specialized command for merging layer settings (visibility, symbology, popups) from one map version to another without replacing layers—useful for promoting configuration changes without data changes.

**`gitmap daemon`**: A background service mode that periodically polls the remote for changes and auto-pulls when divergence is detected. Uses `watchdog` for filesystem monitoring of local changes.

#### 3.8.4 Kebab-Case File Import Workaround

Python module names cannot contain hyphens, but two commands use hyphenated filenames (`layer-settings-merge.py`, `merge-from.py`) for CLI naming consistency. The `main.py` entry point loads these via `importlib.util.spec_from_file_location`:

```python
_layer_settings_merge_path = Path(__file__).parent / "commands" / "layer-settings-merge.py"
_spec = importlib.util.spec_from_file_location("layer_settings_merge", _layer_settings_merge_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
layer_settings_merge = _module.layer_settings_merge
```

This is a pragmatic workaround but introduces a non-standard import pattern. A cleaner solution would rename the files or use a different entrypoint convention—flagged as technical debt.

### 3.9 MCP Server (`apps/mcp/gitmap-mcp/`)

The MCP server exposes GitMap operations as standardized tools for AI agents via the Model Context Protocol.

#### 3.9.1 Tool Inventory

26+ tools registered across six modules:

| Module | Tools |
|--------|-------|
| `repository_tools` | `gitmap_init`, `gitmap_clone`, `gitmap_status` |
| `branch_tools` | `gitmap_branch_create`, `gitmap_branch_delete`, `gitmap_branch_list`, `gitmap_checkout` |
| `commit_tools` | `gitmap_commit`, `gitmap_log`, `gitmap_diff`, `gitmap_merge` |
| `remote_tools` | `gitmap_push`, `gitmap_pull` |
| `stash_tools` | `gitmap_stash_push`, `gitmap_stash_pop`, `gitmap_stash_list`, `gitmap_stash_drop` |
| `context_tools` | `context_explain_changes`, `context_get_timeline`, `context_search_history`, `context_record_lesson` |
| `portal_tools` | `gitmap_notify`, `gitmap_list_maps`, `gitmap_list_groups` |
| `layer_tools` | `gitmap_layer_settings_merge` |

#### 3.9.2 Server Initialization

The server uses `FastMCP` from the `mcp` library. On startup, it locates and loads `.env` from the workspace root (searching up to 5 parent directories) to provide Portal credentials without requiring environment variable exports in the agent's shell session.

#### 3.9.3 AI Agent Use Cases

The MCP server enables workflows such as:
- "Commit the current state of this map with message 'Add fire stations layer'"
- "What changed between main and feature/new-symbology?"
- "Merge feature/new-symbology into main and resolve conflicts by keeping ours"
- "Show me the timeline of all commits made this week"

### 3.10 ArcGIS Pro Toolbox (`integrations/arcgis_pro/GitMap.pyt`)

The `.pyt` file defines a native ArcGIS Pro Python Toolbox exposing nine tools to the Pro ribbon/Catalog UI:

| Tool | Description |
|------|-------------|
| `InitRepo` | Initialize a new GitMap repository |
| `CommitMap` | Create a commit from the current map state |
| `CheckoutBranch` | Switch to a branch |
| `CreateBranch` | Create a new branch |
| `LogHistory` | View commit history |
| `DiffMaps` | Compare two commits |
| `StatusCheck` | Show repository status |
| `PushRemote` | Push to Portal |
| `PullRemote` | Pull from Portal |

Each tool wraps `gitmap_core` calls directly using `arcpy` parameter types (`DEWorkspace`, `GPString`, etc.) and outputs results via `arcpy.AddMessage()`. The `_get_repo()` helper validates the workspace path and imports `gitmap_core`, raising a helpful `ImportError` message if the library is not installed.

### 3.11 OpenClaw Integration (`integrations/openclaw/`)

The OpenClaw integration provides subprocess-based wrappers (`tools.py`) and a plugin descriptor (`openclaw.plugin.json`) for the OpenClaw AI assistant platform. These tools wrap the `gitmap` CLI as subprocess calls, enabling OpenClaw agents to invoke version control operations without importing the Python library directly.

---

## 4. API / Interface Specification

### 4.1 Core Library Public API

#### `Repository` (packages/gitmap_core/repository.py)

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__init__` | `root: Path\|str` | — | Initialize at path |
| `init` | `project_name, user_name, user_email` | `None` | Create new repo |
| `exists()` | — | `bool` | Check if `.gitmap/` exists |
| `is_valid()` | — | `bool` | Validate repo structure |
| `get_current_branch()` | — | `str\|None` | Current branch or None |
| `get_head_commit()` | — | `str\|None` | HEAD commit ID |
| `list_branches()` | — | `list[str]` | All local branches |
| `create_branch` | `name, commit_id=None` | `Branch` | Create branch |
| `checkout_branch` | `name` | `None` | Switch branch |
| `delete_branch` | `name` | `None` | Delete branch |
| `update_branch` | `name, commit_id` | `None` | Advance branch pointer |
| `get_index()` | — | `dict` | Current staging area |
| `update_index` | `map_data` | `None` | Stage new map data |
| `create_commit` | `message, author=None, rationale=None, parent2=None` | `Commit` | Create commit |
| `get_commit` | `commit_id` | `Commit\|None` | Load commit by ID |
| `get_commit_history` | `start_commit=None, limit=None` | `list[Commit]` | Commit log |
| `has_uncommitted_changes()` | — | `bool` | Dirty state check |
| `revert` | `commit_id, rationale=None` | `Commit` | Inverse commit |
| `cherry_pick` | `commit_id, rationale=None` | `Commit` | Apply commit changes |
| `find_common_ancestor` | `a, b` | `str\|None` | LCA of two commits |
| `stash_push` | `message=None` | `dict` | Save index to stash |
| `stash_pop` | `index=0` | `dict` | Apply and remove stash |
| `stash_list()` | — | `list[dict]` | List stash entries |
| `stash_drop` | `index=0` | `dict` | Remove stash entry |
| `stash_clear()` | — | `int` | Remove all stashes |
| `list_tags()` | — | `list[str]` | All tags |
| `create_tag` | `name, commit_id=None` | `str` | Create tag |
| `delete_tag` | `name` | `None` | Delete tag |
| `get_config()` | — | `RepoConfig` | Load config |
| `update_config` | `config` | `None` | Save config |
| `get_context_store()` | — | `ContextStore` | Get event store |
| `regenerate_context_graph` | `output_file, output_format, limit` | `Path\|None` | Generate viz |

#### Module-level functions

```python
find_repository(start_path=None) -> Repository | None
init_repository(path=None, project_name="", user_name="", user_email="") -> Repository
```

#### Diff API (`packages/gitmap_core/diff.py`)

```python
diff_maps(map1, map2) -> MapDiff
diff_layers(layers1, layers2) -> list[LayerChange]
diff_json(obj1, obj2, ignore_order=True) -> dict
format_diff_summary(map_diff) -> str
format_diff_visual(map_diff, label_a, label_b) -> list[tuple[str, str, str]]
format_diff_stats(map_diff) -> dict[str, int]
```

#### Merge API (`packages/gitmap_core/merge.py`)

```python
merge_maps(ours, theirs, base=None) -> MergeResult
resolve_conflict(conflict, resolution: "ours"|"theirs"|"base") -> dict
apply_resolution(merge_result, layer_id, resolved_layer) -> MergeResult
format_merge_summary(result) -> str
```

#### Graph API (`packages/gitmap_core/graph.py`)

```python
build_graph(repo, limit=20) -> list[GraphNode]
```

#### Context API (`packages/gitmap_core/context.py`)

```python
# ContextStore methods
record_event(event_type, repo, payload, actor=None, ref=None, rationale=None) -> Event
get_event(event_id) -> Event | None
get_events_by_type(event_type, limit=50) -> list[Event]
search_events(query, event_types=None, start_date=None, end_date=None, limit=50) -> list[Event]
add_annotation(event_id, annotation_type, content, source="user") -> Annotation
get_annotations(event_id) -> list[Annotation]
record_lesson(content, related_event_id=None, source="user") -> Annotation
add_edge(source_id, target_id, relationship, metadata=None) -> Edge
get_related_events(event_id, relationship=None) -> list[tuple[Event, str]]
get_timeline(ref=None, start_date=None, end_date=None, include_annotations=True, limit=100) -> list[dict]
```

### 4.2 CLI Command Reference

```
gitmap init [--project-name] [--user-name] [--user-email]
gitmap clone <portal-url> <item-id> [--dest]
gitmap status
gitmap commit -m <message> [--rationale <why>]
gitmap diff [<commit-a>] [<commit-b>]
gitmap log [--limit N] [--graph] [--branch <name>]
gitmap show <commit-id>
gitmap branch [--list] [--create <name>] [--delete <name>]
gitmap checkout <branch-or-commit>
gitmap merge <branch>
gitmap merge-from <branch> [--no-commit]
gitmap cherry-pick <commit-id>
gitmap revert <commit-id>
gitmap tag [--list] [--create <name>] [--delete <name>]
gitmap stash [push|pop|list|drop|clear] [--message <msg>]
gitmap push [--branch <name>] [--skip-notifications]
gitmap pull [--branch <name>]
gitmap notify [--branch <name>]
gitmap list [--portal-url] [--folder]
gitmap config [--get <key>] [--set <key> <value>]
gitmap context [--timeline] [--search <query>] [--limit N]
gitmap layer-settings-merge <source-branch> <target-branch>
gitmap auto-pull [--interval N]
gitmap daemon [--start|--stop|--status]
gitmap setup-repos
```

### 4.3 PyPI Package Distribution

Three packages published to PyPI:

```bash
pip install gitmap-core    # Core library: 660+ tests, 96% coverage
pip install gitmap-cli     # CLI: installs 'gitmap' command
pip install gitmap-mcp     # MCP server for AI agents
```

All three packages declare Python ≥ 3.10 and are structured with `pyproject.toml` (hatchling build backend).

---

## 5. Performance Analysis

### 5.1 Commit Creation

Commit creation is dominated by:
1. JSON serialization of `map_data` for ID generation: O(|map|)
2. SHA-256 hash of serialized content: O(|map|)
3. JSON serialization for file write: O(|map|)
4. File I/O: constant overhead + O(|map|) bytes

For a typical web map (50 KB), this is sub-millisecond exclusive of disk I/O. With 100 KB map data and 500 commits, storage is ~50 MB—well within typical filesystem limits for project lifetimes.

### 5.2 History Traversal

`get_commit_history()` traverses a linked list via `parent` pointers: O(depth). For a linear history of 1000 commits, this loads 1000 JSON files sequentially. On modern SSDs this is approximately 100–500 ms depending on file size.

**Optimization opportunity**: An index of commit IDs in topological order would allow O(1) range queries. Currently absent—acceptable for the typical <100 commit project lifecycle but would degrade for long-running repositories.

### 5.3 Common Ancestor Search

`find_common_ancestor()` performs two BFS passes. For two branches diverged 10 commits ago with 100 total commits, Phase 1 visits ~100 commits, Phase 2 visits at most 10. In practice this is fast enough to be imperceptible. For very large histories (1000+ commits), this could take seconds due to file I/O—future optimization with in-memory commit cache is planned.

### 5.4 Diff Engine

`diff_maps()` with `DeepDiff` is O(|map|) in average case. For maps with hundreds of layers and complex nested rendering configurations, `DeepDiff` may take 50–200 ms. This is acceptable for interactive CLI use but would be a bottleneck in high-frequency automated diffing scenarios.

### 5.5 Context Store (SQLite)

SQLite with WAL mode supports concurrent reads and single-writer appends efficiently. The `record_event()` method performs a single `INSERT` + optional annotation `INSERT`. Expected throughput: thousands of events per second—more than sufficient for version control use patterns. The `search_events()` full-text LIKE query on `payload` column will degrade for large event stores (>100K events) without FTS5 support. This is not indexed.

### 5.6 Graph Rendering

`build_graph(repo, limit=20)` collects commits across all branches (up to 4×limit per branch walk), sorts topologically, then renders lane assignments. For a 20-commit limit this is fast. The `_topological_sort()` uses a priority queue simulated by sorted list insertion, giving O(n log n) behavior. For `limit=500` this would still complete in under 100 ms.

---

## 6. Security Considerations

### 6.1 Authentication Model

Portal credentials are handled via `PortalConnection.connect()` with the following priority chain:

1. Explicit username/password arguments.
2. `PORTAL_USER` / `PORTAL_PASSWORD` environment variables (or `ARCGIS_USERNAME` / `ARCGIS_PASSWORD`).
3. `.env` file in current or parent directories (loaded via `python-dotenv`).
4. ArcGIS Pro token authentication (if running in Pro environment).
5. Anonymous access.

**Security concern**: The `.env` file loading searches up to 3 parent directories, which could inadvertently load credentials from a parent project. The directory traversal is shallow but could be tightened to repository-root-only.

**Recommendation**: Credentials should be stored in OS keychain (1Password, macOS Keychain) rather than `.env` files. An `arcgis` token file approach would be more secure.

### 6.2 Repository Data Privacy

All commit data (including the full `map_data` JSON) is stored in plaintext `.json` files under `.gitmap/commits/`. For web maps containing sensitive layer configurations (internal service URLs, API keys embedded in layer definitions), this represents a data exposure risk if the repository directory is accessible to unauthorized users or committed to a public source control system.

**Mitigation**: The `.gitmap` directory should be added to `.gitignore` if the parent directory is a Git repository. No encryption-at-rest is currently implemented.

### 6.3 Input Validation

Branch names are validated to reject spaces (in `create_branch` and `create_tag`). However, there is no validation for:
- Path traversal in branch names (e.g., `../../etc/passwd`).
- Non-printable characters.
- Maximum length.

Since branch names map directly to filesystem paths via `self.heads_dir / name`, a branch name containing `../` could write outside the `.gitmap` directory. This is a medium-severity vulnerability for multi-user environments.

**Recommendation**: Validate branch names against a strict allowlist (`[a-zA-Z0-9._/\-]+`) before creating filesystem paths.

### 6.4 Portal API Security

The `RemoteOperations` class calls `gis.content.add()` and `item.update()` using the authenticated user's permissions. No additional authorization layer is implemented—GitMap inherits whatever Portal permissions the authenticated user has. Write operations to shared items could overwrite other users' work if Portal permissions are too permissive.

### 6.5 MCP Server Security

The MCP server runs as a local process and communicates over stdio with the AI agent. No network exposure is involved in the default configuration. Tool inputs (commit messages, branch names, rationale text) are passed directly to repository operations without sanitization—relevant if the server is adapted for remote use.

---

## 7. Known Limitations & Technical Debt

### 7.1 Pull Does Not Auto-Commit

After `gitmap pull`, the fetched map data is written to `index.json` but not committed. Users must manually run `gitmap commit` to snapshot the pulled state. This inconsistency with Git's pull workflow (which updates the branch pointer) may confuse users and break automation scripts.

**Root cause**: The current design separates "fetch latest state" (pull) from "create a version snapshot" (commit), treating pull as a refresh operation. This may actually be intentional for user workflows where pull is used to inspect changes before committing—but it is undocumented.

### 7.2 Commit ID Collision Handling

The 12-character commit ID prefix provides a ~4.7×10⁻¹⁵ collision probability per pair, but there is no collision detection code. If a collision occurs, `commit.save(self.commits_dir)` would overwrite the existing commit file silently.

### 7.3 Layers Without `id` Field

Layers lacking an `id` field are excluded from all diff, merge, cherry-pick, and revert operations. Some Esri-managed layers (sketch layers, custom popups) may not have stable IDs.

### 7.4 Kebab-Case Command Files

`layer-settings-merge.py` and `merge-from.py` use non-standard `importlib.util` loading. Renaming to `layer_settings_merge.py` / `merge_from.py` with appropriate click command names would eliminate this technical debt.

### 7.5 No Real-Time Collaboration

Two users cannot collaborate on the same `.gitmap` repository simultaneously without risk of corruption—there is no locking mechanism on branch files or the index. This is an acceptable limitation for the single-user local workflow but prevents Git-style team workflows without a dedicated server component.

### 7.6 Full Snapshot Storage

Each commit stores the complete map JSON. For maps with large embedded geometries or base64-encoded images in popup media, this can result in multi-MB commits. A delta-compression layer would significantly reduce storage overhead for high-frequency committers.

### 7.7 No Network-Aware Push Retry

`push()` and `pull()` do not implement retry logic for transient Portal API failures (rate limits, network timeouts). Users must manually retry on failure.

### 7.8 `stash_push` Timestamp-Based ID

The stash file timestamp-based naming (`{int(time.time())}.json`) has a 1-second collision window. Rapid successive stash operations within the same second would overwrite the stash file. Using UUID for stash file naming would eliminate this.

### 7.9 Duplicate Production Notification Logic

The production branch notification code is duplicated across the item-ID push path and the folder-based push path in `remote.py`. Extracting to a `_send_production_notification(item, branch, commit)` helper would eliminate ~80 lines of duplication.

---

## 8. Related Work

### 8.1 Esri Versioned Geodatabases

Esri's traditional versioned geodatabases provide branch-and-reconcile workflows for feature class editing—the closest analog in the GIS ecosystem. Key differences:
- Geodatabase versioning operates at the **data layer** (features, geometry, attributes), not the **cartographic configuration layer**.
- Web map JSON (layer visibility, symbology, popups) is explicitly out of scope for geodatabase versioning.
- Branch versioning (introduced in ArcGIS Enterprise 10.7) adds optimistic locking and REST API access but remains data-focused.

Git-Map fills the orthogonal gap: version control for **how data is presented**, not the data itself.

### 8.2 ArcGIS Versioning Services (REST API)

ArcGIS Versioning Services provide API-level access to traditional versioning workflows via REST. These are feature service-focused and do not address web map configuration management.

### 8.3 Git + Flat Files

Some GIS teams export web map JSON to flat files and use standard Git for version control. This approach works but requires:
- Manual export/import of JSON from Portal.
- Custom scripting for automated workflows.
- No Portal-aware diff/merge semantics.
- No integration with Portal's sharing/notification model.

Git-Map automates this workflow and adds Portal-specific semantics (layer ID indexing, three-way merge) that generic Git diff cannot provide.

### 8.4 Existing GIS Version Control Research

Academic work in GIS version control has historically focused on topological data versioning (Worboys, 1994; Claramunt & Thériault, 1995), spatial history models, and temporal GIS. Web map configuration versioning is a newer problem tied to cloud GIS platform evolution and lacks peer-reviewed treatment to the authors' knowledge—representing a genuine gap this system begins to address.

### 8.5 JSON Version Control Tools

General-purpose JSON versioning tools (json-diff, jsondiffpatch) provide structure-aware diff but lack:
- Domain knowledge of ArcGIS web map semantics (layer IDs, service URLs).
- Three-way merge adapted to the GIS layer model.
- Portal authentication and item management.
- AI-agent integration via MCP.

### 8.6 Novel Aspects

Git-Map's primary novel contributions relative to existing work:
1. **Layer-atomic merge**: Treating each operational layer as the unit of merge conflict detection—analogous to file-level merge in Git but adapted to the ArcGIS JSON schema.
2. **Context graph integration**: Embedded SQLite event store with edge-typed relationships between VCS operations, enabling episodic memory for AI agents.
3. **MCP exposure**: Making all VCS operations available as typed MCP tools is, to the authors' knowledge, the first such integration in the GIS version control space.
4. **Portal-native push/pull**: Bidirectional synchronization with Portal items as the remote, preserving sharing settings and enabling production branch notifications.

---

## 9. Future Work

### 9.1 Network Remote Server

A lightweight HTTP server (`gitmap-server`) providing multi-user collaboration, centralized repository hosting, and conflict resolution UI. This would enable Git-style team workflows (push/pull to a shared server, not just Portal).

### 9.2 Delta Compression

Replace snapshot-per-commit with delta storage (JSON patch arrays) to reduce repository size by 80–90% for typical sequential edit patterns.

### 9.3 Portal Item Monitoring

A webhook-based or polling daemon that detects external edits to Portal items (edits made outside GitMap) and auto-stages them with informational commits.

### 9.4 Conflict Resolution UI

A web-based or TUI conflict resolution interface showing side-by-side layer comparisons with visual map previews.

### 9.5 FTS5 Full-Text Search

Upgrade the `context.db` LIKE-based search to SQLite FTS5 for performant full-text search across large event stores.

### 9.6 Branch Name Validation

Implement strict branch name validation to prevent path traversal and ensure filesystem safety across operating systems.

### 9.7 Auto-Pull Fast-Forward

When a pull results in no conflicts (remote state is a fast-forward from local HEAD), automatically create a commit to mirror Git's merge behavior.

### 9.8 PyPI Ecosystem Badges & CI

Complete GitHub Actions CI pipeline with matrix testing across Python 3.10/3.11/3.12, badge publication, and automated PyPI release on tag.

### 9.9 ArcGIS Pro Ribbon Integration

Enhance the Python Toolbox with custom ribbon buttons and panels for a more native ArcGIS Pro UX, including visual map previews in diff output.

### 9.10 Community Documentation Portal

Full MkDocs-based documentation site with tutorial videos, a quickstart GIF demonstrating the commit/branch/revert workflow, and a community forum for GIS practitioners.

---

## 10. Appendix

### 10.1 Project File Tree (Source Files Only)

```
git-map/
├── apps/
│   ├── cli/gitmap/
│   │   ├── main.py
│   │   ├── help_formatter.py
│   │   ├── pyproject.toml
│   │   └── commands/
│   │       ├── auto_pull.py    branch.py     checkout.py
│   │       ├── cherry_pick.py  clone.py      commit.py
│   │       ├── config.py       context.py    daemon.py
│   │       ├── diff.py         init.py       layer-settings-merge.py
│   │       ├── list.py         log.py        merge.py
│   │       ├── merge-from.py   notify.py     pull.py
│   │       ├── push.py         revert.py     setup_repos.py
│   │       ├── show.py         stash.py      status.py
│   │       ├── tag.py          utils.py
│   ├── client/
│   │   ├── gitmap-client/   # Textual TUI
│   │   └── gitmap-gui/      # Flask web UI
│   └── mcp/gitmap-mcp/
│       ├── main.py
│       ├── pyproject.toml
│       └── scripts/tools/
│           ├── branch_tools.py   commit_tools.py  context_tools.py
│           ├── layer_tools.py    portal_tools.py  remote_tools.py
│           ├── repository_tools.py  stash_tools.py  utils.py
├── integrations/
│   ├── arcgis_pro/GitMap.pyt
│   └── openclaw/
│       ├── tools.py   server.py  index.ts  openclaw.plugin.json
├── packages/gitmap_core/
│   ├── communication.py  compat.py    connection.py
│   ├── context.py        diff.py      graph.py
│   ├── maps.py           merge.py     models.py
│   ├── remote.py         repository.py  visualize.py
│   ├── pyproject.toml
│   └── tests/ (660+ tests)
├── docs/
│   ├── getting-started/   commands/   guides/
├── documentation/project_specs/
├── roadmap.md
├── CHANGELOG.md
├── pyproject.toml
└── mkdocs.yml
```

### 10.2 Dependency List

**`gitmap-core` runtime dependencies:**
```
arcgis>=2.2.0          # ArcGIS API for Python
deepdiff>=6.0.0        # Structural JSON diff
python-dotenv>=1.0.0   # .env file loading
```

**`gitmap-cli` additional dependencies:**
```
click>=8.0.0           # CLI framework
rich>=13.0.0           # Terminal formatting
```

**`gitmap-mcp` additional dependencies:**
```
mcp>=0.1.0             # Model Context Protocol SDK
fastmcp>=0.1.0         # FastMCP server framework
```

**`gitmap-client` additional dependencies:**
```
textual>=0.50.0        # Terminal UI framework
```

**`gitmap-gui` additional dependencies:**
```
flask>=3.0.0           # Web framework
```

**Development dependencies:**
```
pytest>=8.0.0
pytest-cov>=5.0.0
deepdiff>=6.0.0
```

### 10.3 Configuration Reference

**`.gitmap/config.json` schema:**

```json
{
  "version": "1.0",
  "user_name": "TR Ingram",
  "user_email": "tr@example.com",
  "project_name": "Operations Dashboard",
  "auto_visualize": false,
  "remote": {
    "name": "origin",
    "url": "https://your-org.maps.arcgis.com",
    "folder_id": "abc123def456",
    "folder_name": "Operations Dashboard",
    "item_id": "webmap_item_id_from_portal",
    "production_branch": "main"
  }
}
```

**Environment variables:**

| Variable | Purpose |
|----------|---------|
| `PORTAL_USER` | Portal username |
| `PORTAL_PASSWORD` | Portal password |
| `ARCGIS_USERNAME` | Alternative username key |
| `ARCGIS_PASSWORD` | Alternative password key |

### 10.4 Test Coverage Summary

As of March 2026:

| Package | Tests | Coverage |
|---------|-------|---------|
| `gitmap_core` | 640+ | ~96% |
| `gitmap_cli` | 20+ | ~70% |
| `gitmap_mcp` | 15+ | ~65% |
| **Total** | **660+** | **~90% (aggregate)** |

Test coverage is measured via `pytest-cov`. The core library achieves high coverage through dedicated test modules for each source file: `test_models.py`, `test_repository.py`, `test_diff.py`, `test_merge.py`, `test_graph.py`, `test_context.py`, `test_remote.py`, `test_communication.py`, `test_compat.py`, `test_connection.py`, `test_visualize.py`, `test_maps.py`, `test_stash_mcp.py`, and `test_show_command.py`.

### 10.5 Recent Git History (Last 30 Commits)

```
a65a686  feat(cli): grouped help output — organise commands by workflow section
fbb2eaa  fix(cli): register missing 'show' command in main.py
85586ff  fix(graph): wire parent2 through create_commit so merge commits render correctly
66f522b  Merge pull request #110 — community health files
cf35f42  chore: add community health files (issue templates, PR template, CoC, security policy)
fe5d434  Merge pull request #109 — docs: list, lsm, merge-from command pages
ca0850e  docs: add missing command pages for list, lsm, and merge-from
3ba9c79  Merge pull request #108 — docs: missing command pages
e4c0a41  docs: add missing command pages (cherry-pick, config, context, notify, auto-pull, setup-repos, daemon)
f3588c6  Merge pull request #105 — feat: pypi-publish-complete
9914b4c  fix(merge): resolve publish workflow conflicts — keep full 3-package setup
354431d  docs: add show command page, update log docs with --graph and --branch options
b150bcc  feat: grouped help formatter + welcome banner for CLI
d897394  feat: complete PyPI publish setup for all three packages
1295915  Merge pull request #104 — feat: log-graph
22a7089  feat: gitmap log --graph — visual ASCII commit graph with branch labels
db68104  Merge pull request #103 — feat: show-command
94792e3  feat: add 'gitmap show' command — display commit details + diff
c0a51e2  Merge pull request #102 — feat: pypi-publish
eddb53e  feat: PyPI publish — pip install gitmap, dual-package workflow
c0a51e2  Merge pull request #101 — docs: community-launch-strategy
a4eddc3  docs: community launch strategy — blog post, r/gis draft, launch playbook
9ef2123  Merge pull request #100 — feat: landing-page
e995e7d  docs: technical paper v2 — comprehensive v0.6.0 update
e3d841e  feat: landing page — marketing site for community adoption
568c405  feat: ArcGIS Pro Python toolbox — 9 native tools for version-controlling web maps
```

---

*This paper was generated as part of the Git-Map technical documentation series. Repository: `14-TR/Git-Map` (public). License: MIT.*
