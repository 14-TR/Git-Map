# gitmap list

List all available web maps from ArcGIS Online or Portal for ArcGIS.

## Usage

```bash
gitmap list [OPTIONS]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--query TEXT` | `-q` | Search query to filter results (e.g. `title:MyMap`) |
| `--owner TEXT` | `-o` | Filter by owner username |
| `--tag TEXT` | `-t` | Filter by tag |
| `--max-results INT` | `-m` | Maximum results to return (default: 100) |
| `--url TEXT` | `-u` | Portal URL (or set `PORTAL_URL` env var) |
| `--username TEXT` | | Portal username (or set `ARCGIS_USERNAME` env var) |
| `--password TEXT` | | Portal password (or set `ARCGIS_PASSWORD` env var) |

## Examples

```bash
# List all maps in ArcGIS Online
gitmap list

# Filter by owner
gitmap list --owner jsmith

# Filter by tag
gitmap list --tag production

# Combine filters
gitmap list --owner jsmith --tag production

# Search by title
gitmap list --query "title:Flood Risk"

# Connect to a specific Portal
gitmap list --url https://portal.myorg.com/portal --owner jsmith

# Limit results
gitmap list --max-results 25
```

## Output

Results are displayed as a table with four columns:

| Column | Description |
|--------|-------------|
| ID | The Portal item ID (use with `gitmap clone`) |
| Title | Web map display name |
| Owner | Portal username of the owner |
| Type | Item type (always `Web Map`) |

## Authentication

Credentials are read from environment variables by default:

```bash
export ARCGIS_USERNAME=jsmith
export ARCGIS_PASSWORD=mypassword
export PORTAL_URL=https://myorg.maps.arcgis.com
gitmap list
```

Or pass them directly:

```bash
gitmap list --username jsmith --password mypassword --url https://myorg.maps.arcgis.com
```

## Next Steps

Once you have a map ID from `gitmap list`, use `gitmap clone` to start tracking it:

```bash
gitmap clone abc123def456 --url https://myorg.maps.arcgis.com
```
