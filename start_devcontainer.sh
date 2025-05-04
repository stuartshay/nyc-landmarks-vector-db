#!/usr/bin/env bash

# Start Development Container Script
# This script helps build and test the development container

# Set colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Directory where the script is located
PROJECT_DIR="$(pwd)"

echo -e "${BLUE}===== NYC Landmarks Vector DB Development Container =====${NC}"
echo -e "This script will help you test and start the development container."
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

echo -e "${BLUE}Checking Docker status...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running. Please start Docker and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker is running!${NC}"
echo

# Build the container image
echo -e "${BLUE}Building development container image...${NC}"
if docker build -t nyc-landmarks-dev -f .devcontainer/Dockerfile .; then
    echo -e "${GREEN}Container image built successfully!${NC}"
else
    echo -e "${RED}Failed to build container image. See errors above.${NC}"
    exit 1
fi
echo

# Offer to start VS Code with the container if available
if command -v code &> /dev/null; then
    echo -e "${YELLOW}Do you want to open VS Code with the development container? (y/n)${NC}"
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Starting VS Code with the development container...${NC}"
        code --folder-uri vscode-remote://dev-container+${PROJECT_DIR}
        echo -e "${GREEN}VS Code should be opening with the development container.${NC}"
    else
        echo -e "${BLUE}You can manually open VS Code and use the 'Remote-Containers: Open Folder in Container...' command.${NC}"
    fi
else
    echo -e "${YELLOW}VS Code command-line interface not found. You can:${NC}"
    echo "  1. Open VS Code manually"
    echo "  2. Select 'Remote-Containers: Open Folder in Container...' from the command palette"
    echo "  3. Choose this repository folder"
fi

echo
echo -e "${BLUE}===== Container Environment Info =====${NC}"
echo -e "Python version: ${GREEN}3.12${NC}"
echo -e "Container image: ${GREEN}nyc-landmarks-dev${NC}"

echo
echo -e "${GREEN}Happy coding!${NC}"
