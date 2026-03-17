# gitmap lsm

Transfer popup and form settings between web maps.

The `lsm` (layer-settings-merge) command copies `popupInfo` and `formInfo` from layers and tables in a **source** map to matching layers and tables (matched by name) in a **target** map. This is useful when you've configured detailed popups in one map and need to propagate them to related maps without manually re-creating the config.

## Usage

```bash
gitmap lsm SOURCE [TARGET] [OPTIONS]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SOURCE` | Yes | Branch name, commit ID, item ID, or file path of the source map |
| `TARGET` | No | Branch name, commit ID, item ID, or file path of the target map |

If `TARGET` is omitted, you can use `--local-folder` or `--remote-folder` to apply to multiple maps at once.

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | | Preview changes without applying them |
| `--local-folder PATH` | `-lf` | Apply settings to all gitmap repositories in a local folder |
| `--remote-folder TEXT` | `-rf` | Apply settings to all web maps in a Portal folder (by ID or name) |
| `--folder-owner TEXT` | | Portal username who owns the remote folder (defaults to authenticated user) |

!!! note
    `--local-folder` and `--remote-folder` are mutually exclusive. You also cannot use `TARGET` together with a folder option.

## Examples

```bash
# Transfer settings from main branch to feature branch
gitmap lsm main feature/new-layer

# Transfer from a specific commit to the index
gitmap lsm abc123def

# Transfer between JSON files with a dry-run preview
gitmap lsm source.json target.json --dry-run

# Apply settings from main to all repos in a local folder
gitmap lsm main --local-folder /path/to/my-repos

# Apply settings to all maps in a remote Portal folder
gitmap lsm main --remote-folder "Production Maps"

# Apply to a folder owned by a specific user
gitmap lsm main --remote-folder "Production Maps" --folder-owner jsmith
```

## How Matching Works

Layers and tables are matched **by name** (title). If the source has a layer called `Parcels`, the command will find a layer also called `Parcels` in the target and copy its popup/form settings across. Layers with no name match in the target are skipped.

## What Gets Transferred

- `popupInfo` — Popup template configuration (fields, expressions, media)
- `formInfo` — Smart form configuration for feature editing

Layer rendering, symbology, and other layer properties are **not** modified.

## Use Case

This command is particularly useful when:

- You maintain a "master" map with fully configured popups and want to sync those settings to branch maps
- You need to propagate popup updates across a portfolio of maps after a schema change
- You're standing up a new Portal environment and want to replicate popup config from an existing map

## Related Commands

- [`gitmap merge`](merge.md) — Merge full branch contents
- [`gitmap diff`](diff.md) — Compare two map states
- [`gitmap push`](push.md) — Deploy a map to Portal
