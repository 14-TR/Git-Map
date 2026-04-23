# Example: Manage many maps with `setup-repos` and `auto-pull`

This tutorial is for GIS teams that maintain many web maps and want a reliable way to keep local repositories current.

## Scenario

You are responsible for a folder of maps owned by a team or service account. You want to:

1. clone them into a consistent local structure
2. refresh them on a schedule
3. create commits automatically when Portal changes appear

## 1. Bootstrap the repository folder

```bash
mkdir -p repositories
cd repositories
gitmap setup-repos --owner myusername --directory .
```

This creates one local Git-Map repository per discovered map.

Use a dedicated parent folder so automation is easy to reason about later.

## 2. Inspect what was created

```bash
find . -maxdepth 2 -name .gitmap -print
```

You should see each tracked repository containing Git-Map metadata.

## 3. Run a manual sync pass first

```bash
gitmap auto-pull --directory .
```

Start with a manual run before turning on automation. That helps you verify:

- credentials are valid
- the directory is correct
- Portal connectivity works
- the repositories are healthy

## 4. Enable automatic commits for routine updates

```bash
gitmap auto-pull --directory . --auto-commit
```

With `--auto-commit`, Git-Map records a commit when a map changed upstream. This is useful for monitoring production maps or shared operational layers.

## 5. Put the workflow on a schedule

If you use the daemon tooling, keep the command simple and predictable:

```bash
gitmap daemon start --directory /absolute/path/to/repositories
```

Use an absolute path for anything scheduled so background jobs never depend on the current shell location.

## Operating tips

### Keep repositories grouped by purpose

A structure like this stays manageable over time:

```text
repositories/
├── emergency-response/
├── field-ops/
└── public-facing/
```

### Review noisy maps separately

Some maps change constantly. If one repository creates too much commit noise, move it into its own folder and run a different sync cadence.

### Pair auto-pull with release review

Auto-pull is great for observation. When you intend to publish changes back, use the review flow from the release example:

1. branch the map
2. inspect the diff
3. merge only after review
4. push the approved result

## See also

- [gitmap setup-repos](../commands/setup-repos.md)
- [gitmap auto-pull](../commands/auto-pull.md)
- [gitmap daemon](../commands/daemon.md)
