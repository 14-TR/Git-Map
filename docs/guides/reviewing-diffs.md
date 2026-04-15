# Reviewing Diffs and Sharing Change Reports

GitMap's diff tooling is strong enough for day-to-day QA, release reviews, and stakeholder sign-off — but only if your team uses the right output mode for the job.

This guide shows when to use plain text, the Rich table view, and the exportable HTML report.

## Pick the right diff mode

| Use case | Command | Best for |
|----------|---------|----------|
| Quick terminal check before a commit | `gitmap diff` | Solo development and fast sanity checks |
| Human-friendly branch comparison in the terminal | `gitmap diff main feature/my-change --format visual` | Reviewing branch work with clear add/remove/modify signals |
| Shareable artifact for non-CLI reviewers | `gitmap diff main feature/my-change --format html --output reports/feature-my-change.html` | PMs, GIS leads, screenshots, attachments, approval workflows |
| Deep troubleshooting on a modified layer | `gitmap diff --format visual --verbose` | Inspecting property-level JSON changes |

## Recommended branch review workflow

When you're working on a feature branch, review it in the same order every time:

```bash
gitmap checkout feature/new-basemap
gitmap pull --branch feature/new-basemap
gitmap diff main feature/new-basemap --format visual
gitmap diff main feature/new-basemap --format html --output reports/new-basemap.html
```

What this gives you:

1. **A quick terminal review** for your own sanity check
2. **A durable HTML artifact** you can attach to a PR, email, or project ticket
3. **A repeatable review ritual** before every merge to `main`

## Terminal review: `--format visual`

Use visual mode when you want a fast, readable comparison without wading through raw JSON.

```bash
gitmap diff main staging --format visual
```

Look for these signals:

- `+` Added layer or table
- `-` Removed layer or table
- `~` Modified layer or table
- `*` Top-level map property changed

This is the best default for branch-to-branch reviews because it shows **what changed** without overwhelming you with every nested field.

## Detailed investigation: `--verbose`

If the summary tells you a layer changed but not *why*, add verbose mode:

```bash
gitmap diff main feature/symbology --format visual --verbose
```

Verbose mode is especially useful when reviewing:

- renderer and symbology edits
- popup changes
- visibility or opacity tweaks
- basemap and map-level property changes

Tip: start with `--format visual`, then re-run with `--verbose` only when something looks suspicious.

## Sharing with non-technical reviewers: HTML reports

The HTML formatter creates a self-contained report with badges, a color-coded change table, and detailed JSON blocks for modified layers.

```bash
gitmap diff main release/q2-map-update --format html --output reports/q2-map-update.html
```

This is the best option when:

- a GIS manager wants to review changes before deployment
- you need evidence of what changed for a ticket or change request
- the reviewer doesn't have GitMap installed
- you want a stable artifact to archive alongside release notes

### Suggested report naming

Use a predictable naming pattern so reports are easy to find later:

```bash
reports/<source>-vs-<target>.html
```

Examples:

- `reports/main-vs-feature-new-basemap.html`
- `reports/release-q2-vs-main.html`
- `reports/staging-vs-production.html`

## PR-friendly review pattern

A practical pattern for pull requests:

```bash
gitmap diff main feature/parcel-cleanup --format visual
gitmap diff main feature/parcel-cleanup --format html --output reports/parcel-cleanup.html
```

Then in your PR description, include:

- the branch names compared
- a one-line summary of the change
- the path to the generated HTML report

Example:

> Compared `main` → `feature/parcel-cleanup`
>
> Added one flood-risk layer, removed one deprecated table, and updated parcel symbology.
>
> HTML review artifact: `reports/parcel-cleanup.html`

## Suggested team policy

If you're adopting GitMap with a team, this lightweight policy works well:

- **Every merge to `main` gets a branch diff review**
- **Every high-impact change gets an HTML diff artifact**
- **Every unexpected diff gets re-run with `--verbose` before merge**

That gives you a real review loop without adding much process overhead.

## See also

- [gitmap diff](../commands/diff.md)
- [Day-to-Day Workflow](workflow.md)
- [Branching Strategy](branching.md)
