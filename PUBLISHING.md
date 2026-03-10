# Publishing to PyPI

GitMap ships as two packages on PyPI:

| Package | Install | Description |
|---------|---------|-------------|
| `gitmap` | `pip install gitmap` | CLI tool — the main user-facing package |
| `gitmap-core` | `pip install gitmap-core` | Core library for Python integration |

Both use **PyPI Trusted Publishing** (OIDC) — no API tokens needed.

---

## One-Time Setup (do this once per package)

### 1. Create each package on PyPI

Packages must exist before trusted publishing can be configured. First release — publish manually once:

```bash
pip install build twine

# Core library
python -m build packages/gitmap_core --outdir dist/
twine upload dist/*

# Clear dist, then CLI
rm dist/*
python -m build apps/cli/gitmap --outdir dist/
twine upload dist/*
```

### 2. Configure Trusted Publishers on PyPI

For each package (`gitmap-core` and `gitmap`):

1. Go to `https://pypi.org/manage/project/<package-name>/settings/`
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

---

## Publishing a New Release

### Publish `gitmap-core` (library)

```bash
# 1. Bump version in packages/gitmap_core/pyproject.toml
# 2. Tag and push:
git tag core-v0.6.1
git push origin main --tags
```

### Publish `gitmap` (CLI)

```bash
# 1. Bump version in apps/cli/gitmap/pyproject.toml
# 2. Tag and push:
git tag v0.6.1
git push origin main --tags
```

The `publish.yml` workflow fires automatically, runs tests, builds, and pushes to PyPI.

---

## Versioning Convention

| Tag pattern | Package |
|------------|---------|
| `core-v*`  | `gitmap-core` — core library |
| `v*`       | `gitmap` — CLI tool |

Keep versions in sync between both packages for simplicity.

---

## Bumping Both at Once

```bash
# Update both pyproject.toml files to new version (e.g. 0.7.0)
# Then tag both:
git add packages/gitmap_core/pyproject.toml apps/cli/gitmap/pyproject.toml
git commit -m "chore: bump to v0.7.0"
git tag core-v0.7.0
git tag v0.7.0
git push origin main --tags
```

Both publish jobs will run in parallel on their respective tags.
