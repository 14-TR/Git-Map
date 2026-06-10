# GitMap CLI

Command-line interface for GitMap - Git-like version control for ArcGIS web maps.

## Installation

```bash
python -m pip install -e "packages/gitmap_core"
python -m pip install -e "apps/cli/gitmap"
```

Install both editable packages from the repository root. `packages/gitmap_core`
provides the reusable library, while `apps/cli/gitmap` installs the public
`gitmap` command.

## Usage

```bash
gitmap <command> [options]
```

Verify the install:

```bash
gitmap --version
gitmap --help
```

## Commands

### Repository Management
- `gitmap init` - Initialize a new GitMap repository
- `gitmap clone` - Clone a web map from Portal/AGOL
- `gitmap status` - Show working tree status
- `gitmap config` - Get/set repository configuration

### Version Control
- `gitmap commit` - Record changes to the repository
- `gitmap log` - Show commit history
- `gitmap diff` - Show changes between commits
- `gitmap revert` - Revert a commit

### Branching
- `gitmap branch` - List, create, or delete branches
- `gitmap checkout` - Switch branches
- `gitmap merge` - Merge branches
- `gitmap merge-from` - Merge from a remote branch
- `gitmap cherry-pick` - Apply changes from specific commits
- `gitmap stash` - Stash working tree changes

### Remote Operations
- `gitmap push` - Push changes to Portal/AGOL
- `gitmap pull` - Pull changes from Portal/AGOL
- `gitmap auto-pull` - Daemon for automatic pulling
- `gitmap list` - List web maps on Portal/AGOL

### Tags
- `gitmap tag` - Create, list, or delete tags

### Context & Visualization
- `gitmap context` - Manage context graph events

### Layer Operations
- `gitmap layer-settings-merge` - Merge layer settings

### Notifications
- `gitmap notify` - Send notifications to Portal/AGOL users

### Utilities
- `gitmap daemon` - Run background tasks
- `gitmap setup-repos` - Set up multiple repositories

## Examples

```bash
# Initialize a new repository
gitmap init

# Clone a web map
gitmap clone <item-id>

# Make changes and commit
gitmap commit -m "Add new layer"

# Push to Portal
gitmap push

# Create and switch to a new branch
gitmap branch feature/new-layer
gitmap checkout feature/new-layer

# View commit history
gitmap log
```

## Dependencies

- `gitmap_core>=0.1.0` - Core library
- `click>=8.1.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `apscheduler>=3.10.0` - Task scheduling

## Configuration

Configuration is stored in `.gitmap/config.json` within each repository.

## License

MIT
