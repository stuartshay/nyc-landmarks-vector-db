#!/bin/bash

# Build Information Display Script for Build-from-Source DevContainer
# Shows the container build timestamp in the terminal welcome message

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

BUILD_INFO_FILE="/etc/devcontainer-build-info"

# Function to display build information
show_build_info() {
    echo -e "${GREEN}👋 Welcome to NYC Landmarks Vector DB Development Environment (Build-from-Source)${NC}"

    if [ -f "$BUILD_INFO_FILE" ]; then
        BUILD_TIMESTAMP=$(cat "$BUILD_INFO_FILE" 2>/dev/null)
        if [ -n "$BUILD_TIMESTAMP" ]; then
            echo -e "${BLUE}📅 Build Date: ${BUILD_TIMESTAMP} UTC${NC}"
        else
            echo -e "${YELLOW}📅 Build Date: Unknown${NC}"
        fi
    else
        echo -e "${YELLOW}📅 Build Date: Unknown${NC}"
    fi

    echo ""
    echo -e "${BLUE}Use the VS Code task \"Check Development Environment\" to verify setup.${NC}"
    echo -e "${BLUE}Use the task \"Run All Tests\" to run the test suite.${NC}"
    echo ""

    # Check and display virtual environment status
    if [ -f "/workspaces/nyc-landmarks-vector-db/.venv/bin/activate" ]; then
        source /workspaces/nyc-landmarks-vector-db/.venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated automatically${NC}"
    elif [ -f "/workspaces/nyc-landmarks-vector-db/venv/bin/activate" ]; then
        source /workspaces/nyc-landmarks-vector-db/venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated automatically${NC}"
    else
        echo -e "${YELLOW}ℹ️  Virtual environment not found. Create one with: python -m venv .venv${NC}"
    fi
}

# Call the function
show_build_info
