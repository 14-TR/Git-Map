"""GitMap Core Library.

Provides version control functionality for ArcGIS web maps, including
local repository management, Portal authentication, and map operations.

Execution Context:
    Library package - imported by CLI and other applications

Dependencies:
    - arcgis: Portal/AGOL interaction
    - deepdiff: JSON comparison

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

from gitmap_core.models import Branch
from gitmap_core.models import Commit
from gitmap_core.models import Remote
from gitmap_core.models import RepoConfig

__version__ = "0.1.0"

__all__ = [
    "Branch",
    "Commit",
    "Remote",
    "RepoConfig",
    "__version__",
]


