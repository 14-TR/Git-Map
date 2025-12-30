# Code Audit Specification

## Overview

**Purpose**: Define comprehensive code auditing standards and procedures for reviewing code, apps, features, and other repository components to ensure quality, security, maintainability, and compliance with repository standards.

**Scope**: All Python code, applications, features, and repository components that require auditing.

**Version**: 1.0

## Audit Framework

### Audit Types

**Summary**: Different types of audits that can be performed based on the target component.

**Code Audit**: Review individual Python files or modules for code quality, standards compliance, and best practices.

**App Audit**: Review entire applications under `apps/[app_group]/[app]` for structure, architecture compliance, and integration quality.

**Feature Audit**: Review specific features within applications for implementation quality, integration, and adherence to feature requirements.

**Repository Audit**: Review repository-wide patterns, dependencies, and architectural compliance.

### Audit Scope Selection

**Process**: The audit protocol must determine the scope based on user input:
1. If user specifies a file path → Code Audit
2. If user specifies an app path (`apps/[group]/[app]`) → App Audit
3. If user specifies a feature → Feature Audit
4. If user specifies repository-wide → Repository Audit

**Requirements**:
- Must identify target component(s) clearly
- Must determine audit depth (quick scan vs. comprehensive)
- Must respect user's explicit scope requests

## Code Quality Checks

### Formatting & Style Compliance

**Summary**: Verify adherence to PEP 8 and repository formatting standards.

**Checks**:
- PEP 8 compliance (line length, naming conventions, spacing)
- Import order (standard library → third-party → local)
- Function signature formatting (multiline with 8-space indent)
- Separator line formatting for function groups
- Consistent indentation (spaces, not tabs)

**Validation**:
- Use linter tools (flake8, pylint, ruff) where available
- Manual review of formatting patterns
- Check for trailing whitespace and blank lines

### Documentation Standards

**Summary**: Verify completeness and quality of documentation.

**Checks**:
- PEP 257 docstring compliance for all functions/classes/modules
- Module-level docstrings present
- Function docstrings include purpose, parameters, return values, exceptions
- Type hints present for all function parameters and return types
- `from __future__ import annotations` present where needed
- README files present for apps/features where required

**Validation**:
- All public functions have docstrings
- Type hints are complete and accurate
- Documentation matches implementation

### Code Structure & Organization

**Summary**: Verify code follows repository structure standards.

**Checks**:
- Single responsibility principle adherence
- Function/class size and complexity
- Modularization (no code duplication)
- Proper use of `if __name__ == '__main__'` guards
- Path handling uses `pathlib.Path` objects
- Conditional imports use `TYPE_CHECKING` pattern
- Proper separation of concerns

**Validation**:
- Functions are focused and not overly complex
- Shared operations extracted to utilities
- Code organization follows repository patterns

## Security & Best Practices

### Security Checks

**Summary**: Identify potential security vulnerabilities and unsafe practices.

**Checks**:
- Hardcoded credentials or secrets
- SQL injection vulnerabilities
- Path traversal vulnerabilities
- Unsafe file operations
- Missing input validation
- Insecure random number generation
- Exposed sensitive data in logs
- Missing authentication/authorization checks

**Validation**:
- No secrets in code or config files
- Input validation present for user-provided data
- Secure file operations
- Proper error handling that doesn't leak sensitive information

### Error Handling

**Summary**: Verify proper exception handling patterns.

**Checks**:
- Standard exception block pattern followed
- Exception naming conventions (`snake_case + _error`)
- Message format: `<Context description>: {error_alias}`
- F-string usage (no concatenation, `.format()`, or `%` formatting)
- Proper exception chaining (`raise ... from ...`)
- Fallback exception handling present
- No bare `except:` clauses
- Appropriate exception types used

**Validation**:
- All exception blocks follow repository standards
- Error messages are informative and contextual
- Exceptions are properly chained for debugging

### Performance Considerations

**Summary**: Identify potential performance issues and optimization opportunities.

**Checks**:
- Algorithmic complexity analysis
- Unnecessary I/O operations
- Missing caching for expensive operations
- Inefficient data structure usage
- Memory leaks or excessive memory usage
- Missing generators for large datasets
- Proper resource cleanup (context managers)
- Database query optimization

**Validation**:
- Code uses appropriate data structures
- I/O operations are minimized
- Resources are properly managed
- Performance-critical paths are optimized

## Architecture & Integration Compliance

### Dependency Management

**Summary**: Verify dependency usage follows repository policies.

**Checks**:
- Standard library preferred over third-party when possible
- Minimal external dependencies
- Version requirements documented
- No unnecessary imports
- Proper dependency isolation

**Validation**:
- Dependencies are justified and minimal
- Standard library used where appropriate
- Version requirements are clear

### Repository Structure Compliance

**Summary**: Verify component follows repository structure standards.

**Checks**:
- Apps follow `apps/[app_group]/[app]` structure
- Proper file organization within apps
- Naming conventions followed
- Required files present (main.py, runner.py, etc.)
- Feature structure follows standards

**Validation**:
- Structure matches repository architecture
- Required files and directories present
- Naming conventions consistent

## Audit Execution Protocol

### Pre-Audit Assessment

**Process**:
1. Identify target component(s) from user input
2. Determine audit type (Code/App/Feature/Repository)
3. Identify relevant specifications to check against
4. Determine audit depth (quick/comprehensive)

**Required Information**:
- Target path or component name
- Audit scope (file, app, feature, repository)
- Audit depth preference (if not specified, default to comprehensive)

### Audit Execution Steps

**Process**:
1. **Scope Identification**: Determine exact files/components to audit
2. **Specification Loading**: Load relevant specs (repo_spec.md, apps_folder_spec.md, etc.)
3. **Code Analysis**: Perform automated checks where possible (linting, type checking)
4. **Manual Review**: Review code against specification requirements
5. **Issue Identification**: Document findings with severity levels
6. **Report Generation**: Create structured audit report

**Requirements**:
- Must check against all relevant specifications
- Must provide actionable feedback
- Must prioritize issues by severity
- Must reference specific spec sections for violations

### Issue Severity Levels

**Critical**: Violations that cause security risks, data loss, or system failures
**High**: Violations that cause bugs, performance issues, or maintainability problems
**Medium**: Violations that reduce code quality or deviate from standards
**Low**: Minor style issues or suggestions for improvement

### Audit Report Format

**Structure**:
```markdown
# Audit Report: [Component Name]

## Summary
- Total Issues: [count]
- Critical: [count]
- High: [count]
- Medium: [count]
- Low: [count]

## Findings

### [Category Name]

#### [Issue Title] (Severity: [Level])
- **Location**: [file:line]
- **Specification**: [spec reference]
- **Description**: [detailed description]
- **Recommendation**: [how to fix]
```

## Validation Checklist

**Post-Audit Validation**:
- [ ] All relevant specifications checked
- [ ] All issues documented with severity
- [ ] Audit report generated and formatted correctly
- [ ] Recommendations provided for each issue
- [ ] Spec references included for violations
- [ ] Scope accurately identified and audited

## References

- [Repository Specification](../10-architecture/repo_spec.md)
- [Apps Folder Specification](../30-apps/apps_folder_spec.md)
- [Documentation Specification](./docs_spec.md)
- [IDE Agent Specification](./ide_agent.md)
