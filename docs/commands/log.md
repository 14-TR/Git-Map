# gitmap log

Show commit history for the current branch.

## Usage

```bash
gitmap log [OPTIONS]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-n` | 10 | Maximum number of commits to show |
| `--oneline` | | false | Compact one-line format |

## Examples

```bash
gitmap log
gitmap log -n 5
gitmap log --oneline
```

## Output (default)

```
commit a3f2c1b0
Author:    Jane Smith
Date:      2024-06-15 10:23:04
Message:   Added flood layer

commit 9e1b4a22
Author:    Jane Smith
Date:      2024-06-14 14:05:11
Message:   Initial snapshot
```

## Output (--oneline)

```
a3f2c1b0  Added flood layer
9e1b4a22  Initial snapshot
```
