# Dependency Updates

**Date**: May 4, 2025
**Author**: GitHub Copilot

## Summary

This document summarizes the dependency updates made to the NYC Landmarks Vector DB project. All Python packages have been updated to their latest compatible versions to ensure the project uses the most recent, secure, and feature-rich dependencies.

## Key Updates

Major package versions updated:

| Package | Previous Version | New Version |
|---------|-----------------|-------------|
| numpy | 1.26.0 | 2.2.5 |
| pandas | 2.2.0 | 2.2.3 |
| openai | 1.75.0 | 1.77.0 |
| pydantic | 2.11.3 | 2.11.4 |
| pydantic-settings | 2.2.1 | 2.9.1 |
| azure-core | 1.33.0 | 1.34.0 |
| certifi | 2025.1.31 | 2025.4.26 |
| h11 | 0.14.0 | 0.16.0 |
| httpcore | 1.0.8 | 1.0.9 |
| cryptography | 44.0.2 | 44.0.3 |
| charset-normalizer | 3.4.1 | 3.4.2 |
| joblib | 1.4.2 | 1.5.0 |

## Tools Created

Three new utility scripts were created to facilitate dependency management:

1. **direct_update.sh**: Directly updates all key packages in the virtual environment to their latest versions.

2. **update_setup_versions.py**: Python script that updates dependency version specifications in setup.py to match the latest available versions.

3. **update_dependencies.sh**: Orchestrates the update process, regenerating requirements.txt after updating setup.py.

## Usage

To manage dependencies in the future, use the consolidated script with different commands:

```bash
# Update all packages to their latest versions
./manage_packages.sh update

# Sync versions between requirements.txt and setup.py
./manage_packages.sh sync

# Update Pinecone SDK specifically
./manage_packages.sh pinecone

# Check for outdated packages
./manage_packages.sh check

# Show help information
./manage_packages.sh help
```

## Testing Results

All tests were run to verify compatibility with the updated dependencies:

- Unit tests: ✅ All passing
- Functional tests: ✅ All passing

## Notes

- The updated dependencies maintain backward compatibility with the project's code.
- The package versions are now specified with `>=` in setup.py to allow for minor updates while still maintaining the requirements.txt pinned versions for reproducibility.
- Future automatic updates can be performed using these scripts on a regular basis.
