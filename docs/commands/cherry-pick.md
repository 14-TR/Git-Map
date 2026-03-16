# cherry-pick

Apply changes from a specific commit to the current branch.

## Synopsis

```bash
gitmap cherry-pick <COMMIT_HASH> [OPTIONS]
```

## Description

`cherry-pick` creates a new commit on the current branch that contains the same map state as the specified source commit. The new commit gets a fresh ID and timestamp, but carries over the message, author, and map data from the source.

This is useful for selectively applying a change from one branch to another without merging the entire branch history.

## Arguments

| Argument | Description |
|---|---|
| `COMMIT_HASH` | SHA of the commit to cherry-pick (required) |

## Options

| Option | Description |
|---|---|
| `--rationale, -r TEXT` | Optional explanation for the cherry-pick |
| `--help` | Show help and exit |

## Examples

```bash
# Apply a specific commit to the current branch
gitmap cherry-pick abc12345

# Cherry-pick with a rationale
gitmap cherry-pick abc12345 -r "Backporting critical layer visibility fix to hotfix branch"
```

## Workflow

Cherry-pick is most useful when you need to apply a single targeted change across branches:

```bash
# You're on main; a fix was made on feature/symbology
gitmap log --branch feature/symbology --oneline
# a1b2c3d4 Fix layer opacity for print view

# Apply just that fix to main
gitmap cherry-pick a1b2c3d4

# Verify it was applied
gitmap log --oneline
```

## Notes

- If you have uncommitted changes when running `cherry-pick`, you will be prompted to confirm before continuing.
- Use `gitmap log --oneline` or `gitmap log --graph` to find commit hashes.

## See Also

- [`gitmap merge`](merge.md) — merge an entire branch
- [`gitmap log`](log.md) — find commit hashes
- [`gitmap revert`](revert.md) — undo a commit
