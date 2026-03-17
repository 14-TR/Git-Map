# gitmap merge-from

Merge a branch from another GitMap repository into the current branch.

The `merge-from` command enables **cross-repository merges** — it reads map data from a branch in a different local GitMap repository and merges it into the current repository's active branch. This is useful when you maintain a "master" or "template" repository and want to pull its changes into project-specific repositories.

## Usage

```bash
gitmap merge-from SOURCE_REPO SOURCE_BRANCH [OPTIONS]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SOURCE_REPO` | Yes | Path to the source GitMap repository directory |
| `SOURCE_BRANCH` | Yes | Branch name to merge from the source repository |

## Options

| Option | Description |
|--------|-------------|
| `--no-commit` | Perform the merge but don't automatically create a commit |

## Examples

```bash
# Merge 'main' from a master repo into the current branch
gitmap merge-from /path/to/master-repo main

# Merge a specific branch, then commit manually
gitmap merge-from ../template-repo 2.1 --no-commit

# Merge from a sibling directory
gitmap merge-from ../feature-map feature/new-layer
```

## Conflict Resolution

If the merge produces conflicts (layers that differ in both repositories), `merge-from` will prompt you to resolve each one interactively:

```
Merge Conflicts
  Layers: 2
  Tables: 1

Table Conflicts (1):
  Tables will be resolved together.
  Resolve all tables with [ours/theirs/skip] (theirs):

Layer Conflicts (2):
Conflict in layer: Parcels
  Layer ID: abc123
  Resolve with [ours/theirs/skip] (skip): theirs
```

For each conflict you choose:
- **ours** — keep the version from the current repository
- **theirs** — take the version from the source repository
- **skip** — leave the conflict unresolved (merge will not be applied)

If any conflicts remain unresolved, the merge is aborted and the index is not modified.

## Auto-Commit Behavior

By default, `merge-from` creates a merge commit automatically:

```
Merge commit: a3f2c1b0
```

The commit message format is:
```
Merge '<source_branch>' from <source_repo_name> into '<current_branch>'
```

Use `--no-commit` to stage the merge result without committing:

```bash
gitmap merge-from ../master-repo main --no-commit
gitmap diff          # Review what changed
gitmap commit -m "Merged latest template from master repo"
```

## Cross-Repository Merges

Unlike `gitmap merge` (which merges branches within the same repository), `merge-from` works across separate `.gitmap/` repositories on disk. There is no shared commit history between the two repos, so all conflicts are resolved by choosing one side or the other — there is no three-way merge ancestor.

## Related Commands

- [`gitmap merge`](merge.md) — Merge branches within the same repository
- [`gitmap diff`](diff.md) — Compare map states before merging
- [`gitmap lsm`](lsm.md) — Transfer only popup/form settings between maps
