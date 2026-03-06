# gitmap checkout

Switch to a different branch, or restore the index to a specific commit.

## Usage

```bash
gitmap checkout [OPTIONS] TARGET
```

## Examples

```bash
# Switch branches
gitmap checkout main
gitmap checkout feature/new-layer

# Restore index to a specific commit hash
gitmap checkout a3f2c1b0
```

## Notes

- Switching branches updates `HEAD` and loads that branch's latest commit into the index.
- Checking out a commit hash puts the repo in detached-HEAD mode — create a branch to keep changes.
