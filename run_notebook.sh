#!/bin/bash

# Set colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set the Python virtual environment
VENV_PATH="$(pwd)/venv"

# Deactivate any existing virtual environment to prevent nested environments
if [[ -n $VIRTUAL_ENV ]]; then
  echo -e "${BLUE}Deactivating existing virtual environment...${NC}"
  deactivate 2>/dev/null || true
fi

# Activate the virtual environment
echo -e "${BLUE}Activating Python virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Verify Python version
echo -e "${GREEN}Using Python: $(python --version)${NC}"

# Check if jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo -e "${RED}Jupyter is not installed in this environment. Installing...${NC}"
    pip install jupyter
fi

# Load environment variables from .env file
if [ -f .env ]; then
  echo -e "${BLUE}Loading environment variables from .env file...${NC}"
  set -a
  source .env
  set +a
  echo -e "${GREEN}Environment variables loaded successfully.${NC}"
else
  echo -e "${RED}Warning: .env file not found. Environment variables may not be set correctly.${NC}"
fi

# Start Jupyter notebook
echo -e "${BLUE}Starting Jupyter notebook server...${NC}"
cd notebooks
jupyter notebook "$@"
