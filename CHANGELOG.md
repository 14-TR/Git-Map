# Changelog

All notable changes to GitMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.5.0]: https://github.com/14-TR/Git-Map/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/14-TR/Git-Map/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/14-TR/Git-Map/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/14-TR/Git-Map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/14-TR/Git-Map/releases/tag/v0.1.0
