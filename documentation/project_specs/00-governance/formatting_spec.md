# Specification Formatting Standards

## Overview

**Purpose**: Define consistent formatting standards for all specifications in the repository

**Scope**: All specification files in `documentation/project_specs/` directory

**Version**: 1.0

## File Structure

### Content Organization

**Header Hierarchy**:
- `#` - Main specification title
- `##` - Major sections
- `###` - Subsections
- `####` - Detailed subsections (use sparingly)

**Section Patterns**:
1. **Overview/Summary** - Always start with this
2. **Core Rules/Protocols** - Main content
3. **Examples/Implementation** - Code and usage examples
4. **Migration Notes** - Source tracking
5. **References** - Related documents

## Content Formatting

### Protocol Definitions

**Standard Format**:
```
**Protocol Name**: [Brief description]

**Process**: [Step-by-step description]

**Requirements**:
- [Requirement 1]
- [Requirement 2]

**Example**:
```python
# Code example
```

**Notes**:
- [Important note 1]
- [Important note 2]
```

### Code Examples

**Function Formatting**:
```python
def example_function(
        param_1: str,
        param_2: int,
) -> bool:
    """Example docstring following PEP 257."""
    # Implementation
    return True
```

**Class Formatting**:
```python
class ExampleClass:
    """Example class docstring."""
    
    def __init__(self, param: str) -> None:
        """Initialize the class."""
        self.param = param
```

### Migration Tracking

**Format**: `<!-- migrated: source_file.yaml#Lline_number -->`

**Placement**: At the beginning of each migrated section

**Example**:
```markdown
<!-- migrated: session_management_protocol.yaml#L1 -->
**Summary**: A structured protocol for real-time task tracking...
```

## Language Standards

### Terminology

**Consistent Terms**:
- Use **bold** for key terms and concepts
- Use `code` for technical terms, file names, and code references
- Use *italics* sparingly for emphasis

### Lists and Enumerations

**Bullet Points**: Use for requirements, features, and general lists
**Numbered Lists**: Use for procedures, steps, and ordered processes

### Code Blocks

**Python**: Use ````python` for Python code
**YAML**: Use ````yaml` for configuration examples
**JSON**: Use ````json` for JSON examples
**Shell**: Use ````bash` for command examples

## Quality Standards

### Completeness Requirements

**Every Spec Must Include**:
- Clear purpose statement
- Scope definition
- Version information
- Migration tracking (if applicable)
- Related references

### Readability Standards

**Line Length**: Maximum 88 characters for code examples
**Paragraphs**: Keep under 3-4 sentences
**Sections**: Use clear, descriptive headings

### Maintenance Standards

**Update Frequency**: Review quarterly
**Version Control**: Increment version numbers for significant changes
**Deprecation**: Mark old specs as deprecated before removal

## Validation Checklist

- [ ] Content follows header hierarchy
- [ ] Code examples are properly formatted
- [ ] Migration comments are present (if applicable)
- [ ] References section is complete
- [ ] No broken links or references
- [ ] Consistent terminology throughout
- [ ] Examples are executable/testable

## References

- [IDE Agent Specification](../00-governance/ide_agent.md)
- [Repository Specification](../10-architecture/repo_spec.md)
- [Prompt Repository Migration Specification](../99-migrations/prompt_repo_migration_spec.md)
