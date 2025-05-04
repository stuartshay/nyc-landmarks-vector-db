#!/bin/bash
# direct_update.sh - Direct update of Python packages to their latest versions

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Ensure we're using the project's virtual environment
if [ -d "venv" ]; then
  source venv/bin/activate
elif [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo -e "${RED}No virtual environment found. Creating one...${NC}"
  python -m venv venv
  source venv/bin/activate
fi

# Update pip and pip-tools
echo -e "${BLUE}Updating pip and pip-tools...${NC}"
pip install --upgrade pip
pip install --upgrade pip-tools

# Backup current files
echo -e "${BLUE}Creating backups of current files...${NC}"
cp -f requirements.txt requirements.txt.bak || true
cp -f setup.py setup.py.bak || true

# Define key packages to update directly
PACKAGES=(
  # Core dependencies
  "fastapi"
  "uvicorn"
  "openai"
  "pinecone"
  "pypdf"
  "pdfplumber"
  "azure-storage-blob"
  "google-cloud-secret-manager"
  "pydantic"
  "pydantic-settings"
  "python-dotenv"
  "tiktoken"
  "numpy"
  "pandas"
  "tenacity"
  "matplotlib"
  "folium"
  "scikit-learn"

  # Dev dependencies
  "pytest"
  "black"
  "isort"
  "flake8"
  "mypy"
  "mypy_extensions"
  "types-requests"
  "pytest-cov"
  "pytest-dotenv"
  "pytest-asyncio"
  "pre-commit"
  "pip-tools"
  "jupyterlab"
  "ipywidgets"
  "plotly"
  "seaborn"
  "tqdm"
)

# Update packages directly
echo -e "${BLUE}Directly updating key packages to their latest versions...${NC}"
pip install --upgrade ${PACKAGES[@]}

# Save current direct dependencies to requirements.fresh.txt
pip freeze > requirements.fresh.txt

# Regenerate requirements.txt using pip-compile
echo -e "${BLUE}Regenerating requirements.txt with updated dependencies...${NC}"
pip-compile --upgrade --constraint=constraints.txt --output-file=requirements.txt

echo -e "${GREEN}Dependencies updated successfully!${NC}"
echo -e "${YELLOW}Review changes in requirements.txt and install with: pip install -r requirements.txt${NC}"
echo -e "${YELLOW}To install development dependencies: pip install -e '.[dev]'${NC}"
