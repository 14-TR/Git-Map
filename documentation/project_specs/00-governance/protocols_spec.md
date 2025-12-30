# Protocols Specification

## Overview

**Purpose**: Provide a centralized, machine-readable registry of available protocols and how to execute them. This enables the IDE agent to enumerate protocols, resolve them by name/alias, and execute their linked specifications.

**Scope**: Protocols orchestrate repeatable workflows (e.g., scaffolding an app). Each protocol references the authoritative specification that governs its behavior.

**Version**: 1.0

## Protocol Registry

The following protocols are available. Each entry defines a canonical name, intent, command phrases (aliases), the governing spec, and execution semantics.

### Protocol: list protocols

**Canonical Name**: protocols.list

**Intent**: Return the list of all available protocols with their canonical name, short description, and command phrases.

**Command Phrases (aliases)**:
- "list protocols"
- "show protocols"
- "what can you do"

**Governing Spec**: this document (protocols_spec.md)

**Execution**:
1. Enumerate all protocol entries defined under Protocol Registry in this file.
2. Return structured data: `[{ name, description, command_phrases, spec_path }]`.

---

### Protocol: generate protocol

**Canonical Name**: protocols.generate

**Intent**: Scaffold a new protocol entry in the protocols registry and create the corresponding command file, enabling the IDE agent to recognize and execute the new command.

**Command Phrases (aliases)**:
- "generate protocol"
- "create protocol"
- "make new command"
- "add new command"
- "scaffold protocol"

**Governing Spec**: this document (protocols_spec.md)

**Execution**:
1. Follow Protocol Generation Protocol: prompt for canonical name, intent, command phrases, governing spec, execution steps, and validation criteria.
2. Enforce Checklist Gate: prompt for required fields per Prompt Checklist, echo a summary, and require explicit confirmation before any edits.
3. After confirmation, add protocol entry to Protocol Registry section in this file (alphabetically ordered by canonical name).
4. Create command file at `.cursor/commands/[canonical-name-kebab-case].md` following command file format.

**Validation**: Protocol entry added correctly, command file created, canonical name follows naming convention, command phrases are unique, governing spec path is valid.

---

### Protocol: generate app template

**Canonical Name**: apps.generate_template

**Intent**: Scaffold a new app directory under `apps/[app_group]/[app]` following repository standards.

**Command Phrases (aliases)**:
- "generate app template"
- "create app"
- "scaffold app"

**Governing Spec**: `project_specs/30-apps/apps_folder_spec.md`

**Execution**:
1. Follow Scaffolding Protocol in `apps_folder_spec.md`.
2. Enforce Checklist Gate: prompt for required fields per Prompt Checklist, echo a summary, and require explicit confirmation before any edits.
3. After confirmation, create directories/files; ensure docstrings and formatting compliance.

**Validation**: Apply Validation Checklist from `apps_folder_spec.md`.

---

### Protocol: add feature to app

**Canonical Name**: apps.add_feature

**Intent**: Add a new feature to an existing application under `apps/[app_group]/[app]` following repository standards and maintaining app structure.

**Command Phrases (aliases)**:
- "add feature to app"
- "add new feature"
- "add feature"
- "implement feature"
- "add functionality"

**Governing Spec**: `project_specs/30-apps/apps_add_feature_spec.md`

**Execution**:
1. Follow Feature Addition Protocol in `apps_add_feature_spec.md`.
2. Enforce Checklist Gate: prompt for required fields per Prompt Checklist, echo a summary, and require explicit confirmation before any edits.
3. After confirmation, create/modify files in target app; ensure docstrings and formatting compliance.

**Validation**: Apply Validation Checklist from `apps_add_feature_spec.md`.

---

### Protocol: perform audit

**Canonical Name**: audit.perform

**Intent**: Perform comprehensive code audit of specified component (code, app, feature, etc.) following repository standards and best practices.

**Command Phrases (aliases)**:
- "audit code"
- "audit app"
- "audit feature"
- "perform audit"
- "code audit"
- "audit component"

**Governing Spec**: `project_specs/00-governance/audit_spec.md`

**Execution**:
1. Follow Audit Execution Protocol in `audit_spec.md`.
2. Identify target component(s) and determine audit type (Code/App/Feature/Repository).
3. Load relevant specifications and perform comprehensive checks.
4. Generate structured audit report with findings categorized by severity.
5. Provide actionable recommendations for each issue identified.

**Validation**: Apply Validation Checklist from `audit_spec.md`.

---

### Protocol: generate spec

**Canonical Name**: spec.generate

**Intent**: Generate a new spec file based on a template.

**Command Phrases (aliases)**:
- "generate spec"
- "create spec"

**Governing Spec**: `project_specs/90-templates/spec_template.md`

**Execution**:
1. Follow the spec template in `spec_template.md`.


---

### Protocol: release guide

**Canonical Name**: release.guide

**Intent**: Guide the developer to cut a release by creating a `release/#.#.#` branch from `main` for rollback purposes.

**Command Phrases (aliases)**:
- "release guide"
- "release process"
- "release instructions"
- "release steps"
- "create release"

**Governing Spec**: `project_specs/20-operations/cut_release_spec.md`

**Execution**:
1. Follow the steps in the governing spec. Version number is sourced from `release_notes.md` "Current Versions" table.
2. Confirm release notes are updated on `main` branch.
3. Provide copy/paste commands as needed for git actions.
4. Create `release/#.#.#` branch from `main` for rollback purposes.

---

### Protocol: convert template

**Canonical Name**: template.convert

**Intent**: Convert this template repository into an actual project by replacing all placeholders with project-specific values.

**Command Phrases (aliases)**:
- "convert template"
- "initialize project"
- "setup project"
- "convert from template"
- "project setup"
- "initialize repository"

**Governing Spec**: `project_specs/20-operations/template_conversion_spec.md`

**Execution**:
1. Follow the Template Conversion Protocol in `template_conversion_spec.md`.
2. Prompt for required information (repository name, etc.).
3. Perform find-and-replace operations across all documentation and command files.
4. Validate that all placeholders have been replaced.
5. Provide summary of changes made.

**Validation**: All required placeholders replaced, optional placeholders configured or left as-is, directory renamed (if requested) and references updated.

---

## Protocol Resolution Rules

1. Match by canonical name first; if no match, match by case-insensitive alias.
2. If multiple protocols share an alias, ask for disambiguation by returning candidates with descriptions.
3. Return the `spec_path` and `section` (if applicable) that governs execution.

## Agent Behavior for Protocol Execution

When a user invokes a protocol (explicitly or via an alias):
1. Resolve the protocol via the rules above.
2. Load and follow the governing spec exactly.
3. Provide a brief status update, then perform required prompts/edits.
4. Validate outcomes using the spec’s validation checklist.
5. Summarize changes and surface follow-ups.

## Data Shape for "list protocols"

The IDE agent MUST return the following structure for the `protocols.list` protocol:

```
[
  {
    "name": "apps.generate_template",
    "description": "Scaffold a new app under apps/[group]/[app]",
    "command_phrases": ["generate app template", "create app", "scaffold app"],
    "spec_path": "documentation/project_specs/30-apps/apps_folder_spec.md"
  },

]
```

## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [Monorepo Operations Specification](../20-operations/monorepo_ops_spec.md)
- [Apps Folder Architecture Specification](../30-apps/apps_folder_spec.md)


