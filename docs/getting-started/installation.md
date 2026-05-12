# Installation

## Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- ArcGIS Online account **or** Portal for ArcGIS 10.8+
- A non-production test web map for your first clone/push workflow

## Install from PyPI

```bash
pip install gitmap-cli
```

This installs both the core library dependency and the `gitmap` CLI command in one step.

Verify the install:

```bash
gitmap --version
```

If the command is not found, confirm the Python environment's `bin` directory is on your `PATH`, or run GitMap from the same virtual environment where you installed `gitmap-cli`.

!!! tip "Individual packages"
    If you only need the library (no CLI), install `gitmap-core` directly.
    The `gitmap` PyPI name is not the default install path. Install `gitmap-core` only for library/API use.

## Install from Source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map

# Install core library + CLI
pip install -e "packages/gitmap_core"
pip install -e "apps/cli/gitmap"
```

Verify:

```bash
gitmap --version
```

## Environment Variables

Git-Map reads credentials from environment variables when no config is set:

| Variable | Description |
|----------|-------------|
| `ARCGIS_USERNAME` | Your ArcGIS/Portal username |
| `ARCGIS_PASSWORD` | Your ArcGIS/Portal password |
| `PORTAL_URL` | Your Portal URL (defaults to `https://www.arcgis.com`) |

You can also store credentials in the repository config file — see [Working with Portals](../guides/portals.md).

Do not commit `.env` files or credentials. GitMap commands such as `status`, `diff`, `log`, and `commit` operate on the local repository, while `pull` reads from ArcGIS and `push` can update ArcGIS content.

## Upgrading

```bash
pip install --upgrade gitmap-cli
```

---

Next: [Quickstart →](quickstart.md)
