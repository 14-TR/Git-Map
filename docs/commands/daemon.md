# daemon

Manage the background auto-pull daemon.

## Synopsis

```bash
gitmap daemon <SUBCOMMAND> [OPTIONS]
```

## Description

`daemon` runs `auto-pull` on a scheduled interval as a background process. Use the subcommands to start, stop, check status, and view logs.

The daemon persists across terminal sessions. State files live in `~/.gitmap-daemon/`.

## Subcommands

| Subcommand | Description |
|---|---|
| `start` | Start the daemon |
| `stop` | Stop a running daemon |
| `status` | Show daemon status and configuration |
| `logs` | View daemon log output |

---

## daemon start

```bash
gitmap daemon start [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--interval, -i INT` | Auto-pull interval in minutes (default: 60) |
| `--directory, -d TEXT` | Directory of GitMap repos (default: `repositories`) |
| `--branch, -b TEXT` | Branch to pull (default: `main`) |
| `--url, -u TEXT` | Portal URL (or set `PORTAL_URL` env var) |
| `--username TEXT` | Portal username |
| `--auto-commit` | Automatically commit changes after pull |
| `--commit-message, -m TEXT` | Commit message template (`{repo}`, `{date}`) |
| `--skip-errors` | Continue on individual repo failures |

### Examples

```bash
# Start with default settings (60-minute interval)
gitmap daemon start

# Pull every 30 minutes
gitmap daemon start --interval 30

# Pull and commit every hour
gitmap daemon start --interval 60 --auto-commit

# Custom directory and branch
gitmap daemon start \
  --interval 120 \
  --directory ~/gis-projects \
  --branch production
```

---

## daemon stop

```bash
gitmap daemon stop
```

Sends `SIGTERM` to the daemon for a graceful shutdown. Waits up to 10 seconds; force-kills if it doesn't respond.

---

## daemon status

```bash
gitmap daemon status
```

Shows whether the daemon is running, its PID, and the current configuration:

```
GitMap Auto-Pull Daemon Status

  Status     ✓ Running
  PID        12345
  Interval   60 minutes
  Directory  repositories
  Branch     main
  Auto-commit  True
  Log File   ~/.gitmap-daemon/daemon.log (4.2 KB)
```

---

## daemon logs

```bash
gitmap daemon logs [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--lines, -n INT` | Number of log lines to show (default: 50) |
| `--follow, -f` | Follow log output continuously (like `tail -f`) |

### Examples

```bash
# View last 50 lines
gitmap daemon logs

# View last 100 lines
gitmap daemon logs --lines 100

# Follow live log output
gitmap daemon logs --follow
```

---

## Daemon State Files

| File | Purpose |
|---|---|
| `~/.gitmap-daemon/daemon.pid` | Running process PID |
| `~/.gitmap-daemon/config.json` | Active daemon configuration |
| `~/.gitmap-daemon/daemon.log` | Log output from all runs |

## Alternatives

For simple scheduled sync without a persistent daemon, use cron directly:

```bash
# Every hour
0 * * * * cd /path/to/project && gitmap auto-pull --auto-commit
```

## See Also

- [`gitmap auto-pull`](auto-pull.md) — run a one-shot sync
- [`gitmap setup-repos`](setup-repos.md) — bulk clone Portal maps
