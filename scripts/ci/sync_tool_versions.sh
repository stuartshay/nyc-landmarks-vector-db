#!/bin/bash
# sync_tool_versions.sh
#
# This script synchronizes tool versions from .tool-versions across all configuration files
# including setup scripts, Dockerfiles, and GitHub Actions workflows.
#
# Usage: ./scripts/ci/sync_tool_versions.sh
#
# Note: This script is designed to be run from the root directory of the project.

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔧 Synchronizing tool versions from .tool-versions"
echo "Project root: $PROJECT_ROOT"

# Load versions from .tool-versions
TOOL_VERSIONS_FILE="$PROJECT_ROOT/.tool-versions"

if [[ ! -f "$TOOL_VERSIONS_FILE" ]]; then
    echo "❌ Error: .tool-versions file not found at $TOOL_VERSIONS_FILE"
    exit 1
fi

# Extract versions
GITLEAKS_VERSION=$(grep "^gitleaks " "$TOOL_VERSIONS_FILE" | awk '{print $2}')
TERRAFORM_VERSION=$(grep "^terraform " "$TOOL_VERSIONS_FILE" | awk '{print $2}')
PYTHON_VERSION=$(grep "^python " "$TOOL_VERSIONS_FILE" | awk '{print $2}')

echo "📋 Tool versions from .tool-versions:"
echo "  Gitleaks: $GITLEAKS_VERSION"
echo "  Terraform: $TERRAFORM_VERSION"
echo "  Python: $PYTHON_VERSION"

# Validate versions
if [[ -z "$GITLEAKS_VERSION" ]] || [[ -z "$TERRAFORM_VERSION" ]] || [[ -z "$PYTHON_VERSION" ]]; then
    echo "❌ Error: Could not load all required versions from .tool-versions"
    exit 1
fi

MODIFIED_FILES=()

# Function to update a file if it exists
update_file_if_exists() {
    local file="$1"
    local description="$2"

    if [[ ! -f "$file" ]]; then
        echo "⚠️  File not found: $file"
        return 0
    fi

    local original_content
    original_content=$(cat "$file")

    # Create temporary file for modifications
    local temp_file="${file}.tmp"
    cp "$file" "$temp_file"

    # Apply updates to temp file
    case "$file" in
        */setup_env.sh)
            sed -i "s/readonly GITLEAKS_VERSION=\"[^\"]*\"/readonly GITLEAKS_VERSION=\"$GITLEAKS_VERSION\"/" "$temp_file"
            sed -i "s/readonly TERRAFORM_VERSION=\"[^\"]*\"/readonly TERRAFORM_VERSION=\"$TERRAFORM_VERSION\"/" "$temp_file"
            ;;
        *Dockerfile*)
            sed -i "s|gitleaks/releases/download/v[0-9.]*[0-9]/|gitleaks/releases/download/v$GITLEAKS_VERSION/|g" "$temp_file"
            sed -i "s|gitleaks_[0-9.]*[0-9]_linux|gitleaks_${GITLEAKS_VERSION}_linux|g" "$temp_file"
            ;;
        *.yml|*.yaml)
            sed -i "s|gitleaks/releases/download/v[0-9.]*[0-9]/|gitleaks/releases/download/v$GITLEAKS_VERSION/|g" "$temp_file"
            sed -i "s|gitleaks_[0-9.]*[0-9]_linux|gitleaks_${GITLEAKS_VERSION}_linux|g" "$temp_file"
            sed -i "s|python-version: \"[0-9.]*[0-9]\"|python-version: \"$PYTHON_VERSION\"|g" "$temp_file"
            sed -i "s|terraform_version: \"~[0-9.]*[0-9]\"|terraform_version: \"~$TERRAFORM_VERSION\"|g" "$temp_file"
            sed -i "s|terraform-version: \"~[0-9.]*[0-9]\"|terraform-version: \"~$TERRAFORM_VERSION\"|g" "$temp_file"
            ;;
    esac

    # Check if file was actually modified
    if ! diff -q "$file" "$temp_file" > /dev/null 2>&1; then
        mv "$temp_file" "$file"
        MODIFIED_FILES+=("$file")
        echo "✅ Updated: $description"
    else
        rm "$temp_file"
        echo "🔄 No changes: $description"
    fi
}

echo ""
echo "🔄 Updating configuration files..."

# Update key files
update_file_if_exists "$PROJECT_ROOT/setup_env.sh" "setup_env.sh (gitleaks & terraform versions)"
update_file_if_exists "$PROJECT_ROOT/.devcontainer/Dockerfile.prebuilt" "DevContainer Dockerfile (gitleaks version)"
update_file_if_exists "$PROJECT_ROOT/.github/workflows/pre-commit.yml" "GitHub Actions pre-commit workflow"
update_file_if_exists "$PROJECT_ROOT/.github/workflows/test-devcontainer.yml" "GitHub Actions test-devcontainer workflow"

echo ""
echo "📊 Summary:"
if [[ ${#MODIFIED_FILES[@]} -eq 0 ]]; then
    echo "✅ All files are already synchronized with .tool-versions!"
else
    echo "📝 Updated ${#MODIFIED_FILES[@]} file(s):"
    for file in "${MODIFIED_FILES[@]}"; do
        echo "  - $file"
    done

    echo ""
    echo "🎯 Next steps:"
    echo "  1. Review changes: git diff"
    echo "  2. Test locally: gitleaks detect --source=. --config=.gitleaks.toml --no-git"
    echo "  3. Commit: git add -A && git commit -m 'Sync tool versions from .tool-versions'"
fi

echo ""
echo "✅ Tool version synchronization complete!"
