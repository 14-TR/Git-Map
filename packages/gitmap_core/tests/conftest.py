"""Shared test configuration and fixtures for gitmap_core tests.

Provides:
- arcgis mock: installs a lightweight MagicMock for the ``arcgis`` package into
  ``sys.modules`` so tests can run without an ESRI license or the real SDK.
- Common fixtures reused across test modules.

Notes:
    This file is loaded by pytest *before* any test modules in this directory
    are imported, so the sys.modules patching takes effect before
    ``gitmap_core.communication`` (and other modules) try to do
    ``from arcgis.gis import GIS``.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Install arcgis stub into sys.modules
# ---------------------------------------------------------------------------
# arcgis requires an ESRI license and cannot be installed via pip in standard
# CI or developer environments.  Rather than skipping all tests, we register
# lightweight MagicMock objects for the sub-modules that gitmap_core imports.
# Tests that need specific behaviour can refine these mocks with ``patch``.

def _install_arcgis_mock() -> None:
    """Add arcgis stub modules to sys.modules if not already present."""
    if "arcgis" in sys.modules and not isinstance(sys.modules["arcgis"], MagicMock):
        # Real arcgis is installed – nothing to do.
        return

    arcgis_stub = MagicMock()
    arcgis_stub.__version__ = "2.4.0"
    arcgis_stub.__name__ = "arcgis"

    # arcgis.gis sub-module (GIS, Item …)
    arcgis_gis_stub = MagicMock()
    arcgis_gis_stub.__name__ = "arcgis.gis"

    sys.modules.setdefault("arcgis", arcgis_stub)
    sys.modules.setdefault("arcgis.gis", arcgis_gis_stub)

    # Also wire the gis attribute so ``import arcgis; arcgis.gis`` works.
    arcgis_stub.gis = arcgis_gis_stub


_install_arcgis_mock()


# ---------------------------------------------------------------------------
# Patch module-level sentinels that were already imported as None
# ---------------------------------------------------------------------------
# If gitmap_core.communication was imported before conftest ran (e.g. via an
# earlier conftest or plugin), its module-level ``GIS`` sentinel may still be
# ``None``.  Fix that up so tests see a truthy sentinel by default.

def _fix_already_imported_sentinels() -> None:
    comm_key = "gitmap_core.communication"
    if comm_key in sys.modules:
        mod = sys.modules[comm_key]
        if getattr(mod, "GIS", None) is None:
            mod.GIS = sys.modules["arcgis.gis"].GIS  # type: ignore[attr-defined]


_fix_already_imported_sentinels()


# ---------------------------------------------------------------------------
# Gracefully skip test_diff.py when deepdiff/numpy are unavailable
# ---------------------------------------------------------------------------
# deepdiff depends on numpy.  On some platforms (e.g. Python 3.14 with a
# broken numpy wheel) importing deepdiff raises AttributeError before any
# test runs, causing pytest collection to abort entirely.  We register the
# file in ``collect_ignore`` so the rest of the suite still runs cleanly.

collect_ignore: list[str] = []

try:
    from deepdiff import DeepDiff  # noqa: F401
except Exception:
    collect_ignore.append("test_diff.py")
