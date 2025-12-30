# Template Conversion Specification

## Overview

**Purpose**: Define the procedure for converting this template repository into an actual project repository by replacing all placeholders with project-specific values.

**Scope**: Replacing placeholders throughout documentation, specs, commands, and configuration files with actual project values.

**Version**: 1.0

## Preconditions

- User has cloned or copied the template repository
- User has determined the actual repository name
- User has determined optional configuration values (paths, package names, etc.)

## Placeholders to Replace

### Required Placeholders

1. **`GitMap`** - The actual repository/project name
   - Used in: documentation, specs, release notes, commands
   - Example: If repository name is "ProjectIQ", replace all instances

2. **`gitmap`** - Lowercase version of repository name (for paths/naming)
   - Used in: environment naming, path references
   - Example: "projectiq" (snake_case or lowercase)

### Optional Placeholders (Can be configured later)

3. **`[venv_root_path]`** - Virtual environment root path
   - Default: Can be left as placeholder or configured
   - Example: `W:\GIS_Python_Envs` or `/path/to/venvs`

4. **`[github_root_path]`** - GitHub repositories root path
   - Default: Can be left as placeholder or configured
   - Example: `W:\GIS_Github` or `/path/to/repos`

5. **`[package_name]`** - First-party package names (if applicable)
   - Default: Can be left as placeholder
   - Example: `utility_manager`, `my_package`

## Conversion Process

### Step 1: Gather Information

**Required Information**:
- Repository name (e.g., "ProjectIQ", "MyProject")
- Repository name in lowercase/snake_case (e.g., "projectiq", "my_project")

**Optional Information**:
- Virtual environment root path
- GitHub repositories root path
- First-party package names (if any)

### Step 2: Replace Placeholders

**Files to Update**:

1. **Documentation Files**:
   - `documentation/nav_spec.md`
   - `documentation/project_specs/**/*.md` (all spec files)
   - `documentation/project_specs/20-operations/release_notes.md`

2. **Command Files**:
   - `.cursor/commands/*.md` (all command files)

3. **Configuration Files** (if any):
   - Any config files that reference placeholders

**Replacement Rules**:
- `GitMap` → Actual repository name (e.g., "ProjectIQ")
- `gitmap` → Lowercase/snake_case version (e.g., "projectiq")
- `[venv_root_path]` → Actual venv path or leave as placeholder
- `[github_root_path]` → Actual GitHub path or leave as placeholder
- `[package_name]` → Actual package names or leave as placeholder

### Step 3: Update Directory Names (Optional)

If desired, rename `project_specs` directory to match project naming:
- Option A: Keep `project_specs` (works fine, just a directory name)
- Option B: Rename to `gitmap_specs` (e.g., `projectiq_specs`)
- Option C: Rename to `project_specs` (generic)

**If renaming directory**:
- Update all references in `nav_spec.md`
- Update all references in command files
- Update all references in spec files

### Step 4: Update Release Notes

Update `release_notes.md`:
- Replace `GitMap` with actual name
- Update initial release entry if needed
- Remove template note if desired

### Step 5: Validation

**Checklist**:
- [ ] All `GitMap` placeholders replaced
- [ ] All `gitmap` placeholders replaced
- [ ] Optional placeholders configured or left as-is
- [ ] Directory renamed (if applicable) and all references updated
- [ ] Release notes updated
- [ ] No remaining template placeholders (except intentionally left ones)
- [ ] All file paths in specs/commands are correct
- [ ] Git repository initialized (if starting fresh)

## Automated Conversion

The conversion can be automated using find-and-replace:

```bash
# Replace GitMap with actual name
find documentation .cursor -type f -name "*.md" -exec sed -i '' 's/\[Repository Name\]/ProjectIQ/g' {} +

# Replace gitmap with lowercase version
find documentation .cursor -type f -name "*.md" -exec sed -i '' 's/\[repository\]/projectiq/g' {} +
```

**Note**: Always review changes after automated replacement to ensure correctness.

## Post-Conversion Steps

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Converted from template"
   ```

2. **Update README** (if exists):
   - Replace template information with project-specific information

3. **Review and Customize**:
   - Review all specs for project-specific customizations
   - Remove any specs that don't apply to your project
   - Add any project-specific specs as needed

## Guardrails

- **Backup First**: Always create a backup or work in a copy before conversion
- **Review Changes**: Don't blindly replace - review each change
- **Test Commands**: After conversion, test that commands still work
- **Version Control**: Commit conversion as a single commit for easy rollback

## References

- [Navigation Specification](../nav_spec.md)
- [Architecture Specification](../10-architecture/architecture_spec.md)
- [Release Notes](./release_notes.md)

