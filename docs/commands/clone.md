# gitmap clone

Clone a web map from Portal into a new local repository.

Use a non-production test web map for your first clone. `clone` reads the
Portal item and creates a local GitMap repository; it does not modify the
Portal item.

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

## First-run checklist

1. Open the web map item page in ArcGIS Online or Portal.
2. Copy the item ID from the URL, such as `...?id=abc123def456`.
3. Confirm the map is safe to test against before cloning it.
4. Configure credentials through `PORTAL_URL` and `ARCGIS_USERNAME`, or through the matching GitMap config values.
5. Run `gitmap status` after cloning to confirm the new repository is on `main` with a clean working tree.

## Notes

- `clone` initializes a new repo, connects to Portal, pulls the specified item, and creates an initial commit — all in one step.
- Equivalent to `gitmap init && gitmap pull && gitmap commit -m "Initial clone"`.
- The generated `.gitmap/` directory contains local repository state for the cloned map. Keep it with the project folder if you want to preserve history.
