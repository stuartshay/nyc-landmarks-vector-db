# Tool Version Management

This directory contains scripts for managing tool versions consistently across the NYC Landmarks Vector DB project.

## Overview

The project uses a centralized approach to manage external tool versions (like gitleaks, terraform, python) across multiple configuration files including:

- Setup scripts (`setup_env.sh`)
- DevContainer Dockerfiles (`.devcontainer/Dockerfile.prebuilt`)
- GitHub Actions workflows (`.github/workflows/*.yml`)
- CI/CD scripts

## Files

### Core Version Configuration

- **`.tool-versions`** (project root) - Central source of truth for all tool versions
- **`scripts/versions.sh`** - Utility script to load versions from `.tool-versions`

### CI Scripts

- **`sync_tool_versions.sh`** - Synchronizes versions from `.tool-versions` to all configuration files
- **`validate_tool_versions.sh`** - Validates that all files use consistent versions
- **`sync_versions.sh`** - Synchronizes Python package versions between `requirements.txt` and `setup.py` (different purpose)

## Usage

### Updating Tool Versions

1. **Update the central configuration:**

   ```bash
   # Edit .tool-versions file
   vim .tool-versions
   ```

1. **Synchronize across all files:**

   ```bash
   ./scripts/ci/sync_tool_versions.sh
   ```

1. **Validate consistency:**

   ```bash
   ./scripts/ci/validate_tool_versions.sh
   ```

1. **Test the changes:**

   ```bash
   # Test gitleaks specifically
   gitleaks detect --source=. --config=.gitleaks.toml --no-git

   # Run pre-commit checks
   pre-commit run gitleaks-scan --all-files
   ```

### Example Workflow

```bash
# Update gitleaks to version 8.22.0
echo "gitleaks 8.22.0" > .tool-versions
echo "terraform 1.10.3" >> .tool-versions
echo "python 3.13.1" >> .tool-versions

# Sync the change everywhere
./scripts/ci/sync_tool_versions.sh

# Verify everything is consistent
./scripts/ci/validate_tool_versions.sh

# Test the change
gitleaks version  # Should show 8.22.0 (if installed locally)

# Commit the changes
git add -A
git commit -m "Update gitleaks to 8.22.0"
```

## Supported Tools

Currently managed tools:

- **gitleaks** - Secret scanning and detection
- **terraform** - Infrastructure as Code
- **python** - Programming language version for CI/CD

## Files Updated by Sync Script

When you run `sync_tool_versions.sh`, these files are automatically updated:

- `setup_env.sh` - Updates `GITLEAKS_VERSION` and `TERRAFORM_VERSION` constants
- `.devcontainer/Dockerfile.prebuilt` - Updates gitleaks download URLs
- `.github/workflows/pre-commit.yml` - Updates gitleaks download URLs and Python version
- `.github/workflows/test-devcontainer.yml` - Updates Python and Terraform versions

## Integration with CI/CD

The version management system integrates with:

1. **Pre-commit hooks** - Ensures consistent gitleaks version between local and CI
1. **GitHub Actions** - Uses centralized versions for all workflows
1. **DevContainer** - Ensures development environment uses same tool versions
1. **Setup scripts** - Local development setup uses consistent versions

## Benefits

1. **Consistency** - All environments use the same tool versions
1. **Maintainability** - Update versions in one place
1. **Reliability** - Prevents version drift between local and CI
1. **Automation** - Scripts handle the tedious work of updating multiple files

## Troubleshooting

### Version Mismatch Errors

If `validate_tool_versions.sh` reports mismatches:

```bash
# Fix automatically
./scripts/ci/sync_tool_versions.sh

# Or fix manually by editing the specific files
```

### Gitleaks CI Failures

If gitleaks fails in CI but passes locally:

1. Check versions are consistent: `./scripts/ci/validate_tool_versions.sh`
1. Update local gitleaks: Install version from `.tool-versions`
1. Test locally: `gitleaks detect --source=. --config=.gitleaks.toml --no-git`

### Adding New Tools

To add a new tool to version management:

1. Add it to `.tool-versions`
1. Update `scripts/ci/sync_tool_versions.sh` to handle the new tool
1. Update `scripts/ci/validate_tool_versions.sh` to check the new tool
1. Test the changes

## Best Practices

1. **Always use the sync script** after updating `.tool-versions`
1. **Validate before committing** using the validation script
1. **Test locally** before pushing changes
1. **Update DevContainer** if tool versions change significantly
1. **Document breaking changes** in version updates
