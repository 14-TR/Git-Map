# Prompt Repo Structure Specification

## 1. Overview

**Purpose**: This document is the master guide to the `documentation`. Its sole purpose is to orchestrate the IDE agent's understanding of the available specifications, directing it to the correct document for any given task. It acts as a top-level index or "router" for the other specs.

**Scope**: This specification is limited to defining the structure and purpose of the files within the `documentation/project_specs/` directory. The agent should consult this file first to determine which specialized specification to use for a task.

## 2. IDE Configuration Snippet

To ensure the IDE agent always consults this orchestrator first, add the following rule to your .cursorrules (e.g., `settings.json` or the relevant agent configuration panel).

```markdown
Agent Preamble:
Before responding to any prompt, you MUST follow these steps:
1.  Read the file `documentation/nav_spec.md`.
2.  Use the "Specification Index" in that file to identify the correct, specialized specification for the user's request.
3.  Strictly follow the rules and protocols outlined in the selected specification to complete the task.
```

## 3. Specification Directory (`documentation/project_specs/`)

This directory contains the full suite of specifications that define the standards and protocols for the `GitMap` repository. The agent must use the appropriate spec based on the context of the user's request.

### How to Use These Specifications

1.  **Start Here**: Always begin by consulting this document (`nav_spec.md`) to identify the correct spec.
2.  **Select the Right Tool**: Based on the user's request, navigate to the relevant specification listed below.
3.  **Apply the Rules**: Adhere to the rules and protocols within the selected specification for the duration of the task.

### Specification Index

-   `00-governance/audit_spec.md`: Code auditing standards and procedures for reviewing code, apps, features, and repository components.
-   `00-governance/docs_spec.md`: Documentation standards (docstrings, READMEs, specs).
-   `00-governance/formatting_spec.md`: Spec file formatting standards.
-   `00-governance/ide_agent.md`: Agent behavior, session/task management, error handling, output formatting.
-   `00-governance/protocols_spec.md`: Protocol registry and execution routing.
-   `10-architecture/architecture_spec.md`: Monorepo architecture, environments, branching, SemVer, and legacy migration.
-   `10-architecture/repo_spec.md`: Core coding standards (Python version, dependencies, PEP 8/257, pathlib, structure).
-   `20-operations/monorepo_ops_spec.md`: Dev/prod operations (venv lifecycle, editable installs, guardrails).
-   `20-operations/cut_release_spec.md`: Release process for creating rollback branches.
-   `20-operations/template_conversion_spec.md`: Procedure for converting template repository to actual project.
-   `20-operations/release_notes.md`: GitMap release history and next release value.
-   `30-apps/apps_add_feature_spec.md`: Protocol for adding new features to existing applications under `apps/[app_group]/[app]`.
-   `30-apps/apps_folder_spec.md`: `apps/[app_group]/[app]` structure, scaffolding protocol, validation.
-   `30-apps/arcgis_api_mapping.md`: Mapping of project functionality to ArcGIS API for Python modules and tools.
-   `90-templates/spec_template.md`: Specification template and validation.