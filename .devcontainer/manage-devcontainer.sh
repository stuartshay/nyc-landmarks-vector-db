#!/bin/bash

# DevContainer Management Script
# This script helps switch between different DevContainer configurations

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

DEVCONTAINER_DIR="/workspaces/nyc-landmarks-vector-db/.devcontainer"
ORIGINAL_CONFIG="$DEVCONTAINER_DIR/devcontainer.json"
PREBUILT_CONFIG="$DEVCONTAINER_DIR/devcontainer.prebuilt.json"
BACKUP_CONFIG="$DEVCONTAINER_DIR/devcontainer.json.backup"

show_help() {
    echo -e "${BLUE}DevContainer Management Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  switch-to-prebuilt   Switch to pre-built container configuration"
    echo "  switch-to-build      Switch to build-from-source configuration"
    echo "  status               Show current configuration status"
    echo "  build-local          Build the pre-built container locally"
    echo "  test-prebuilt        Test the pre-built container"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 switch-to-prebuilt"
    echo "  $0 status"
    echo "  $0 build-local"
    echo ""
}

check_current_config() {
    if [ -f "$ORIGINAL_CONFIG" ]; then
        if grep -q '"image"' "$ORIGINAL_CONFIG"; then
            echo "prebuilt"
        elif grep -q '"dockerFile"' "$ORIGINAL_CONFIG"; then
            echo "build"
        else
            echo "unknown"
        fi
    else
        echo "missing"
    fi
}

switch_to_prebuilt() {
    echo -e "${BLUE}Switching to pre-built container configuration...${NC}"

    if [ ! -f "$PREBUILT_CONFIG" ]; then
        echo -e "${RED}Error: Pre-built configuration not found at $PREBUILT_CONFIG${NC}"
        exit 1
    fi

    # Backup current config
    if [ -f "$ORIGINAL_CONFIG" ]; then
        echo -e "${YELLOW}Backing up current configuration...${NC}"
        cp "$ORIGINAL_CONFIG" "$BACKUP_CONFIG"
    fi

    # Copy prebuilt config
    cp "$PREBUILT_CONFIG" "$ORIGINAL_CONFIG"
    echo -e "${GREEN}✅ Switched to pre-built container configuration${NC}"
    echo -e "${YELLOW}📝 Original configuration backed up to devcontainer.json.backup${NC}"
    echo -e "${BLUE}🔄 Rebuild your DevContainer in VS Code to use the pre-built image${NC}"
}

switch_to_build() {
    echo -e "${BLUE}Switching to build-from-source configuration...${NC}"

    if [ ! -f "$BACKUP_CONFIG" ]; then
        echo -e "${RED}Error: No backup configuration found${NC}"
        echo -e "${YELLOW}You may need to manually restore the original configuration${NC}"
        exit 1
    fi

    # Restore from backup
    cp "$BACKUP_CONFIG" "$ORIGINAL_CONFIG"
    echo -e "${GREEN}✅ Switched to build-from-source configuration${NC}"
    echo -e "${BLUE}🔄 Rebuild your DevContainer in VS Code to build from source${NC}"
}

show_status() {
    echo -e "${BLUE}DevContainer Configuration Status${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    CURRENT_CONFIG=$(check_current_config)

    case "$CURRENT_CONFIG" in
        "prebuilt")
            echo -e "Current configuration: ${GREEN}Pre-built container${NC}"
            IMAGE_NAME=$(grep '"image"' "$ORIGINAL_CONFIG" | sed 's/.*"image": *"\([^"]*\)".*/\1/')
            echo -e "Using image: ${BLUE}$IMAGE_NAME${NC}"
            ;;
        "build")
            echo -e "Current configuration: ${YELLOW}Build from source${NC}"
            DOCKERFILE=$(grep '"dockerFile"' "$ORIGINAL_CONFIG" | sed 's/.*"dockerFile": *"\([^"]*\)".*/\1/')
            echo -e "Using Dockerfile: ${BLUE}$DOCKERFILE${NC}"
            ;;
        "unknown")
            echo -e "Current configuration: ${RED}Unknown${NC}"
            ;;
        "missing")
            echo -e "Current configuration: ${RED}Missing${NC}"
            ;;
    esac

    echo ""
    echo "Available configurations:"
    echo "  - devcontainer.json (current)"
    echo "  - devcontainer.prebuilt.json (pre-built template)"
    if [ -f "$BACKUP_CONFIG" ]; then
        echo "  - devcontainer.json.backup (backup)"
    fi
    echo ""

    # Show container registry status
    echo -e "${BLUE}Container Registry Status:${NC}"
    echo "  - GitHub Container Registry: ghcr.io/stuartshay/nyc-landmarks-devcontainer"
    echo "  - Docker Hub: stuartshay/nyc-landmarks-devcontainer"
    echo ""
}

build_local() {
    echo -e "${BLUE}Building pre-built container locally...${NC}"

    if [ ! -f "$DEVCONTAINER_DIR/Dockerfile.prebuilt" ]; then
        echo -e "${RED}Error: Dockerfile.prebuilt not found${NC}"
        exit 1
    fi

    echo -e "${YELLOW}This will build the container with all dependencies pre-installed${NC}"
    echo -e "${YELLOW}Build time: 5-10 minutes${NC}"
    echo ""

    # Build the container
    docker build \
        -f "$DEVCONTAINER_DIR/Dockerfile.prebuilt" \
        -t nyc-landmarks-devcontainer:local \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        /workspaces/nyc-landmarks-vector-db

    echo -e "${GREEN}✅ Container built successfully${NC}"
    echo -e "${BLUE}Image: nyc-landmarks-devcontainer:local${NC}"
    echo -e "${YELLOW}You can now use this image in your devcontainer.json${NC}"
}

test_prebuilt() {
    echo -e "${BLUE}Testing pre-built container...${NC}"

    # Test if container can be run
    docker run --rm nyc-landmarks-devcontainer:local python --version
    docker run --rm nyc-landmarks-devcontainer:local pip list | grep -E "(pytest|black|isort|mypy|pinecone)" | head -10

    echo -e "${GREEN}✅ Pre-built container test completed${NC}"
}

# Main script logic
case "${1:-help}" in
    "switch-to-prebuilt")
        switch_to_prebuilt
        ;;
    "switch-to-build")
        switch_to_build
        ;;
    "status")
        show_status
        ;;
    "build-local")
        build_local
        ;;
    "test-prebuilt")
        test_prebuilt
        ;;
    "help"|*)
        show_help
        ;;
esac
