"""Global configuration and state management for GitMap GUI."""
from pathlib import Path
from typing import Optional

# Global repository reference
repo: Optional[object] = None
repo_path: Optional[Path] = None
repositories_dir: Optional[Path] = None

# Global portal connection (session-scoped)
portal_connection: Optional[object] = None
portal_gis: Optional[object] = None

# Global merge state for multi-step merge operations
merge_state: Optional[dict] = None
