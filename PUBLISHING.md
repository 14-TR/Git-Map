# Publishing to PyPI

GitMap uses **PyPI Trusted Publishing** (OIDC) — no API tokens needed once configured.

GitMap currently publishes two user-facing packages. The root `gitmap` PyPI name is occupied by an unrelated project, so it is not part of the active publish contract unless that name is transferred or explicitly re-approved.

| PyPI Package | Tag Pattern | Install |
|---|---|---|
| `gitmap-core` | `core-v*` | `pip install gitmap-core` |
| `gitmap-cli` | `cli-v*` | `pip install gitmap-cli` |

> **Most users want `pip install gitmap-cli`** — it installs the `gitmap` console command and depends on `gitmap-core`. Use `pip install gitmap-core` only for library/API use.

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

# Do not build/upload the root gitmap meta-package while the PyPI name is unavailable.
```

### 2. Configure Trusted Publishers on PyPI

Do this for **each** active package after it exists on PyPI:

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

### 3. Create the GitHub `pypi` Environment

1. Go to `https://github.com/14-TR/Git-Map/settings/environments`
2. Create environment named **`pypi`**
3. (Optional) Add "Required reviewers" for extra safety

---

## Publishing a New Release

Before tagging, run the local release guardrails:

```bash
python3 scripts/release_checks.py
python3 -m build packages/gitmap_core --outdir dist/
python3 -m build apps/cli/gitmap --outdir dist/
python3 scripts/verify_dist_install.py core
python3 scripts/verify_dist_install.py cli
```

This verifies that the published package versions, dependency pins, project metadata, publish workflow tag patterns, and dist-install smoke tests are still aligned.
The publish workflow now runs the same clean-venv install smoke test for `core` and `cli` before uploading artifacts to PyPI.

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

### Full release (core + CLI)

```bash
# 1. Bump versions in the core/CLI pyproject.toml files + main.py
# 2. Commit
git add packages/gitmap_core/pyproject.toml \
        apps/cli/gitmap/pyproject.toml \
        apps/cli/gitmap/main.py
git commit -m "chore: release v0.7.0"

# 3. Tag both active packages — publish.yml fires for each
git tag core-v0.7.0
git tag cli-v0.7.0
git push origin main --tags
```

---

## Versioning Convention

The active publishable packages should stay in sync (same version number).

| Component | File to update |
|---|---|
| `gitmap-core` | `packages/gitmap_core/pyproject.toml` |
| `gitmap-cli` | `apps/cli/gitmap/pyproject.toml` + `apps/cli/gitmap/main.py` |

---

## Verify on PyPI

After tags are pushed and workflow runs succeed:

```bash
pip install gitmap-cli       # CLI (installs the gitmap command and core dependency)
pip install gitmap-core      # core library only
gitmap --version             # should show new version
```
