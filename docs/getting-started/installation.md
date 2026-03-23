# Installation

## Requirements

- Python 3.11, 3.12, or 3.13
- ArcGIS Online account **or** Portal for ArcGIS 10.8+

## Install from PyPI

```bash
pip install gitmap
```

This installs both the core library and the `gitmap` CLI command in one step.

Verify the install:

```bash
gitmap --version
```

!!! tip "Individual packages"
    If you only need the library (no CLI), install `gitmap-core` directly.
    The `gitmap` meta-package is the recommended install for most users.

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

## Upgrading

```bash
pip install --upgrade gitmap
```

---

Next: [Quickstart →](quickstart.md)
