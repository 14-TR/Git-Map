# gitmap tag

Create or list version tags.

## Usage

```bash
gitmap tag [OPTIONS] [NAME]
```

## Options

| Option | Description |
|--------|-------------|
| `--message` / `-m` | Annotate the tag with a message |
| `--list` | List all tags |

## Examples

```bash
# Create a lightweight tag
gitmap tag v1.0.0

# Create an annotated tag
gitmap tag v1.0.0 -m "First production release"

# List all tags
gitmap tag --list
```
