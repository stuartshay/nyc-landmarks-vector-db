# Tool Version Management

This document describes the comprehensive tool version management system for the NYC Landmarks Vector DB project, which provides `requirements.txt`-style tracking for external tools.

## Overview

Similar to how Python dependencies are managed with `requirements.txt`, this project uses a centralized system to track and manage versions of external tools like `gitleaks`, `terraform`, and `python`.

## Key Files

### `.tool-versions`

The primary source of truth for all tool versions. Format:

```
# Tool versions for NYC Landmarks Vector DB
# Comments explain version choices and rationale
gitleaks 8.21.4   # Latest version for enhanced secret detection
terraform 1.10.3  # Stable release with GCP provider compatibility
python 3.13.1     # Latest stable with performance improvements
```

### `.tool-versions.lock`

Auto-generated lock file that pins exact versions in `requirements.txt` style:

```
gitleaks==8.21.4
terraform==1.10.3
python==3.13.1
```

## Management Commands

### Using Make Targets (Recommended)

```bash
# Show tool version management help
make tool-versions

# List current tool versions and installation status
make tool-versions-list

# Check for available updates
make tool-versions-check

# Generate .tool-versions.lock file
make tool-versions-freeze

# Validate version consistency across configs
make tool-versions-validate
```

### Using Scripts Directly

```bash
# Comprehensive tool version manager
./scripts/manage_tool_versions.sh list
./scripts/manage_tool_versions.sh check
./scripts/manage_tool_versions.sh freeze
./scripts/manage_tool_versions.sh validate

# Individual operations
./scripts/ci/validate_tool_versions.sh
./scripts/ci/sync_tool_versions.sh
./scripts/ci/generate_tool_lock.sh
```

## Workflow

### 1. Updating Tool Versions

1. Edit `.tool-versions` with new versions
1. Generate lock file: `make tool-versions-freeze`
1. Sync across configs: `./scripts/ci/sync_tool_versions.sh`
1. Validate consistency: `make tool-versions-validate`
1. Commit both `.tool-versions` and `.tool-versions.lock`

### 2. Checking Current Status

```bash
# See current versions and what's installed
make tool-versions-list

# Example output:
# 📦 gitleaks: 8.21.4
#    └─ ✅ Installed: 8.21.4
# 📦 terraform: 1.10.3
#    └─ ⚠️  Installed: 1.12.2 (expected: 1.10.3)
```

### 3. Checking for Updates

```bash
make tool-versions-check

# Automatically checks GitHub releases and other sources
# for available updates
```

## Integration Points

### Pre-commit Hooks

Tool version consistency is automatically validated in pre-commit:

```yaml
- id: tool-version-consistency
  name: Validate tool version consistency
  entry: ./scripts/ci/validate_tool_versions.sh
```

### CI/CD Integration

GitHub Actions workflows automatically sync and validate versions:

```yaml
- name: Sync Tool Versions
  run: ./scripts/ci/sync_tool_versions.sh
```

### Setup Scripts

Local environment setup uses centralized versions:

```bash
# setup_env.sh sources versions from .tool-versions
source scripts/versions.sh
```

## Benefits

1. **Single Source of Truth**: All tool versions in `.tool-versions`
1. **Requirements.txt Style**: Familiar workflow for Python developers
1. **Automatic Validation**: Pre-commit and CI checks prevent version drift
1. **Update Tracking**: Easy to see what needs updating
1. **Lock File**: Reproducible builds with exact version pinning
1. **Version History**: Git tracks all version changes

## Best Practices

1. **Always commit both files**: `.tool-versions` and `.tool-versions.lock`
1. **Use exact versions**: Avoid ranges, pin specific versions
1. **Document version choices**: Add comments explaining version decisions
1. **Regular updates**: Check for updates monthly with `make tool-versions-check`
1. **Validate before merge**: Pre-commit hooks catch inconsistencies
1. **Test after updates**: Ensure new versions work with the project

## Troubleshooting

### Version Mismatch Detected

```bash
# Check what's inconsistent
make tool-versions-validate

# Sync all configs to match .tool-versions
./scripts/ci/sync_tool_versions.sh
```

### Tool Not Found

```bash
# Install missing tools
./setup_env.sh

# Or install specific tools manually
# (gitleaks, terraform, etc.)
```

### Lock File Out of Date

```bash
# Regenerate lock file
make tool-versions-freeze
```

## Example Workflow

```bash
# 1. Check current status
make tool-versions-list

# 2. Check for updates
make tool-versions-check

# 3. Update .tool-versions file manually
vim .tool-versions

# 4. Generate new lock file
make tool-versions-freeze

# 5. Sync to all config files
./scripts/ci/sync_tool_versions.sh

# 6. Validate everything is consistent
make tool-versions-validate

# 7. Commit changes
git add .tool-versions .tool-versions.lock
git commit -m "Update tool versions"
```

This system ensures that tool versions are managed as rigorously as Python dependencies, providing consistency, traceability, and ease of maintenance across the entire project.
