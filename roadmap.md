# Git-Map Roadmap

**Vision:** Open-source version control for ArcGIS web maps. The git for GIS.

**Goal:** Community adoption — get real users.

## Priority Queue (architect picks top incomplete item)

1. README overhaul — installation guide, quickstart tutorial, GIF/video demos showing core workflows
2. PyPI publish — `pip install gitmap`, proper package metadata, badges
3. CLI polish — better error messages, help text, colored output
4. CI/CD pipeline — GitHub Actions for tests on every PR
5. Documentation site — mkdocs with tutorials, API reference, examples
6. Landing page on ingramgeoai.com with value prop + install instructions
7. Demo video for portfolio (60-90 sec showing commit/branch/revert workflow)
8. Branch diff visualization — visual comparison of map states
9. ArcGIS Pro integration — Python toolbox wrapper
10. Blog post / r/gis launch strategy

## Constraints
- Python package, keep dependencies minimal
- All work on `jig/*` branches, PRs to main
- Tests must pass before PR (currently 450+)
- No breaking changes to existing CLI interface
