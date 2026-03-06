# gitmap commit

Record changes to the repository by creating a new commit snapshot.

## Usage

```bash
gitmap commit [OPTIONS]
```

## Options

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--message` | `-m` | ✓ | Commit message |
| `--author` | `-a` | | Override the commit author |
| `--rationale` | `-r` | | Optional rationale (why this change was made) |

## Examples

```bash
# Basic commit
gitmap commit -m "Initial snapshot"

# With author override
gitmap commit -m "Added flood layer" --author "Jane Smith"

# With rationale for audit trail
gitmap commit -m "Removed deprecated layer" -r "Layer decommissioned per ticket #42"
```

## Output

```
Created commit a3f2c1b0

  Message:    Added flood layer
  Author:     Jane Smith
  Timestamp:  2024-06-15T10:23:04
  Layers:     6

Branch 'main' updated to a3f2c1b0
```

## Notes

- If the index matches the last commit (nothing changed), Git-Map prints `Nothing to commit` and exits cleanly.
- Commits are immutable snapshots — you can always revert to them.
- The `--rationale` field is stored in the commit and shown in `gitmap log` for audit purposes.
