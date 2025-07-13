#!/bin/bash
# validate_tool_versions.sh
#
# This script validates that tool versions are consistent across all configuration files
#
# Usage: ./scripts/ci/validate_tool_versions.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔍 Validating tool version consistency across configuration files"

# Load expected versions from .tool-versions
TOOL_VERSIONS_FILE="$PROJECT_ROOT/.tool-versions"
EXPECTED_GITLEAKS=$(grep "^gitleaks " "$TOOL_VERSIONS_FILE" | awk '{print $2}')
EXPECTED_TERRAFORM=$(grep "^terraform " "$TOOL_VERSIONS_FILE" | awk '{print $2}')
EXPECTED_PYTHON=$(grep "^python " "$TOOL_VERSIONS_FILE" | awk '{print $2}')

echo "📋 Expected versions from .tool-versions:"
echo "  Gitleaks: $EXPECTED_GITLEAKS"
echo "  Terraform: $EXPECTED_TERRAFORM"
echo "  Python: $EXPECTED_PYTHON"

# Track validation errors
ERRORS=()

# Function to check a version in a file
check_version() {
    local file="$1"
    local tool="$2"
    local expected="$3"
    local pattern="$4"

    if [[ ! -f "$file" ]]; then
        echo "⚠️  File not found: $file"
        return 0
    fi

    local found_version
    found_version=$(grep -oP "$pattern" "$file" 2>/dev/null | head -n1)

    if [[ -n "$found_version" ]]; then
        if [[ "$found_version" == "$expected" ]]; then
            echo "✅ $file: $tool version $found_version (correct)"
        else
            echo "❌ $file: $tool version $found_version (expected $expected)"
            ERRORS+=("$file: $tool version mismatch")
        fi
    else
        echo "🔄 $file: No $tool version found (may not use this tool)"
    fi
}

echo ""
echo "🔄 Checking version consistency..."

# Check gitleaks versions
check_version "$PROJECT_ROOT/setup_env.sh" "gitleaks" "$EXPECTED_GITLEAKS" 'readonly GITLEAKS_VERSION="\K[^"]*'
check_version "$PROJECT_ROOT/.devcontainer/Dockerfile.prebuilt" "gitleaks" "$EXPECTED_GITLEAKS" 'gitleaks_\K[0-9.]*[0-9]'
check_version "$PROJECT_ROOT/.github/workflows/pre-commit.yml" "gitleaks" "$EXPECTED_GITLEAKS" 'gitleaks_\K[0-9.]*[0-9]'

# Check terraform versions
check_version "$PROJECT_ROOT/setup_env.sh" "terraform" "$EXPECTED_TERRAFORM" 'readonly TERRAFORM_VERSION="\K[^"]*'

# Check python versions
check_version "$PROJECT_ROOT/.github/workflows/pre-commit.yml" "python" "$EXPECTED_PYTHON" 'python-version: "\K[^"]*'

echo ""
echo "📊 Validation Summary:"
if [[ ${#ERRORS[@]} -eq 0 ]]; then
    echo "✅ All tool versions are consistent!"
    exit 0
else
    echo "❌ Found ${#ERRORS[@]} version inconsistency(ies):"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
    echo ""
    echo "🔧 To fix: Run ./scripts/ci/sync_tool_versions.sh"
    exit 1
fi
