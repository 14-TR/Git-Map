# Repository Specification

## Overview

**Purpose**: Generate professional, maintainable, highly readable Python code adhering to modern best practices, and brutally optimized for elite performance under real-world conditions

**Scope**: All Python code, documentation, and development practices in the repository

**Version**: 1.0

## Vision & Stakeholders

<!-- migrated: overview.yaml#L1 -->
**Summary**: Core vision and stakeholder requirements for the repository.

**Name**: Python Standards  
**Description**: Enforces professional, maintainable, and highly optimized Python code  
**Version**: 1.0

## Architecture Invariants

**Summary**: Core technical standards and requirements that must be followed.

### Python Standards
<!-- migrated: standards.yaml#L1 -->
**Requirements**:
- **Formatting**: PEP 8
- **Docstrings**: PEP 257  
- **Python Version**: 3.11+
- **Preferred Libraries**: Standard library over third-party when possible
- **Path Handling**: Use pathlib for all file path operations

### Import Standards
<!-- migrated: standards.yaml#L6 -->
**Import Order**:
1. Standard library imports
2. Third-party library imports  
3. Local module imports

**Required Imports**:
- `from __future__ import annotations` for type hints
- Always use typing module for type hints

## Code Structure Rules

**Summary**: Standards for code organization and structure.

### Modularization
<!-- migrated: code_structure.yaml#L1 -->
**Requirements**:
- **Small, single-responsibility functions/classes**
- **Avoid duplication**: Refactor shared operations into utilities
- **Main guard**: Required unless excluded: `if __name__ == '__main__'`

### File Path Handling
<!-- migrated: code_structure.yaml#L4 -->
**Requirement**: Convert to Path objects immediately

### Conditional Imports
<!-- migrated: code_structure.yaml#L5 -->
**Pattern**: Use TYPE_CHECKING for circular import prevention  
**Example**:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import module
```

### Timeout Protection
<!-- migrated: code_structure.yaml#L8 -->
**Pattern**: Use threading with timeout for long-running operations  
**Example**:
```python
operation_completed = threading.Event()
result = [None]  # Use list to store result from thread
thread = threading.Thread(target=operation_function)
thread.daemon = True
thread.start()
success = operation_completed.wait(timeout)
if not success:
    raise TimeoutError(f"Operation timed out after {timeout} seconds")
```

## Dependency Policy

**Summary**: Standards for managing external dependencies and library selection.

### Library Selection
**Requirements**:
- Prefer standard library over third-party libraries
- Use pathlib for all file path operations
- Maintain minimal external dependencies

### Version Requirements
**Requirements**:
- Python 3.11+ required
- Type hints mandatory for all new code
- Future annotations import required

## Performance Standards

**Summary**: Standards for code performance and optimization.

### Optimization Guidelines
**Requirements**:
- Profile before optimizing
- Focus on algorithmic complexity first
- Use appropriate data structures
- Minimize I/O operations
- Cache expensive computations

### Memory Management
**Requirements**:
- Use generators for large datasets
- Avoid unnecessary object creation
- Proper resource cleanup with context managers


## Exception Handling Standards

**Summary**: Standards for error handling and exception management.

### Exception Handling Protocol
**Requirements**:
- **try_except_wrap**: True (always use exception handling)
- **boilerplate_exceptions**: Always default to exception handling defined in this ruleset
- **custom_exceptions**: Use where needed, only when requested

### Timeout Exceptions
**Pattern**: Create custom timeout exceptions for operation-specific timeouts
**Example**: 
```python
class CloneTimeout(Exception):
    """Exception raised when a clone operation times out."""
```

### Standard Exception Block
**Naming Conventions**: 
- error_alias: snake_case of exception + _error
- message_variable: msg
**Message Format**: `<Context description>: {error_alias}`
**Pattern Rules**:
1. `except <ExceptionType> as <error_alias>`
2. Build msg = '<Context>: {error_alias}'
3. `raise RuntimeError(msg) from <error_alias>`
4. fallback: `except Exception as general_error`
**F-String Requirement**: All messages must use Python f-strings only, no string concatenation, .format(), or %-style formatting

### Function Formatting Standards
**Separator Line**: `# ---- {some name or type of function} Functions -----------------------------------------------------------------------------------------------`
**Signature Style**: Multiline with 8-space indent, one parameter per line
**Layout**:
```python
def <function_name>(
        <param_1>: <type>,
        <param_2>: <type>,
        <param_n>: <type>,
) -> <ReturnType>:
```
**Rules**: Opening parenthesis on same line as function name, parameters start on next line, trailing commas, closing paren on new line, return annotation inline
**Docstring Required**: True
**Sample Conformity**: All functions must mirror structural layout demonstrated in get_databases()

<!-- migrated: exception_handling.yaml#Lexception_handling.try_except_wrap -->
**try_except_wrap**: True

<!-- migrated: output_standards.yaml#Loutput_standards.complete_code -->
**complete_code**: True

## References

- [Documentation Specification](../00-governance/docs_spec.md)
- [Specification Formatting Standards](../00-governance/formatting_spec.md)
- [IDE Agent Specification](../00-governance/ide_agent.md)
- [Application Specification](../30-apps/apps_folder_spec.md)