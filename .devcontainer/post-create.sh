#!/bin/bash

# Post-create setup script for the development container
# This script handles Python environment setup after container creation

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐍 Setting up Python development environment...${NC}"

# Change to workspace directory
cd /workspaces/nyc-landmarks-vector-db

# Create virtual environment
echo -e "${BLUE}📦 Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Installing requirements.txt...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Requirements installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Install package in development mode
echo -e "${BLUE}Installing package in development mode...${NC}"
pip install -e .
echo -e "${GREEN}✅ Package installed in development mode${NC}"

# Install pre-commit hooks
echo -e "${BLUE}🔧 Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  pre-commit not found, skipping hook installation${NC}"
fi

echo -e "${GREEN}🎉 Python development environment setup complete!${NC}"
echo -e "${BLUE}Virtual environment: $(pwd)/venv${NC}"
echo -e "${BLUE}Python interpreter: $(pwd)/venv/bin/python${NC}"
echo -e "${BLUE}To activate manually: source venv/bin/activate${NC}"
