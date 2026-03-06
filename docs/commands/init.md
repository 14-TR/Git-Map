# gitmap init

Initialize a new GitMap repository in the current directory (or a specified path).

## Usage

```bash
gitmap init [OPTIONS] [PATH]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--project-name` | `-n` | directory name | Human-readable project name |
| `--user-name` | `-u` | `""` | Default author name for commits |
| `--user-email` | `-e` | `""` | Default author email |

## Examples

```bash
# Initialize in the current directory
gitmap init

# Set project metadata
gitmap init --project-name "Downtown Parcels" --user-name "Jane Smith"

# Initialize at a specific path
gitmap init /path/to/project
```

## What It Creates

```
.gitmap/
├── config.json       # Project settings (name, author, remote)
├── HEAD              # Current branch pointer → refs/heads/main
├── index.json        # Empty staging area
├── refs/
│   └── heads/
│       └── main      # Initial branch
└── objects/
    └── commits/      # Commit storage (empty until first commit)
```

## Notes

- Running `init` in a directory that already has a `.gitmap/` folder prints a warning and exits without modifying anything.
- The default branch is always `main`.
