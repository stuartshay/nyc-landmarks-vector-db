#!/bin/bash
# sync_versions.sh - Script to synchronize package versions between setup.py and requirements.txt
# This script ensures that when Dependabot updates dependencies in requirements.txt,
# the corresponding versions in setup.py are also updated.

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

echo -e "${BLUE}Synchronizing package versions between setup.py and requirements.txt...${NC}"

# Location of files
SETUP_PY="setup.py"
REQUIREMENTS_TXT="requirements.txt"

# Check if files exist
if [ ! -f "$SETUP_PY" ]; then
    echo -e "${RED}Error: $SETUP_PY not found${NC}"
    exit 1
fi

if [ ! -f "$REQUIREMENTS_TXT" ]; then
    echo -e "${RED}Error: $REQUIREMENTS_TXT not found${NC}"
    exit 1
fi

# Create a temp file
TEMP_FILE=$(mktemp)

# Extract package versions from requirements.txt
echo -e "${BLUE}Extracting package versions from requirements.txt...${NC}"

# Parse the requirements.txt file - extract only lines with == and no indentation
grep -E "^[a-zA-Z0-9_-]+==.*$" "$REQUIREMENTS_TXT" | sort > "$TEMP_FILE"

# Update packages in setup.py
echo -e "${BLUE}Updating packages in setup.py...${NC}"

UPDATED=0

# Read through each line in temp file
while read -r line; do
    # Split the line into package name and version
    PKG_NAME=$(echo "$line" | cut -d'=' -f1)
    PKG_VERSION=$(echo "$line" | cut -d'=' -f3)

    # Skip if either is empty
    if [ -z "$PKG_NAME" ] || [ -z "$PKG_VERSION" ]; then
        continue
    fi

    # Check if package exists in setup.py with >= version specifier
    if grep -q "\"$PKG_NAME>=" "$SETUP_PY"; then
        # Extract current version in setup.py
        CURRENT_VERSION=$(grep -o "\"$PKG_NAME>=.*\"" "$SETUP_PY" | cut -d'>' -f2 | cut -d'=' -f2 | cut -d'"' -f1)

        # Compare versions and update if necessary (only comparing numbers, not equality)
        if [ "$CURRENT_VERSION" != "$PKG_VERSION" ]; then
            echo -e "${YELLOW}Updating $PKG_NAME: $CURRENT_VERSION -> $PKG_VERSION${NC}"
            # Use perl for more reliable replacement
            perl -i -pe "s/\"$PKG_NAME>=$CURRENT_VERSION\"/\"$PKG_NAME>=$PKG_VERSION\"/g" "$SETUP_PY"
            UPDATED=1
        fi
    else
        echo -e "${BLUE}Package $PKG_NAME found in requirements.txt but not in setup.py with >= format${NC}"
    fi
done < "$TEMP_FILE"

# Clean up
rm "$TEMP_FILE"

# After updating setup.py, regenerate requirements.txt if changes were made
if [ $UPDATED -eq 1 ]; then
    echo -e "${YELLOW}Changes made to setup.py, regenerating requirements.txt...${NC}"

    # Check if pip-compile is installed
    if command -v pip-compile &> /dev/null; then
        pip-compile --constraint=constraints.txt --output-file=requirements.txt
    else
        echo -e "${RED}Warning: pip-compile not found. Please install it with:${NC}"
        echo -e "${BLUE}pip install pip-tools${NC}"
        echo -e "${RED}Then regenerate requirements.txt manually.${NC}"
    fi
fi

echo -e "${GREEN}Version synchronization complete!${NC}"

# Instructions for next steps
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Review changes to setup.py and requirements.txt"
echo -e "2. Commit changes if they look good:"
echo -e "   git add setup.py requirements.txt"
echo -e "   git commit -m \"Sync package versions between setup.py and requirements.txt\""
echo -e "3. Push changes to your branch"
