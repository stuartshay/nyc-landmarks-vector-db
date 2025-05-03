# Dependabot Sync Instructions

This file provides instructions for Dependabot to understand our dependency management workflow.

## Version Management

- `requirements.txt` is the source of truth for exact versions
- `setup.py` contains flexible version ranges (using `>=`)
- After Dependabot updates `requirements.txt`, our GitHub workflow runs `sync_versions.sh` 
  to update the corresponding versions in `setup.py`

## Workflow

1. Dependabot creates a PR updating dependency versions in `requirements.txt`
2. Our GitHub workflow automatically syncs these changes to `setup.py`
3. The workflow commits these changes to the PR
4. Once approved, the PR keeps both files in sync

## Manual Process

If you need to manually sync versions between `requirements.txt` and `setup.py`:

```bash
# Make the script executable if not already
chmod +x sync_versions.sh

# Run the script
./sync_versions.sh

# Regenerate requirements.txt if needed
pip-compile --constraint=constraints.txt --output-file=requirements.txt
```

## Additional Notes

- Never modify both files manually - use the workflow
- Always commit changes to both files together
- For new packages, add them to `setup.py` first, then generate `requirements.txt`
