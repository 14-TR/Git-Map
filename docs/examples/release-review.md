# Example: Review and release a map change with an HTML diff

This walkthrough shows a lightweight release ritual for teams that want a clear audit trail before publishing a map change.

## Scenario

You made edits on `feature/new-basemap` and want to:

1. compare the branch against `main`
2. generate a review artifact for a GIS lead or PM
3. merge the change after approval
4. push the approved map to Portal

## Workflow

### 1. Sync both sides of the comparison

```bash
gitmap checkout main
gitmap pull
gitmap checkout feature/new-basemap
gitmap pull --branch feature/new-basemap
```

This makes sure your branch review is based on fresh portal state, not stale local data.

### 2. Run a quick terminal diff

```bash
gitmap diff main feature/new-basemap --format visual
```

Use the terminal diff to answer the fast questions first:

- did the right layers change?
- did anything unexpected disappear?
- are the edits small enough to merge safely?

### 3. Generate a shareable HTML report

```bash
mkdir -p reports
gitmap diff main feature/new-basemap --format html --output reports/main-vs-feature-new-basemap.html
```

The HTML file is useful when the reviewer:

- does not use the CLI
- wants a durable artifact for a ticket
- needs a visual report to archive with release notes

## Suggested approval note

When you send the report for review, keep the summary tight:

> Compared `main` to `feature/new-basemap`.
> Basemap changed, one hydrology layer was added, and parcel visibility was updated.
> Review artifact: `reports/main-vs-feature-new-basemap.html`

## 4. Merge after approval

```bash
gitmap checkout main
gitmap merge feature/new-basemap
```

If the merge reports conflicts, stop and resolve them before deployment.

## 5. Push the approved state

```bash
gitmap push
```

At this point the reviewed branch state becomes the live map state in Portal.

## Optional: tag the release

```bash
gitmap tag release-2026-04-basemap -m "Approved basemap refresh"
```

Tagging gives you a clean rollback anchor for future investigations.

## Why this pattern works

It creates a repeatable release loop:

- branch for safety
- diff for clarity
- HTML artifact for review
- merge for traceability
- push for deployment

## See also

- [Reviewing Diffs and Sharing Change Reports](../guides/reviewing-diffs.md)
- [Day-to-Day Workflow](../guides/workflow.md)
- [gitmap diff](../commands/diff.md)
