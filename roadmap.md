# Git-Map Roadmap

**Vision:** Open-source version control for ArcGIS web maps. The git for GIS.

**Goal:** Community adoption: real GIS users can safely try Git-Map, understand
what it changes, and decide whether it fits their workflow.

## Shipped Foundation

- **Shipped:** README overhaul with install, source install, quickstart,
  examples, and demo workflow.
- **Shipped:** PyPI packaging and release guardrails for `gitmap`.
- **Shipped:** CI smoke/package checks for built distributions.
- **Shipped:** CLI error-message polish and ruff cleanup.
- **Shipped:** Documentation pages for installation, quickstart, commands, and
  diff review.
- **Shipped:** Landing page with value proposition and install instructions.
- **Shipped:** Branch/JSON diff foundations for reviewable map-state changes,
  including terminal, JSON, and HTML report output.
- **Prototype:** ArcGIS Pro Python toolbox exists and is documented, but still
  needs an explicit validation/polish pass before it is treated as a primary
  adoption path.
- **Prototype:** OpenClaw integration exists, but needs path/config and
  parameter cleanup before being promoted as a reliable agent integration.

## Roadmap Tracks

### Track 1: First-User Onboarding

**Status:** Next

Make a GIS user successful on a safe, non-production web map in under 10
minutes.

- Add "find your ArcGIS web map item ID" guidance.
- Add a visible safe-map warning: start with a disposable or non-production map.
- Explain exactly what `gitmap push` modifies in ArcGIS Online or Portal.
- Add a first-run troubleshooting checklist for credentials, package install,
  and Portal/AGOL connection issues.
- Re-test the quickstart from a clean environment.

### Track 2: Demo and Trust Assets

**Status:** Next

Show the core value in 60-90 seconds before asking users to install anything.

- Write a demo script covering clone, branch, edit/pull, diff, commit, merge,
  push, and revert.
- Record a terminal GIF or short video using a non-production map.
- Link the asset from the README and documentation landing page.
- Keep the demo workflow aligned with commands that a new user can repeat.

### Track 3: Real-User Validation

**Status:** Next

Put Git-Map in front of 1-3 GIS users before larger feature investment.

- Create a low-risk test protocol using a non-critical web map.
- Ask users where onboarding, trust, or terminology breaks down.
- Convert observed friction into GitHub issues.
- Re-rank later roadmap tracks after feedback.

### Track 4: Diff and Review UX

**Status:** Later

Make map changes reviewable for GIS users, not only developers.

- Improve branch comparison beyond the current structured JSON/HTML diff
  foundations.
- Add sample before/after review artifacts.
- Document a team review workflow for high-impact map changes.
- Explore visual comparison output only after first-user validation confirms it
  is the highest-leverage adoption blocker.

### Track 5: ArcGIS Pro Status and Polish

**Status:** Prototype

Clarify whether the ArcGIS Pro toolbox is shipped, prototype, or future-facing,
then polish the matching path.

- Validate install from an ArcGIS Pro Python environment.
- Preserve the "no extension license required" trust note.
- Align README, docs, technical paper, and roadmap language.
- Document limitations clearly if the toolbox remains prototype-stage.

### Track 6: OpenClaw and Agent Integration Repair

**Status:** Prototype

Turn the existing OpenClaw integration from prototype code into a reliable local
agent tool.

- Remove hardcoded `~/Desktop/Git-Map` assumptions.
- Normalize `repo_path` and `cwd` parameter naming across TypeScript, Python,
  and docs.
- Add a health smoke path.
- Ensure OpenClaw integration tests complete without environment-dependent
  hangs.
- Demonstrate one successful agent-driven `gitmap_status` against a local repo.

### Track 7: Contributor Activation

**Status:** Later

Make it obvious how an outside contributor can help.

- Add 5-10 good-first-issue candidates tied to these roadmap tracks.
- Add targeted test commands by area: docs, CLI, core, ArcGIS Pro, OpenClaw.
- Add a "first PR in 30 minutes" path.
- Use labels for onboarding, docs, diff/review, ArcGIS Pro, OpenClaw, and
  contributor experience.

## Next Three PRs

1. **First-user quickstart safety pass**: update README and quickstart with
   item-ID discovery, safe-map guidance, `push` behavior, and first-run fixes.
2. **Demo script asset**: add a reusable 60-90 second demo script and wire a
   placeholder/link into README/docs.
3. **Real-user validation packet**: add the non-production test protocol and a
   short feedback questionnaire.

## Constraints

- Python package, keep dependencies minimal.
- All work on `jig/*` branches, PRs to main.
- Tests must pass before PR.
- No breaking changes to existing CLI interface.
- Adoption work should not overstate prototype integrations; mark ArcGIS Pro
  and OpenClaw status honestly until they are validated end-to-end.
