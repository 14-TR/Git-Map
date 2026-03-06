# Branching Strategy

Git-Map branches are lightweight — create as many as you need. This guide suggests a strategy that works well for most teams.

## Recommended Branch Layout

```
main          ← production (always deployable)
staging       ← QA / client review
feature/*     ← individual changes
hotfix/*      ← urgent production fixes
```

## Flow

```
feature/x  →  staging  →  main
hotfix/y                →  main
```

1. Create a `feature/` branch for each change.
2. Merge to `staging` for review/QA.
3. Merge `staging` to `main` and push to production.
4. For urgent fixes, branch from `main` as `hotfix/`, fix, merge directly to `main`.

## Naming Conventions

| Prefix | Use Case |
|--------|----------|
| `feature/` | New layers, symbology changes, data updates |
| `hotfix/` | Urgent production fixes |
| `experiment/` | Risky changes you might not keep |
| `archive/` | Preserved state of a historical map version |

## Tips

- Keep branches short-lived — merge and delete when done.
- Use `gitmap stash` to quickly save work-in-progress before switching branches.
- Tag stable states before major changes: `gitmap tag pre-overhaul`.
