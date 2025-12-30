# ArcGIS API for Python Functionality Mapping

## Overview

**Purpose**: Map GitMap project functionality and patterns to the corresponding ArcGIS API for Python modules and tools, enabling developers to implement GIS workflows following repository standards.

**Scope**: Core ArcGIS API for Python modules, common operations, and their alignment with GitMap's app architecture.

**Version**: 1.0

## Module Index

The ArcGIS API for Python is organized into modules. This mapping identifies which modules support specific project workflows.

| Module | Primary Use Case | GitMap App Group |
|--------|-----------------|------------------|
| `arcgis.gis` | Portal connection, authentication, content management | `apps/portal/` |
| `arcgis.features` | Feature layers, editing, spatial queries | `apps/arcgis/` |
| `arcgis.mapping` | Web maps, web scenes, layer management | `apps/arcgis/` |
| `arcgis.raster` | Imagery and raster analysis | `apps/arcgis/` |
| `arcgis.network` | Routing, service areas, network analysis | `apps/arcgis/` |
| `arcgis.geoanalytics` | Big data distributed analysis | `apps/arcgis/` |
| `arcgis.geoenrichment` | Demographic and location data enrichment | `apps/arcgis/` |
| `arcgis.geocoding` | Address matching, reverse geocoding | `apps/arcgis/` |

---

## Functionality Mapping

### 1. Portal & GIS Management (`arcgis.gis`)

**Module**: `arcgis.gis.GIS`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Connect to Portal/AGOL | `GIS(url, username, password)` | `apps/portal/connect/` |
| Search content | `gis.content.search()` | `apps/portal/content_search/` |
| Get user info | `gis.users.get()` | `apps/portal/user_management/` |
| List groups | `gis.groups.search()` | `apps/portal/group_management/` |
| Manage items | `gis.content.add()`, `item.update()`, `item.delete()` | `apps/portal/item_management/` |

**Integration Pattern**:
```python
from arcgis.gis import GIS

def connect_to_portal(
        portal_url: str,
        username: str,
        password: str,
) -> GIS:
    """
    Establish connection to ArcGIS Portal or ArcGIS Online.
    
    Args:
        portal_url: Portal URL (e.g., https://org.maps.arcgis.com)
        username: Portal username
        password: Portal password
        
    Returns:
        GIS: Authenticated GIS connection object
    """
    try:
        gis = GIS(portal_url, username, password)
        return gis
    except Exception as connection_error:
        msg = f"Failed to connect to portal {portal_url}: {connection_error}"
        raise RuntimeError(msg) from connection_error
```

---

### 2. Content Management (`arcgis.gis.ContentManager`)

**Module**: `arcgis.gis.ContentManager`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Search items | `content.search(query, item_type)` | `apps/portal/content_search/` |
| Add item | `content.add(item_properties, data)` | `apps/portal/publishing/` |
| Clone items | `content.clone_items()` | `apps/portal/content_migration/` |
| Bulk operations | `content.bulk_update()` | `apps/portal/content_admin/` |

**Suggested App Structure**:
```
apps/
  portal/
    content_manager/
      docs/
        content_manager_spec.md
      configs/
        content_manager_config.json
      scripts/
        search_operations.py
        crud_operations.py
        migration_operations.py
      main.py
```

---

### 3. User & Group Administration (`arcgis.gis.UserManager`, `arcgis.gis.GroupManager`)

**Module**: `arcgis.gis.UserManager`, `arcgis.gis.GroupManager`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Create user | `users.create()` | `apps/portal/user_provisioning/` |
| Update user | `user.update()` | `apps/portal/user_management/` |
| Assign roles | `user.update(role)` | `apps/portal/role_management/` |
| Create group | `groups.create()` | `apps/portal/group_management/` |
| Manage membership | `group.add_users()`, `group.remove_users()` | `apps/portal/group_management/` |
| Share items | `item.share(groups)` | `apps/portal/sharing_manager/` |

---

### 4. Feature Layer Operations (`arcgis.features`)

**Module**: `arcgis.features.FeatureLayer`, `arcgis.features.FeatureLayerCollection`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Query features | `layer.query()` | `apps/arcgis/feature_query/` |
| Edit features | `layer.edit_features()` | `apps/arcgis/feature_editor/` |
| Append data | `layer.append()` | `apps/arcgis/data_loader/` |
| Truncate & load | `layer.manager.truncate()` | `apps/arcgis/data_loader/` |
| Calculate fields | `layer.calculate()` | `apps/arcgis/field_calculator/` |

**Integration Pattern**:
```python
from arcgis.features import FeatureLayer

def query_features(
        layer_url: str,
        where_clause: str = "1=1",
        out_fields: list[str] | None = None,
) -> list[dict]:
    """
    Query features from a feature layer.
    
    Args:
        layer_url: Feature layer REST endpoint URL
        where_clause: SQL where clause for filtering
        out_fields: List of fields to return
        
    Returns:
        list[dict]: List of feature dictionaries
    """
    try:
        layer = FeatureLayer(layer_url)
        result = layer.query(
            where=where_clause,
            out_fields=out_fields or ["*"],
            return_geometry=True,
        )
        return [f.as_dict for f in result.features]
    except Exception as query_error:
        msg = f"Failed to query features from {layer_url}: {query_error}"
        raise RuntimeError(msg) from query_error
```

---

### 5. Publishing & Service Management

**Module**: `arcgis.gis.Item`, `arcgis.features.FeatureLayerCollection`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Publish from file | `item.publish()` | `apps/arcgis/publishing/` |
| Overwrite service | `flc.manager.overwrite()` | `apps/arcgis/service_update/` |
| Update service definition | `item.update()` | `apps/arcgis/service_admin/` |
| Enable editing | `flc.manager.update_definition()` | `apps/arcgis/service_admin/` |

---

### 6. Web Maps & Applications (`arcgis.mapping`)

**Module**: `arcgis.mapping.WebMap`, `arcgis.mapping.WebScene`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Create web map | `WebMap()` | `apps/arcgis/webmap_builder/` |
| Add layers | `webmap.add_layer()` | `apps/arcgis/webmap_builder/` |
| Configure popups | `layer.popupInfo` | `apps/arcgis/webmap_config/` |
| Export to image | `webmap.export_to_image()` | `apps/arcgis/map_export/` |

---

### 7. Geoprocessing & Analysis

**Module**: `arcgis.geoprocessing`, `arcgis.features.analysis`

| Functionality | ArcGIS API Method | Example App |
|--------------|-------------------|-------------|
| Buffer | `analysis.create_buffers()` | `apps/arcgis/spatial_analysis/` |
| Overlay | `analysis.overlay_layers()` | `apps/arcgis/spatial_analysis/` |
| Summarize | `analysis.summarize_within()` | `apps/arcgis/spatial_analysis/` |
| Custom GP | `geoprocessing.import_toolbox()` | `apps/arcgis/geoprocessing/` |

---

## Recommended App Group Structure

Based on the functionality mapping, here is the recommended folder organization:

```
apps/
  portal/                           # Portal/AGOL administration
    connection/                     # Authentication & connection management
    content_manager/                # Content CRUD operations
    user_management/                # User provisioning & administration
    group_management/               # Group lifecycle management
    sharing_manager/                # Item sharing & permissions
    content_migration/              # Cross-portal content migration
    
  arcgis/                           # Feature/spatial operations
    feature_query/                  # Feature layer queries
    feature_editor/                 # Feature editing workflows
    data_loader/                    # Bulk data loading (append/truncate)
    publishing/                     # Service publishing workflows
    service_admin/                  # Service definition management
    spatial_analysis/               # Analysis operations
    webmap_builder/                 # Web map creation/configuration
    
  analysis/                          # Hosted analysis operations
    spatial_tools/                  # Buffer, overlay, summarize
    geocoding/                      # Address matching workflows
    routing/                        # Network analysis
```

---

## Configuration Strategy

Each app should use JSON configuration under `configs/`:

```json
{
  "portal": {
    "url": "https://org.maps.arcgis.com",
    "auth_method": "builtin"
  },
  "target_items": {
    "item_types": ["Feature Service", "Web Map"],
    "owner_filter": null
  },
  "operation": {
    "dry_run": true,
    "batch_size": 100,
    "timeout_seconds": 300
  }
}
```

---

## Environment Requirements (Docker-Only)

**All development and execution happens in Docker containers. No local Python installation required.**

---

### Project Docker Setup

**Base Dockerfile** (`docker/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ArcGIS API for Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "main.py"]
```

**requirements.txt**:
```
arcgis>=2.3.0
python-dotenv>=1.0.0
```

---

### Docker Compose (Recommended)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # Development shell - interactive development
  dev:
    build:
      context: .
      dockerfile: docker/Dockerfile
    volumes:
      - .:/app
      - arcgis-cache:/root/.cache
    env_file:
      - .env
    stdin_open: true
    tty: true
    command: /bin/bash

  # Run a specific app
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    volumes:
      - ./apps:/app/apps
      - ./configs:/app/configs
      - ./data:/app/data
    env_file:
      - .env
    command: python apps/${APP_GROUP}/${APP_NAME}/main.py

  # Jupyter notebook for exploration
  notebook:
    image: ghcr.io/esri/arcgis-python-api-notebook
    ports:
      - "8888:8888"
    volumes:
      - .:/home/jovyan/work
    env_file:
      - .env

volumes:
  arcgis-cache:
```

**.env** (git-ignored):
```bash
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

---

### Development Workflow

**Start interactive dev shell**:
```bash
docker compose run --rm dev
```

**Run a specific app**:
```bash
APP_GROUP=portal APP_NAME=content_manager docker compose run --rm app
```

**Launch Jupyter for exploration**:
```bash
docker compose up notebook
# Open http://localhost:8888 in browser
```

**Run tests**:
```bash
docker compose run --rm dev pytest
```

**One-off script execution**:
```bash
docker compose run --rm dev python apps/portal/content_manager/main.py
```

---

### VS Code / Cursor Dev Container (Optional)

For IDE integration, add `.devcontainer/devcontainer.json`:
```json
{
  "name": "GitMap ArcGIS",
  "dockerComposeFile": ["../docker-compose.yml"],
  "service": "dev",
  "workspaceFolder": "/app",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  }
}
```

This allows Cursor to develop directly inside the container.

---

### Available Functionality (Docker)

| ✅ Works in Docker | ❌ Not Available |
|--------------------|------------------|
| Portal/AGOL connection & auth | `arcpy` module |
| Content management (CRUD) | Local geodatabases (.gdb) |
| User/Group administration | Desktop geoprocessing tools |
| Feature layer queries & edits | .aprx project files |
| Hosted service publishing | |
| Web maps & web scenes | |
| Hosted spatial analysis | |
| Geocoding & routing services | |

---

## References

- [ArcGIS API for Python Guide](https://developers.arcgis.com/python/latest/guide/)
- [ArcGIS API Docker Setup](https://developers.arcgis.com/python/latest/guide/install-and-set-up/docker/)
- [Apps Folder Specification](./apps_folder_spec.md)
- [Repository Specification](../10-architecture/repo_spec.md)
- [Architecture Specification](../10-architecture/architecture_spec.md)

