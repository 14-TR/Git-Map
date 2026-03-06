# Publishing to PyPI

GitMap uses **PyPI Trusted Publishing** (OIDC) — no API tokens needed.

## One-Time Setup (do this once)

### 1. Create the package on PyPI
Go to https://pypi.org/manage/account/ → "Your projects" → the package must exist before trusted publishing can be configured.

First release: publish manually once:
```bash
pip install build twine
python -m build packages/gitmap_core --outdir dist/
twine upload dist/*
# Enter your PyPI username/password or use an API token
```

### 2. Configure Trusted Publisher on PyPI
After the package exists:
1. Go to https://pypi.org/manage/project/gitmap-core/settings/
2. Click **"Add a new publisher"** under "Trusted Publishers"
3. Fill in:
   - **Owner:** `14-TR`
   - **Repository:** `Git-Map`
   - **Workflow:** `publish.yml`
   - **Environment:** `pypi`

### 3. Create the GitHub Environment
1. Go to `https://github.com/14-TR/Git-Map/settings/environments`
2. Create environment named **`pypi`**
3. (Optional) Add protection rules like "require approval"

## Publishing a New Release

Once setup is done, publishing is just a tag:

```bash
# Bump version in packages/gitmap_core/pyproject.toml first
git add packages/gitmap_core/pyproject.toml
git commit -m "chore: bump core to v0.6.1"
git tag core-v0.6.1
git push origin main --tags
```

The `publish.yml` workflow fires automatically, runs tests, builds, and pushes to PyPI.

## Versioning Convention

| Tag pattern | Package |
|------------|---------|
| `core-v*`  | `gitmap-core` (this package) |

## Package Name

The package is published as **`gitmap-core`** on PyPI:
```
pip install gitmap-core
```
