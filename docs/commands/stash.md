# gitmap stash

Temporarily set aside uncommitted changes so you can switch context.

## Usage

```bash
gitmap stash [COMMAND]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| (none) | Stash current changes |
| `pop` | Apply the most recent stash and remove it |
| `list` | Show all stashed states |
| `drop` | Delete a stash entry |

## Examples

```bash
gitmap stash           # Save changes and clean the index
gitmap stash pop       # Restore the last stash
gitmap stash list      # View saved stashes
gitmap stash drop 0    # Delete stash entry 0
```
