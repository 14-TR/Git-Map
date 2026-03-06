# gitmap pull

Fetch the latest map data from Portal and update the local staging area (index). Does not auto-commit.

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
