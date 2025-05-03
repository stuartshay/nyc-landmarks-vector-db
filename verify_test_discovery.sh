#!/bin/bash
# Test Discovery Verification Script
# This script helps verify that pytest can properly discover tests

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Verifying test discovery...${NC}"

# Activate the virtual environment
source venv311/bin/activate

# Check pytest version
echo -e "${BLUE}Pytest version:${NC}"
pytest --version

# Collect tests only (no execution)
echo -e "\n${BLUE}Discovered tests:${NC}"
pytest --collect-only -v

echo -e "\n${BLUE}Test discovery complete.${NC}"
echo -e "${YELLOW}If you don't see your tests listed above, check your test naming and structure.${NC}"
echo -e "${YELLOW}Tests should follow the pattern: test_*.py with test_* functions.${NC}"

# VS Code specific instructions
echo -e "\n${BLUE}VS Code Test Explorer:${NC}"
echo -e "1. Open the Testing view in VS Code (flask icon in the sidebar)"
echo -e "2. Click the refresh button if tests aren't visible"
echo -e "3. Tests should be organized by file and test function"
echo -e "4. You can run individual tests by clicking the play button next to them"
