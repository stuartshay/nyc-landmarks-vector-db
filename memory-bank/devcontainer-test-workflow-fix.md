# DevContainer Test Workflow Fix

## Issue Description

The GitHub Actions workflow `test-devcontainer.yml` was failing because:

1. **Container persistence problem**: Virtual environment `.venv` created in one step wasn't available in subsequent steps
1. **Image reference mismatch**: Test workflow was building images locally instead of using the pre-built images from GHCR
1. **Dependabot interference**: Build workflow was running unnecessarily on dependabot branches
1. **Workflow dependency issues**: Test workflow wasn't receiving the correct image tag from the build workflow

## Root Cause Analysis

### Primary Issues Identified:

1. **Container Persistence**: Each test step ran in separate `docker run --rm` commands, losing state between steps
1. **Image Source**: Test workflow rebuilt images locally instead of pulling from GitHub Container Registry (GHCR)
1. **Branch Filtering**: Build workflow lacked dependabot branch filtering, causing unnecessary builds
1. **Communication Gap**: Build workflow didn't pass the specific image tag to test workflow

## Solution Implemented

### 1. **Fixed Build Workflow (`build-devcontainer.yml`)**

#### Added Dependabot Filtering:

```yaml
build:
  runs-on: ubuntu-latest
  # Prevent running on dependabot branches
  if: github.actor != 'dependabot[bot]' && !startsWith(github.head_ref, 'dependabot/')
```

#### Updated Test Triggering:

```yaml
trigger-tests:
  runs-on: ubuntu-latest
  needs: [build]  # Removed build-dockerhub dependency
  if: success() && github.actor != 'dependabot[bot]'
  steps:
    - name: Trigger Test DevContainer workflow
      uses: actions/github-script@v7
      with:
        script: |
          const imageTag = `ghcr.io/${{ github.repository_owner }}/nyc-landmarks-devcontainer:${{ github.ref_name }}`;
          const result = await github.rest.actions.createWorkflowDispatch({
            owner: context.repo.owner,
            repo: context.repo.repo,
            workflow_id: 'test-devcontainer.yml',
            ref: context.ref,
            inputs: {
              triggered_by: 'build-devcontainer',
              build_run_id: '${{ github.run_id }}',
              image_tag: imageTag  # Pass specific GHCR image tag
            }
          });
```

### 2. **Fixed Test Workflow (`test-devcontainer.yml`)**

#### Added Image Tag Input:

```yaml
on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: "Container image tag to test"
        required: false
        default: "ghcr.io/stuartshay/nyc-landmarks-devcontainer:latest"
        type: string
```

#### Replaced Local Builds with GHCR Pulls:

```yaml
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Pull pre-built image
  run: |
    IMAGE_TAG="${{ inputs.image_tag || 'ghcr.io/stuartshay/nyc-landmarks-devcontainer:latest' }}"
    echo "Pulling image: ${IMAGE_TAG}"
    docker pull "${IMAGE_TAG}"
    docker tag "${IMAGE_TAG}" test:latest
    echo "✅ Image pulled and tagged as test:latest"
```

#### Maintained Consolidated Test Steps:

The comprehensive environment setup test continues to run all validations in a single container instance to ensure state persistence.

### Test Coverage

The workflow now validates:

1. **Container Functionality**

   - Basic Python/pip functionality
   - Pre-installed packages availability

1. **Post-create Script Execution**

   - Virtual environment creation
   - Package installations in venv
   - Project package installation
   - Pre-commit hooks setup

1. **DevContainer Configuration**

   - JSON syntax validation
   - Script syntax validation
   - Workflow syntax validation

## Benefits of the Fix

1. **Efficiency**:

   - No unnecessary builds on dependabot branches
   - Faster tests using pre-built images from GHCR
   - Reduced GitHub Actions minutes usage

1. **Reliability**:

   - Tests the exact same image that was built
   - Container persistence ensures state consistency
   - Proper GHCR authentication

1. **Maintainability**:

   - Clear separation between build and test workflows
   - Better error reporting and debugging information
   - Consistent image tagging strategy

1. **Resource Optimization**:

   - Prevents redundant container builds
   - Uses GitHub's container registry infrastructure
   - Eliminates Docker Hub dependencies for testing

## Files Modified

- `.github/workflows/build-devcontainer.yml`: Added dependabot filtering, updated trigger mechanism
- `.github/workflows/test-devcontainer.yml`: Added GHCR image pulling, removed local builds
- `memory-bank/devcontainer-test-workflow-fix.md`: Updated documentation

## Validation

- ✅ YAML syntax validated
- ✅ Bash script syntax validated
- ✅ Workflow structure verified
- ✅ Container persistence issue resolved
- ✅ GHCR image reference implemented
- ✅ Dependabot filtering added
- ✅ Image tag passing mechanism implemented

## Key Improvements

1. **Dependabot Exclusion**: Build workflow no longer runs on dependabot branches
1. **GHCR Integration**: Test workflow pulls from GitHub Container Registry instead of rebuilding
1. **Image Tag Communication**: Build workflow passes specific image tag to test workflow
1. **Authentication**: Proper GHCR authentication for image pulling
1. **Fallback Support**: Manual workflow runs still work with default image tags

## Related Documentation

- [DevContainer Test Workflow](../.github/workflows/test-devcontainer.yml)
- [DevContainer Build Workflow](../.github/workflows/build-devcontainer.yml)
- [Post-create Script](../.devcontainer/post-create-prebuilt.sh)
- [Contributing Guidelines](../CONTRIBUTING.md)
