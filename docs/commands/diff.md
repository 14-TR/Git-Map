# gitmap diff

Show changes between the current index and the last commit, or between two commits.

## Usage

```bash
gitmap diff [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--commit` | Compare a specific commit against its parent |

## Examples

```bash
# Diff index vs HEAD
gitmap diff

# Diff a specific commit
gitmap diff --commit a3f2c1b0
```

## Output

```
Diff: index → a3f2c1b0

  + layer "Flood Zones"      (added)
  ~ layer "Parcels"          symbology changed
  - layer "Old Boundaries"   (removed)
```
