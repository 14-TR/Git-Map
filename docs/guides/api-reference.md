# Python API Reference

Git-Map's core library (`gitmap-core`) can be used as a Python library in your own scripts and applications.

## Installation

```bash
pip install gitmap-core
```

## Repository Operations

```python
from gitmap_core.repository import Repository

# Initialize a new repository
repo = Repository("/path/to/project")
repo.init(project_name="My Map", user_name="Jane Smith")

# Check status
print(repo.get_current_branch())  # "main"
print(repo.has_uncommitted_changes())  # True/False
```

## Creating Commits

```python
# Stage and commit
commit = repo.create_commit(
    message="Added hydrology layer",
    author="Jane Smith"
)
print(f"Created commit {commit.id}")
```

## Branch Operations

```python
# Create and switch branches
repo.create_branch("feature/new-layer")
repo.checkout_branch("feature/new-layer")

# List branches
branches = repo.list_branches()  # ["main", "feature/new-layer"]
```

## Diffing Maps

```python
from gitmap_core.diff import diff_maps, format_diff_summary

commit_a = repo.get_commit("abc123")
commit_b = repo.get_commit("def456")

diff = diff_maps(commit_a.map_data, commit_b.map_data)
print(format_diff_summary(diff))
```

## Merging

```python
from gitmap_core.merge import merge_maps

result = merge_maps(
    ours=our_map_data,
    theirs=their_map_data,
    base=base_map_data
)

if result.conflicts:
    print(f"{len(result.conflicts)} conflicts found")
else:
    print("Clean merge!")
```

## Portal Connection

```python
from gitmap_core.connection import PortalConnection

conn = PortalConnection()
conn.connect(
    url="https://your-org.maps.arcgis.com",
    username="user",
    password="pass"
)
```

## Context Store

```python
# Access the event history
with repo.get_context_store() as store:
    timeline = store.get_timeline(limit=20)
    for event in timeline:
        print(f"{event['timestamp']} — {event['event_type']}: {event['ref']}")
```

---

For the full API surface, see the [Technical Paper](../technical-paper.md) (§4.1).
