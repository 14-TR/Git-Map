"""GitMap Core Library.

Provides version control functionality for ArcGIS web maps, including
local repository management, Portal authentication, and map operations.

Execution Context:
    Library package - imported by CLI and other applications

Dependencies:
    - arcgis: Portal/AGOL interaction
    - deepdiff: JSON comparison

Metadata:
    Version: 0.5.0
    Author: GitMap Team
"""
from __future__ import annotations

# Core data models - loaded eagerly for common use cases
from gitmap_core.context import Annotation, ContextStore, Edge, Event
from gitmap_core.models import Branch, Commit, Remote, RepoConfig
from gitmap_core.visualize import GraphData

__version__ = "0.5.0"

# Public API - core data models loaded eagerly
__all__ = [
    # Core data models (eager load for common access patterns)
    "Annotation",
    "Branch",
    "Commit",
    "ContextStore",
    "Edge",
    "Event",
    "GraphData",
    "Remote",
    "RepoConfig",
    "__version__",
    # Visualization functions (lazy loaded - optional utilities)
    "generate_ascii_graph",
    "generate_ascii_timeline",
    "generate_html_visualization",
    "generate_mermaid_flowchart",
    "generate_mermaid_git_graph",
    "generate_mermaid_timeline",
    "visualize_context",
]


# ---- Lazy Import Functions ----------------------------------------------------------------------------------
# These are loaded on-demand to reduce initial import time and memory footprint.
# Only imported when actually called, avoiding unnecessary dependencies.


def generate_ascii_graph(*args, **kwargs):
    """Generate ASCII representation of commit graph (lazy import)."""
    from gitmap_core.visualize import generate_ascii_graph as _func
    return _func(*args, **kwargs)


def generate_ascii_timeline(*args, **kwargs):
    """Generate ASCII timeline visualization (lazy import)."""
    from gitmap_core.visualize import generate_ascii_timeline as _func
    return _func(*args, **kwargs)


def generate_html_visualization(*args, **kwargs):
    """Generate HTML visualization (lazy import)."""
    from gitmap_core.visualize import generate_html_visualization as _func
    return _func(*args, **kwargs)


def generate_mermaid_flowchart(*args, **kwargs):
    """Generate Mermaid flowchart (lazy import)."""
    from gitmap_core.visualize import generate_mermaid_flowchart as _func
    return _func(*args, **kwargs)


def generate_mermaid_git_graph(*args, **kwargs):
    """Generate Mermaid git graph (lazy import)."""
    from gitmap_core.visualize import generate_mermaid_git_graph as _func
    return _func(*args, **kwargs)


def generate_mermaid_timeline(*args, **kwargs):
    """Generate Mermaid timeline (lazy import)."""
    from gitmap_core.visualize import generate_mermaid_timeline as _func
    return _func(*args, **kwargs)


def visualize_context(*args, **kwargs):
    """Visualize context graph (lazy import)."""
    from gitmap_core.visualize import visualize_context as _func
    return _func(*args, **kwargs)
