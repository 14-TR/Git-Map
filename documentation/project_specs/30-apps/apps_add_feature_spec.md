# Apps Add Feature Specification

## Overview

**Purpose**: Define the protocol for adding new features to existing applications under `apps/[app_group]/[app]` while maintaining repository standards and app structure.

**Scope**: Applies to all existing applications inside `apps/` at the most granular level: `apps/[app_group]/[app]`. This protocol guides the IDE agent in extending existing apps with new functionality.

**Version**: 1.0

## Feature Addition Protocol

**Protocol Name**: Add Feature to App

**Process**:
1. Engineer issues: "add feature to app" or "add new feature" and specifies target app `apps/[app_group]/[app]`.
2. IDE agent validates that the target app exists and has the required structure (`main.py`, `docs/`, `scripts/`, etc.).
3. IDE agent prompts the engineer for must-have information (see Prompt Checklist) and echoes back a summary.
4. HARD GATE: No file or directory edits may occur until the engineer confirms the summary.
5. IDE agent reviews existing app structure:
   - Reads `docs/[app_name]_spec.md` to understand app purpose and architecture
   - Reviews `main.py` and `runner.py` to understand orchestration flow
   - Examines `scripts/` directory to identify integration points
   - Reviews `configs/[app_name]_config.json` to understand configuration structure
6. IDE agent determines file structure:
   - New standalone feature → create new file in `scripts/`
   - Extension of existing feature → modify existing file
   - New orchestration logic → update `main.py` or `runner.py`
7. IDE agent creates/modifies files following repository standards.
8. IDE agent updates `docs/[app_name]_spec.md` to document the new feature.
9. IDE agent updates `configs/[app_name]_config.json` if configuration is needed.

## Prompt Checklist (IDE Agent → Engineer)

The agent MUST ask for and record the following one at a time before generation:
- Target app path (`apps/[app_group]/[app]`).
- Feature name and brief description.
- Feature purpose and how it fits into the existing app.
- Inputs and outputs for the new feature (data sources, files, services, return values).
- Where the feature should be added:
  - New script file in `scripts/`
  - Extend existing script
  - New module/package
  - Update orchestration (`main.py`/`runner.py`)
- Dependencies (internal `packages/`, external libs).
- Configuration requirements (new config entries, env vars, config file updates).
- Testing requirements (unit tests, integration tests).
- Integration points with existing app code (which functions/modules will interact with this feature).

## File Structure Decisions

### New Standalone Feature
- Create new file in `scripts/[feature_name].py`
- Add import and call in `main.py` or appropriate orchestration point

### Extension of Existing Feature
- Modify existing file in `scripts/`
- Ensure backward compatibility

### New Orchestration Logic
- Update `main.py` or `runner.py`
- Maintain existing orchestration flow where possible

## Requirements

- All new/modified Python files must:
  - Include top-level module docstrings per `docs_spec.md` (Module Docstring Template)
  - Follow function/class formatting and typing per `repo_spec.md` (Function Formatting Standards)
  - Implement exception handling per `repo_spec.md` (Exception Handling Standards)
- Imports must be fully qualified (no relative imports).
- New files must pass linters and adhere to formatting standards.
- App specification document must be updated to reflect new feature.

## Specification Update Requirements

When updating `docs/[app_name]_spec.md`:
- Add new section describing the feature
- Update Orchestration Flow if feature changes app flow
- Update Inputs/Outputs section
- Update Configuration section if config changes
- Update Dependencies section if new dependencies added
- Update Runbook if execution changes
- Update Acceptance Criteria if needed

## Configuration Update Requirements

When updating `configs/[app_name]_config.json`:
- Add new configuration entries with clear names
- Include comments/documentation for new entries
- Maintain existing configuration structure
- Ensure backward compatibility (new entries should have defaults)

## Validation Checklist

- [ ] Target app exists and has required structure
- [ ] Feature files created/modified in correct locations
- [ ] App specification (`docs/[app_name]_spec.md`) updated with feature documentation
- [ ] Configuration updated if needed (`configs/[app_name]_config.json`)
- [ ] Orchestration files (`main.py`/`runner.py`) updated if needed
- [ ] No relative imports; adheres to formatting and typing standards
- [ ] Exception handling follows `repo_spec.md` standards
- [ ] Lint passes with no errors
- [ ] Prompt Checklist answers recorded and confirmed before generation
- [ ] Integration points properly connected
- [ ] Backward compatibility maintained (if applicable)

## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [Apps Folder Architecture Specification](./apps_folder_spec.md)
- [Repository Specification](../10-architecture/repo_spec.md)
