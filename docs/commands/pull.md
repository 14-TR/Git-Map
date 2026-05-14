# gitmap pull

Fetch the latest map data from Portal and update the local staging area (index). Does not auto-commit.

Use `pull` after making or reviewing a Portal-side map change that should be
captured in your current branch. It is a Portal read operation: the local
branch changes, but the Portal item is not updated.

## Usage

```bash
gitmap pull [OPTIONS]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--branch` | `-b` | Branch to pull (defaults to current branch) |
| `--url` | `-u` | Portal URL |
| `--username` | | Portal username |
| `--rationale` | `-r` | Reason for this pull (stored in audit log) |

## Examples

```bash
gitmap pull
gitmap pull --branch main
gitmap pull --url https://portal.example.com
gitmap pull -r "Syncing production changes after client meeting"
```

## Safe review loop

```bash
gitmap pull
gitmap status
gitmap diff main feature/hydrology-update --format visual
gitmap commit -m "Update hydrology layers"
```

If you are pulling into a feature branch, review the diff against `main` before
committing. If the diff is not what you expected, stop before `commit` and
inspect the Portal item or local branch selection.

## Output

```
Connecting to https://www.arcgis.com...
Authenticated as jsmith
Pulling branch 'main'...

Pulled 'main' from Portal

  Layers: 5

Changes staged. Use 'gitmap diff' to review and 'gitmap commit' to save.
```

## Notes

- `pull` only updates the index. You still need to `commit` to record the version.
- Review changes with `gitmap diff` before committing.
- Repositories cloned from a single web map can pull the original Portal item into
  the current local branch before any GitMap remote folder has been created.
- `pull` and `push` are intentionally separate. `pull` reads from Portal into GitMap; `push` publishes a chosen branch state back to Portal.
