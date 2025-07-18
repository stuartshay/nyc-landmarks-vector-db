#!/bin/bash
# Version management utility for NYC Landmarks Vector DB
# Usage: source scripts/versions.sh to load version variables

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOL_VERSIONS_FILE="$PROJECT_ROOT/.tool-versions"

# Function to get version from .tool-versions file
get_tool_version() {
    local tool_name="$1"
    if [[ -f "$TOOL_VERSIONS_FILE" ]]; then
        grep "^$tool_name " "$TOOL_VERSIONS_FILE" | awk '{print $2}' | head -n1
    else
        echo "ERROR: .tool-versions file not found at $TOOL_VERSIONS_FILE" >&2
        return 1
    fi
}

# Export version variables
export GITLEAKS_VERSION=$(get_tool_version "gitleaks")
export TERRAFORM_VERSION=$(get_tool_version "terraform")
export PYTHON_VERSION=$(get_tool_version "python")
export MDFORMAT_VERSION=$(get_tool_version "mdformat")
export MDFORMAT_GFM_VERSION=$(get_tool_version "mdformat-gfm")
export MDFORMAT_BLACK_VERSION=$(get_tool_version "mdformat-black")
export MDFORMAT_FRONTMATTER_VERSION=$(get_tool_version "mdformat-frontmatter")
export MDFORMAT_FOOTNOTE_VERSION=$(get_tool_version "mdformat-footnote")

# Validate that versions were loaded
if [[ -z "$GITLEAKS_VERSION" ]]; then
    echo "WARNING: Could not load gitleaks version from .tool-versions" >&2
fi

if [[ -z "$TERRAFORM_VERSION" ]]; then
    echo "WARNING: Could not load terraform version from .tool-versions" >&2
fi

if [[ -z "$PYTHON_VERSION" ]]; then
    echo "WARNING: Could not load python version from .tool-versions" >&2
fi

# Function to display all loaded versions
show_versions() {
    echo "=== Tool Versions ==="
    echo "Gitleaks: ${GITLEAKS_VERSION:-'NOT SET'}"
    echo "Terraform: ${TERRAFORM_VERSION:-'NOT SET'}"
    echo "Python: ${PYTHON_VERSION:-'NOT SET'}"
    echo "mdformat: ${MDFORMAT_VERSION:-'NOT SET'}"
    echo "mdformat-gfm: ${MDFORMAT_GFM_VERSION:-'NOT SET'}"
    echo "mdformat-black: ${MDFORMAT_BLACK_VERSION:-'NOT SET'}"
    echo "mdformat-frontmatter: ${MDFORMAT_FRONTMATTER_VERSION:-'NOT SET'}"
    echo "mdformat-footnote: ${MDFORMAT_FOOTNOTE_VERSION:-'NOT SET'}"
    echo "===================="
}

# If script is run directly (not sourced), show versions
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    show_versions
fi
