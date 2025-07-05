#!/bin/bash

# Docker Hub Setup Helper for GitHub Actions
# This script provides instructions for setting up Docker Hub integration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Docker Hub Setup Helper${NC}"
echo -e "${BLUE}=========================${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: This script must be run from within a Git repository${NC}"
    exit 1
fi

# Get repository information
REPO_OWNER=$(git config --get remote.origin.url | sed -n 's#.*/\([^/]*\)/.*#\1#p')
REPO_NAME=$(git config --get remote.origin.url | sed -n 's#.*/\([^/]*\)\.git#\1#p')

if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
    echo -e "${RED}Error: Could not determine repository owner and name${NC}"
    exit 1
fi

echo -e "${GREEN}Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo ""

echo -e "${YELLOW}📋 Docker Hub Setup Instructions${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

echo -e "${BLUE}1. Create Docker Hub Access Token:${NC}"
echo "   a. Go to https://hub.docker.com"
echo "   b. Sign in to your Docker Hub account"
echo "   c. Click your profile → Account Settings"
echo "   d. Go to Security → Access Tokens"
echo "   e. Click 'New Access Token'"
echo "   f. Name: 'GitHub Actions - ${REPO_NAME}'"
echo "   g. Permissions: Read, Write, Delete"
echo "   h. Copy the generated token (you won't see it again!)"
echo ""

echo -e "${BLUE}2. Add GitHub Repository Secrets:${NC}"
echo "   a. Go to https://github.com/${REPO_OWNER}/${REPO_NAME}/settings/secrets/actions"
echo "   b. Click 'New repository secret'"
echo "   c. Add the following secrets:"
echo ""
echo -e "${GREEN}   Secret Name: DOCKERHUB_USERNAME${NC}"
echo "   Secret Value: [Your Docker Hub username]"
echo ""
echo -e "${GREEN}   Secret Name: DOCKERHUB_TOKEN${NC}"
echo "   Secret Value: [The access token you just created]"
echo ""

echo -e "${BLUE}3. Container Images Will Be Published To:${NC}"
echo "   📦 GitHub Container Registry: ghcr.io/${REPO_OWNER}/nyc-landmarks-devcontainer"
echo "   📦 Docker Hub: ${REPO_OWNER}/nyc-landmarks-devcontainer"
echo ""

echo -e "${BLUE}4. Verify Setup:${NC}"
echo "   After adding the secrets, the next GitHub Actions run will:"
echo "   ✅ Build and push to GitHub Container Registry (always enabled)"
echo "   ✅ Build and push to Docker Hub (if secrets are available)"
echo ""

echo -e "${YELLOW}💡 Note: Docker Hub integration is optional!${NC}"
echo "The DevContainer will work perfectly with just GitHub Container Registry."
echo "Docker Hub provides an additional public registry for wider access."
echo ""

echo -e "${BLUE}5. Check Current Status:${NC}"
if command -v gh &> /dev/null; then
    echo "Checking GitHub Actions runs..."
    gh run list --workflow="Build DevContainer" --limit 3
else
    echo "Install GitHub CLI (gh) to check run status automatically"
    echo "Or visit: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions"
fi
echo ""

echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "Once you add the Docker Hub secrets, your containers will be published to both registries."
