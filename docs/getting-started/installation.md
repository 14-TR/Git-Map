# Installation

## Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- ArcGIS Online account **or** Portal for ArcGIS 10.8+

## Install from PyPI

```bash
pip install gitmap
gitmap --version
```

This installs both the core library and the `gitmap` CLI command in one step.

!!! tip "Individual packages"
    If you only need the library (no CLI), install `gitmap-core` directly.
    The `gitmap` meta-package is the recommended install for most users.

## Install from source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/gitmap_core[dev]"
pip install -e "apps/cli/gitmap"
gitmap --version
```

## Environment variables

Git-Map reads credentials from environment variables when no config is set:

| Variable | Description |
|----------|-------------|
| `PORTAL_URL` | Your Portal URL (defaults to `https://www.arcgis.com`) |
| `ARCGIS_USERNAME` | Preferred ArcGIS/Portal username variable |
| `ARCGIS_PASSWORD` | Preferred ArcGIS/Portal password variable |
| `PORTAL_USER` | Backwards-compatible username alias |
| `PORTAL_PASSWORD` | Backwards-compatible password alias |

Example `.env` file:

```env
PORTAL_URL=https://your-org.maps.arcgis.com
ARCGIS_USERNAME=your_username
ARCGIS_PASSWORD=your_password
# Optional backwards-compatible aliases:
# PORTAL_USER=your_username
# PORTAL_PASSWORD=your_password
```

You can also store credentials in the repository config file — see [Working with Portals](../guides/portals.md).

## First-run verification

After installing, run:

```bash
gitmap --version
gitmap doctor
```

If `gitmap doctor` reports missing credentials, check your shell or `.env` file for typos before trying a clone or push.

## Upgrading

```bash
pip install --upgrade gitmap
```

---

Next: [Quickstart →](quickstart.md)
