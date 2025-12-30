# Architecture Specification

## Overview

**Purpose**: Define GitMap's monorepo architecture, boundaries, and release/versioning rules.

**Scope**: Repository layout, environment strategy, branching model, versioning, and releases.

**Version**: 1.0

## Monorepo Layout

- **`packages/`**: First-party libraries (e.g., `[package_name]`).
- **`apps/`**: Runnable applications and orchestrators.
- **`documentation/`**: Specs, guides, and READMEs.
- **`configs/`**: Configuration files and environment templates.

Requirements:
- Enforce clear ownership per directory.
- Libraries in `packages/` must be importable and tested independently.
- Apps depend on published APIs from `packages/` only (no deep imports).

## Environment Strategy

**Virtual Environments**
- All deployed venvs live at `[venv_root_path]` (configure as needed).

**Naming Conventions**
- Developer clone: `gitmap_[username]`.

## Repositories

**Locations**
- All cloned repositories are saved under `[github_root_path]` (configure as needed), typically at `[github_root_path]/GitMap`.

**Roles**
- `GitMap_[developer]`: Development repo (e.g., `GitMap_[username]`)
- `GitMap_main`: Main repo (source of truth for release branches)
- `GitMap_production`: Production repo (pinned to current release branch) - optional

**Clone Naming**
- `gitmap_[role/username]`
- Example: `GitMap_main`, `GitMap_production`, `GitMap_[username]`

## Branching Model

**Rules**
- Create child branches from `main`.
- Grandchild branches may be created from a child, but they must merge back into their parent child branch (never directly into `main`).

**Branch Type Identifiers**
- `feature/`: New functionality or enhancements
- `bugfix/` or `fix/`: Non-urgent fixes
- `hotfix/`: Urgent fixes to production
- `release/`: Preparing a release (often temporary)
- `chore/`: Maintenance, cleanup, dependencies
- `refactor/`: Code changes that don’t alter features but restructure code
- `test/` or `experiment/`: Spikes, prototypes, experimental work
- `docs/`: Documentation updates

**Branch Naming**
- Child: `[developer]/[identifier]/[description]`.
- Grandchild: `[developer]/[identifier]/[description] | [developer]/[identifier]/[description]`.

## Versioning & Releases

**Semantic Versioning (SemVer)**
- **MAJOR**: Breaking change requiring callers/tools to change.
- **MINOR**: Backward compatible new functionality.
- **PATCH**: Bug fixes or internal changes without public behavior changes.

**Release Branches**
- Use `release/x.y.z` for creating rollback branches.
- Create `release/#.#.#` branches from `main` for rollback purposes.
- Release branches are read-only and used for rollback only.

## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [Repository Specification](../10-architecture/repo_spec.md)
- [Application Specification](../30-apps/apps_folder_spec.md)

