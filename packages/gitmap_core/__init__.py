"""GitMap Core Library.

Provides version control functionality for ArcGIS web maps, including
local repository management, Portal authentication, and map operations.

Execution Context:
    Library package - imported by CLI and other applications

Dependencies:
    - arcgis: Portal/AGOL interaction
    - deepdiff: JSON comparison

Metadata:
    Version: 0.3.0
    Author: GitMap Team
"""
from __future__ import annotations

from gitmap_core.context import Annotation
from gitmap_core.context import ContextStore
from gitmap_core.context import Edge
from gitmap_core.context import Event
from gitmap_core.models import Branch
from gitmap_core.models import Commit
from gitmap_core.models import Remote
from gitmap_core.models import RepoConfig
from gitmap_core.visualize import GraphData
from gitmap_core.visualize import generate_ascii_graph
from gitmap_core.visualize import generate_ascii_timeline
from gitmap_core.visualize import generate_html_visualization
from gitmap_core.visualize import generate_mermaid_flowchart
from gitmap_core.visualize import generate_mermaid_git_graph
from gitmap_core.visualize import generate_mermaid_timeline
from gitmap_core.visualize import visualize_context

__version__ = "0.4.0"

__all__ = [
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
    "generate_ascii_graph",
    "generate_ascii_timeline",
    "generate_html_visualization",
    "generate_mermaid_flowchart",
    "generate_mermaid_git_graph",
    "generate_mermaid_timeline",
    "visualize_context",
]


