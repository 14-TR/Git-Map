# CLAUDE.md - GitMap Project Guide

This document is the primary reference for AI assistants (Claude Code, Cursor, etc.) working on the GitMap project.

## Project Overview

**GitMap** provides Git-like version control for ArcGIS Online and Enterprise Portal web maps. Branch, commit, diff, merge, push, and pull maps using familiar workflows.

### Monorepo Structure

```
GitMap/
├── apps/                    # Runnable applications
│   ├── cli/gitmap/          # CLI application
│   ├── client/              # Client applications
│   │   ├── gitmap-client/   # TUI client (Textual)
│   │   └── gitmap-gui/      # Web GUI (Flask)
│   └── mcp/gitmap-mcp/      # MCP server
├── packages/                # First-party libraries
│   └── gitmap_core/         # Core library
├── configs/                 # Configuration templates
├── docker/                  # Docker configuration
└── documentation/           # Specifications and docs
    └── project_specs/       # Detailed specifications
```

### Key Applications

- **gitmap CLI**: Git-like commands for web map version control
- **gitmap-gui**: Flask-based web interface for visual management
- **gitmap-client**: Terminal UI client using Textual framework
- **gitmap-mcp**: MCP server for IDE integration

---

## Quick Start Commands

```bash
# Install core library
pip install -e packages/gitmap_core

# Install CLI
pip install -e apps/cli/gitmap

# Run GUI
cd apps/client/gitmap-gui && python -m gitmap_gui

# Run TUI client
cd apps/client/gitmap-client && python -m gitmap_client
```

---

## Protocol System

Before responding to requests, consult `documentation/nav_spec.md` to identify the correct specification. Available protocols:

| Protocol | Command Phrases | Governing Spec |
|----------|-----------------|----------------|
| `protocols.list` | "list protocols", "what can you do" | protocols_spec.md |
| `apps.generate_template` | "generate app template", "create app" | apps_folder_spec.md |
| `apps.add_feature` | "add feature to app", "implement feature" | apps_add_feature_spec.md |
| `audit.perform` | "audit code", "perform audit" | audit_spec.md |
| `spec.generate` | "generate spec", "create spec" | spec_template.md |
| `release.guide` | "release guide", "create release" | cut_release_spec.md |

### Checklist Gate (Mandatory)

When a governing spec defines a Prompt Checklist:
1. Collect checklist answers one-by-one
2. Echo back a summary for confirmation
3. **Block ALL edits** until engineer confirms
4. Store captured answers in session task list

---

## Python Standards

### Version & Style

- **Python**: 3.11+
- **Formatting**: PEP 8
- **Docstrings**: PEP 257 (Google-style)
- **Path Handling**: Always use `pathlib.Path`
- **Type Hints**: Required for all functions

### Required Import

```python
from __future__ import annotations
```

### Import Order

1. Standard library imports
2. Third-party library imports
3. Local module imports

### Function Formatting

```python
# ---- Helper Functions -----------------------------------------------------------------------

def example_function(
        param_1: str,
        param_2: int,
        param_3: Optional[str] = None,
) -> bool:
    """
    One-line purpose sentence.

    Args:
        param_1: Description of param_1.
        param_2: Description of param_2.
        param_3: Description of param_3.

    Returns:
        bool: Description of return value.

    Raises:
        ValueError: When validation fails.
    """
    return True
```

### Exception Handling

```python
try:
    result = some_operation()
except SpecificError as specific_error:
    msg = f"Failed to perform operation: {specific_error}"
    raise RuntimeError(msg) from specific_error
except Exception as general_error:
    msg = f"Unexpected error during operation: {general_error}"
    raise RuntimeError(msg) from general_error
```

**Rules**:
- Error alias: `snake_case` of exception + `_error`
- Message variable: `msg`
- Always use f-strings (no `.format()` or `%` formatting)
- Always chain exceptions with `from`

---

## App Structure

### Directory Layout (Required)

```
apps/[app_group]/[app]/
├── docs/
│   └── [app_name]_spec.md
├── configs/
│   └── [app_name]_config.json
├── scripts/           # Core implementation
├── main.py            # Orchestrator entrypoint
└── runner.py          # Optional; overrides orchestrator
```

### Module Docstring Template

```python
"""
One-line summary.

Extended description paragraph(s).

Key Features:
    - Feature 1
    - Feature 2

Dependencies:
    - dependency 1
    - dependency 2

Metadata:
    Author: Name
    Version: 1.0
"""
```

---

## Code Quality Checks

### Must-Have

- [ ] PEP 8 compliance
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions/classes/modules
- [ ] No hardcoded credentials
- [ ] pathlib.Path for file operations
- [ ] Proper exception handling with chaining
- [ ] Main guard: `if __name__ == '__main__'`

### Avoid

- [ ] Bare `except:` clauses
- [ ] String concatenation for error messages
- [ ] Relative imports in apps
- [ ] Deep imports from packages (use public API)
- [ ] Unnecessary external dependencies

---

## Branching Model

### Branch Types

| Prefix | Purpose |
|--------|---------|
| `feature/` | New functionality |
| `bugfix/` | Non-urgent fixes |
| `hotfix/` | Urgent production fixes |
| `release/` | Release preparation |
| `chore/` | Maintenance, dependencies |
| `refactor/` | Code restructuring |
| `docs/` | Documentation updates |

### Naming Convention

- Child: `[developer]/[type]/[description]`
- Example: `jdoe/feature/add-layer-merge`

---

## Task Management

Maintain lightweight progress visibility:
- Provide 1-3 sentence status updates before major actions
- Maintain a concise task list for active goals
- Update task statuses as work progresses
- Confirm completion and summarize changes

---

## Tool Output Formatting

When a tool returns formatted output (e.g., `table`, `formatted_output`):
- Use the tool's format directly
- Do not reformat or restructure the output
- Preserve the tool's intent

---

## Key Specifications Reference

| Topic | Specification File |
|-------|-------------------|
| Agent Behavior | `00-governance/ide_agent.md` |
| Documentation | `00-governance/docs_spec.md` |
| Formatting | `00-governance/formatting_spec.md` |
| Protocols | `00-governance/protocols_spec.md` |
| Code Audit | `00-governance/audit_spec.md` |
| Architecture | `10-architecture/architecture_spec.md` |
| Python Standards | `10-architecture/repo_spec.md` |
| App Structure | `30-apps/apps_folder_spec.md` |
| Add Features | `30-apps/apps_add_feature_spec.md` |
| ArcGIS API | `30-apps/arcgis_api_mapping.md` |

All specifications are in `documentation/project_specs/`.

---

## ArcGIS Integration

GitMap works with ArcGIS Portal and ArcGIS Online. Authentication:

```bash
# Environment variables
PORTAL_URL=https://your-org.maps.arcgis.com
PORTAL_USER=your_username
PORTAL_PASSWORD=your_password
```

Key CLI commands:
- `gitmap clone <item_id>` - Clone web map from Portal
- `gitmap push` - Push changes to Portal
- `gitmap pull` - Pull changes from Portal
- `gitmap lsm` - Layer settings merge (popup/form transfer)
- `gitmap list` - List available web maps
- `gitmap context` - Visualize event history

---

## Error Response Protocol

1. Handle errors gracefully without losing context
2. Explain issues clearly with actionable solutions
3. Guide users through resolution steps
4. Never expose sensitive information in error messages

---

## Performance Guidelines

- Profile before optimizing
- Focus on algorithmic complexity first
- Use generators for large datasets
- Minimize I/O operations
- Use context managers for resource cleanup
- Cache expensive computations

---

## Git Commit Standards

When creating commits:
1. Run `git status` and `git diff` first
2. Summarize the nature of changes
3. Draft concise 1-2 sentence message focusing on "why"
4. Never commit secrets or credentials
5. End commit message with session link when applicable

---

## Links

- [Main README](README.md)
- [Release Notes](documentation/project_specs/20-operations/release_notes.md)
- [CLI Docs](apps/cli/gitmap/docs/gitmap_spec.md)
- [MCP Docs](apps/mcp/gitmap-mcp/docs/gitmap_mcp_spec.md)
