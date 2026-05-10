# Git-Map Roadmap

**Vision:** Open-source version control for ArcGIS web maps. The git for GIS.

**Goal:** Community adoption — get real users.

## Shipped Foundation

- README overhaul with install, source install, quickstart, examples, and demo workflow.
- PyPI packaging and release guardrails for `gitmap`.
- CI smoke/package checks for built distributions.
- CLI error-message polish and ruff cleanup.
- Documentation pages for installation, quickstart, commands, and diff review.
- Landing page with value proposition and install instructions.
- Branch/JSON diff foundations for reviewable map-state changes.

## Priority Queue (architect picks top incomplete item)

1. Demo video for portfolio — 60-90 seconds showing clone, commit, branch, diff, merge, and revert workflow.
2. Branch diff visualization — visual comparison of map states beyond current structured JSON diff foundations.
3. ArcGIS Pro integration — Python toolbox wrapper for desktop GIS users.
4. Blog post / r/gis launch strategy — adoption push after demo/video assets are ready.
5. Real-user validation — run a low-risk test with a GIS user and record onboarding friction.

## Constraints
- Python package, keep dependencies minimal
- All work on `jig/*` branches, PRs to main
- Tests must pass before PR
- No breaking changes to existing CLI interface
