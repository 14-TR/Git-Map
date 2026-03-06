# gitmap branch

List existing branches, create a new branch, or delete a branch.

## Usage

```bash
gitmap branch [OPTIONS] [NAME]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--delete` | `-d` | Delete the named branch |

## Examples

```bash
# List all branches
gitmap branch

# Create a new branch
gitmap branch feature/new-layer

# Delete a branch
gitmap branch --delete feature/old-experiment
```

## Output (listing)

```
  feature/new-layer
* main
  staging
```

The `*` marks the current branch.
