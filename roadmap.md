# GitMap Roadmap

GitMap is open-source version control for ArcGIS web maps: **the git for GIS**.

The next product goal is community adoption: help real GIS users safely try
GitMap, understand the workflow, trust what it changes, and find clear ways to
contribute.

## Current project foundation

Shipped or substantially in place:

- **Shipped:** README with install, source install, quickstart, examples, and
  demo workflow.
- **Shipped:** PyPI packaging and release guardrails for `gitmap`.
- **Shipped:** CI smoke/package checks for built distributions.
- **Shipped:** CLI error-message polish and ruff cleanup.
- **Shipped:** Documentation pages for installation, quickstart, commands,
  Portal usage, and diff review.
- **Shipped:** Landing page content with value proposition and install
  instructions.
- **Shipped:** Branch, commit, merge, revert, and JSON diff foundations for
  reviewable map-state changes, including terminal, JSON, and HTML report
  output.
- **Prototype:** ArcGIS Pro Python toolbox exists and is documented, but still
  needs an explicit validation/polish pass before it is treated as a primary
  adoption path.
- **Prototype:** OpenClaw integration exists, but needs path/config and
  parameter cleanup before being promoted as a reliable agent integration.
- **Prototype:** MCP/agent workflow surfaces exist, but should stay secondary
  until the core GIS-user onboarding path is validated.

## Roadmap principles

1. **Adoption before polish loops.** Prioritize the first successful user
   workflow before major new features.
2. **Safe by default.** Make it obvious when a command only reads local state
   versus when it changes Portal content.
3. **Show the workflow.** A short demo is more valuable than another feature if
   it helps GIS users understand the value.
4. **Validate with real GIS users.** Let onboarding friction guide feature
   priorities.
5. **Keep contributor work small.** Turn roadmap tracks into clear, labeled,
   PR-sized issues.

## Near-term tracks

### Track 1: First-user onboarding

**Goal:** A GIS user can try GitMap on a non-production web map in under 10
minutes.

**Status:** In progress / safety guidance substantially shipped; needs clean
first-user validation.

**Why it matters:** The docs now cover the main first-run safety issues, but
the workflow still needs validation from a clean environment and real GIS
users.

**Shipped / substantially in place:**

- Non-production test-map guidance in README, installation docs, quickstart,
  and Portal docs.
- Web map item-ID discovery guidance in README and quickstart.
- Local/read/write command safety language, including clear `gitmap push`
  warnings.
- First-run troubleshooting for credentials, install/path issues, item IDs,
  wrong directories, and permissions.

**Remaining work:**

- Test the quickstart on a clean machine or clean virtual environment.
- Ask 1-3 GIS users to complete the quickstart without coaching.
- Convert observed friction into follow-up issues.

**Success signal:** A new user can complete clone, branch, pull/edit, diff,
commit, merge, and push on a test map without private help.

### Track 2: Demo and trust assets

**Goal:** Show the core value in 60-90 seconds.

**Status:** In progress; demo script and placeholders are in place, recording still needed.

**Shipped / substantially in place:**

- Demo script for clone, branch, pull/edit, diff, commit, merge, push, and
  trust captions.
- README and docs placeholders pointing visitors toward the script.

**Remaining work:**

- Record a terminal GIF or video using a safe sample workflow.
- Embed the demo in the README, docs home page, and landing page.
- Add final captions or thumbnails for GIS analysts, GIS managers, and
  developers.

**Success signal:** A visitor can understand GitMap's purpose without reading
the full docs.

### Track 3: Real-user validation loop

**Goal:** Get feedback from 1-3 GIS users before investing in larger feature
work.

**Status:** Next after onboarding/demo assets.

**Planned work:**

- Prepare a low-risk test protocol using a non-critical ArcGIS web map.
- Ask users to complete the quickstart while noting friction.
- Collect feedback on install, credentials, item IDs, diff readability, and
  push safety.
- Convert friction into GitHub issues and reprioritize this roadmap.

**Success signal:** Roadmap priorities are backed by observed GIS-user friction
instead of assumptions.

### Track 4: Diff and review UX

**Goal:** Make map changes reviewable by GIS users, not only developers.

**Status:** Later.

**Planned work:**

- Improve branch comparison beyond the current structured JSON/HTML diff
  foundations.
- Produce a shareable HTML or visual review artifact for stakeholders.
- Highlight layer additions/removals, visibility changes, renderer changes,
  popup changes, and basemap changes.
- Add docs showing how a team reviews a branch before merge/push.

**Success signal:** A GIS manager or analyst can answer "what changed?" from a
GitMap diff without inspecting raw JSON.

### Track 5: ArcGIS Pro integration status and polish

**Goal:** Make the ArcGIS Pro story honest and testable.

**Status:** Prototype / needs validation.

**Context:** The repo already includes ArcGIS Pro toolbox documentation, so this
should not be treated as purely future work. The next step is to verify what
works in a real ArcGIS Pro Python environment and document the status clearly.

**Planned work:**

- Confirm whether the toolbox is shipped, prototype, or experimental.
- Test install in the ArcGIS Pro Python environment.
- Align README, docs, technical paper, and roadmap language with the verified
  status.
- Preserve clear notes about no ArcGIS extension license requirement and when
  `arcpy` is needed.
- Document limitations clearly if the toolbox remains prototype-stage.

**Success signal:** Users know whether the ArcGIS Pro toolbox is ready to try
and what limitations to expect.

### Track 6: OpenClaw and agent integration repair

**Goal:** Make GitMap usable as a reliable agent/OpenClaw tool surface.

**Status:** Prototype / repair needed.

**Context:** `integrations/openclaw/` includes a Python server, TypeScript
plugin, tool wrappers, and tests. It is real, but it still has prototype
assumptions that need cleanup before launch.

**Known repair targets:**

- Replace hardcoded `~/Desktop/Git-Map` assumptions with configurable or
  project-relative paths.
- Normalize parameter names between TypeScript and Python (`repo_path` vs
  `cwd`).
- Make the server URL configurable from plugin config.
- Add or verify a health smoke test.
- Ensure the OpenClaw test suite completes without hanging.
- Demonstrate one successful agent-driven `gitmap_status` against a local test
  repo.

**Success signal:** OpenClaw can call GitMap tools against a local repo with
predictable parameters and no path assumptions.

### Track 7: Contributor activation

**Goal:** Make it easy for external contributors to help.

**Status:** Later.

**Planned work:**

- Create 5-10 good-first-issue candidates across docs, tests, diff UX,
  OpenClaw, and ArcGIS Pro polish.
- Add labels that match roadmap tracks.
- Expand contributing docs with targeted test commands for each project area.
- Add a "first PR in 30 minutes" path for docs/test-only contributors.

**Success signal:** A new contributor can pick an issue, run the relevant
checks, and open a small PR without project-specific coaching.

## Recommended execution order

1. First-user onboarding pass.
2. Demo script and video/GIF asset.
3. Real-user validation with 1-3 GIS users.
4. Roadmap reprioritization from feedback.
5. Diff/review UX improvements.
6. ArcGIS Pro validation/polish.
7. OpenClaw/agent integration repair.
8. Contributor activation and issue labeling.

## Next three PRs

### PR 1: First-user quickstart safety pass

**Files:**

- `README.md`
- `docs/getting-started/quickstart.md`
- `docs/guides/portals.md`

**Scope:** Add safe test-map guidance, item-ID discovery, Portal write warnings,
and first-run troubleshooting.

### PR 2: Demo script and asset placeholder

**Files:**

- `marketing/demo-script.md`
- `README.md`
- `docs/index.md`

**Scope:** Write the 60-90 second demo script and add placeholders for the
recording.

### PR 3: Real-user validation packet

**Files:**

- `docs/validation/first-user-test.md`
- `docs/validation/feedback-questionnaire.md`

**Scope:** Add the non-production test protocol and a short feedback
questionnaire.

### PR 4: OpenClaw prototype repair plan

**Files:**

- `integrations/openclaw/README.md`
- `integrations/openclaw/tools.py`
- `integrations/openclaw/server.py`
- `integrations/openclaw/index.ts`
- `integrations/openclaw/tests/test_tools.py`

**Scope:** Normalize path and parameter assumptions, then add a reliable
health/status smoke test.

## Later opportunities

- Hosted demo map or synthetic sample map fixture.
- Rich web-based diff viewer.
- Case-study blog post after the first real user succeeds.
- GIS team workflow guide for staging/production maps.
- Release notes cadence and GitHub Discussions/community support loop.

## Constraints

- Python package, keep dependencies minimal.
- All work on `jig/*` branches, PRs to main.
- Tests must pass before PR.
- No breaking changes to existing CLI interface.
- Adoption work should not overstate prototype integrations; mark ArcGIS Pro
  and OpenClaw status honestly until they are validated end-to-end.
