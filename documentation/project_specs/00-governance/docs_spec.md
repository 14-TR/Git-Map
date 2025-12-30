# Documentation Specification

## Overview

**Purpose**: Define standards and templates for all repository documentation (docstrings, READMEs, specs).

**Scope**: All documentation authored in this repository, including module and function docstrings, application/spec docs, and README content.

**Version**: 1.0

## Function Docstrings

<!-- migrated: documentation.yaml#L1 -->
**Style**: PEP 257 / Google-style

**Includes**:
- Purpose
- Parameter Descriptions
- Return Explanation
- Example Usage (optional)

### Function Docstring Template
<!-- migrated: documentation.yaml#L6 -->
**Required**: true

**Format**:
```
"""
    <One-line purpose sentence>

    Args:
        <param_1>: <description>.
        <param_2>: <description>.

    Returns:
        <ReturnType>: <description of the return value>.

    Raises:
        <ExceptionType>: <reason raised>.
"""
```

**Notes**:
- Indent section headers four spaces beyond opening quotes
- Align descriptions after a single space
- Maintain blank line before each section header
- Keep lines ≤ 88 characters

## Module Docstrings

### Module Docstring Template
<!-- migrated: documentation.yaml#L20 -->
**Required**: true

**Format**:
```
"""
<One-line summary>

<Extended description paragraph(s)>

Key Features:
    - <bullet 1>
    - <bullet 2>

Dependencies:
    - <dependency 1>
    - <dependency 2>

Metadata:
    <additional metadata fields as needed>
"""
```

**Notes**:
- Indent bullets with four spaces
- Use exactly the section titles 'Key Features:', 'Dependencies:', and 'Metadata:'
- Keep line length ≤ 88 characters
- Place this docstring at the very top of every module file


Prohibitions:

- Never use `internal` outside `packages/**`.

## Script Documentation

<!-- migrated: documentation.yaml#L35 -->
**Script Docstrings Include**:
- Execution Context
- Module Dependencies

## Inline Comments

<!-- migrated: documentation.yaml#L37 -->
**Purpose**: Clarify non-obvious or critical logic

**Guidelines**:
- Explain the "why" not the "what"
- Focus on business logic and edge cases
- Keep comments up-to-date with code changes
- Use clear, concise language

## Top-Level Summary

<!-- migrated: documentation.yaml#L38 -->
**Requirement**: Must conform to module_docstring_template

**Application**: Every module file must have a proper top-level docstring

## README Generation Standards

<!-- migrated: readme_generation.yaml#L1 -->
### Template Structure
<!-- migrated: readme_generation.yaml#L3 -->
**Mandatory Sections**:

#### Header
- Project Title: Centered, H1
- Badges: e.g., Python version, build status (optional)

#### Overview
- A concise paragraph explaining the script's purpose, what problem it solves, and its primary output

#### Key Features
- Bulleted list of the most important capabilities

#### Architecture
- **Mermaid Diagram**: A `graph TD` or similar Mermaid diagram illustrating the workflow and component interactions
- **Architecture Notes**: A detailed explanation of the design, data flow, key decisions, and tradeoffs

#### Component Breakdown
For each major function/class/module:
- Name and one-line description
- Detailed purpose
- Parameters/Arguments table
- Return value description

#### Setup and Configuration
- **Prerequisites**: List of software, libraries, or credentials needed
- **Installation**: Step-by-step installation instructions
- **Configuration**: Details on how to set up `.env` or other config files, with examples

#### Usage
- Execution command(s) with clear examples for various use cases
- Explanation of command-line arguments

#### Dependencies
- List of all internal and external dependencies

#### Error Handling
- Explanation of how exceptions are handled and reported to the user

### Mermaid Diagram Standard
<!-- migrated: readme_generation.yaml#L35 -->
**Type**: `graph TD`
**Style**: Use clear, descriptive names for nodes. Use quotes for all node text. Use `<br/>` for line breaks.
**Requirement**: A Mermaid diagram is mandatory for any script with more than one major component or external interaction.

### Content Rules
<!-- migrated: readme_generation.yaml#L39 -->
**Clarity**: Must be understandable by a user with basic domain knowledge but no prior experience with this specific script
**Completeness**: All configurable options and execution paths must be documented
**Accuracy**: Documentation must be kept in sync with the code

### Override Clause
<!-- migrated: readme_generation.yaml#L43 -->
This README generation protocol is mandatory for all new scripts and must be applied retroactively when existing scripts are significantly modified.

## Documentation Quality Standards

### Clarity Requirements
- Use clear, concise language
- Avoid technical jargon when possible
- Provide context for complex concepts
- Include examples for abstract ideas

### Completeness Standards
- Cover all public APIs and interfaces
- Document all configuration options
- Include error handling information
- Provide troubleshooting guidance

### Maintenance Guidelines
- Keep documentation synchronized with code
- Review and update regularly
- Version documentation with code releases
- Solicit feedback from users
