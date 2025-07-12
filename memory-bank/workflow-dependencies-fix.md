# GitHub Actions Workflow Dependencies Fix

## Issue Description

The "Build DevContainer" and "Test DevContainer" workflows were running simultaneously, which created several problems:

1. **Resource Contention**: Both workflows were building Docker images at the same time
1. **Race Conditions**: Tests might run before builds complete
1. **Inefficiency**: Redundant builds when tests should use built images
1. **Logic Error**: Testing should only happen after successful builds

## Root Cause Analysis

### Original Configuration

Both workflows had similar triggers:

**Build DevContainer** (`.github/workflows/build-devcontainer.yml`):

```yaml
on:
  push:
    branches: [master, develop]
    paths:
      - ".devcontainer/**"
      - "requirements.txt"
      - "setup.py"
      - "pyproject.toml"
  pull_request:
    branches: [master, develop]
    paths:
      - ".devcontainer/**"
      # ... more paths
```

**Test DevContainer** (`.github/workflows/test-devcontainer.yml`):

```yaml
on:
  push:
    branches: [master, develop]
    paths:
      - ".devcontainer/**"
  pull_request:
    branches: [master, develop]
    paths:
      - ".devcontainer/**"
```

### Problem

Both workflows triggered on changes to `.devcontainer/**`, causing parallel execution.

## Solution Implemented

### Changed Test DevContainer Trigger

Modified the Test DevContainer workflow to use `workflow_run` trigger:

```yaml
on:
  # Run after Build DevContainer workflow completes successfully
  workflow_run:
    workflows: ["Build DevContainer"]
    types:
      - completed
    branches: [master, develop]
  # Also allow manual triggering
  workflow_dispatch:
```

### Added Success Condition

Added a condition to only run tests if the build workflow succeeded:

```yaml
jobs:
  test-dockerfile:
    runs-on: ubuntu-latest
    # Only run if the Build DevContainer workflow succeeded
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'workflow_dispatch' }}
    steps:
      # ... rest of job
```

## Benefits of the Fix

1. **Sequential Execution**: Tests now wait for builds to complete
1. **Resource Efficiency**: No parallel Docker builds
1. **Logical Flow**: Build → Test is now enforced
1. **Failure Prevention**: Tests only run if builds succeed
1. **Manual Override**: Still allows manual triggering for testing

## Workflow Execution Flow

### Before Fix

```
PR/Push → Build DevContainer (starts immediately)
       → Test DevContainer (starts immediately)
       ↓
   [Both run in parallel - PROBLEM]
```

### After Fix

```
PR/Push → Build DevContainer (starts immediately)
       ↓
   [Build completes successfully]
       ↓
   Test DevContainer (triggered by workflow_run)
       ↓
   [Tests run with built images]
```

## Technical Details

### workflow_run Trigger

- Triggers when specified workflows complete
- Provides access to `github.event.workflow_run.conclusion`
- Supports filtering by branch and workflow name

### Condition Logic

- `github.event.workflow_run.conclusion == 'success'`: Only run if build succeeded
- `github.event_name == 'workflow_dispatch'`: Allow manual triggering
- Combined with OR operator for flexibility

## Files Modified

1. `.github/workflows/test-devcontainer.yml`:
   - Changed trigger from `push`/`pull_request` to `workflow_run`
   - Added success condition to first job
   - Maintained `workflow_dispatch` for manual testing

## Validation

- ✅ Build DevContainer completes first
- ✅ Test DevContainer triggers after build success
- ✅ Manual triggering still works
- ✅ No parallel execution observed
- ✅ Resource efficiency improved

## Future Considerations

1. **Monitoring**: Track workflow execution times
1. **Optimization**: Consider caching strategies between workflows
1. **Error Handling**: Add retry logic if needed
1. **Documentation**: Update contributor guidelines

## Related Documentation

- [Build DevContainer Workflow](../.github/workflows/build-devcontainer.yml)
- [Test DevContainer Workflow](../.github/workflows/test-devcontainer.yml)
- [GitHub Actions workflow_run Documentation](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
