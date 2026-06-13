# GitMap: Version Control for ArcGIS Web Maps

- **Author:** TR Ingram
- **Date:** May 13, 2026
- **Version:** 3.1
- **Repository:** `14-TR/Git-Map`
- **Status:** Public alpha, v0.7.0

---

## Abstract

ArcGIS Online and ArcGIS Enterprise web maps are mutable JSON artifacts that encode operational layers, tables, popups, renderers, basemaps, extents, and map-level configuration. In many professional GIS teams, these artifacts function as production software assets, yet they are commonly governed through manual naming conventions, cloned Portal items, screenshots, and informal change logs. GitMap addresses this governance gap by adapting distributed version control concepts to ArcGIS web map state. The system stores immutable full-map JSON snapshots in a local `.gitmap` repository, provides branch, commit, diff, merge, revert, cherry-pick, stash, tag, push, and pull workflows, and exposes map-aware review artifacts through terminal, JSON, visual, and HTML diff outputs.

This paper describes the May 2026 implementation of GitMap v0.7.0. The current public system is a Python monorepo composed of `gitmap-core`, `gitmap-cli`, integration prototypes for ArcGIS Pro and OpenClaw, and MkDocs documentation. Its central technical claim is pragmatic rather than theoretical: treating ArcGIS web map JSON as a first-class versioned artifact enables safer review and rollback workflows for map configuration changes that are not covered by geodatabase versioning. Current validation consists of 825 collected core tests, 69 collected integration tests for ArcGIS Pro/OpenClaw surfaces, CLI/package smoke coverage, documentation builds, and repository-level adoption roadmaps. The primary remaining threats to validity are limited real-user validation, dependence on ArcGIS Portal API behavior, prototype-stage integration surfaces, and the absence of a production multi-user remote service.

---

## 1. Problem Statement

ArcGIS web maps are not static documents. A single web map item can encode multiple operational layers, feature service URLs, renderer definitions, layer visibility, popup templates, form configuration, table references, basemap metadata, and application-facing defaults. These fields change during ordinary GIS operations: adding hydrants, replacing a parcel layer, changing a flood-risk symbology rule, disabling a layer during an incident, or adjusting popups for public consumption.

The platform-level governance problem is that a web map item usually has one current JSON payload. Portal item metadata can show ownership, sharing, and modified dates, but it does not provide Git-like history over the full web map definition. GIS teams therefore face several recurrent risks:

- A bad configuration change can overwrite the production state without a clean rollback path.
- Parallel experiments on cartography, popups, or layer ordering require cloned items and manual reconciliation.
- Reviewers often cannot answer "what changed?" without opening Portal and inspecting layer configuration by hand.
- Promotion from test maps to production maps depends on institutional memory rather than deterministic diffs.
- Automation and AI-assisted workflows lack a durable local record of why map states changed.

GitMap targets this gap. It does not replace feature editing, enterprise geodatabase versioning, or service-level deployment tooling. It focuses on the web map configuration artifact: the JSON that controls how spatial data is assembled and presented.

---

## 2. Contributions

This implementation contributes the following engineering and research artifacts:

1. A local repository format, `.gitmap/`, for storing ArcGIS web map snapshots, branch references, tags, stashes, remote configuration, and optional context events.
2. A Python core library, `packages/gitmap_core`, implementing repository state, model serialization, diffing, merging, graph rendering, remote Portal synchronization, and context storage.
3. A CLI, `gitmap`, with Git-style commands for map repositories, including `clone`, `branch`, `checkout`, `pull`, `diff`, `commit`, `merge`, `push`, `show`, `revert`, `stash`, `tag`, `doctor`, `daemon`, and shell completions.
4. An ArcGIS-aware diff engine that separates operational layers, tables, and map-level properties, then summarizes nested JSON changes for human review.
5. A layer/table-atomic three-way merge method that identifies conflicts when the same ArcGIS layer or table is changed independently on both sides of a branch merge.
6. A remote synchronization layer for ArcGIS Online and Portal that can update the original cloned web map item on `main` and represent branches as Portal items when needed.
7. Integration prototypes for ArcGIS Pro and OpenClaw, documented as prototype-stage until each path is validated end-to-end in its target environment.
8. A public documentation and adoption track that prioritizes safe first-user onboarding, a 60-90 second demo, and real GIS-user validation before larger feature expansion.

---

## 3. System Architecture

### 3.1 Monorepo Layout

The current implementation is organized as a Python monorepo:

```text
git-map/
  pyproject.toml                    # meta-package, v0.7.0
  README.md                         # public user entry point
  roadmap.md                        # May 2026 adoption roadmap
  docs/                             # MkDocs documentation
  docs/technical-paper.md           # this paper
  packages/gitmap_core/             # core library
  apps/cli/gitmap/                  # Click/Rich CLI package
  apps/mcp/gitmap-mcp/              # MCP package surface, not primary adoption path
  integrations/arcgis_pro/          # ArcGIS Pro Python toolbox prototype
  integrations/openclaw/            # OpenClaw plugin/server prototype
  marketing/                        # demo and launch materials
```

The public package metadata declares v0.7.0 and Python `>=3.11,<3.15`, matching the README support matrix for Python 3.11, 3.12, 3.13, and 3.14. The top-level `gitmap` package is a convenience meta-package depending on `gitmap-core>=0.7.0` and `gitmap-cli>=0.7.0`.

### 3.2 Repository Format

A GitMap repository lives under a `.gitmap/` directory inside a map project folder:

```text
.gitmap/
  config.json
  HEAD
  index.json
  refs/
    heads/
    remotes/
    tags/
  objects/
    commits/
  stash/
  context.db
```

`HEAD` is either attached to a branch reference or detached at a commit ID. Branches and tags are filesystem references. Commit objects are JSON files containing full map snapshots. `index.json` is the current staged map payload, usually loaded from Portal by `gitmap pull` or initialized during clone. `context.db` is an optional SQLite event graph used for operation history and future agent-facing context.

This format favors transparency and recoverability over storage efficiency. A GIS analyst can inspect commits as JSON files, copy a repository directory, and reason about state without running a server. The tradeoff is that every commit stores a full web map snapshot rather than a delta.

### 3.3 Core Components

`packages/gitmap_core/repository.py` is the state manager for repository initialization, refs, HEAD, index operations, commits, history traversal, branching, tags, stashes, reverts, cherry-picks, common-ancestor search, and context graph regeneration.

`packages/gitmap_core/diff.py` provides map-aware diffing. It indexes operational layers and tables by `id`, classifies changes as added, removed, or modified, and uses DeepDiff for nested layer/property detail. It also renders summaries, visual table rows, statistics, and self-contained HTML reports.

`packages/gitmap_core/merge.py` provides a three-way layer/table merge. It treats each layer or table as an atomic semantic unit. If both sides modify the same item relative to the base, the merge records a conflict and preserves the current side until the user resolves it.

`packages/gitmap_core/remote.py` connects local state to ArcGIS Online or Portal. For cloned repositories, pushing `main` can update the original web map item. For branches or non-clone workflows, GitMap can create or update Portal items named and tagged by project, branch, and commit.

`packages/gitmap_core/context.py` stores operation events, annotations, and typed edges in SQLite. It is deliberately non-blocking: context recording failures must not prevent commits, merges, or pushes.

### 3.4 CLI and Integration Surfaces

The `gitmap` CLI is the primary supported user interface. The current command surface is grouped by workflow: repository setup, snapshot/history, branching, remote sync, Portal utilities, and tooling. `gitmap --version` reports `0.7.0` in the active development environment.

The ArcGIS Pro toolbox in `integrations/arcgis_pro/GitMap.pyt` wraps nine operations for an ArcGIS Pro UI flow: initialize repository, commit map, status, create branch, checkout branch, log history, diff maps, push, and pull. Its README correctly presents this as a toolbox workflow and notes that `arcpy` imports occur inside tool execution so the toolbox can be tested outside ArcGIS Pro.

The OpenClaw integration in `integrations/openclaw/` exposes nine tool wrappers through a local Python server and TypeScript plugin, including the non-Portal `gitmap_health` readiness check. Recent docs and tests show repaired path/config normalization, including `GITMAP_ROOT`, `serverUrl`, and `repo_path` to `cwd` translation. The local health path has been smoke-tested from a clean checkout; Portal-mutating workflows remain prototype-stage until demonstrated against an approved test repository.

---

## 4. Methods and Implementation Details

### 4.1 Snapshot Commit Model

A GitMap commit stores a complete ArcGIS web map JSON payload plus metadata:

```text
Commit = {
  id: 12-character SHA-256 prefix,
  message,
  author,
  timestamp,
  parent,
  parent2,
  map_data
}
```

The commit ID is generated from a deterministic JSON serialization of commit-relevant fields and truncated to 12 hexadecimal characters. This mirrors short Git hashes in usability while keeping file names compact. Because full snapshots are stored, reconstructing any commit is O(1) with respect to history depth; the system reads the target commit file rather than replaying deltas.

The cost is linear storage growth. This is acceptable for many web map workflows because typical web map JSON is much smaller than source imagery or feature datasets. It becomes less attractive for maps with large embedded payloads or extremely frequent automated commits.

### 4.2 Diff Semantics

The diff method separates three domains:

- `operationalLayers`: layer-level changes.
- `tables`: table-level changes.
- all other map properties: map-level JSON changes.

Layers and tables are indexed by their ArcGIS `id` field. This allows GitMap to classify a layer as modified even when its position in the list changes. For modified objects, DeepDiff provides nested field paths, and GitMap formats those paths into reviewer-friendly summaries such as changed visibility, popup, renderer, or nested property fields.

This design intentionally avoids treating the full JSON as undifferentiated text. A generic textual diff can identify that JSON changed, but it does not know that a layer was added, a table was removed, or a renderer property changed inside a stable layer identity.

### 4.3 Merge Semantics

The merge engine applies a three-way algorithm over stable layer/table IDs:

```text
if ours == theirs:
    keep ours
elif base exists and ours == base:
    take theirs
elif base exists and theirs == base:
    keep ours
else:
    record conflict and keep ours temporarily
```

Items present only on one side are interpreted relative to the base. A layer added only in the source branch can be added to the merged result. A layer deleted by one side and modified by the other becomes a conflict. Tables follow the same logic.

The method is conservative. It avoids automatically merging two independent edits inside the same layer, even if the fields differ. This reduces the risk of producing invalid ArcGIS JSON from an over-clever nested merge. The price is more user-visible conflicts when two branches touch different properties of the same layer.

### 4.4 Remote Synchronization

GitMap's remote layer maps local branch state to ArcGIS Portal content:

- Clone/main workflow: when a repository has `remote.item_id` and the current branch is `main`, push can update the original web map item's data.
- Branch workflow: non-main branches can be represented as Portal items tagged with GitMap project, branch, and commit metadata.
- Pull workflow: Portal item data is loaded into `index.json`; users then inspect and commit the pulled state.

This separation makes Portal writes explicit. `gitmap pull` updates local staged state but does not automatically create a commit. That differs from `git pull` in a source-code repository, but it supports a GIS workflow where analysts inspect fetched Portal state before deciding what to snapshot.

### 4.5 Context and Rationale Capture

The context store records events such as commits, branches, merges, reverts, stashes, and tags. It supports annotations, lessons, event search, and relationship edges. The design goal is not just audit history but rationale recovery: why did a map change, what operation caused it, and what downstream operation depended on it?

This is especially relevant to AI-assisted GIS workflows. A future agent can inspect prior map operations and annotations rather than inferring intent from raw JSON diffs alone. The current implementation stores this data locally in SQLite and treats context capture as best-effort so it never blocks core repository operations.

---

## 5. Data Sources and Assumptions

GitMap's primary input is the ArcGIS web map JSON returned by ArcGIS Online or Portal for ArcGIS. The system assumes:

- The web map payload is JSON-serializable.
- `operationalLayers` and `tables` are list-like collections when present.
- Layer and table `id` fields are stable enough to serve as semantic identities across commits.
- Portal credentials, when needed, are provided through environment variables, `.env`, explicit command parameters, or the ArcGIS runtime environment.
- The current user has sufficient Portal permissions for any requested push/update operation.

The system does not version underlying feature data, rasters, hosted feature service records, or geodatabase branch versions. It versions the web map configuration layer that references those services.

Sensitive data may appear in web map JSON: internal service URLs, tokenized layer URLs, popups with proprietary text, or other organization-specific configuration. For that reason, `.gitmap/` repositories should be treated as potentially sensitive unless the map payload has been inspected and approved for public release.

---

## 6. Evaluation and Validation Status

### 6.1 Repository Evidence

The May 13, 2026 development checkout reports:

- Version: `gitmap, version 0.7.0`.
- Python support: `>=3.11,<3.15` in package metadata.
- Core tests collected: 798 under `packages/gitmap_core/tests`.
- Integration tests collected: 69 across `integrations/openclaw/tests/test_tools.py` (40) and `integrations/arcgis_pro/test_toolbox.py` (29).
- Public docs: README, MkDocs command pages, quickstart, Portal guide, roadmap, and marketing demo script.
- Recent git history: May 2026 work focused on first-user safety, demo placeholders, roadmap/adoption tracks, path normalization, and CLI/doc polish.

### 6.2 Validation Coverage

The test suite covers repository operations, model serialization, diffing, merge behavior, graph rendering, context store behavior, remote compatibility shims, communication/notification behavior, CLI registration/error messages, packaging metadata, doctor command behavior, show command behavior, stash/MCP-related helpers, ArcGIS Pro toolbox behavior, and OpenClaw wrapper normalization.

The CLI help surface is validated by command registration tests and direct smoke execution. Documentation is intended to be validated by `mkdocs build --strict` for docs-facing changes. Release guardrail scripts exist for package metadata and distribution checks.

### 6.3 Current Validation Gap

The highest-value missing validation is not another unit test. It is observed GIS-user workflow validation. The roadmap now correctly narrows the next proof to this question: can a real GIS analyst use GitMap on a disposable ArcGIS web map, understand the diff/review path, and trust what will happen before anything is pushed back to Portal?

A serious validation packet should include:

- a safe disposable web map item,
- clean-environment install steps,
- expected command outputs,
- a terminal GIF or short video,
- a first-user feedback form,
- issue creation from observed friction,
- explicit separation between local read-only commands and Portal write commands.

---

## 7. Limitations and Threats to Validity

### 7.1 Real-User Adoption Has Not Yet Been Proven

The implementation has extensive local tests, but tests do not prove that GIS users can successfully adopt the workflow. The roadmap explicitly marks first-user validation and a 60-90 second demo as next product proofs.

### 7.2 Portal API Behavior Is a Moving Target

GitMap depends on the ArcGIS Python API and Portal item behavior. Compatibility shims exist for folder and content operations, but Portal API changes, authentication differences, organizational policies, or item permission models can change runtime behavior outside unit-test assumptions.

### 7.3 Layer Identity Is Imperfect

Diff and merge quality depends on stable layer/table IDs. Layers without IDs are ignored by layer-level diffing, and certain ArcGIS-generated or sketch-like objects may not behave like stable application-layer entities.

### 7.4 Merge Is Conservative

Layer-atomic conflict detection avoids invalid nested merges, but it can over-report conflicts when two branches edit independent properties of the same layer. This is a deliberate safety choice, not a final optimal merge strategy.

### 7.5 Full Snapshots Increase Storage

Full snapshots simplify checkout and rollback, but they do not scale as efficiently as delta compression. Large embedded payloads or high-frequency automation could produce repository bloat.

### 7.6 Branch Name and Filesystem Safety Need Hardening

Branch and tag names map to filesystem paths. Validation should continue tightening around path traversal, non-printable characters, operating-system portability, and maximum lengths.

### 7.7 Prototype Integrations Should Stay Labeled as Prototypes

ArcGIS Pro and OpenClaw integrations are real code paths with tests, but they should not be marketed as primary supported adoption paths until validated end-to-end in the intended runtime environments.

### 7.8 Security Depends on Local Hygiene

Web map JSON may contain private service URLs or organizational configuration. `.env` files and `.gitmap/` content must stay out of public repositories unless inspected. Public PR text and docs should not include production map IDs, private hosts, credentials, or tailnet URLs.

---

## 8. Related Work and Positioning

### 8.1 Esri Geodatabase Versioning

Traditional and branch versioned geodatabases solve a different problem: multi-user editing and reconciliation of spatial data. GitMap operates one layer above that. It versions web map configuration: which services are referenced, how layers are drawn, what popups show, and how a map is assembled for users.

### 8.2 Generic Git for Exported JSON

A team can manually export web map JSON and put it in Git. That approach gives history but no Portal-aware clone/pull/push workflow, no layer/table-aware summaries, no ArcGIS-specific branch item strategy, and no GIS-first CLI affordances. GitMap automates the export/import loop and gives map-specific review outputs.

### 8.3 JSON Diff and Patch Libraries

General JSON diff tools operate on structural trees but lack domain semantics. GitMap builds on structural comparison but interprets ArcGIS layers and tables as reviewable entities. This is closer to source-control UX for maps than to raw JSON comparison.

### 8.4 DevOps for GIS

GitMap aligns with a broader movement toward GIS DevOps: reproducible deployments, reviewable configuration, promotion paths, automated checks, and rollback. Its distinctive scope is web map configuration rather than geoprocessing code, infrastructure-as-code, or feature data replication.

---

## 9. Future Work

The roadmap should prioritize adoption proof before feature expansion:

1. Build a first-user validation packet with a disposable sample map and expected outputs.
2. Record and embed a 60-90 second demo showing clone, branch, pull/edit, diff, commit, merge, and push safety.
3. Run 1-3 GIS users through the quickstart without coaching and convert friction into labeled issues.
4. Improve diff/review UX for non-developer GIS stakeholders, especially HTML reports and visual summaries of layer visibility, renderer, popup, table, and basemap changes.
5. Validate the ArcGIS Pro toolbox in a real ArcGIS Pro Python environment and update all docs based on evidence.
6. Validate the OpenClaw integration against a local test repository and remove any remaining hardcoded path assumptions.
7. Harden branch/tag validation, path safety, credential handling, and public-doc leakage scans.
8. Evaluate delta storage or JSON patch compression if real workflows show repository size growth.
9. Design a collaborative remote service only after the local single-user workflow has demonstrated adoption.

---

## 10. Reproducibility Notes

The following commands reproduce the evidence used for this paper from the local checkout:

```bash
cd git-map
.venv/bin/gitmap --version
.venv/bin/gitmap --help
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest integrations/openclaw/tests/test_tools.py integrations/arcgis_pro/test_toolbox.py --collect-only -q
.venv/bin/python -m mkdocs build --strict
```

For a full implementation gate, run the full core test suite and documentation build:

```bash
cd git-map
.venv/bin/python -m pytest packages/gitmap_core/tests
.venv/bin/python -m pytest integrations/openclaw/tests/test_tools.py integrations/arcgis_pro/test_toolbox.py
.venv/bin/python -m mkdocs build --strict
```

No external publishing is required for this paper. Portal write commands such as `gitmap push` should be tested only against non-production web map items unless TR explicitly approves a production workflow.

---

## 11. Revision Notes for v3.1

This update replaces stale March 2026 claims with evidence from the May 13, 2026 checkout. Major corrections include:

- Updated project status from v0.6.0+ to v0.7.0 public alpha.
- Updated Python support from 3.10+ to `>=3.11,<3.15`.
- Reframed MCP/OpenClaw and ArcGIS Pro work as integration/prototype surfaces rather than primary validated adoption paths.
- Updated validation evidence to 825 collected core tests and 69 collected integration tests.
- Added the May 2026 product focus: first-user onboarding, short demo asset, and real GIS-user validation.
- Reorganized limitations around adoption validity, Portal API dependence, layer identity, conservative merge semantics, storage growth, path safety, and privacy.

---

*This paper is a local technical documentation artifact for the public GitMap repository. It was not published externally by this cron run.*
