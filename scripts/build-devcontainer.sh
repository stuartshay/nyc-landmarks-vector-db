#!/bin/bash
# Build DevContainer with centralized tool versions
# Usage: ./scripts/build-devcontainer.sh [tag]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source the versions
source "$SCRIPT_DIR/versions.sh"

# Default tag if not provided
TAG="${1:-nyc-landmarks-devcontainer:local}"

echo "Building DevContainer with tool versions:"
echo "  Gitleaks: $GITLEAKS_VERSION"
echo "  Tag: $TAG"

# Build the container with version build args
docker build \
    -f "$PROJECT_ROOT/.devcontainer/Dockerfile.prebuilt" \
    --build-arg "GITLEAKS_VERSION=$GITLEAKS_VERSION" \
    --build-arg "BUILD_TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M:%S')" \
    -t "$TAG" \
    "$PROJECT_ROOT"

echo "✅ DevContainer built successfully with tag: $TAG"
echo "🔍 Verify gitleaks version:"
docker run --rm "$TAG" gitleaks version
