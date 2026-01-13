# GitMap Release Notes

## Overview

**Purpose**: Centralize GitMap repository release history with concise notes per version.

**Scope**: Tracks repository-level SemVer releases and notable changes impacting developers and operations.

## Current Versions

| Component         | Version | Source                                   |
| ---               | ---     | ---                                      |
| GitMap (repo)  | 1.5.0   | `documentation/project_specs/20-operations/release_notes.md` |
| gitmap-cli     | 0.5.0   | `apps/cli/gitmap/pyproject.toml`         |
| gitmap_core    | 0.4.0   | `packages/gitmap_core/pyproject.toml`    |
| gitmap-mcp     | 0.2.0   | `apps/mcp/gitmap-mcp/pyproject.toml`     |

## Releases

### [release/1.5.0] (Pending)

**Type**: Minor

- Added auto-commit functionality to `auto-pull` command
- Introduced `--auto-commit` flag to automatically commit changes after successful pulls
- Added `--commit-message` option with template variable support (`{repo}`, `{date}`)
- Enhanced progress display to show commit IDs when auto-commit is enabled
- Added `auto_pull` configuration section to `gitmap_config.json` with default settings
- Updated summary messages to provide guidance based on auto-commit status
- Maintains backward compatibility with auto-commit disabled by default
- Updated `gitmap-cli` documentation with auto-commit feature usage examples

### [release/1.4.2]

### [release/1.4.2]

**Type**: Patch

- Fixed CLI version synchronization between `pyproject.toml` and hardcoded version strings
- Updated `__version__` in `apps/cli/gitmap/__init__.py` from 0.3.0 to 0.4.0
- Updated version in `apps/cli/gitmap/main.py` docstring and `@click.version_option` decorator
- Updated version in `apps/cli/gitmap/docs/gitmap_spec.md` documentation
- Resolves issue where `gitmap --version` displayed 0.3.0 despite package being 0.4.0

### [release/1.4.1]

**Type**: Patch

- Fixed `auto_visualize` to trigger for all GitMap commands, not just `commit`
- Added automatic context graph regeneration after: `merge`, `branch`, `pull`, `push`, `lsm`, and `init` commands
- Changed context graph direction from TB (top-bottom) to BT (bottom-top)
- Newest events now appear at the top of the visualization for better visibility
- Resolves issue where recent commits and operations were not visible in graph preview
- All commands that record context events now respect the `auto_visualize` config setting

### [release/1.4.0]

**Type**: Minor

- Improved context graph visualization with branch-aware event tracking
- Events now track which branch they occurred on (commit, lsm, push, pull)
- Fixed Mermaid syntax for reliable rendering across all viewers
- Parallel branches displayed correctly with events grouped by branch
- Merge commits shown with distinct hexagon shape and orange color
- Both parent branches connect to merge points showing branch rejoin
- Deduplicated merge events when corresponding commit event exists
- Removed annotation nodes for cleaner graph visualization
- Temporal links flow from oldest to newest (chronological order)
- Records main branch event during `gitmap init`
- Added `auto_visualize` config option for automatic graph regeneration
- Added `regenerate_context_graph()` method to Repository class
- Push and pull events now always recorded (not just with rationale)
- Added `gitmap config --auto-visualize` CLI option

### [release/1.3.1]

**Type**: Patch

- Fixed `gitmap context export` command AttributeError when accessing repository configuration
- Corrected improper direct attribute access to `repo.config.name` in `context.py`
- Updated to use proper `repo.get_config()` method and `config.project_name` attribute
- Resolves "'Repository' object has no attribute 'config'" error during context graph export
- Ensures context export functionality works correctly for all output formats (Mermaid, ASCII, HTML)

### [release/1.3.0]

**Type**: Minor

- Added context graph storage system for episodic memory and event tracking
- Implemented SQLite-backed event store in `gitmap_core.context` module
- Added support for recording events with rationales, lessons, outcomes, and issues
- Introduced relationship tracking between events (caused_by, reverts, related_to, learned_from)
- Added MCP server context tools: `context_search_history`, `context_get_timeline`, `context_explain_changes`, `context_record_lesson`
- Enables IDE agents to maintain context awareness across operations and sessions
- Provides full-text search across events and annotations for historical context retrieval
- Supports chronological timeline views with optional annotation inclusion
- Allows recording and querying of lessons learned for knowledge retention
- Updated `gitmap_core` to version 0.3.0
- Updated `gitmap-mcp` to version 0.2.0

### [release/1.2.0]

**Type**: Minor

- Added `auto-pull` command for automatic repository synchronization
- Scans directories for GitMap repositories and pulls updates for all found repositories
- Supports pulling from main branch or specified branch via `--branch` option
- Provides detailed progress tracking with rich terminal output during bulk pull operations
- Includes error handling with `--skip-errors` flag to continue processing despite failures
- Generates comprehensive summary reports showing successful and failed pulls
- Can be scheduled via cron/systemd timer for automated synchronization workflows
- Fixed branch checking bug to properly handle string branch names from `list_branches()`
- Complements existing `setup-repos` command by keeping cloned repositories up to date

### [release/1.1.0]

**Type**: Minor

- Added `setup-repos` command for bulk repository setup automation
- Automates cloning of multiple web maps from Portal/AGOL into a repositories directory
- Supports filtering options: `--owner`, `--tag`, `--query`, and `--max-results`
- Creates organized directory structure with `.gitmap` folders for each cloned map
- Includes progress tracking with rich terminal output during bulk operations
- Supports `--skip-existing` flag to skip maps that already have directories
- Provides detailed summary of successful and failed clones
- Streamlines workflow for users setting up local repositories for multiple maps

### [release/1.0.3]

**Type**: Patch

- Fixed pull logic to mirror push behavior for main branch item retrieval
- Enhanced `RemoteOperations.pull()` to directly pull from original `item_id` for main branch when configured
- Ensures consistent behavior between push and pull operations for main branch
- Properly updates local index and remote tracking reference when pulling from main branch item
- Falls back to folder-based logic if original item is not found

### [release/1.0.1]

**Type**: Patch

- Refactored Portal URL handling to require explicit configuration via `PORTAL_URL` environment variable
- Removed default fallback to ArcGIS Online to prevent unintended behavior
- Updated MCP server documentation to clarify Portal URL usage and configuration requirements
- Enhanced Portal URL retrieval functions across all MCP tools (layer, portal, remote, repository tools)
- Improved error handling and validation for Portal URL configuration
- Ensures consistent Portal URL handling across all GitMap MCP server tools

### [release/1.0.0]

**Type**: Major

- Added GitMap MCP server implementation for Cursor IDE integration
- MCP server provides tools for repository, branch, commit, remote, layer, and portal management
- Includes comprehensive configuration documentation and example settings for Cursor integration
- Enables GitMap functionality to be accessed directly from Cursor IDE via MCP protocol
- Initial MCP server version 0.1.0

### [release/0.3.0]

**Type**: Minor

- Added `list` command to list all available web maps from Portal/AGOL
- Added filtering options to `list` command: `--owner`, `--tag`, and `--query`
- Improved notification handling with detailed status reporting after push operations
- Fixed sharing information access issue (SharingManager object handling)
- Enhanced push command to display notification status and reasons when notifications fail
- Added better error messages explaining why notifications weren't sent (e.g., item not shared with groups)
- Updated `notify_item_group_users` to properly access item sharing information
- Added `list_webmaps` function to `gitmap_core.maps` module

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
