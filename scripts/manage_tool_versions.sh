#!/bin/bash
# manage_tool_versions.sh
#
# Comprehensive tool version management similar to pip-tools
#
# Usage:
#   ./scripts/manage_tool_versions.sh list              # List current versions
#   ./scripts/manage_tool_versions.sh check             # Check for updates
#   ./scripts/manage_tool_versions.sh update [tool]     # Update tool(s)
#   ./scripts/manage_tool_versions.sh freeze            # Generate lock file
#   ./scripts/manage_tool_versions.sh validate          # Validate consistency

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TOOL_VERSIONS_FILE="$PROJECT_ROOT/.tool-versions"
LOCK_FILE="$PROJECT_ROOT/.tool-versions.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Load versions from .tool-versions
load_versions() {
    if [[ ! -f "$TOOL_VERSIONS_FILE" ]]; then
        log_error ".tool-versions file not found"
        exit 1
    fi

    declare -g -A TOOL_VERSIONS
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ ^([a-zA-Z0-9_-]+)[[:space:]]+(.+)$ ]]; then
            tool="${BASH_REMATCH[1]}"
            version="${BASH_REMATCH[2]}"
            TOOL_VERSIONS["$tool"]="$version"
        fi
    done < "$TOOL_VERSIONS_FILE"
}

# List current tool versions
cmd_list() {
    log_info "Current tool versions:"
    echo ""

    load_versions

    for tool in "${!TOOL_VERSIONS[@]}"; do
        version="${TOOL_VERSIONS[$tool]}"
        echo "📦 $tool: $version"

        # Show installation status if tool is available
        case "$tool" in
            "gitleaks")
                if command -v gitleaks >/dev/null 2>&1; then
                    local_version=$(gitleaks version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "unknown")
                    if [[ "$local_version" == "$version" ]]; then
                        echo "   └─ ✅ Installed: $local_version"
                    else
                        echo "   └─ ⚠️  Installed: $local_version (expected: $version)"
                    fi
                else
                    echo "   └─ ❌ Not installed"
                fi
                ;;
            "terraform")
                if command -v terraform >/dev/null 2>&1; then
                    local_version=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || echo "unknown")
                    if [[ "$local_version" == "$version" ]]; then
                        echo "   └─ ✅ Installed: $local_version"
                    else
                        echo "   └─ ⚠️  Installed: $local_version (expected: $version)"
                    fi
                else
                    echo "   └─ ❌ Not installed"
                fi
                ;;
            "python")
                if command -v python3 >/dev/null 2>&1; then
                    local_version=$(python3 --version 2>&1 | grep -oP 'Python \K[0-9.]+' || echo "unknown")
                    if [[ "$local_version" == "$version" ]]; then
                        echo "   └─ ✅ Installed: $local_version"
                    else
                        echo "   └─ ⚠️  Installed: $local_version (expected: $version)"
                    fi
                else
                    echo "   └─ ❌ Not installed"
                fi
                ;;
        esac
        echo ""
    done
}

# Check for available updates
cmd_check() {
    log_info "Checking for tool updates..."
    echo ""

    load_versions

    local updates_available=false

    for tool in "${!TOOL_VERSIONS[@]}"; do
        current_version="${TOOL_VERSIONS[$tool]}"
        echo "🔍 Checking $tool (current: $current_version)"

        case "$tool" in
            "gitleaks")
                # Check GitHub releases for latest version
                latest_version=$(curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | jq -r '.tag_name' | sed 's/^v//')
                ;;
            "terraform")
                # Check HashiCorp releases
                latest_version=$(curl -s https://api.releases.hashicorp.com/v1/releases/terraform | jq -r '.[0].version')
                ;;
            "python")
                # This is more complex, would need Python.org API or manual checking
                latest_version="manual-check-required"
                ;;
            *)
                latest_version="unknown"
                ;;
        esac

        if [[ "$latest_version" == "manual-check-required" ]]; then
            echo "   └─ ⚠️  Manual check required for latest version"
        elif [[ "$latest_version" == "unknown" ]]; then
            echo "   └─ ❓ Unable to check for updates"
        elif [[ "$latest_version" != "$current_version" ]]; then
            echo "   └─ 🆙 Update available: $latest_version"
            updates_available=true
        else
            echo "   └─ ✅ Up to date"
        fi
        echo ""
    done

    if [[ "$updates_available" == true ]]; then
        echo ""
        log_warning "Updates are available. Use 'update' command to upgrade tools."
    else
        log_success "All tools are up to date!"
    fi
}

# Generate lock file
cmd_freeze() {
    log_info "Generating tool version lock file..."

    if [[ -f "$LOCK_FILE" ]]; then
        cp "$LOCK_FILE" "$LOCK_FILE.backup"
    fi

    "$SCRIPT_DIR/ci/generate_tool_lock.sh"

    log_success "Lock file generated: .tool-versions.lock"
}

# Validate version consistency
cmd_validate() {
    log_info "Validating tool version consistency..."
    "$SCRIPT_DIR/ci/validate_tool_versions.sh"
}

# Show usage
show_usage() {
    echo "🔧 Tool Version Manager for NYC Landmarks Vector DB"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  list       List current tool versions and installation status"
    echo "  check      Check for available updates"
    echo "  freeze     Generate .tool-versions.lock file"
    echo "  validate   Validate version consistency across configs"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 list                    # Show current versions"
    echo "  $0 check                   # Check for updates"
    echo "  $0 freeze                  # Generate lock file"
    echo ""
}

# Main command dispatcher
case "${1:-help}" in
    "list")
        cmd_list
        ;;
    "check")
        cmd_check
        ;;
    "freeze")
        cmd_freeze
        ;;
    "validate")
        cmd_validate
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
