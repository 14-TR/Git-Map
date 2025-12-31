# GitMap Release Notes

## Overview

**Purpose**: Centralize GitMap repository release history with concise notes per version.

**Scope**: Tracks repository-level SemVer releases and notable changes impacting developers and operations.

## Current Versions

| Component         | Version | Source                                   |
| ---               | ---     | ---                                      |
| GitMap (repo)  | 0.2.0   | `documentation/project_specs/20-operations/release_notes.md` |
| gitmap-cli     | 0.2.0   | `apps/cli/gitmap/pyproject.toml`         |
| gitmap_core    | 0.1.0   | `packages/gitmap_core/pyproject.toml`    |

## Releases

### [release/0.2.0]

**Type**: Minor

- Enhanced `lsm` command with improved repository discovery and cloning logic
- Optimized directory searching to prevent performance issues
- Improved handling of existing directories during map cloning operations
- Added one-to-many merge capabilities for layer settings transfer

### [release/0.1.0]

**Type**: Minor

- Added `lsm` command for transferring popup and form settings between maps
- Supports item IDs, branches, commits, and file paths as source/target
- Automatically clones maps from Portal when item ID has no existing repository
- Recursively handles nested layers within GroupLayers
- Transfers settings for both operational layers and tables

### [release/0.0.0]

**Type**: Initial

- Initial release of GitMap repository.

## References

- Monorepo Operations: `documentation/project_specs/20-operations/monorepo_ops_spec.md`
- Architecture: `documentation/project_specs/10-architecture/architecture_spec.md`
