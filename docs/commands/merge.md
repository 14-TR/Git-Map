# gitmap merge

Merge another branch into the current branch.

## Usage

```bash
gitmap merge [OPTIONS] BRANCH
```

## Examples

```bash
gitmap merge feature/new-layer
gitmap merge staging
```

## Notes

- Git-Map performs a logical merge of the map JSON — layer additions, removals, and property changes are combined.
- Conflicts (e.g., both branches changed the same layer setting differently) are reported for manual resolution.
- After a successful merge, a merge commit is created automatically.
