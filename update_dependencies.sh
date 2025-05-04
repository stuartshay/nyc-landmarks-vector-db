#!/bin/bash
# update_dependencies.sh - Script to update all dependencies to their latest compatible versions

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

echo -e "${BLUE}Updating all Python dependencies to latest compatible versions...${NC}"

# Ensure we have the necessary tools
pip install --quiet --upgrade pip pip-tools

# Create a backup of the current requirements.txt
echo -e "${BLUE}Creating backup of requirements.txt...${NC}"
cp requirements.txt requirements.txt.bak

# Update setup.py directly installed packages for the latest versions
echo -e "${BLUE}Getting latest versions for direct dependencies...${NC}"
python -m pip_upgrade_tool.main -p pinecone-client pypdf pdfplumber azure-storage-blob \
    google-cloud-secret-manager pydantic pydantic-settings python-dotenv tiktoken \
    numpy pandas tenacity matplotlib folium scikit-learn fastapi uvicorn openai \
    pytest black isort flake8 mypy mypy_extensions types-requests pytest-cov \
    pytest-dotenv pytest-asyncio pre-commit pip-tools jupyterlab ipywidgets \
    plotly seaborn tqdm

# Regenerate requirements.txt with the latest compatible versions
echo -e "${BLUE}Regenerating requirements.txt with latest compatible versions...${NC}"
pip-compile --upgrade --constraint=constraints.txt

echo -e "${GREEN}Dependencies updated successfully!${NC}"
echo -e "${YELLOW}Review the changes in requirements.txt and commit them to the repository.${NC}"
echo -e "${YELLOW}Run './sync_versions.sh' to synchronize versions between setup.py and requirements.txt${NC}"
