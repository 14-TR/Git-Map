# Installation

## Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- ArcGIS Online account **or** Portal for ArcGIS 10.8+
- A non-production test web map for your first clone/push workflow

## Install from source

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e "apps/cli/gitmap"
```

Use a Python 3.11+ interpreter when creating the virtual environment. If `python3` on your machine still resolves to Python 3.9 or 3.10, use an explicit executable such as `python3.11`, `python3.12`, or `python3.13`.

This installs the `gitmap` CLI from the current checkout.

Verify the install:

```bash
gitmap --version
gitmap --help
```

If the command is not found, confirm the virtual environment is activated, or run GitMap from the same shell where you installed the editable packages.

!!! warning "PyPI install status"
    The `gitmap-cli` PyPI package is not currently a supported first-user install path.
    Use the source install flow above until published installs are verified for supported Python versions.

## Library-only install

```bash
python -m pip install -e "packages/gitmap_core"
```

Verify:

```bash
gitmap --version
```

## Environment Variables

Git-Map reads credentials from environment variables when no config is set:

| Variable | Description |
|----------|-------------|
| `PORTAL_USER` | Preferred Portal username variable |
| `PORTAL_PASSWORD` | Preferred Portal password variable |
| `ARCGIS_USERNAME` | Alternate ArcGIS/Portal username variable |
| `ARCGIS_PASSWORD` | Alternate ArcGIS/Portal password variable |
| `PORTAL_URL` | Your Portal URL (defaults to `https://www.arcgis.com`) |

GitMap accepts either `PORTAL_USER` / `PORTAL_PASSWORD` or `ARCGIS_USERNAME` / `ARCGIS_PASSWORD`. Set only one username/password pair for a given shell or `.env` file so it is obvious which credentials GitMap will use.

You can also store credentials in the repository config file — see [Working with Portals](../guides/portals.md).

Do not commit `.env` files or credentials. GitMap commands such as `status`, `diff`, `log`, and `commit` operate on the local repository, while `pull` reads from ArcGIS and `push` can update ArcGIS content.

## Upgrading

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "packages/gitmap_core[dev]"
python -m pip install -e "apps/cli/gitmap"
```

---

Next: [Quickstart →](quickstart.md)
