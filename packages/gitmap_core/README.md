# GitMap Core

Core library for GitMap - Version control for ArcGIS web maps.

## Installation

```bash
pip install -e .
```

## Modules

- **models.py** - Data classes for Commit, Branch, Remote, RepoConfig
- **repository.py** - Local `.gitmap` repository management
- **connection.py** - Portal/AGOL authentication
- **maps.py** - Web map JSON operations
- **diff.py** - JSON comparison and layer diffing
- **merge.py** - Layer-level merge logic
- **remote.py** - Push/pull operations to Portal
- **communication.py** - Portal/AGOL user notifications and group helpers
- **compat.py** - ArcGIS API version compatibility layer (2.2.x-2.4.x)
- **context.py** - SQLite-backed context/event store for IDE agents
- **visualize.py** - Mermaid, ASCII, and HTML visualization of context graphs

## Usage

```python
from gitmap_core import Commit, Branch, RepoConfig
from gitmap_core.repository import Repository, init_repository

# Initialize a new repository
repo = init_repository("/path/to/project")

# Create a commit
commit = repo.create_commit(message="Initial commit", author="John")

# List branches
branches = repo.list_branches()
```

## Dependencies

- `arcgis>=2.2.0,<3.0.0` - ArcGIS API for Python
- `deepdiff>=6.0.0` - JSON comparison


