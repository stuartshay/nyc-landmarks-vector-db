#!/bin/bash

# Debug script to identify mdformat issues
# This script helps identify which files are being modified by mdformat

set -e

echo "🔍 mdformat Debug Script"
echo "========================"

# Check if mdformat is available
if ! command -v mdformat &> /dev/null; then
    echo "❌ mdformat not found. Please install it first."
    exit 1
fi

echo "📋 mdformat version: $(mdformat --version)"
echo ""

# Find all markdown files
echo "📁 All markdown files in project:"
find . -name "*.md" | grep -v ".venv" | grep -v ".git" | sort
echo ""

# Test mdformat on specific directories (like in CI)
echo "🧪 Testing mdformat on specific directories:"
if mdformat --check --wrap keep docs/ memory-bank/ README.md CONTRIBUTING.md 2>&1; then
    echo "✅ mdformat check passed on specific directories"
else
    echo "❌ mdformat check failed on specific directories"
fi
echo ""

# Test individual files to find problematic ones
echo "🔍 Testing individual files:"
for file in docs/*.md memory-bank/*.md README.md CONTRIBUTING.md; do
    if [ -f "$file" ]; then
        echo "Testing: $file"
        if mdformat --check --wrap keep "$file" 2>/dev/null; then
            echo "  ✅ $file - OK"
        else
            echo "  ❌ $file - would be modified"
            echo "    Current content (first 3 lines):"
            head -3 "$file" | sed 's/^/      /'
            echo "    After mdformat (first 3 lines):"
            mdformat --wrap keep "$file" --stdout 2>/dev/null | head -3 | sed 's/^/      /' || echo "      [Failed to format]"
            echo ""
        fi
    fi
done

# Check git status
echo "📊 Git status:"
git status --porcelain || echo "No changes"
echo ""

# Test the pre-commit hook specifically
echo "🚀 Testing pre-commit mdformat hook:"
if pre-commit run mdformat --all-files; then
    echo "✅ pre-commit mdformat hook passed"
else
    echo "❌ pre-commit mdformat hook failed"
fi

echo ""
echo "🏁 Debug script completed"
