# Publishing to PyPI

GitMap uses **PyPI Trusted Publishing** (OIDC) — no API tokens needed once configured.

GitMap ships three packages:

| PyPI Package | Tag Pattern | Install |
|---|---|---|
| `gitmap-core` | `core-v*` | `pip install gitmap-core` |
| `gitmap-cli` | `cli-v*` | `pip install gitmap-cli` |
| `gitmap` (meta) | `v*` | `pip install gitmap` |

> **Most users want `pip install gitmap`** — it installs both core and CLI automatically.

---

## One-Time Setup

### 1. Build and upload each package manually (first time only)

```bash
pip install build twine

# Core library
python -m build packages/gitmap_core --outdir dist/
twine upload dist/gitmap_core-*

# CLI
python -m build apps/cli/gitmap --outdir dist/
twine upload dist/gitmap_cli-*

# Meta-package
python -m build . --outdir dist/
twine upload dist/gitmap-*
```

### 2. Configure Trusted Publishers on PyPI

Do this for **each** of the three packages after they exist on PyPI:

1. Go to `https://pypi.org/manage/project/<package-name>/settings/`
2. Click **"Add a new publisher"** under "Trusted Publishers"
3. Fill in:
   - **Owner:** `14-TR`
   - **Repository:** `Git-Map`
   - **Workflow:** `publish.yml`
   - **Environment:** `pypi`

Packages to configure:
- `https://pypi.org/manage/project/gitmap-core/settings/`
- `https://pypi.org/manage/project/gitmap-cli/settings/`
- `https://pypi.org/manage/project/gitmap/settings/`

### 3. Create the GitHub `pypi` Environment

1. Go to `https://github.com/14-TR/Git-Map/settings/environments`
2. Create environment named **`pypi`**
3. (Optional) Add "Required reviewers" for extra safety

---

## Publishing a New Release

Before tagging, run the local release guardrail:

```bash
python3 scripts/release_checks.py
```

This verifies that the published package versions, dependency pins, project metadata, and publish workflow tag patterns are still aligned.

### Patch release (core fix)

```bash
# Bump version in packages/gitmap_core/pyproject.toml
git add packages/gitmap_core/pyproject.toml
git commit -m "chore: bump core to v0.6.1"
git tag core-v0.6.1
git push origin main --tags
```

### Patch release (CLI fix)

```bash
# Bump version in apps/cli/gitmap/pyproject.toml and main.py
git add apps/cli/gitmap/pyproject.toml apps/cli/gitmap/main.py
git commit -m "chore: bump cli to v0.6.1"
git tag cli-v0.6.1
git push origin main --tags
```

### Full release (all packages)

```bash
# 1. Bump versions in all three pyproject.toml files + main.py
# 2. Commit
git add packages/gitmap_core/pyproject.toml \
        apps/cli/gitmap/pyproject.toml \
        apps/cli/gitmap/main.py \
        pyproject.toml
git commit -m "chore: release v0.7.0"

# 3. Tag all three — publish.yml fires for each
git tag core-v0.7.0
git tag cli-v0.7.0
git tag v0.7.0
git push origin main --tags
```

---

## Versioning Convention

All three packages should stay in sync (same version number).

| Component | File to update |
|---|---|
| `gitmap-core` | `packages/gitmap_core/pyproject.toml` |
| `gitmap-cli` | `apps/cli/gitmap/pyproject.toml` + `apps/cli/gitmap/main.py` |
| `gitmap` meta | `pyproject.toml` (root) |

---

## Verify on PyPI

After tags are pushed and workflow runs succeed:

```bash
pip install gitmap           # meta-package (installs core + cli)
pip install gitmap-core      # core library only
pip install gitmap-cli       # CLI only (also installs core)
gitmap --version             # should show new version
```
