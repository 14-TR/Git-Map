# Git-Map: A Version Control System for ArcGIS Web Maps

**TR Ingram**  
*Independent Researcher / GIS Software Engineer*  
*Wyoming, USA*

---

## Abstract

Web maps published through ArcGIS Online (AGOL) and ArcGIS Enterprise Portal represent complex, stateful GIS products whose operational layer configurations, symbology, popups, and cartographic properties evolve continuously over time. Despite this complexity, Esri's platform offers no native mechanism to snapshot, branch, or revert a web map's JSON definition — leaving GIS professionals to rely on ad hoc strategies such as periodic item cloning, manual change logs, or informal naming conventions like "Map_v3_FINAL_2." This paper presents **Git-Map**, a Python-based version control system that brings Git's conceptual model — commits, branches, merges, cherry-picks, and reverts — to ArcGIS web map items. The system stores complete snapshots of a map's operational layer JSON at each commit, implements three-way merge logic at the layer level, provides a property-level diff engine built on `DeepDiff`, exposes all operations through a Model Context Protocol (MCP) server for AI-agent workflows, and maintains an SQLite-backed event graph for episodic context tracking. With 674 tests achieving 96% code coverage across Portal and AGOL environments, Git-Map demonstrates that rigorous software engineering practices can close the version control gap in modern GIS workflows.

---

## 1. Introduction

### 1.1 Problem Statement

A web map in ArcGIS Online or Portal for ArcGIS is fundamentally a JSON document — a structured payload conforming to the Esri web map specification — stored as an `applicationJSON` item in the Portal content system. This document encodes the complete operational state of a map: which feature layers are included (`operationalLayers`), their visibility, rendering, popup configurations, drawing info, spatial reference, extent, and basemap selection. Changes to any of these properties are reflected immediately in the item's data, with no history retained.

The implications for professional GIS workflows are significant. A solution engineer configuring a complex operations dashboard may introduce a breaking layer change, discover the error hours later, and have no reliable path back to the known-good state. A team of GIS analysts collaborating on a shared web map has no mechanism to work in parallel on feature additions without risk of overwriting each other's changes. A QA/QC process for map promotion from development to production environments must rely on manual comparison and institutional memory rather than deterministic diff output.

Esri's platform does provide *versioned geodatabases* for feature class editing — a mature, branch-and-reconcile workflow for vector data — but this mechanism operates at the geodatabase layer and does not extend to the web map item itself. Portal's built-in item revision history tracks ownership and sharing metadata changes but does not snapshot the full JSON payload. ArcGIS Versioning Services (traditional and branch versioning) address data editing workflows, not cartographic configuration management.

Git-Map addresses this gap by treating the web map JSON as the artifact under version control, applying concepts from distributed version control systems (DVCS) to the GIS domain.

### 1.2 Contributions

This paper makes the following contributions:

1. **A formal model** for applying DVCS concepts (commits, branches, remotes, staging areas) to ArcGIS web map items, with semantics appropriate to the JSON-document nature of the artifact.

2. **A three-way merge algorithm** operating at the operational layer granularity, capable of auto-resolving non-conflicting parallel changes and surfacing genuine conflicts for human resolution.

3. **A compatibility abstraction layer** that normalizes behavioral differences across `arcgis` Python API versions 2.2.x through 2.4.x and across Portal vs. AGOL deployment targets.

4. **An MCP server integration** that exposes all Git-Map operations as structured tools consumable by AI coding agents and LLM-based automation pipelines.

5. **An SQLite-backed context graph** providing episodic memory of operations, rationales, and inter-event relationships for human and agent audit trails.

---

## 2. Related Work

### 2.1 ArcGIS Version Management Services

Esri's versioning infrastructure exists at the geodatabase level, not the web map level. Traditional versioning (ArcSDE) supports a parent-child edit isolation model where a DEFAULT version represents the authoritative state and child versions allow isolated editing with reconcile/post operations for re-integration. Branch versioning, introduced in ArcGIS Enterprise 10.6, extends this model to feature services accessed via web clients, enabling offline-capable workflows without requiring ArcMap. However, both mechanisms are scoped to `Workspace`-level transactional boundaries in the geodatabase — they track changes to feature geometries and attributes, not to the web map's operational layer configuration.

The Portal REST API provides item-level write operations (`updateItem`, `addItem`) that are atomic and non-versioned. A `GET /sharing/rest/content/items/{itemId}/data` returns the current JSON payload; there is no `?version=` parameter or history endpoint. Esri's ArcGIS Notebooks environment provides Python-based automation but does not expose a version control abstraction for web map items.

### 2.2 Portal Versioning Limitations

Portal's item versioning model records metadata events — title changes, tag updates, sharing group changes, thumbnail replacements — but does not snapshot the `data` payload. This is architecturally significant: the item's `modified` timestamp and `size` field will change when a user saves map layer changes, but the previous state is irretrievably overwritten. Portal's "protected" item flag prevents deletion but not modification.

ArcGIS Online's organizational content management supports "Copy Item" operations that create independent duplicates with new item IDs, which GIS administrators sometimes use manually as informal snapshots. This approach does not scale: it generates item sprawl, consumes storage quota, breaks sharing group memberships, and creates no structured relationship between copies that would support comparison or rollback.

### 2.3 General-Purpose Version Control for Structured Data

The literature on version control for non-code artifacts is limited but growing. Systems like DVC (Data Version Control) address the ML dataset versioning problem by tracking file hashes and storing large binary objects outside Git. DBngin and Liquibase address database schema versioning. None of these systems address the GIS web map domain, where the artifact is a complex JSON document with domain-specific semantics (layer ordering, spatial references, service URL references) and lives in a remote content management system rather than on the local filesystem.

Git-Map's approach is closest in spirit to tools like `git-annex` (managing remote binary content through a local metadata store) and JSON Patch (RFC 6902 diff-and-apply semantics), but implements domain-aware merge logic rather than generic structural diffing.

---

## 3. Architecture

### 3.1 System Overview

Git-Map is organized as a Python monorepo with two primary packages:

```
/packages/gitmap_core/     — Core library (models, repository, diff, merge, context)
/apps/mcp/gitmap-mcp/      — MCP server exposing gitmap_core as agent tools
```

The `gitmap_core` package has minimal external dependencies: `arcgis>=2.3.0` for Portal connectivity, `deepdiff>=6.0.0` for structural JSON comparison, `click>=8.1.0` for CLI construction, and `rich>=13.0.0` for terminal formatting. The SQLite-backed context store uses only stdlib `sqlite3`. This dependency discipline keeps the install footprint small — important for environments where GIS analysts must install tooling within constrained Conda/Python environments managed by IT departments.

### 3.2 Repository Structure

A Git-Map repository is a `.gitmap/` directory collocated with the project workspace. The structure mirrors Git's object store design:

```
.gitmap/
├── config.json          — RepoConfig: author, remote, project metadata
├── HEAD                 — Pointer: "ref: refs/heads/main" or commit ID
├── index.json           — Staging area: current web map JSON snapshot
├── context.db           — SQLite event graph
├── refs/
│   ├── heads/           — One file per branch, content = commit ID
│   ├── remotes/origin/  — Remote tracking refs
│   └── tags/            — Named commit references
└── objects/
    └── commits/         — {commit_id}.json files
```

This layout is intentionally analogous to Git's internal structure, reducing the cognitive overhead for GIS professionals already familiar with Git. Unlike Git, which uses content-addressed blob storage with pack files, Git-Map stores complete JSON snapshots per commit. This design choice accepts storage overhead in exchange for simplicity — a reasonable tradeoff given that web map JSON documents are typically 10–500 KB, and commit histories in practice are tens to low hundreds of commits.

### 3.3 Core Data Models

All persistent data structures are defined in `models.py` using Python `dataclasses`:

**`Commit`** is the primary snapshot object:
```python
@dataclass
class Commit:
    id: str           # SHA-256[:12] of (message + map_data + parent)
    message: str
    author: str
    timestamp: str    # ISO 8601
    parent: str | None
    parent2: str | None   # Non-None for merge commits
    map_data: dict[str, Any]   # Complete web map JSON
```

The commit ID is computed as `hashlib.sha256(json.dumps({message, map_data, parent}, sort_keys=True)).hexdigest()[:12]` — a content-addressed 12-character hex string that makes accidental ID collisions computationally negligible while remaining human-readable.

**`Branch`** is a named pointer: `name: str, commit_id: str`, stored as a one-line file under `.gitmap/refs/heads/{name}`.

**`Remote`** encodes Portal connection details: `url`, `folder_id`, `folder_name`, `item_id`, and `production_branch` — the last being used to trigger stakeholder notifications when a push targets the designated production branch.

**`RepoConfig`** stores per-repository settings including `user_name`, `user_email`, `project_name`, and an optional `auto_visualize` flag that triggers automatic context graph regeneration after each commit.

### 3.4 Repository Class

The `Repository` class (`repository.py`) encapsulates all filesystem operations. It exposes typed path properties (`commits_dir`, `heads_dir`, `context_db_path`) and implements the full operation surface: `init`, `create_commit`, `checkout_branch`, `create_branch`, `revert`, `cherry_pick`, `stash_push`, `stash_pop`, `find_common_ancestor`, and tag management.

Repository discovery uses an upward traversal pattern:

```python
def find_repository(start_path: Path | str | None = None) -> Repository | None:
    current = Path(start_path or Path.cwd()).resolve()
    while current != current.parent:
        if (current / ".gitmap").is_dir():
            return Repository(current)
        current = current.parent
    return None
```

This matches Git's behavior of searching parent directories, allowing `gitmap` commands to work from any subdirectory of a project.

---

## 4. Core Operations

### 4.1 Commit

The commit workflow follows a stage-then-commit model identical to Git:

1. **Stage**: `repository.update_index(map_data)` writes the web map JSON to `.gitmap/index.json`. In a portal-connected workflow, `gitmap pull` fetches the live item JSON and stages it automatically.

2. **Commit**: `repository.create_commit(message, author, rationale)` reads the index, computes the commit ID, serializes the `Commit` dataclass to `.gitmap/objects/commits/{id}.json`, advances the current branch ref, and records a `commit` event in the context store.

The `rationale` parameter is a first-class field — not part of the commit message — that is stored as an `Annotation` of type `rationale` in the context graph. This separation of *what changed* (commit message) from *why it changed* (rationale) supports audit trail requirements in regulated GIS environments.

### 4.2 Branch

Branch operations are file operations on `.gitmap/refs/heads/`:

- **Create**: `create_branch(name, commit_id=None)` creates a new file with the target commit ID. Nested branch names (e.g., `feature/layer-symbology`) are handled by `branch_path.parent.mkdir(parents=True, exist_ok=True)`.
- **Checkout**: `checkout_branch(name)` updates `HEAD` to point to the branch ref, then loads the branch's tip commit data into `index.json`, restoring the working state.
- **Delete**: Guarded against deleting the current branch.

### 4.3 Merge with Three-Way Base

The `merge_maps()` function in `merge.py` implements three-way merge semantics at the operational layer granularity. The merge algorithm:

```
For each layer ID in union(ours.layers, theirs.layers, base.layers):
    if ours == theirs:         → no conflict, use ours
    elif ours == base:         → only theirs changed, use theirs (auto-resolve)
    elif theirs == base:       → only ours changed, use ours (auto-resolve)
    else:                      → both changed, MergeConflict raised
    
    if in ours but not in base:    → we added (keep)
    if in theirs but not in base:  → they added (append)
    if in base but not in ours and theirs changed: → delete/modify conflict
```

The common ancestor commit is found via `Repository.find_common_ancestor(commit_id_a, commit_id_b)`, which uses a two-pass BFS: first collecting the full ancestor set of branch A, then walking branch B's ancestry until a common node is found. This correctly handles merge commits by following both `parent` and `parent2` pointers.

A `MergeResult` dataclass captures the outcome:
```python
@dataclass
class MergeResult:
    success: bool
    merged_data: dict[str, Any]
    conflicts: list[MergeConflict]
    added_layers: list[str]
    removed_layers: list[str]
    modified_layers: list[str]
```

Successful merges are committed immediately with `parent2` set to the merged branch's tip commit, preserving the full DAG topology.

### 4.4 Checkout

`checkout_branch` handles both branch switching and state restoration:

```python
def checkout_branch(self, name: str) -> None:
    self._write_head(name)
    commit_id = self.get_branch_commit(name)
    if commit_id:
        commit = self.get_commit(commit_id)
        self._write_index(commit.map_data)
    else:
        self._write_index({})   # New branch with no commits
```

Detached HEAD state (checking out a specific commit rather than a branch) is supported by writing the commit ID directly to `HEAD` rather than a ref pointer.

### 4.5 Revert

`revert(commit_id)` creates an inverse commit — it does not rewrite history. The algorithm computes the changes introduced by the target commit (by comparing it to its parent), then applies the inverse of those changes to the current HEAD state:

```python
def _compute_revert(self, current_data, commit_data, parent_data):
    # For each layer modified by commit: restore to parent version
    # For each layer added by commit: remove from current
    # For each layer removed by commit: re-add from parent
```

The revert commit is linked to the original commit in the context graph via an edge with `relationship="reverts"`, creating an auditable inverse-action record.

### 4.6 Cherry-Pick

`cherry_pick(commit_id)` applies the *diff* of a specific commit (relative to its parent) onto the current branch:

```python
def _apply_cherry_pick(self, current_data, commit_data, parent_data):
    # Layers added by commit: add to current if not present
    # Layers modified by commit: update in current
    # Layers removed by commit: remove from current
```

This is semantically equivalent to computing `patch = commit - commit.parent` and applying `patch` to `current`. The resulting commit message is annotated with `(cherry picked from commit {id[:8]})`, matching Git's convention.

### 4.7 Stash

The stash implementation uses a JSON-based stack at `.gitmap/stash/stash_list.json` with individual entry files named by timestamp hash. `stash_push` saves the current index, restores the HEAD commit state, and prepends the entry to the stack. `stash_pop`, `stash_drop`, and `stash_clear` manipulate this stack with appropriate file management.

---

## 5. Diff Engine

### 5.1 MapDiff Data Model

The diff module (`diff.py`) defines a structured change representation:

```python
@dataclass
class LayerChange:
    layer_id: str
    layer_title: str
    change_type: str   # 'added' | 'removed' | 'modified'
    details: dict[str, Any]   # DeepDiff output for modified layers

@dataclass
class MapDiff:
    layer_changes: list[LayerChange]
    table_changes: list[LayerChange]
    property_changes: dict[str, Any]   # Top-level map property changes
```

### 5.2 Diff Algorithm

`diff_maps(map1, map2)` performs a three-level comparison:

1. **Layer-level**: Indexes both `operationalLayers` lists by layer `id`, then identifies added (in map1 but not map2), removed (in map2 but not map1), and modified (in both but different) layers.

2. **Property-level**: For modified layers, invokes `DeepDiff(layer2, layer1, ignore_order=True)` to produce a structured diff of individual JSON fields. This surfaces changes at the property level — e.g., that `drawingInfo.renderer.type` changed from `simple` to `classBreaks`, or that `minScale` was updated from `0` to `500000`.

3. **Map-level properties**: Compares all top-level map properties excluding `operationalLayers` and `tables` using DeepDiff. This captures basemap changes, extent modifications, and spatial reference updates.

### 5.3 Visual Output

The `format_diff_visual()` function produces a list of `(symbol, name, detail)` tuples suitable for rendering as a Rich table:

```
Symbol  Layer                      Detail
------  -------------------------  ---------------------------
+       Traffic Incidents          Added in feature/incidents
~       Parcel Boundaries          3 field(s) changed
-       Deprecated Reference Layer Present in main, removed here
```

The `format_diff_stats()` function returns aggregate counts (`added`, `removed`, `modified`, `total`) for programmatic consumption by MCP tools and CI/CD pipelines.

### 5.4 Branch-to-Branch Diff

The diff engine operates on any two `dict` snapshots. The MCP `gitmap_diff` tool resolves branch names or commit IDs to their `map_data` dicts and invokes `diff_maps`, enabling cross-branch comparison without requiring a working Portal connection (all comparison data is local in the commit objects).

---

## 6. Compatibility Layer

### 6.1 Design Rationale

The Esri ArcGIS API for Python (`arcgis`) undergoes regular breaking changes between minor versions, particularly in the `content.folders` API surface and in the behavior of `GIS.content.search()`. Organizations running ArcGIS Enterprise may be locked to specific `arcgis` package versions by IT policy. Git-Map must function reliably across this version spread.

### 6.2 Version Detection

`compat.py` implements version detection using `@lru_cache`:

```python
@lru_cache(maxsize=1)
def get_arcgis_version() -> tuple[int, int, int]:
    import arcgis
    version_str = getattr(arcgis, "__version__", "0.0.0")
    parts = version_str.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2].split("-")[0]))
```

The cache ensures version detection occurs exactly once per process, avoiding repeated import overhead in hot paths.

### 6.3 API Shims

The most significant API divergence is in the folder management surface:

```python
FOLDERS_API_CHANGE_VERSION = (2, 3, 0)

def create_folder(gis: GIS, folder_name: str) -> dict[str, Any] | None:
    if check_minimum_version(*FOLDERS_API_CHANGE_VERSION):
        result = gis.content.folders.create(folder_name)   # 2.3.0+
    else:
        result = gis.content.create_folder(folder_name)    # < 2.3.0
```

Return value normalization is handled by `_extract_folder_info()`, which inspects both dict-style (`result.get("id")`) and object-style (`getattr(result, "id", None)`) responses, as different Portal versions return different types from the same nominal API call.

The `get_user_folders()` shim implements three fallback strategies — `user.folders`, `gis.content.folders.list()`, and user item enumeration — to handle Portal configurations where certain API paths are restricted or return empty results.

### 6.4 Test Coverage

The compatibility layer is exercised by `test_compat.py`, which mocks `arcgis` version strings and verifies that the correct API path is invoked for each version range. The full test suite comprises **674 tests** across 13 test modules, achieving **96% code coverage**. Tests run entirely without a live Portal connection by mocking `arcgis.gis.GIS` and item objects at the `unittest.mock` boundary.

---

## 7. MCP Server Integration

### 7.1 Model Context Protocol Overview

The Model Context Protocol (MCP) is an open standard for exposing application functionality as typed tools consumable by AI coding agents and LLMs. Git-Map implements an MCP server using the `FastMCP` framework, enabling Cursor AI, Claude Code, and other MCP-compatible agents to invoke Git-Map operations as structured function calls within a coding session.

### 7.2 Server Architecture

The MCP server (`apps/mcp/gitmap-mcp/main.py`) uses `FastMCP` with an `stdio` transport, suitable for subprocess-based agent integrations:

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("gitmap")

# Tools registered from modular script files:
mcp.tool(gitmap_commit)
mcp.tool(gitmap_branch_create)
mcp.tool(gitmap_merge)
mcp.tool(gitmap_diff)
mcp.tool(gitmap_push)
mcp.tool(gitmap_pull)
mcp.tool(gitmap_stash_push)
mcp.tool(context_get_timeline)
# ... 20+ additional tools
```

### 7.3 Tool Categories

Tools are organized into domain modules under `scripts/tools/`:

| Module | Tools Exposed |
|---|---|
| `commit_tools.py` | `gitmap_commit`, `gitmap_log`, `gitmap_diff`, `gitmap_merge` |
| `branch_tools.py` | `gitmap_branch_create`, `gitmap_branch_delete`, `gitmap_branch_list`, `gitmap_checkout` |
| `remote_tools.py` | `gitmap_push`, `gitmap_pull` |
| `stash_tools.py` | `gitmap_stash_push`, `gitmap_stash_pop`, `gitmap_stash_list`, `gitmap_stash_drop` |
| `context_tools.py` | `context_get_timeline`, `context_search_history`, `context_record_lesson`, `context_explain_changes` |
| `portal_tools.py` | `gitmap_list_maps`, `gitmap_list_groups`, `gitmap_notify` |
| `layer_tools.py` | `gitmap_layer_settings_merge` |
| `repository_tools.py` | `gitmap_init`, `gitmap_status`, `gitmap_revert`, `gitmap_cherry_pick` |

### 7.4 Agent Workflow Integration

The MCP server enables AI agents to participate in GIS versioning workflows without requiring Portal credentials in the agent's context. A typical agent workflow:

1. Agent calls `gitmap_pull(repo_path, branch="main")` to fetch the current map state from Portal into the local commit store.
2. Agent analyzes the diff via `gitmap_diff(repo_path, branch_a="main", branch_b="feature/new-layer")`.
3. Agent proposes a merge via `gitmap_merge(repo_path, source_branch="feature/new-layer")`, receives a `MergeResult` JSON payload including any conflicts.
4. Agent records its reasoning via `context_record_lesson(repo_path, content="Merged symbology update; kept main branch renderer due to contrast ratio requirements")`.
5. Agent calls `gitmap_push(repo_path, branch="main")` to publish the merged map back to Portal.

This workflow demonstrates the MCP server's role as a semantic bridge between LLM-native reasoning and domain-specific GIS operations.

### 7.5 Configuration

The MCP server is configured for Cursor via `CURSOR_MCP_CONFIG.md`, with JSON configuration specifying the server binary path, working directory, and environment variable pass-through for Portal credentials (`ARCGIS_URL`, `ARCGIS_USERNAME`, `ARCGIS_PASSWORD`).

---

## 8. Conflict Resolution

### 8.1 Conflict Representation

A `MergeConflict` object captures the full context of an unresolvable difference:

```python
@dataclass
class MergeConflict:
    layer_id: str
    layer_title: str
    ours: dict[str, Any]     # Our version of the layer
    theirs: dict[str, Any]   # Their version
    base: dict[str, Any] | None   # Common ancestor version (may be None)
```

When `base` is available (three-way merge), the conflict can be displayed as a two-sided diff against a known prior state. When `base` is absent (two-way merge), only the `ours`/`theirs` comparison is available.

### 8.2 Three-Way Merge Strategy

The three-way merge algorithm at the layer level handles four distinct cases:

1. **No conflict — identical**: Both branches have the same layer content. Auto-resolved, ours kept.

2. **No conflict — only ours changed**: `ours != base` and `theirs == base`. Auto-resolved, ours kept.

3. **No conflict — only theirs changed**: `theirs != base` and `ours == base`. Auto-resolved, theirs applied.

4. **Conflict — both changed**: `ours != base` and `theirs != base`. `MergeConflict` raised, `ours` retained as placeholder pending resolution.

The delete/modify conflict case — where one branch deletes a layer that the other branch modifies — is explicitly detected: if a layer ID appears in `base` and `theirs` (with modification) but not in `ours` (deleted), a conflict is raised with `ours={}` signaling the deletion intent.

### 8.3 Conflict Resolution API

Conflicts are resolved programmatically via `resolve_conflict(conflict, resolution)`:

```python
def resolve_conflict(conflict: MergeConflict, resolution: str) -> dict[str, Any]:
    if resolution == "ours":    return conflict.ours
    elif resolution == "theirs": return conflict.theirs
    elif resolution == "base":   return conflict.base   # Three-way only
```

`apply_resolution(merge_result, layer_id, resolved_layer)` patches the `MergeResult`'s merged data in-place. An empty `resolved_layer` dict signals deletion — the layer is removed from `operationalLayers` or `tables` respectively.

### 8.4 Property-Level Conflict Surfacing

While the merge algorithm operates at layer granularity (treating each layer as an atomic unit), the diff engine operates at property granularity. When a conflict is presented to the user or agent, the `DeepDiff` output on `conflict.ours` vs `conflict.theirs` can surface which specific properties differ:

```
Layer: Parcel Boundaries (id: layer_parcels_01)
  CONFLICT: Both branches modified this layer.
  ours:   drawingInfo.renderer.type = "classBreaks"
  theirs: drawingInfo.renderer.type = "simple"
  base:   drawingInfo.renderer.type = "simple"
```

This property-level granularity in the conflict display reduces resolution time by directing the resolver's attention to the specific field in dispute, rather than requiring comparison of entire layer JSON blobs.

---

## 9. Performance

### 9.1 SQLite Optimization

The `ContextStore` class applies several SQLite performance optimizations:

**WAL Mode**: Write-Ahead Logging is enabled on every connection:
```python
self._conn.execute("PRAGMA journal_mode=WAL")
```
WAL mode allows concurrent reads during writes and dramatically improves write throughput for the event recording pattern (one write per operation, many reads during history queries).

**Indexed Queries**: The schema creates targeted indexes at initialization:
```sql
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_ref ON events(ref);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_annotations_event ON annotations(event_id);
```
These indexes cover the four primary query patterns: type-filtered history, ref-filtered lookup (commit ID or branch name), chronological timeline retrieval, and annotation join.

**Lazy Connection**: The `_connection` property uses lazy initialization — the SQLite connection is not opened until the first database operation. This avoids the file descriptor overhead for operations that don't touch the context store (e.g., pure local branch operations).

### 9.2 Context Store Lifecycle Management

Early versions of the codebase opened `ContextStore` instances without guaranteed closure, leaking SQLite file descriptors. The current implementation enforces proper lifecycle management through three mechanisms:

1. **Context manager protocol**: `ContextStore` implements `__enter__` / `__exit__`, enabling `with self.get_context_store() as store:` usage throughout `repository.py`.

2. **`__del__` finalizer**: `def __del__(self) -> None: self.close()` provides a last-resort cleanup in case the context manager path is not used.

3. **Non-blocking event recording**: All context store writes in `create_commit`, `revert`, `cherry_pick`, and stash operations are wrapped in `try/except Exception: pass` blocks. Context recording failure does not propagate to the primary operation — a commit succeeds even if the event graph write fails (e.g., disk full, database locked).

### 9.3 Commit Hash Performance

Commit ID generation serializes the full map JSON for hashing. For large web maps (500+ KB JSON), this adds measurable latency. The current implementation uses `json.dumps({..}, sort_keys=True)` to ensure deterministic serialization before SHA-256 hashing. Future optimizations could cache the JSON serialization from the index read, avoiding a second serialization pass.

### 9.4 Test Suite Performance

674 tests complete in under 10 seconds on a modern Mac (M-series). Tests use `tmp_path` (pytest's temporary directory fixture) exclusively — no shared mutable state between tests. The MCP stash tests (`test_stash_mcp.py`) inject the MCP scripts directory into `sys.path` at fixture setup time to import `tools.stash_tools` directly, enabling end-to-end testing of the MCP tool layer without running the MCP server process.

---

## 10. Future Work

### 10.1 PyPI Distribution (gitmap-core)

The roadmap's highest-priority distribution goal is publishing `gitmap-core` to PyPI under the package name `gitmap-core`, enabling `pip install gitmap-core` without cloning the repository. The `pyproject.toml` is already structured for this — `packages/gitmap_core` is the installable package, and `[tool.pytest.ini_options]` with `pythonpath = ["packages"]` supports editable development installs. The remaining work is: finalizing package metadata (classifiers, long description, trove identifiers), adding a GitHub Actions CI/CD pipeline for automated testing and release publishing, and resolving any namespace conflicts.

### 10.2 Real-Time Collaboration

The current model is single-user, local-first. Future work could introduce a shared remote context: a Portal-hosted webhook receiver that intercepts web map save events (via the Portal webhook API, available since Enterprise 10.9) and automatically creates commits in a shared Git-Map repository. This would enable passive capture of all team members' edits without requiring explicit `gitmap commit` invocations — closer to an autosave-with-version-history model.

### 10.3 Webhook Triggers and CI/CD Integration

The `Remote.production_branch` field already supports a notification hook on push to designated production branches. A natural extension is a full webhook pipeline: on `gitmap push` to `production`, trigger a Portal webhook that notifies a Teams/Slack channel, runs an automated diff report, or initiates a downstream GIS service cache rebuild. Integration with GitHub Actions (or similar CI) would enable automated map quality checks — e.g., validating that all layer service URLs are reachable, all popup templates reference valid field names — before a push to the production branch is permitted.

### 10.4 ArcGIS Pro Integration

A Python Toolbox (`.pyt`) wrapper around `gitmap_core` operations would expose Git-Map functionality within ArcGIS Pro's Geoprocessing pane. This lowers the entry barrier for GIS professionals not comfortable with CLI tools. The `Repository` class's filesystem-based design maps naturally to ArcGIS Pro's project directory concept.

### 10.5 Property-Level Merge Granularity

The current merge algorithm treats each operational layer as an atomic unit: if two branches modify the same layer, a conflict is raised regardless of which properties were changed. A future refinement could implement property-level auto-merge — if branch A changes `minScale` and branch B changes `opacity` on the same layer, these are non-conflicting property changes that could be merged automatically. This requires extending `MergeConflict` to carry property-level diff context and implementing a recursive merge at the property level.

---

## References

1. Esri. (2024). *Web Map Specification*. ArcGIS Developers Documentation. https://developers.arcgis.com/web-map-specification/

2. Esri. (2024). *ArcGIS API for Python — Content Management*. ArcGIS Developers Documentation. https://developers.arcgis.com/python/

3. Esri. (2023). *ArcGIS Enterprise: Versioned Geodatabases*. ArcGIS Enterprise Documentation. https://enterprise.arcgis.com/en/geodatabase/latest/manage-geodatabases/types-of-geodatabase-versioning.htm

4. Chacon, S., & Straub, B. (2014). *Pro Git* (2nd ed.). Apress. https://git-scm.com/book

5. Hunt, A., & Thomas, D. (2000). *The Pragmatic Programmer*. Addison-Wesley.

6. Model Context Protocol Specification. (2024). Anthropic. https://modelcontextprotocol.io/

7. Quinlan, E. (2019). *DeepDiff: A Python library for deep comparison of dictionaries, strings, iterables and other objects.* https://github.com/seperman/deepdiff

8. SQLite Consortium. (2024). *WAL Mode*. SQLite Documentation. https://www.sqlite.org/wal.html

9. RFC 6902. (2013). *JavaScript Object Notation (JSON) Patch*. Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc6902

10. Esri. (2022). *ArcGIS Enterprise Webhooks*. ArcGIS Enterprise Documentation. https://enterprise.arcgis.com/en/server/latest/administer/windows/using-webhooks.htm

---

*Manuscript prepared March 2026. All code examples reference the Git-Map repository at commit depth consistent with v0.1.0 development branch.*
