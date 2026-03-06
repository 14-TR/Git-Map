# gitmap revert

Restore the repository to a previous commit state.

## Usage

```bash
gitmap revert [OPTIONS] COMMIT
```

## Examples

```bash
# Revert to a specific commit hash
gitmap revert a3f2c1b0
```

## Notes

- `revert` loads the target commit's map data into the index and creates a new revert commit — it does **not** rewrite history.
- Use `gitmap log --oneline` to find the commit hash you want to restore.
- After reverting, use `gitmap push` to deploy the restored version to Portal.
