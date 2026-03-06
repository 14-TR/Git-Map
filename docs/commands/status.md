# gitmap status

Show the current state of the working tree — branch, latest commit, and whether there are uncommitted changes.

## Usage

```bash
gitmap status
```

## Output

```
╭─ GitMap Status ──────────────────────╮
│ On branch: main                      │
╰──────────────────────────────────────╯
Latest commit: a3f2c1b0 - Initial snapshot

Changes not committed:
  + layer "Flood Zones" added
  ~ layer "Parcels" symbology changed

Use "gitmap commit -m <message>" to commit changes
```

When the working tree is clean:

```
╭─ GitMap Status ──────────────────╮
│ On branch: main                  │
╰──────────────────────────────────╯
Nothing to commit, working tree clean
```
