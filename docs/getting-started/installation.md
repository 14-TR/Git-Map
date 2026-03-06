# Installation

## Requirements

- Python 3.11, 3.12, or 3.13
- ArcGIS Online account **or** Portal for ArcGIS 10.8+

## Install from PyPI

```bash
pip install gitmap-core
```

Verify the install:

```bash
gitmap --version
```

## Install from Source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
pip install -e "packages/gitmap_core"
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
pip install --upgrade gitmap-core
```

---

Next: [Quickstart →](quickstart.md)
