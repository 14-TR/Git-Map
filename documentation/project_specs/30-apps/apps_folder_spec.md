# Apps Folder Architecture Specification

## Overview

**Purpose**: Define the canonical structure and scaffolding protocol for `apps/[app_group]/[app]` directories, including minimum files/folders and the IDE agent prompts required to generate a new app.

**Scope**: Applies to all runnable applications inside `apps/` at the most granular level: `apps/[app_group]/[app]`.

**Version**: 1.0

## Directory Structure

**Minimum Required Layout**:

```
apps/
  [app_group]/
    [app]/
      docs/
        [app_name]_spec.md
      configs/
        [app_name]_config.json
      scripts/
      main.py          # Orchestrator entrypoint
      runner.py        # Optional; may override orchestrator behavior
```

**Requirements**:
- `docs/[app_name]_spec.md` must exist and describe the app’s purpose, inputs/outputs, orchestration flow, and operational guardrails.
- `main.py` is the default orchestrator entrypoint. It must be runnable directly via `python main.py`.
- `runner.py` is optional; when present, it may override or extend orchestrator behavior (e.g., CLI parsing, environment setup). If both exist, `runner.py` should import and call `main.py` with a specific configuration.
- `configs/` houses configuration templates and environment-specific files.
- `scripts/` is the core directory for all application logic, including models, business logic, and app-specific utilities. This is where the main implementation resides. The `main.py` file is reserved for orchestration and entrypoint logic only.

Orchestrator selection precedence: prefer `runner.py` when present; otherwise `main.py`.

## Scaffolding Protocol

**Protocol Name**: Generate App Template

**Process**:
1. Engineer issues: "generate app template, in apps/[app_group]/[app]".
2. IDE agent validates that `[app_group]` and `[app]` are snake_case and unique within `apps/`.
3. IDE agent prompts the engineer for must-have information (see Prompt Checklist) and echoes back a summary.
4. HARD GATE: No file or directory edits may occur until the engineer confirms the summary.
5. IDE agent generates the directory structure and minimal files.
6. IDE agent writes `docs/[app_name]_spec.md` using the spec template and captured answers.
7. IDE agent creates boilerplate `main.py` and optional `runner.py` with compliant docstrings per repository standards.

**Requirements**:
- All generated Python files must:
  - Include top-level module docstrings per `docs_spec.md` (Module Docstring Template)
  - Follow function/class formatting and typing per `repo_spec.md` (Function Formatting Standards)
  - Implement exception handling per `repo_spec.md` (Exception Handling Standards)
- Imports must be fully qualified (no relative imports) where applicable.
- Scripts must be invocable directly (prefer `python script.py`).
- New files must pass linters and adhere to formatting standards.

## Prompt Checklist (IDE Agent → Engineer)

The agent MUST ask for and record the following one at a time before generation:
- App name (`[app]`) and group (`[app_group]`).
- One-line purpose statement for the app.
- Primary inputs and outputs (data sources, files, services).
- Execution context (manual CLI, scheduled task, ArcGIS Pro, etc.).
- Environment requirements (venv name, ArcGIS Pro version if applicable).
- Configuration strategy (env vars, config files under `configs/`).
- Critical dependencies (internal `packages/`, external libs).
- Operational guardrails (idempotency, retries, failure notifications).
- Acceptance criteria for "base app ready" state.

## Boilerplate File Standards

### `docs/[app_name]_spec.md`

**Pattern**: Use `spec_template.md` sections and `docs_spec.md` rules. Minimum sections:
- Overview (Purpose, Scope, Version)
- Orchestration Flow (with Mermaid diagram if multi-component)
- Inputs/Outputs
- Configuration
- Error Handling
- Dependencies
- Runbook (how to run, parameters)
- Acceptance Criteria

### `main.py` (Orchestrator)

**Implementation Requirements**:
1. Provide a module docstring that includes Execution Context, Dependencies, and Metadata per `docs_spec.md`.
2. Expose a `main()` function returning an integer exit code and guard with `if __name__ == "__main__":` to allow `python main.py` execution.
3. Apply exception handling per `repo_spec.md` (Exception Handling Standards): wrap orchestration in `try/except`, construct an f-string message, and `raise RuntimeError(msg) from error_alias`.
4. Contain minimal orchestration that delegates to functions in `scripts/`.

## Validation Checklist

- [ ] Directory created at `apps/[app_group]/[app]/` with required subfolders
- [ ] `docs/[app_name]_spec.md` authored with agreed sections
- [ ] `main.py` present, runnable via `python main.py`
- [ ] `runner.py` present (optional) and defers to orchestrator
- [ ] No relative imports; adheres to formatting and typing standards
- [ ] Exception handling and function formatting follow `repo_spec.md`
- [ ] Lint passes with no errors
- [ ] Prompt Checklist answers recorded and confirmed before generation

## Migration Notes

<!-- migrated: apps_folder_spec.yaml#L1 -->

## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [Architecture Specification](../10-architecture/architecture_spec.md)
- [Repository Specification](../10-architecture/repo_spec.md)

