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

To update dependencies in the future:

```bash
# Option 1: Direct update (simplest)
./direct_update.sh

# Option 2: Update setup.py first, then regenerate requirements
./update_dependencies.sh

# Option 3: Manual synchronization after Dependabot updates
./sync_versions.sh
```

## Testing Results

All tests were run to verify compatibility with the updated dependencies:

- Unit tests: ✅ All passing
- Functional tests: ✅ All passing

## Notes

- The updated dependencies maintain backward compatibility with the project's code.
- The package versions are now specified with `>=` in setup.py to allow for minor updates while still maintaining the requirements.txt pinned versions for reproducibility.
- Future automatic updates can be performed using these scripts on a regular basis.
