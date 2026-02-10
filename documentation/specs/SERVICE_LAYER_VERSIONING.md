# Feature: Service Layer Versioning

## Problem

GitMap currently versions web map JSON, but many organizations define symbology (renderers, labels, popups) at the **feature service** level rather than overriding in web maps. This means symbology changes aren't captured in GitMap commits.

## Solution

Extend GitMap to pull and version feature layer definitions alongside web map JSON.

## Scope

### What to Capture

For each `operationalLayer` with a feature service URL:
- `drawingInfo` (renderer, transparency, labelingInfo)
- `templates` (editing templates)
- `typeIdField` + `types` (subtypes with per-type symbology)
- `fields` schema (field definitions, domains)
- `popupInfo` at service level (if different from web map)

### Storage Structure

```
.gitmap/
├── index.json              # web map JSON (existing)
├── layers/                 # NEW: service layer definitions
│   ├── {layerId}.json      # full layer definition
│   └── ...
└── objects/                # existing commit objects
```

### Commands

- `gitmap pull --include-layers` — fetch layer definitions with web map
- `gitmap diff --layers` — show layer-level changes (symbology, fields)
- `gitmap push --layers` — push layer definition changes back to service (requires edit permissions)

### API Endpoints

Feature Server REST API:
- `GET {serviceUrl}/{layerId}?f=json` — layer definition
- `POST {serviceUrl}/{layerId}/updateDefinition` — push changes (admin)

## Implementation Phases

### Phase 1: Read-Only Capture
- [ ] Extract layer URLs from operationalLayers
- [ ] Fetch layer definitions on `pull`
- [ ] Store in `.gitmap/layers/`
- [ ] Include in commit snapshots
- [ ] Basic diff output for layer changes

### Phase 2: Smart Diffing
- [ ] Renderer-specific diff (color changes, break values)
- [ ] Symbol comparison (type, size, color)
- [ ] Label expression diff
- [ ] Field schema changes

### Phase 3: Push Support
- [ ] `updateDefinition` for symbology push
- [ ] Permission checking
- [ ] Conflict detection with service state

## Open Questions

1. How to handle layers from external services (not in same Portal)?
2. Version layer definitions per-commit or track separately?
3. Handle secured services requiring separate auth?

## Related

- Branch: `jig/feature/arcgis-version-compat` (API compatibility)
- Esri docs: https://developers.arcgis.com/rest/services-reference/enterprise/layer-feature-service/
