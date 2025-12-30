# IDE Agent Specification

## Overview

**Purpose**: Define the behavior, protocols, and standards for IDE-based AI agents in development workflows

**Scope**: All IDE agent interactions and development assistance

**Version**: 1.0


## On Request Behavior

<!-- migrated: on_request.yaml#L1 -->
**Summary**: Guidelines for responsive and proactive agent behavior.

**Requirements**:
- **Responsive Mode**: Actively respond to user requests and queries
- **Proactive Suggestions**: Offer helpful recommendations when appropriate
- **Flexible Adaptation**: Adjust approach based on user preferences and needs


## Protocol Invocation and Routing

**Summary**: The agent must resolve and execute user intents via the protocol registry.

**Requirements**:
- **Start with Nav**: Before responding, consult `documentation/nav_spec.md` to select the correct specialized spec.
- **List Protocols**: When asked to enumerate capabilities (e.g., "list protocols"), execute `protocols.list` per `protocols_spec.md` and return the required data shape.
- **Resolve Aliases**: When a user calls a protocol by alias (e.g., "generate app template"), resolve via `protocols_spec.md` rules (prefer canonical name; otherwise case-insensitive alias; disambiguate if multiple match).
- **Follow Governing Spec**: After resolution, execute the linked spec exactly (e.g., `apps_folder_spec.md` for scaffolding), including prompts, edits, and validation checklists.
- **Status Updates**: Provide brief progress notes at key steps and summarize outcomes per session protocols.

## Checklist Gate (Mandatory Pre-Execution Prompts)

**Requirement**: If the governing spec defines a Prompt Checklist, the agent MUST enforce a hard gate before any edits or file generation.

**Rules**:
- Collect checklist answers one-by-one and echo back a concise summary for confirmation.
- Block ALL edits until the engineer explicitly confirms the summary (Yes/Proceed).
- If an edit is attempted without a confirmed checklist, abort the edit and return to prompting.

**Evidence & Recording**:
- Store the captured answers in the session task list and include them in the final summary.
- When applicable (e.g., app scaffolding), write the details into the generated spec (`docs/[app_name]_spec.md`).

**Decision Rule**:
- Prompts confirmed? → proceed with edits.
- Prompts missing or unconfirmed? → do not edit; continue prompting.

## Status Updates and Task Tracking

**Summary**: Maintain lightweight progress visibility and track active tasks to completion.

**Requirements**:
- **Micro Status Updates**: Provide a 1–3 sentence update before major actions and after completing a step (e.g., file edits, generation, validations).
- **Task List**: Maintain a concise list of active tasks for the goal; update statuses as work progresses (in progress → completed) and reconcile before starting new edits.
- **Completion Check**: When all tasks are finished, confirm completion, summarize changes at a high level, and surface any follow-ups.

## Exception Handling

<!-- migrated: exception_handling.yaml#L1 -->
**Summary**: Standards for error handling and recovery procedures.

### Error Response Protocol

**Requirements**:
- **Graceful Degradation**: Handle errors without losing context
- **Clear Communication**: Explain issues and provide actionable solutions
- **Recovery Procedures**: Guide users through error resolution steps

### Function Formatting Rules
<!-- migrated: function_formatting_rules.yaml#L1 -->
**Requirements**:
- **Consistent Structure**: Follow established function formatting patterns
- **Clear Documentation**: Include comprehensive docstrings for all functions
- **Type Hints**: Use proper type annotations for all parameters and returns

## Output Standards

<!-- migrated: output_standards.yaml#L1 -->
**Summary**: Quality requirements for all code and documentation output.

### Code Quality Requirements

**Standards**:
- **Readability**: Clear, well-structured code that's easy to understand
- **Maintainability**: Modular design with proper separation of concerns
- **Performance**: Efficient algorithms and optimized execution
- **Documentation**: Comprehensive comments and docstrings



## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Protocols Specification](../00-governance/protocols_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [Repository Specification](../10-architecture/repo_spec.md)
- [Apps Folder Architecture Specification](../30-apps/apps_folder_spec.md)
