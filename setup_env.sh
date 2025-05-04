#!/bin/bash

# This script sets up a Python virtual environment with all required dependencies
# for running the NYC Landmarks Vector DB notebooks

# Set colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Python environment for NYC Landmarks Vector DB...${NC}"

# Directory where the script is located
PROJECT_DIR="$(pwd)"
VENV_DIR="${PROJECT_DIR}/venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python -m venv "$VENV_DIR"
else
    echo -e "${GREEN}Virtual environment already exists at ${VENV_DIR}${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Verify Python version
echo -e "${GREEN}Using $(python --version)${NC}"

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install pip-tools for dependency management
echo -e "${BLUE}Installing pip-tools for dependency management...${NC}"
pip install pip-tools

# Install dependencies from requirements.txt
echo -e "${BLUE}Installing dependencies from requirements.txt...${NC}"
pip install -r requirements.txt

# Install matplotlib (required for the notebook but might not be in requirements.txt)
echo -e "${BLUE}Ensuring matplotlib is installed...${NC}"
pip install matplotlib

# Install the package itself in development mode with dev dependencies
echo -e "${BLUE}Installing the package in development mode with dev dependencies...${NC}"
pip install -e ".[dev]"

# Verify Pinecone version
echo -e "${BLUE}Checking Pinecone version...${NC}"
pip show pinecone

# Verify pre-commit is installed and set up hooks
echo -e "${BLUE}Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}Pre-commit hooks installed successfully!${NC}"
else
    echo -e "${RED}pre-commit is not installed. Please check your installation.${NC}"
fi

echo -e "${GREEN}Environment setup complete!${NC}"
echo -e "${GREEN}To activate this environment, run:${NC}"
echo -e "   source ${VENV_DIR}/bin/activate"
echo -e "${GREEN}To start the Jupyter notebook, run:${NC}"
echo -e "   bash run_notebook.sh"
