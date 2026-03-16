# context

Visualize and export the event history graph.

## Synopsis

```bash
gitmap context <SUBCOMMAND> [OPTIONS]
```

## Description

`context` provides visualization of your GitMap repository's event history — commits, pushes, pulls, merges, and branches — rendered as ASCII diagrams, Mermaid charts, or HTML reports.

## Subcommands

| Subcommand | Description |
|---|---|
| `show` | Display event history in the terminal |
| `timeline` | Display a timeline view of events |
| `export` | Export the graph to a file |
| `graph` | Show a graph of relationships |

---

## context show

```bash
gitmap context show [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--format, -f TEXT` | Output format: `ascii`, `mermaid`, `mermaid-timeline` (default: `ascii`) |
| `--limit, -n INT` | Max events to display (default: 20) |
| `--type, -t TEXT` | Filter by event type: `commit`, `push`, `pull`, `merge`, `branch`, `diff` (repeatable) |

### Examples

```bash
# Show recent events (ASCII)
gitmap context show

# Show as Mermaid diagram
gitmap context show --format mermaid

# Show only commits and pushes
gitmap context show --type commit --type push

# Limit to last 10 events
gitmap context show --limit 10
```

---

## context timeline

```bash
gitmap context timeline [OPTIONS]
```

Same options as `show`. Renders events in a chronological timeline format.

```bash
gitmap context timeline
gitmap context timeline --format mermaid-timeline
```

---

## context export

```bash
gitmap context export [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--format, -f TEXT` | Format: `mermaid`, `mermaid-timeline`, `mermaid-git`, `ascii`, `ascii-graph`, `html` |
| `--output, -o PATH` | Output file path |
| `--theme TEXT` | HTML theme: `light` or `dark` |
| `--title TEXT` | Title for the exported visualization |

### Examples

```bash
# Export as Mermaid diagram
gitmap context export --format mermaid -o graph.md

# Export as HTML report with dark theme
gitmap context export --format html --theme dark -o history.html

# Export ASCII graph to file
gitmap context export --format ascii-graph -o graph.txt

# Export Mermaid git graph
gitmap context export --format mermaid-git -o commits.md
```

---

## Auto-Visualization

Enable automatic graph regeneration after each event:

```bash
gitmap config --auto-visualize
```

When enabled, the context graph rebuilds after commits, pushes, pulls, and branch operations. Disable with:

```bash
gitmap config --no-auto-visualize
```

## See Also

- [`gitmap log`](log.md) — view commit history
- [`gitmap config`](config.md) — enable auto-visualization
