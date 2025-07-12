#!/bin/bash

# Simplified post-create script for pre-built DevContainer
# This script handles only project-specific setup since dependencies are pre-installed

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up NYC Landmarks Vector DB project (pre-built container)...${NC}"

# Change to workspace directory
cd /workspaces/nyc-landmarks-vector-db

# Create virtual environment if it doesn't exist
echo -e "${BLUE}📦 Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment and installing project...${NC}"
source .venv/bin/activate

# Upgrade pip in venv
pip install --upgrade pip

# Install pre-commit in the virtual environment
echo -e "${BLUE}Installing pre-commit in virtual environment...${NC}"
pip install pre-commit

# Install project requirements
echo -e "${BLUE}Installing project requirements...${NC}"
pip install -r requirements.txt

# Install only the project package in development mode
# Dependencies are now installed from requirements.txt
echo -e "${BLUE}Installing project package in development mode...${NC}"
pip install -e .
echo -e "${GREEN}✅ Project package installed${NC}"

# Install pre-commit hooks
echo -e "${BLUE}🔧 Setting up pre-commit hooks...${NC}"
if [ -x "$(command -v pre-commit)" ]; then
    pre-commit install
    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"

    # Initialize pre-commit environments to speed up first run
    echo -e "${BLUE}🚀 Initializing pre-commit hook environments...${NC}"
    echo -e "${YELLOW}This may take a few minutes but will speed up future pre-commit runs${NC}"
    pre-commit install-hooks || {
        echo -e "${YELLOW}⚠️  Some pre-commit hooks failed to initialize (this is often normal)${NC}"
        echo -e "${YELLOW}   They will be installed on first use${NC}"
    }
    echo -e "${GREEN}✅ Pre-commit environments initialized${NC}"
else
    echo -e "${RED}❌ pre-commit not found in activated environment${NC}"
    exit 1
fi

# Set up Git configuration if not already set
echo -e "${BLUE}⚙️  Configuring Git...${NC}"
if [ -z "$(git config --global user.name)" ]; then
    echo -e "${YELLOW}Setting default Git user.name to 'Developer'${NC}"
    git config --global user.name "Developer"
fi

if [ -z "$(git config --global user.email)" ]; then
    echo -e "${YELLOW}Setting default Git user.email${NC}"
    git config --global user.email "developer@example.com"
fi

# Configure Git to be more permissive with safe directories in containers
git config --global --add safe.directory /workspaces/nyc-landmarks-vector-db

echo -e "${GREEN}✅ Git configured${NC}"

# Create necessary directories
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p .gcp
mkdir -p test_output/notebooks
mkdir -p .cache
chmod 755 .gcp test_output .cache

# Verify environment
echo -e "${BLUE}🔍 Verifying environment...${NC}"
python --version
pip --version

# Quick test of key imports
echo -e "${BLUE}🧪 Testing key package imports...${NC}"
python -c "
import sys
try:
    import pytest, black, isort, mypy, flake8
    print('✅ Development tools imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

try:
    import pinecone, numpy, pandas, matplotlib
    print('✅ Data science packages imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

try:
    import fastapi, uvicorn
    print('✅ Web framework packages imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

print('✅ All core packages working correctly!')
"

# Final status
echo -e "${GREEN}🎉 Pre-built DevContainer setup complete!${NC}"
echo -e "${BLUE}Setup time: Much faster than building from scratch!${NC}"
echo -e "${BLUE}Virtual environment: $(pwd)/.venv${NC}"
echo -e "${BLUE}Python interpreter: $(pwd)/.venv/bin/python${NC}"
echo -e "${BLUE}To activate manually: source .venv/bin/activate${NC}"
echo -e "${YELLOW}💡 Most dependencies are pre-installed in the container${NC}"
echo -e "${YELLOW}   Only project-specific setup was needed${NC}"
