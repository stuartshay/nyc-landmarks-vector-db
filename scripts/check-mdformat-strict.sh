#!/bin/bash
# Script to check mdformat with strict failure on warnings (matching CI behavior)

set -e

echo "🔍 Running mdformat with strict warning detection..."

# Create temporary file for output
temp_output=$(mktemp)

# Run mdformat and capture output
if pre-commit run mdformat --all-files --verbose > "$temp_output" 2>&1; then
    # Show the output
    cat "$temp_output"

    # Check for warnings
    if grep -q "Warning:" "$temp_output"; then
        echo ""
        echo "❌ mdformat warnings detected - this would fail in CI!"
        echo "🔧 Fix the Python code blocks mentioned above."
        rm "$temp_output"
        exit 1
    else
        echo ""
        echo "✅ No mdformat warnings detected - CI should pass!"
        rm "$temp_output"
        exit 0
    fi
else
    # mdformat itself failed
    cat "$temp_output"
    echo ""
    echo "❌ mdformat hook failed!"
    rm "$temp_output"
    exit 1
fi
