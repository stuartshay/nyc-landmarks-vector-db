#!/bin/bash
# generate_tool_lock.sh
#
# Generates a tool version lock file similar to requirements.txt
# This captures the exact state of all tools for reproducible builds
#
# Usage: ./scripts/ci/generate_tool_lock.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

TOOL_VERSIONS_FILE="$PROJECT_ROOT/.tool-versions"
LOCK_FILE="$PROJECT_ROOT/.tool-versions.lock"

if [[ ! -f "$TOOL_VERSIONS_FILE" ]]; then
    echo "❌ ERROR: .tool-versions file not found"
    exit 1
fi

echo "🔒 Generating tool version lock file..."

# Create lock file header
cat > "$LOCK_FILE" << 'EOF'
# Tool Version Lock File
# Generated automatically - DO NOT EDIT MANUALLY
# This file pins exact versions for reproducible builds
#
# To update versions:
#   1. Edit .tool-versions
#   2. Run ./scripts/ci/generate_tool_lock.sh
#   3. Commit both files together
#
# Generated on: $(date -u '+%Y-%m-%d %H:%M:%S UTC')

EOF

# Add generation timestamp
sed -i "s/Generated on: .*/Generated on: $(date -u '+%Y-%m-%d %H:%M:%S UTC')/" "$LOCK_FILE"

# Process each tool version
echo "📋 Processing tool versions:"
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
        echo "$line" >> "$LOCK_FILE"
        continue
    fi

    # Parse tool and version
    if [[ "$line" =~ ^([a-zA-Z0-9_-]+)[[:space:]]+(.+)$ ]]; then
        tool="${BASH_REMATCH[1]}"
        version="${BASH_REMATCH[2]}"

        echo "  ✅ $tool==$version"
        echo "$tool==$version" >> "$LOCK_FILE"
    fi
done < "$TOOL_VERSIONS_FILE"

echo ""
echo "🎯 Lock file generated: .tool-versions.lock"
echo "💡 Commit this file alongside .tool-versions for version tracking"

# Show diff if lock file existed before
if [[ -f "$LOCK_FILE.backup" ]]; then
    echo ""
    echo "📊 Changes from previous lock:"
    diff "$LOCK_FILE.backup" "$LOCK_FILE" || true
    rm -f "$LOCK_FILE.backup"
fi
