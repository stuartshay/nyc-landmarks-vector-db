NYC Landmarks Vector Database - Package Management

## Dependency Management Strategy

This project implements a comprehensive dependency management strategy to ensure consistent and reproducible environments across development, testing, and production. The approach focuses on maintaining synchronization between direct dependencies in `setup.py` and the complete dependency tree in `requirements.txt`.

### Key Components

1. **setup.py**: Contains direct dependencies with version constraints (using `>=` format)
   - Core dependencies required for the package to function
   - Organized into base requirements and optional extra dependencies (dev, lint, coverage)
   - Specifies Python version requirements and other package metadata

2. **requirements.txt**: Comprehensive pinned dependency list generated via pip-compile
   - Contains exact versions (using `==` format) for all dependencies, including transitive ones
   - Auto-generated file that should not be manually edited
   - Ensures reproducible environments across different systems

3. **constraints.txt**: Constrains certain dependencies to specific versions
   - Used to avoid problematic versions or enforce specific dependency choices
   - Applied during pip-compile to generate requirements.txt

4. **manage_packages.sh**: Central script for managing dependencies
   - Provides unified interface for common dependency operations
   - Automates synchronization between setup.py and requirements.txt
   - Handles version updates and special cases (e.g., Pinecone SDK)

## Package Management Workflow

### Understanding the `manage_packages.sh` Script

The script provides several commands:

- `update`: Updates all packages to their latest compatible versions
  - Directly updates key packages in the virtual environment
  - Regenerates requirements.txt to reflect the changes
  - Synchronizes setup.py versions with requirements.txt

- `sync`: Synchronizes versions between requirements.txt and setup.py
  - Extracts package versions from requirements.txt
  - Updates matching packages in setup.py with the `>=` format
  - Regenerates requirements.txt if any changes were made to setup.py

- `pinecone`: Special command for updating the Pinecone SDK
  - Handles the special case of updating from pinecone-client to pinecone
  - Ensures proper version installation

- `check`: Lists outdated packages in the current environment

### Expected Behavior

When running `./manage_packages.sh sync`:

1. The script extracts package versions from `requirements.txt` (only direct lines with `==`)
2. It looks for matching packages in `setup.py` that use the `>=` version format
3. If found, it updates the version in `setup.py` to match the version in `requirements.txt`
4. If packages appear in `requirements.txt` but not in `setup.py` with the `>=` format, this is normal and expected behavior since:
   - `requirements.txt` includes all transitive dependencies (dependencies of dependencies)
   - `setup.py` only lists direct dependencies that the project explicitly depends on
   - Some packages in `requirements.txt` may be pulled in by other dependencies
   - Development dependencies might be listed in `setup.py` under `extras_require`
   - The script only updates packages that already exist in `setup.py` with the `>=` format

### Adding New Dependencies

When adding new dependencies to the project:

1. Add the dependency to `setup.py` with the appropriate version constraint (`>=version`)
2. Run `./manage_packages.sh sync` to update requirements.txt
3. Review the changes and commit both files

### Updating Dependencies

To update all dependencies:

1. Run `./manage_packages.sh update` to update all key packages
2. Review the changes to both files
3. Run tests to ensure compatibility with the updated versions
4. Commit the changes if tests pass

## Common Issues and Solutions

### Mismatched Versions

If versions in `setup.py` and `requirements.txt` become out of sync:
- Run `./manage_packages.sh sync` to synchronize them
- Review the changes to ensure they make sense

### Missing Dependencies in setup.py

If a package appears in `requirements.txt` but not in `setup.py`:
- Determine if it's a direct dependency or transitive dependency
- If direct, add it to `setup.py` in the appropriate section
- If transitive, no action is needed

### Dependency Conflicts

If pip-compile fails due to dependency conflicts:
- Add constraints to `constraints.txt` to resolve the conflicts
- Run `./manage_packages.sh sync` again

## Best Practices

1. Always use `manage_packages.sh` for dependency management operations
2. Never modify `requirements.txt` directly, as it's auto-generated
3. Add direct dependencies to `setup.py`, not requirements.txt
4. Run tests after updating dependencies to ensure compatibility
5. Always commit both `setup.py` and `requirements.txt` together
6. Document any special dependency handling in this file

## Example Commands

```bash
# Synchronize requirements.txt and setup.py
./manage_packages.sh sync

# Update all packages to their latest versions
./manage_packages.sh update

# Check for outdated packages
./manage_packages.sh check

# Update Pinecone SDK specifically
./manage_packages.sh pinecone
