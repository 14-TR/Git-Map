# gitmap clone

Clone a web map from Portal into a new local repository.

## Usage

```bash
gitmap clone [OPTIONS] ITEM_ID [PATH]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--url` | `-u` | Portal URL |
| `--username` | | Portal username |
| `--branch` | `-b` | Branch name to create (default: `main`) |

## Examples

```bash
# Clone by Portal item ID
gitmap clone abc123def456

# Clone to a named directory
gitmap clone abc123def456 my-project

# Clone from a specific Portal
gitmap clone abc123def456 --url https://portal.example.com
```

## Notes

- `clone` initializes a new repo, connects to Portal, pulls the specified item, and creates an initial commit — all in one step.
- Equivalent to `gitmap init && gitmap pull && gitmap commit -m "Initial clone"`.
