# gitmap doctor

Check your GitMap environment for common issues.

## Usage

```bash
gitmap doctor [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--portal` | Attempt to connect to Portal and verify credentials |
| `--fix` | Show install commands for any missing packages |
| `--help` | Show help and exit |

## Description

`gitmap doctor` runs a series of checks against your local environment and reports any issues it finds:

1. **Python version** — ensures you're running Python 3.11 or newer
2. **Required packages** — verifies `click`, `rich`, and `deepdiff` are installed
3. **Optional packages** — notes if `apscheduler` or `arcgis` are missing (with context about what they enable)
4. **Environment variables** — shows which Portal credentials are set (`PORTAL_URL`, `ARCGIS_USERNAME`, `ARCGIS_PASSWORD`)
5. **Current directory** — detects if you're inside a GitMap repository and shows branch/commit count
6. **Portal connectivity** *(with `--portal`)* — attempts an authenticated connection to your configured Portal

Exit code is `0` when no issues are found, `1` otherwise — useful for scripting.

## Examples

```bash
# Basic environment check
gitmap doctor

# Also test Portal connectivity
gitmap doctor --portal

# Show install commands for missing packages
gitmap doctor --fix
```

## Example Output

```
GitMap Doctor — environment diagnostics

─── Python ───
  ✓ Python 3.12.0

─── Required Packages ───
  ✓ click
  ✓ rich
  ✓ deepdiff

─── Optional Packages ───
  ✓ apscheduler
  ⊘ arcgis  (optional)

─── Environment Variables ───
  ✓ PORTAL_URL=https://myorg.maps.arcgis.com
  ✓ ARCGIS_USERNAME=myuser
  ⊘ ARCGIS_PASSWORD  (not set)

─── Current Directory ───
  ✓ In a GitMap repository  (/home/user/my-map)
  ✓ Branch: main
  ✓ Commits: 14

✓ No issues found. GitMap is ready to use.
```

## See Also

- [`gitmap init`](init.md) — initialize a new repository
- [`gitmap config`](config.md) — view or update repository configuration
