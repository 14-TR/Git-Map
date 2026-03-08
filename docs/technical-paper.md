# Git-Map: A Version Control System for ArcGIS Web Maps

**TR Ingram**  
*Independent Researcher / GIS Software Engineer*  
*Wyoming, USA*

**Date:** March 8, 2026  
**Version:** 2.0

---

## Abstract

Web maps published through ArcGIS Online (AGOL) and ArcGIS Enterprise Portal represent complex, stateful GIS artifacts whose operational layer configurations, symbology, popups, and cartographic properties evolve continuously over time. Despite this complexity, Esri's platform offers no native mechanism to snapshot, branch, or revert a web map's JSON definition — leaving GIS professionals to rely on ad hoc strategies such as periodic item cloning, manual change logs, or informal naming conventions like "Map\_v3\_FINAL\_2." This paper presents **Git-Map** (v0.6.0), a Python-based version control system that brings Git's conceptual model — commits, branches, merges, cherry-picks, stashes, and reverts — to ArcGIS web map items. The system stores complete snapshots of a map's operational layer JSON at each commit, implements three-way merge logic at the layer level, provides a property-level diff engine built on `DeepDiff`, exposes all operations through a Model Context Protocol (MCP) server for AI-agent workflows, wraps nine operations as native ArcGIS Pro Python toolbox tools, maintains an SQLite-backed event graph for episodic context tracking, and is distributed as a PyPI package. With 660+ tests achieving up to 96% code coverage across Portal and AGOL environments, Git-Map demonstrates that rigorous software engineering practices can close the version control gap in modern GIS workflows.

---

## 1. Introduction

### 1.1 Problem Statement

A web map in ArcGIS Online or Portal for ArcGIS is fundamentally a JSON document — a structured payload conforming to the Esri web map specification — stored as an `applicationJSON` item in the Portal content system. This document encodes the complete operational state of a map: which feature layers are included (`operationalLayers`), their visibility, rendering, popup configurations, drawing info, spatial reference, extent, and basemap selection. Changes to any of these properties are reflected immediately in the item's data, with no history retained.

The implications for professional GIS workflows are significant. A solution engineer configuring a complex operations dashboard may introduce a breaking layer change, discover the error hours later, and have no reliable path back to the known-good state. A team of GIS analysts collaborating on a shared web map has no mechanism to work in parallel on feature additions without risk of overwriting each other's changes. A QA/QC process for map promotion from development to production environments must rely on manual comparison and institutional memory rather than deterministic diff output.

Esri's platform does provide *versioned geodatabases* for feature class editing — a mature, branch-and-reconcile workflow for vector data — but this mechanism operates at the geodatabase layer and does not extend to the web map item itself. Portal's built-in item revision history tracks ownership and sharing metadata changes but does not snapshot the full JSON payload. ArcGIS Versioning Services (traditional and branch versioning) address data editing workflows, not cartographic configuration management.

Git-Map addresses this gap by treating the web map JSON as the artifact under version control, applying concepts from distributed version control systems (DVCS) to the GIS domain.

### 1.2 Contributions

This paper makes the following contributions:

1. A formal architecture for a content-addressable, commit-based version control system operating on ArcGIS web map JSON.
2. A layer-atomic three-way merge algorithm adapted from Git's merge strategy to GIS-specific data structures.
3. A `DeepDiff`-backed property-level diff engine producing structured `MapDiff` objects.
4. An SQLite-backed event graph (`ContextStore`) enabling episodic memory and AI-agent context awareness.
5. A Model Context Protocol (MCP) server exposing all GitMap operations to AI coding agents.
6. A native ArcGIS Pro Python Toolbox (.pyt) wrapping nine core GitMap operations.
7. An OpenClaw integration providing subprocess-based tool wrappers for agent-driven map management.

### 1.3 Scope

This paper covers Git-Map version 0.6.0 as of March 2026. The system supports ArcGIS Online and Portal for ArcGIS ≥ 10.9, requires Python ≥ 3.10, and is distributed under the MIT license. The scope includes the `gitmap_core` library, `gitmap` CLI, MCP server, ArcGIS Pro toolbox, and OpenClaw integration. Geodatabase versioning, feature editing workflows, and ArcGIS Server service management are explicitly out of scope.

---

## 2. System Architecture

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Git-Map Monorepo                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    packages/gitmap_core                       │  │
│  │  ┌──────────┐ ┌────────┐ ┌──────┐ ┌─────────┐ ┌─────────┐  │  │
│  │  │repository│ │ merge  │ │ diff │ │ context │ │  maps   │  │  │
│  │  │   .py    │ │  .py   │ │  .py │ │   .py   │ │   .py   │  │  │
│  │  └────┬─────┘ └────────┘ └──────┘ └────┬────┘ └─────────┘  │  │
│  │       │                                 │                    │  │
│  │  ┌────┴────┐  ┌──────────┐  ┌──────────┴───┐               │  │
│  │  │ models  │  │connection│  │  visualize   │               │  │
│  │  │   .py   │  │   .py   │  │     .py      │               │  │
│  │  └─────────┘  └──────────┘  └──────────────┘               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▲                                      │
│          ┌───────────────────┼───────────────────┐                 │
│          │                   │                   │                 │
│  ┌───────┴──────┐  ┌─────────┴───────┐  ┌───────┴──────────┐     │
│  │apps/cli      │  │apps/mcp         │  │integrations/     │     │
│  │gitmap CLI    │  │gitmap-mcp       │  │arcgis_pro/       │     │
│  │(25 commands) │  │(MCP server)     │  │GitMap.pyt        │     │
│  └──────────────┘  └─────────────────┘  └──────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────┐                               │
│  │  integrations/openclaw/         │                               │
│  │  tools.py + server.py           │                               │
│  └─────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
         │                                │
         ▼                                ▼
 ┌───────────────┐              ┌──────────────────┐
 │  Local .gitmap│              │  ArcGIS Portal/  │
 │  Directory    │◄────────────►│  AGOL Remote     │
 │  (filesystem) │   push/pull  │                  │
 └───────────────┘              └──────────────────┘
```

### 2.2 Repository On-Disk Layout

The `.gitmap` directory mirrors the conceptual layout of Git's `.git`:

```
<project-root>/
└── .gitmap/
    ├── config.json          # RepoConfig: user, remote, project_name
    ├── HEAD                 # "ref: refs/heads/main" or bare commit ID
    ├── index.json           # Staging area (current map JSON snapshot)
    ├── context.db           # SQLite event graph
    ├── refs/
    │   ├── heads/           # Local branches (files containing commit IDs)
    │   │   └── main
    │   ├── remotes/
    │   │   └── origin/      # Remote tracking refs
    │   └── tags/            # Tag refs (commit ID pointers)
    ├── objects/
    │   └── commits/         # Content-addressed commit JSON files
    │       └── <hash12>.json
    └── stash/
        ├── stash_list.json  # Ordered stack of stash metadata
        └── <timestamp>.json # Individual stash payloads
```

### 2.3 Data Flow

**Commit flow:**
```
Portal Item → maps.get_webmap_json() → index.json (staging)
→ repository.create_commit() → SHA-256 hash → objects/commits/<id>.json
→ refs/heads/<branch> updated → context.db event recorded
```

**Push flow:**
```
local commit → remote.push_branch() → Portal folder created
→ branch item uploaded as JSON → metadata item updated
```

**Pull flow:**
```
Portal branch item → remote.pull_branch() → local commits reconstructed
→ index.json updated → HEAD updated
```

**Merge flow:**
```
two branch tips → find_common_ancestor() BFS traversal
→ merge.merge_maps(ours, theirs, base) → MergeResult
→ conflicts reported or auto-resolved → new merge commit
```

### 2.4 Technology Stack

| Layer | Technology | Justification |
|---|---|---|
| Core language | Python 3.10+ | ArcGIS API for Python constraint |
| Portal API | arcgis ≥ 2.3.0 | Official Esri Python SDK |
| CLI framework | Click 8.1+ | Composable commands, type coercion |
| Output rendering | Rich 13+ | Colored tables, progress bars |
| Diff engine | DeepDiff 6+ | Recursive JSON comparison |
| MCP server | FastMCP (mcp SDK) | AI agent tool exposure |
| Context DB | SQLite (stdlib) | Zero dependency, embedded |
| Lint/format | Ruff | Fast, comprehensive |
| Testing | pytest + coverage | Industry standard |

---

## 3. Implementation

### 3.1 Core Library (`packages/gitmap_core/`)

#### 3.1.1 `repository.py` — Repository Management

The `Repository` class is the central coordinator of all local operations. It is instantiated with a root path and lazily validates the `.gitmap` directory structure.

**Key design decisions:**

- **Content-addressed commits:** `_generate_commit_id()` computes a SHA-256 hash over `{"message": ..., "map_data": ..., "parent": ...}` with `sort_keys=True`, then truncates to 12 hex characters. This provides collision resistance adequate for typical GIS team sizes (expected commit counts in the low thousands) while keeping IDs human-readable. The 12-character hash has 2^48 ≈ 281 trillion possible values; birthday collision probability for 10,000 commits is approximately 1.8×10^-7.

- **Snapshot semantics:** Each commit stores the *complete* web map JSON, not a delta. This trades storage for simplicity — reading any historical state requires loading a single JSON file rather than replaying a patch chain. For typical web maps (50–500 KB JSON), this is acceptable; for maps with extremely large layer counts it may warrant future optimization.

- **HEAD/branch model:** HEAD is a text file containing either `ref: refs/heads/<branch>` (attached) or a bare commit ID (detached). Branch files under `refs/heads/` contain the commit ID they point to. This exactly mirrors Git's ref system.

- **Index as staging area:** `index.json` holds the current staged map JSON. This serves both as the staging buffer before a commit and as the "working state" after a checkout. Unlike Git, there is no separate working tree vs. index distinction — the staged JSON is the map state.

**`find_common_ancestor(commit_id_a, commit_id_b)`** implements a two-phase BFS:
1. Phase 1: Collect the complete ancestor set of commit A (both `parent` and `parent2` pointers followed, supporting merge commits). O(n) where n = commits reachable from A.
2. Phase 2: BFS from commit B, returning the first visited node present in A's ancestor set. This yields the *nearest* common ancestor by visiting B's lineage youngest-first. O(m) where m = commits reachable from B.

Combined complexity: O(n + m), where n and m are the ancestor commit counts. Space: O(n) for the ancestor set.

**Context recording** is performed non-blocking after every mutating operation (commit, revert, cherry-pick, tag, stash). If context recording fails, the primary operation completes normally — correctness is not sacrificed for observability.

#### 3.1.2 `models.py` — Data Models

Four dataclasses form the data model:

**`Commit`**: Core version control artifact.
```python
@dataclass
class Commit:
    id: str           # 12-char SHA-256 prefix
    message: str      # Commit message
    author: str       # Author name
    timestamp: str    # ISO 8601
    parent: str | None    # Single parent (or None for initial commit)
    parent2: str | None   # Second parent for merge commits
    map_data: dict[str, Any]  # Complete web map JSON snapshot
```

**`Branch`**: Named ref — name plus commit ID.

**`Remote`**: Portal URL, folder ID, item ID, and optional `production_branch` field. When `production_branch` is set and a push targets that branch, the communication module triggers Portal group notifications.

**`RepoConfig`**: Persisted to `config.json`. Includes `auto_visualize` flag — when true, `repository.regenerate_context_graph()` is called after every commit to refresh the Mermaid context graph.

All models implement `to_dict()`/`from_dict()` round-trip serialization and `save()`/`load()` file I/O methods.

#### 3.1.3 `merge.py` — Three-Way Layer Merge

The merge algorithm treats each operational layer (identified by its `id` field) as an atomic unit. This is the correct granularity for web map conflicts: in practice, two GIS analysts working on the same map typically add/remove/reconfigure distinct layers, rarely modifying the same layer simultaneously.

**Algorithm (`merge_maps(ours, theirs, base)`):**

For each layer encountered across both branches:

| Layer in ours? | Layer in theirs? | Layer in base? | Action |
|---|---|---|---|
| Yes | Yes | Yes | Three-way: if only ours changed → use ours; if only theirs changed → use theirs; if both changed → CONFLICT |
| Yes | Yes | No | Both added same ID (possibly different content) → CONFLICT if different |
| Yes | No | Yes | They deleted it; we kept it → keep it (our retention wins) |
| Yes | No | No | We added it → include |
| No | Yes | Yes | We deleted it; if they modified → CONFLICT; else respect deletion |
| No | Yes | No | They added it → include |

`MergeConflict` records `ours`, `theirs`, and `base` versions. The conflict resolution API (`resolve_conflict(conflict, resolution)`) accepts `"ours"`, `"theirs"`, or `"base"` strategy strings and is idempotent.

Tables (`tables` array) are processed identically to operational layers. The basemap is compared as a unit — if one branch changes it and the other doesn't, the change is accepted; if both change it, the merge must be resolved manually.

**Complexity:** O(L₁ + L₂ + L_b) where L₁, L₂, L_b are the layer counts in each version. Dictionary indexing makes all lookups O(1) average case.

#### 3.1.4 `diff.py` — Differential Analysis

`diff_maps(map1, map2)` produces a `MapDiff` containing:
- `layer_changes`: List of `LayerChange` objects (added/removed/modified)
- `table_changes`: Same structure for table entries
- `property_changes`: `DeepDiff` output for non-layer, non-table map properties

`DeepDiff` is configured with `ignore_order=True` to treat the operational layers list as a set keyed by ID, preventing spurious "modified" signals from layer reordering.

Three rendering functions serve different consumers:
- `format_diff_summary()` → human-readable string for CLI output
- `format_diff_visual()` → list of `(symbol, name, detail)` tuples for Rich Table rendering
- `format_diff_stats()` → `{added, removed, modified, total}` dictionary for MCP tool responses

#### 3.1.5 `context.py` — SQLite Event Graph

The `ContextStore` class provides episodic memory for agent-driven workflows. It wraps a SQLite database at `.gitmap/context.db` with two tables:

**`events`** schema:
```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT,
    repo TEXT NOT NULL,
    ref TEXT,
    payload TEXT NOT NULL,  -- JSON blob
    rationale TEXT          -- Optional human/agent explanation
);
```

**`edges`** schema (graph relationships between events):
```sql
CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship TEXT NOT NULL,  -- e.g., "reverts", "cherry_picked_from"
    metadata TEXT                -- JSON blob
);
```

**`annotations`** schema: Free-form notes attached to events, supporting lesson capture.

The `ContextStore` implements Python's context manager protocol (`__enter__`/`__exit__`) for safe connection management, and a `__del__` finalizer (added in v0.6.0 to fix a resource leak) ensures the SQLite connection is closed on garbage collection.

Key query methods:
- `get_timeline(limit)` → chronological event list
- `search_events(query, event_type, limit)` → full-text search over payload JSON
- `explain_changes(ref)` → structured explanation of a specific commit's context
- `record_lesson(lesson_text, event_id)` → append agent lessons to the graph

#### 3.1.6 `remote.py` — Portal Remote Operations

`RemoteOperations` manages the bidirectional sync between local commits and Portal:

**Push:** Each branch is stored as a Portal item of type `JSON` within a project-specific folder (`<project_name>_GitMap`). A separate `.gitmap_meta` item holds the metadata index mapping branch names to Portal item IDs. The `compat.py` module handles API differences between Portal 10.9 and AGOL (`create_folder`, `get_user_folders` differ in response structure between versions).

**Pull:** Fetches the branch item from Portal, reconstructs commit history, and updates the local repository. If the remote has diverged, the pull command advises the user to merge.

**Production branch notifications:** When `remote.production_branch` is set in config and a push targets that branch, `communication.notify_item_group_users()` sends Portal messages to all group members with access to the item.

#### 3.1.7 `maps.py` — Web Map JSON Operations

`get_webmap_json(item)` validates that an item is of type `Web Map` before calling `item.get_data()`. `get_webmap_by_id(gis, item_id)` wraps the lookup and validation in one call. `stage_map_json(repo, map_data)` writes to `index.json`. `publish_map_json(gis, map_data, title, folder_id)` creates or updates a Portal item with the merged map state.

#### 3.1.8 `visualize.py` — Context Graph Rendering

Generates Mermaid or HTML visualizations of the context event graph. When `auto_visualize=True` in `RepoConfig`, `repository.regenerate_context_graph()` is called after each commit, writing `context-graph.md` to the repo root. The graph renders events bottom-to-top (BT direction) with annotations shown as separate nodes.

#### 3.1.9 `compat.py` — ArcGIS API Compatibility Layer

Bridges behavioral differences between ArcGIS API for Python versions and Portal configurations. `create_folder(gis, name)` handles the case where Portal returns the folder object directly vs. as a dict. `get_user_folders(gis)` normalizes the response format. Error path coverage was improved from 86% to 96% in v0.6.0 via targeted test additions.

#### 3.1.10 `connection.py` — Portal Authentication

`PortalConnection` dataclass wraps a `GIS` object. The factory function `create_connection(url, username, password, env_path)` resolves credentials from environment variables (with `.env` file support via `python-dotenv`), CLI flags, or the system environment. Supported Portal targets: ArcGIS Online (`https://www.arcgis.com`) and any Portal for ArcGIS URL.

#### 3.1.11 `communication.py` — Portal Notifications

`notify_item_group_users(gis, item_id, message)` retrieves the groups that share access to a Portal item, iterates over group members, and sends Portal messages to each user. This is triggered automatically on pushes to the `production_branch`. A separate `notify` CLI command enables ad-hoc group notifications.

---

### 3.2 CLI Application (`apps/cli/`)

The `gitmap` CLI is built with Click 8 and registered as a `console_scripts` entry point in `pyproject.toml`. The main group (`cli` in `main.py`) registers 25 commands:

`init`, `clone`, `status`, `commit`, `log`, `branch`, `checkout`, `diff`, `merge`, `merge-from`, `push`, `pull`, `revert`, `cherry-pick`, `stash`, `tag`, `context`, `list`, `notify`, `config`, `daemon`, `auto-pull`, `setup-repos`, `layer-settings-merge`

**Architectural note:** Two commands (`layer-settings-merge` and `merge-from`) have hyphenated filenames and are loaded via `importlib.util.spec_from_file_location()` at startup — a necessary workaround for Python's module naming constraints that prohibits hyphens in identifiers. This is a known technical debt item.

**Output formatting:** All commands use Rich for terminal output — `rich.console.Console` for status messages, `rich.table.Table` for tabular data (diff output, branch listings, log entries), and `rich.progress` for operations with observable duration.

**Branch verbose listing** (`branch -v`) shows each branch name alongside its HEAD commit ID and commit message — added in v0.6.0 as a CLI polish item.

**Log filtering** (`log --branch <name>`) filters commit history to a specific branch — also added in v0.6.0.

---

### 3.3 MCP Server (`apps/mcp/gitmap-mcp/`)

The MCP server (`main.py`) uses the `FastMCP` class from Anthropic's `mcp` SDK to expose GitMap operations as tools consumable by AI agents in Cursor, Claude, or any MCP-compatible environment.

**Tool categories:**

| Module | Tools |
|---|---|
| `repository_tools.py` | `gitmap_init`, `gitmap_status` |
| `commit_tools.py` | `gitmap_commit`, `gitmap_log`, `gitmap_diff`, `gitmap_merge` |
| `branch_tools.py` | `gitmap_branch_list`, `gitmap_branch_create`, `gitmap_branch_delete`, `gitmap_checkout` |
| `remote_tools.py` | `gitmap_push`, `gitmap_pull` |
| `layer_tools.py` | `gitmap_layer_settings_merge` |
| `portal_tools.py` | `gitmap_list_maps`, `gitmap_list_groups`, `gitmap_notify` |
| `stash_tools.py` | `gitmap_stash_push`, `gitmap_stash_pop`, `gitmap_stash_list`, `gitmap_stash_drop` |
| `context_tools.py` | `context_get_timeline`, `context_explain_changes`, `context_search_history`, `context_record_lesson` |

The MCP server performs `.env` discovery at startup by walking up from `__file__` up to 5 directory levels, enabling credential injection without requiring explicit configuration by the AI agent. All tools return structured dictionaries rather than formatted strings, enabling agent-side post-processing.

---

### 3.4 ArcGIS Pro Toolbox (`integrations/arcgis_pro/GitMap.pyt`)

Nine tools are wrapped as ArcGIS Pro Python Toolbox tools, each inheriting from ArcGIS Pro's `object` base and implementing `getParameterInfo()`, `execute()`, and optionally `updateMessages()`:

1. **InitRepo** — Initializes a new GitMap repository in a workspace folder
2. **CommitMap** — Creates a commit from the current staged map state
3. **CheckoutBranch** — Switches to a specified branch
4. **CreateBranch** — Creates a new branch from HEAD
5. **LogHistory** — Displays commit history in the ArcGIS Pro Messages window
6. **DiffMaps** — Compares two commits and reports layer changes
7. **StatusCheck** — Shows staged changes vs. HEAD
8. **PushRemote** — Pushes current branch to configured Portal remote
9. **PullRemote** — Pulls updates from Portal remote

The toolbox uses `arcpy.Parameter` for input definition and `arcpy.AddMessage()` / `arcpy.AddError()` for output. The `_get_repo(workspace)` helper function wraps `Repository(Path(workspace))` with an `ImportError` guard that produces a user-friendly message if `gitmap_core` is not installed in the ArcGIS Pro Python environment.

---

### 3.5 OpenClaw Integration (`integrations/openclaw/`)

The OpenClaw integration provides subprocess-based wrappers around the `gitmap` CLI, enabling the AI assistant "Jig" to manage web maps through natural language. `tools.py` exposes functions that build CLI argument arrays, invoke `subprocess.run()`, and parse structured output from stdout/stderr.

`_find_gitmap()` uses a fallback chain: (1) check `PATH` via `shutil.which()`, (2) run as Python module from source directory, (3) last-resort module invocation. This ensures the tool works whether GitMap is installed globally or only in development mode.

The MCP server wrapper (`server.py`) re-exposes these tool functions as FastMCP tools with JSON schemas, enabling use from any MCP-compatible AI agent.

---

## 4. API / Interface Specification

### 4.1 CLI Commands

#### `gitmap init [--project-name TEXT] [--user TEXT] [--email TEXT] [PATH]`
Initializes a `.gitmap` repository. Creates directory structure, initial config, HEAD pointing to `main`, empty index, and context database.

#### `gitmap clone <item-id> [--url TEXT] [--username TEXT] [--password TEXT]`
Clones a Portal web map into a new local repository, fetching the map JSON and initializing commit history.

#### `gitmap status`
Compares `index.json` against HEAD commit. Reports staged vs. unstaged changes using `diff_maps()`. Exit codes: 0 = clean, 1 = changes present.

#### `gitmap commit -m <message> [--author TEXT] [--rationale TEXT]`
Creates a commit from the current index. `--rationale` populates the context graph annotation for agent reasoning.

#### `gitmap log [--limit N] [--branch NAME]`
Displays commit history as Rich table. `--branch` filters to a specific branch lineage.

#### `gitmap branch [-v] [-d NAME] [NAME [COMMIT]]`
Lists branches (with verbose `-v`), creates a new branch, or deletes an existing one with `-d`.

#### `gitmap checkout <branch>`
Switches HEAD to a branch and restores `index.json` from that branch's HEAD commit.

#### `gitmap diff [<commit-a> [<commit-b>]]`
Compares index vs. HEAD (no args), or two commits, or two branches. Renders as Rich table with `+`/`-`/`~` symbols.

#### `gitmap merge <branch>`
Three-way merges the named branch into current branch. Reports conflicts if any; creates a merge commit with `parent2` set if successful.

#### `gitmap merge-from <branch> [--strategy ours|theirs]`
Merge with explicit conflict resolution strategy.

#### `gitmap push [--url TEXT] [--username TEXT] [--password TEXT]`
Pushes current branch to Portal, creating folder and items as needed.

#### `gitmap pull [--url TEXT] [--username TEXT] [--password TEXT]`
Pulls updates from Portal remote for the current branch.

#### `gitmap revert <commit-id> [--rationale TEXT]`
Creates a new inverse commit that undoes the specified commit's changes.

#### `gitmap cherry-pick <commit-id> [--rationale TEXT]`
Applies changes from a specific commit to the current branch.

#### `gitmap stash [push|pop|list|drop|clear] [OPTIONS]`
Stash stack operations. `push` saves the current index to a stack entry and restores HEAD state. `pop` applies and removes the most recent stash. `drop` removes without applying.

#### `gitmap tag [NAME] [COMMIT]`
Lists all tags (no args) or creates a tag pointing to a commit.

#### `gitmap context [timeline|explain|search|lesson] [OPTIONS]`
Queries the context graph. `timeline` shows recent events; `explain <ref>` explains a commit's context; `search <query>` searches event payloads; `lesson <text>` records an agent lesson.

#### `gitmap list [--url TEXT] [--username TEXT]`
Lists web maps accessible from a Portal connection.

#### `gitmap notify --item-id TEXT --message TEXT [--url TEXT]`
Sends Portal messages to all group members sharing access to an item.

#### `gitmap config [--user TEXT] [--email TEXT] [--remote-url TEXT]`
Reads or updates repository configuration.

#### `gitmap auto-pull [--interval SECONDS]`
Daemon mode: polls Portal for changes and pulls automatically.

#### `gitmap layer-settings-merge <source-branch>`
Specialized merge that applies only layer settings (symbology, popups) without affecting layer membership.

### 4.2 Core Library API

#### `Repository(root: Path | str)`
Constructor. Does not require `.gitmap` to exist yet.

#### `repository.init(project_name, user_name, user_email) → None`
#### `repository.exists() → bool`
#### `repository.is_valid() → bool`
#### `repository.get_current_branch() → str | None`
#### `repository.get_head_commit() → str | None`
#### `repository.list_branches() → list[str]`
#### `repository.create_branch(name, commit_id=None) → Branch`
#### `repository.update_branch(name, commit_id) → None`
#### `repository.delete_branch(name) → None`
#### `repository.checkout_branch(name) → None`
#### `repository.get_index() → dict`
#### `repository.update_index(map_data) → None`
#### `repository.create_commit(message, author=None, rationale=None) → Commit`
#### `repository.get_commit(commit_id) → Commit | None`
#### `repository.get_commit_history(start_commit=None, limit=None) → list[Commit]`
#### `repository.revert(commit_id, rationale=None) → Commit`
#### `repository.cherry_pick(commit_id, rationale=None) → Commit`
#### `repository.stash_push(message=None) → dict`
#### `repository.stash_pop(index=0) → dict`
#### `repository.stash_list() → list[dict]`
#### `repository.stash_drop(index=0) → dict`
#### `repository.stash_clear() → int`
#### `repository.list_tags() → list[str]`
#### `repository.create_tag(name, commit_id=None) → str`
#### `repository.delete_tag(name) → None`
#### `repository.find_common_ancestor(commit_id_a, commit_id_b) → str | None`
#### `repository.get_config() → RepoConfig`
#### `repository.update_config(config) → None`
#### `repository.has_uncommitted_changes() → bool`
#### `repository.get_context_store() → ContextStore`
#### `repository.regenerate_context_graph(...) → Path | None`

#### `find_repository(start_path=None) → Repository | None`
Walks up directory tree looking for `.gitmap`. Returns `None` if not found.

#### `merge_maps(ours, theirs, base=None) → MergeResult`
#### `diff_maps(map1, map2) → MapDiff`
#### `format_diff_visual(map_diff, label_a, label_b) → list[tuple[str, str, str]]`
#### `format_diff_stats(map_diff) → dict[str, int]`

### 4.3 Error Handling

All public methods raise `RuntimeError` with descriptive messages on failure. CLI commands catch these and display via `click.echo(..., err=True)` with a non-zero exit code. The `resolve_conflict()` function raises `ValueError` for invalid resolution strategies. Portal API errors propagate as `RuntimeError` wrappers.

---

## 5. Performance Analysis

### 5.1 Critical Path Complexity

| Operation | Time Complexity | Space Complexity | Notes |
|---|---|---|---|
| `create_commit()` | O(L log L) | O(L) | L = layers; sort_keys JSON serialization |
| `diff_maps()` | O(L₁ + L₂) | O(L₁ + L₂) | DeepDiff per-layer comparison |
| `merge_maps()` | O(L₁ + L₂ + L_b) | O(L₁ + L₂ + L_b) | Dict indexing, single pass |
| `find_common_ancestor()` | O(n + m) | O(n) | n, m = reachable commits |
| `get_commit_history()` | O(k) | O(k) | k = requested limit |
| `stash_push()` | O(L) | O(L) | Full index snapshot |
| `context_store.record_event()` | O(1) amortized | O(1) | SQLite insert |

### 5.2 Storage Characteristics

Because each commit stores a full JSON snapshot, storage grows as O(C × S) where C = commit count and S = average map JSON size. For a typical 50 KB web map with 100 commits, storage is approximately 5 MB — acceptable for local filesystem use. Deduplication or delta storage would reduce this substantially for repos with high commit frequency and minor changes per commit, but is not currently implemented.

### 5.3 Bottlenecks

**Portal API latency:** Push and pull operations are bounded by Portal API response times (typically 200ms–2s per REST call). Large branch histories require multiple round trips. The `auto-pull` daemon adds polling overhead proportional to check interval.

**DeepDiff on large maps:** The `DeepDiff` library performs recursive comparison, which for maps with 50+ layers and complex symbology JSON can take 50–500ms. This is only incurred during `diff` and `merge` operations, not during commit creation.

**SQLite I/O:** Context recording opens and closes a SQLite connection per event (via context manager). For high-frequency commit workflows, this could be optimized with connection pooling, but is acceptable for typical GIS team cadence.

### 5.4 Scaling Characteristics

Git-Map is designed for team sizes of 2–20 GIS analysts with commit cadence measured in hours, not seconds. At this scale, all operations complete comfortably within human-perceptible time bounds. The architecture would require redesign for CI/CD-style automated commit pipelines with sub-second cadence.

---

## 6. Security Considerations

### 6.1 Authentication Model

Portal credentials are passed via:
1. CLI flags (`--username`, `--password`) — visible in process table, not recommended for production
2. Environment variables (`PORTAL_USERNAME`, `PORTAL_PASSWORD`) — preferred
3. `.env` file discovered by walking parent directories — convenient for development

**Red flag:** The `.env` discovery walks up 3–5 directory levels, which could inadvertently load credentials from a parent project directory. A `.gitmap/.env` convention would be more secure.

### 6.2 Data Privacy

Web map JSON may contain embedded credentials (service URLs with tokens, API keys embedded in layer definitions). Git-Map does not filter or redact this content — it stores whatever the Portal API returns verbatim. Commit objects in `.gitmap/objects/commits/` should be treated as potentially containing sensitive Portal service credentials and excluded from general file sharing.

### 6.3 Input Validation

- Branch names: validated for non-empty and no-space constraints. More comprehensive validation (no `..`, no control characters) matching Git's ref validation rules is not yet implemented.
- Tag names: same minimal validation as branches.
- Commit IDs passed to `get_commit()`, `revert()`, `cherry_pick()` are validated by checking file existence in `objects/commits/`.
- Portal item IDs are passed directly to `gis.content.get()` without format validation — a malformed ID will raise a Portal API error rather than a meaningful exception.

### 6.4 Attack Surface

The MCP server runs locally and accepts connections from the configured MCP client only (no network exposure in default configuration). The OpenClaw integration invokes the `gitmap` CLI via `subprocess.run()` — shell injection is mitigated by using list-form subprocess arguments rather than shell string concatenation.

---

## 7. Known Limitations & Technical Debt

### 7.1 Current Limitations

1. **No delta compression:** Full JSON snapshots per commit. A 500 KB map with 1,000 commits = 500 MB of storage. For active teams, this may become problematic without periodic garbage collection.

2. **No conflict markers in JSON:** When a merge conflict is detected, `index.json` retains `ours` and the conflict is only reported in terminal output. Unlike Git's `<<<<<<<`/`=======`/`>>>>>>>` markers, there is no in-file conflict representation — the user must re-run `merge` with an explicit resolution flag.

3. **Minimal branch name validation:** Branch names with `/` create nested directory structure (e.g., `feature/layer-update` → `refs/heads/feature/layer-update`), which works correctly. Names with `..`, null bytes, or backslashes are not rejected and could cause unexpected behavior.

4. **Layer ordering not preserved in merge:** The merge algorithm treats layers as a set keyed by ID, discarding relative order. If two branches reorder layers differently, the merge output order is implementation-defined (Python dict insertion order from the iteration sequence).

5. **No atomic writes:** File writes to `index.json`, branch refs, and commit files are not atomic (no write-to-temp-then-rename). A process kill during a commit could leave the repository in a partially committed state.

6. **Hyphenated command filenames:** `layer-settings-merge.py` and `merge-from.py` are loaded via `importlib.util` workaround. These should be renamed to `layer_settings_merge.py` and `merge_from.py` with CLI aliases set in `@click.command(name="...")` decorators.

7. **`production_branch` notification is fire-and-forget:** `notify_item_group_users()` does not confirm message delivery or handle partial failures across group members.

### 7.2 Technical Debt

- `remote.py` contains a complex folder-discovery fallback chain (three separate lookup strategies) that is difficult to test and maintain. This should be refactored into a clean `get_folder_id(gis, name) → str | None` function with explicit priority ordering.
- `stash_push()` generates a stash ID using `int(time.time())` which is not monotonic under clock adjustments and could collide within a 1-second window. A UUID4 would be more appropriate.
- The MCP server imports tools from two different paths (package import vs. direct file import fallback) — this dual-import pattern adds maintenance overhead.
- `visualize.py` uses `direction="BT"` (bottom-to-top) hardcoded — this is not exposed as a configuration option.

---

## 8. Related Work

### 8.1 Esri's Built-in Versioning

ArcGIS's traditional versioning and branch versioning systems (ArcSDE, Enterprise Geodatabase) manage feature edits at the record level within geodatabases. They do not apply to web map items, dashboards, or application configuration. Git-Map is complementary to, not competitive with, these systems.

### 8.2 Git-Based GIS Workflows

**DVC (Data Version Control)** [Iterative, 2017] tracks large binary and data files alongside Git, but operates at the file level rather than on Portal-hosted JSON APIs. **Kart** (formerly Sno) provides Git-like versioning for geospatial vector data in GeoPackage format, again operating on local files rather than cloud-hosted map configurations.

**GeoGig** [BoundlesGeo, 2013] provides a DAG-based version control system for geospatial features and addresses history, branching, and merging of vector data — conceptually similar to Git-Map but for feature geometry rather than map configuration.

### 8.3 Git for Configuration Management

The use of Git (or Git-like systems) for configuration-as-code is well established: GitOps for Kubernetes manifests, Terraform state management via remote backends, and Ansible playbook versioning. Git-Map applies this philosophy to the GIS configuration domain, where Esri's proprietary REST APIs serve as the "runtime environment" analogous to a Kubernetes cluster.

### 8.4 Novelty

Git-Map's distinguishing characteristics are:
1. **Domain-specific merge semantics:** Layer-atomic three-way merge tuned to web map structure, rather than line-level text diffing.
2. **Live Portal synchronization:** Bidirectional push/pull against a live Portal API, not just local file tracking.
3. **AI-native design:** MCP server, context graph, and `rationale` fields are first-class features, not afterthoughts.
4. **ArcGIS Pro integration:** Native toolbox embedding for users who do not use command-line tools.

---

## 9. Future Work

### 9.1 Roadmap Items

From `roadmap.md`, the following items remain incomplete as of v0.6.0:

1. **Demo video** (60–90 seconds showing commit/branch/revert workflow) — highest community adoption value
2. **Landing page on ingramgeoai.com** — prerequisite for organic discovery
3. **Blog post / r/gis launch strategy** — community seeding

### 9.2 Architectural Evolution

**Delta compression:** Replace full-snapshot commits with a delta format (store only changed layers as JSON patches per RFC 6902). This would reduce storage O(C × S) to O(C × ΔS) for incremental workflows.

**Atomic writes:** Implement write-to-temp-then-atomic-rename for all state files. Critical for correctness under concurrent access or interrupted operations.

**Conflict markers in staged JSON:** Introduce a `__gitmap_conflict__` sentinel structure within `index.json` to represent unresolved conflicts inline, enabling GUI tooling to present conflict resolution interfaces.

**Web UI:** A browser-based repository explorer (commit graph visualization, layer diff side-by-side, merge conflict resolution) would dramatically lower the adoption barrier for non-CLI users.

**ArcGIS Pro ribbon integration:** Promote the `.pyt` toolbox tools to custom ribbon buttons in an ArcGIS Pro add-in (`.esriaddin` package), enabling one-click commit/branch/push without opening the Catalog pane.

**Multi-remote support:** The current config supports a single remote named `origin`. Supporting named remotes (analogous to Git's `git remote add <name> <url>`) would enable cross-organization workflows.

**Conflict resolution for layer ordering:** Preserve a canonical layer ordering even after merge by adopting a deterministic merge order policy (e.g., "ours order, then theirs additions appended").

**Signed commits:** Add an optional GPG or SSH signature field to `Commit` for audit trail integrity in regulated environments.

**GitHub Actions CI:** The roadmap lists CI/CD pipeline as item 4 — adding automated tests on PR with ArcGIS Online sandbox credentials would significantly improve confidence in remote operation correctness.

---

## 10. Appendix

### A. Full File Tree

```
git-map/
├── apps/
│   ├── cli/
│   │   └── gitmap/
│   │       ├── commands/          # 25 CLI command modules
│   │       │   ├── auto_pull.py
│   │       │   ├── branch.py
│   │       │   ├── checkout.py
│   │       │   ├── cherry_pick.py
│   │       │   ├── clone.py
│   │       │   ├── commit.py
│   │       │   ├── config.py
│   │       │   ├── context.py
│   │       │   ├── daemon.py
│   │       │   ├── diff.py
│   │       │   ├── init.py
│   │       │   ├── layer-settings-merge.py
│   │       │   ├── list.py
│   │       │   ├── log.py
│   │       │   ├── merge.py
│   │       │   ├── merge-from.py
│   │       │   ├── notify.py
│   │       │   ├── pull.py
│   │       │   ├── push.py
│   │       │   ├── revert.py
│   │       │   ├── setup_repos.py
│   │       │   ├── stash.py
│   │       │   ├── status.py
│   │       │   ├── tag.py
│   │       │   └── utils.py
│   │       └── main.py
│   └── mcp/
│       └── gitmap-mcp/
│           ├── main.py
│           └── scripts/tools/
│               ├── branch_tools.py
│               ├── commit_tools.py
│               ├── context_tools.py
│               ├── layer_tools.py
│               ├── portal_tools.py
│               ├── remote_tools.py
│               ├── repository_tools.py
│               ├── stash_tools.py
│               └── utils.py
├── docs/
│   ├── technical-paper.md        # This document
│   └── commands/                 # Per-command documentation
├── integrations/
│   ├── arcgis_pro/
│   │   └── GitMap.pyt            # 9-tool Python Toolbox
│   └── openclaw/
│       ├── tools.py
│       ├── server.py
│       └── tests/
├── packages/
│   └── gitmap_core/
│       ├── compat.py
│       ├── communication.py
│       ├── connection.py
│       ├── context.py
│       ├── diff.py
│       ├── maps.py
│       ├── merge.py
│       ├── models.py
│       ├── remote.py
│       ├── repository.py
│       ├── visualize.py
│       └── tests/                # 660+ test cases
├── landing/
│   └── index.html                # Marketing landing page
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
├── roadmap.md
└── mkdocs.yml
```

### B. Dependency List

**Runtime dependencies** (from `pyproject.toml`):

| Package | Version Constraint | Purpose |
|---|---|---|
| arcgis | ≥ 2.3.0 | ArcGIS Portal/AGOL API |
| click | ≥ 8.1.0 | CLI framework |
| rich | ≥ 13.0.0 | Terminal output formatting |
| deepdiff | ≥ 6.0.0 | Recursive JSON comparison |
| python-dotenv | ≥ 1.0.0 | .env credential loading |

**Development dependencies:**

| Package | Version Constraint | Purpose |
|---|---|---|
| pytest | ≥ 8.0 | Test runner |
| coverage | ≥ 7.0 | Code coverage measurement |
| ruff | ≥ 0.9.0 | Linting and formatting |

**MCP server additional dependency:**
- `mcp` (Anthropic MCP SDK) — not declared in top-level `pyproject.toml`; declared separately in the MCP app's requirements.

### C. Configuration Reference

**`.gitmap/config.json` schema:**
```json
{
  "version": "1.0",
  "user_name": "string",
  "user_email": "string",
  "project_name": "string",
  "auto_visualize": false,
  "remote": {
    "name": "origin",
    "url": "https://www.arcgis.com",
    "folder_id": "string | null",
    "folder_name": "string | null",
    "item_id": "string | null",
    "production_branch": "string | null"
  }
}
```

**Environment variables:**
```
PORTAL_URL         - Portal base URL
PORTAL_USERNAME    - Portal username
PORTAL_PASSWORD    - Portal password
GITMAP_AUTO_PULL_INTERVAL  - Daemon poll interval in seconds (default: 300)
```

### D. Test Coverage Summary (v0.6.0)

| Module | Test Count (approx.) | Coverage |
|---|---|---|
| repository.py | 200+ | ~95% |
| merge.py | 100+ | ~98% |
| diff.py | 80+ | ~97% |
| context.py | 60+ | ~92% |
| compat.py | 40+ | 96% |
| models.py | 50+ | ~99% |
| remote.py | 80+ | ~88% |
| maps.py | 40+ | ~90% |
| **Total** | **660+** | **~95% avg** |

### E. Version History

| Version | Date | Key Changes |
|---|---|---|
| 0.6.0 | 2026-03-05 | MCP stash tools, branch-to-branch diff, find_common_ancestor, ArcGIS Pro toolbox, landing page, PyPI publish, MkDocs site |
| 0.5.0 | 2025-02-14 | Communication module, Portal notifications, 608+ tests |
| 0.4.0 | 2025-02-10 | stash, cherry-pick, tag, revert commands; ArcGIS API compat layer |
| < 0.4.0 | 2024 | Initial CLI, core commit/branch/merge/diff/push/pull |

---

*This paper was auto-generated by the Git-Map paper generator (Jig, OpenClaw) on 2026-03-08 and reflects the state of the codebase at v0.6.0. Peer review and empirical benchmark data remain areas for future work.*
