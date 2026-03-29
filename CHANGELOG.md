# Changelog

All notable changes to GitMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-03-29

### Added
- `gitmap completions` command — generates and auto-installs shell completion scripts for bash, zsh, and fish (via `gitmap completions --install <shell>`)
- `gitmap doctor` diagnostic command — checks Python version, required packages, environment variables, and (optionally) Portal connectivity; exits non-zero when issues found (useful for scripting)
- `--format html` option on `gitmap diff` — exports a self-contained dark-themed HTML diff report for sharing with stakeholders
- `--output` option on `gitmap diff` for custom report file paths
- Rich spinner progress indicators on `gitmap push`, `gitmap pull`, and `gitmap clone` — network operations now show live feedback instead of bare dim text
- Context-aware error hints on `push`/`pull`/`clone` for common failure modes (auth errors, item not found)
- "Nothing to push" guard on `gitmap push` when repository has no commits
- `epilog` tip hints on `gitmap pull` and `gitmap clone` pointing to recommended follow-up commands
- Documentation: `gitmap completions` command reference page added to the MkDocs site

### Changed
- Python 3.14 supported — all three packages (`gitmap-core`, `gitmap-cli`, `gitmap`) now declare `requires-python = ">=3.11,<3.15"`; CI matrix extended to include Python 3.14; all 734 tests pass
- `gitmap push` output now shows auth username inline (✓ Pushed as username) rather than a separate dim line
- `gitmap clone` output now shows the local path alongside item ID, title, and layer count

## [0.6.0] - 2026-03-05

### Added
- MCP stash tools (stash_push, stash_pop, stash_list, stash_drop) exposed via MCP server
- gitmap_merge tool added to MCP server
- Branch-to-branch diff support (gitmap diff <source> <target>)
- find_common_ancestor implementation for 3-way merge base detection
- Integration tests for OpenClaw tools (test_openclaw)
- pyproject.toml with consolidated pytest config and ruff lint rules
- Dev dependency: rich for CLI formatting and tests

### Changed
- Test suite expanded to 660+ tests (up from 608)
- compat.py error-path branch coverage improved from 86% to 96%
- Ruff: resolved 67 lint issues across repository.py, diff.py, visualize.py, and test modules

### Fixed
- ContextStore.__del__ now closes SQLite connection on garbage collection (resource leak)
- Ambiguous variable names (F811, E741, F841, B007) in repository.py and visualize.py
- CLI dependency guard extended to include rich in test_diff.py
- CI workflow updated to install CLI deps and apply skip markers for cross-app tests

## [0.5.0] - 2025-02-14

### Added
- Communication module for Portal user/group notifications
- Push notifications to group members on production branch updates
- `notify` command for sending messages to Portal groups

### Changed
- Improved `__init__.py` efficiency with lazy imports
- Enhanced test coverage across all core modules (608+ tests)

### Fixed
- Pytest config path for test collection on fresh clones
- Type errors in repository and diff modules (mypy compliance)

## [0.4.0] - 2025-02-10

### Added
- `stash` command to save work-in-progress without committing
- `cherry-pick` command to apply specific commits to current branch
- `tag` command for marking specific commits with version labels
- `revert` command to undo specific commits with inverse changes
- ArcGIS API version compatibility layer for broader Portal support

### Fixed
- Folder creation handling for different Portal versions
- Feature branch pushing to root content (skip folder creation)
- Empty folder creation result handling

## [0.3.0] - 2025-01-20

### Added
- Context visualization in multiple formats (Mermaid flowchart, timeline, git-graph, ASCII, HTML)
- GitHub Actions workflow for automated testing
- Auto-regenerate context graph on branch, merge, pull, push, and init operations

### Changed
- Improved flowchart branch/merge linking visualization
- Enhanced git-graph with merge, LSM, and branch event display

## [0.2.0] - 2025-01-10

### Added
- Auto-pull daemon with interval-based scheduling
- Auto-commit functionality with customizable commit messages
- GitMap TUI client with Textual framework
- GitMap GUI with modular architecture
- Services browser with one-click item ID copy
- LSM (Layer Settings Merge) health check and redesigned page

### Changed
- Reorganized GUI navigation structure

## [0.1.0] - 2024-12-30

### Added
- Initial release with core version control features
- `init` - Initialize a new GitMap repository
- `clone` - Clone a web map from Portal/AGOL
- `commit` - Save changes with a message
- `branch` - Create and manage branches
- `checkout` - Switch between branches
- `diff` - Compare map versions
- `merge` - Merge branches with conflict resolution
- `push` - Upload changes to Portal/AGOL
- `pull` - Download changes from Portal/AGOL
- `log` - View commit history
- `status` - Show repository status
- `config` - Manage repository configuration
- `list` - Discover web maps from Portal
- `setup-repos` - Bulk repository setup with owner filtering
- `lsm` - Layer Settings Merge for transferring popup/form settings

---

[0.6.0]: https://github.com/14-TR/Git-Map/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/14-TR/Git-Map/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/14-TR/Git-Map/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/14-TR/Git-Map/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/14-TR/Git-Map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/14-TR/Git-Map/releases/tag/v0.1.0
