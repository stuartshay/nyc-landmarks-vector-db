#!/bin/bash
#
# manage_packages.sh - Comprehensive script for managing Python dependencies
#
# This script provides several commands for updating, syncing, and managing
# dependencies in the NYC Landmarks Vector DB project.
#
# Usage:
#   ./manage_packages.sh [command]
#
# Commands:
#   update       - Update all packages to their latest versions
#   sync         - Sync versions between requirements.txt and setup.py
#   pinecone     - Update Pinecone SDK specifically
#   check        - Check for outdated packages
#   help         - Show this help message

set -e  # Exit on error

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Configuration
SETUP_PY="setup.py"
REQUIREMENTS_TXT="requirements.txt"
CONSTRAINTS_TXT="constraints.txt"

# Display help message
show_help() {
  echo -e "${BLUE}NYC Landmarks Vector DB Package Manager${NC}"
  echo -e "--------------------------------------------------------"
  echo -e "Usage: ./manage_packages.sh [command]"
  echo -e ""
  echo -e "Commands:"
  echo -e "  ${GREEN}update${NC}      Update all packages to their latest versions"
  echo -e "  ${GREEN}sync${NC}        Sync versions between requirements.txt and setup.py"
  echo -e "  ${GREEN}pinecone${NC}    Update Pinecone SDK specifically"
  echo -e "  ${GREEN}check${NC}       Check for outdated packages"
  echo -e "  ${GREEN}help${NC}        Show this help message"
}

# Ensure we're using the project's virtual environment
ensure_venv() {
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  elif [ -d "venv311" ]; then
    source venv311/bin/activate
  else
    echo -e "${RED}No virtual environment found. Please create one first.${NC}"
    exit 1
  fi

  echo -e "${BLUE}Using Python: $(which python)${NC}"
  echo -e "${BLUE}Python version: $(python --version)${NC}"
}

# Update packages to their latest versions
update_packages() {
  echo -e "${BLUE}Updating all Python dependencies to latest compatible versions...${NC}"

  # Ensure we have the necessary tools
  pip install --upgrade pip pip-tools

  # Create backup of current files
  echo -e "${BLUE}Creating backup of current files...${NC}"
  cp -f $REQUIREMENTS_TXT ${REQUIREMENTS_TXT}.tmp || true
  cp -f $SETUP_PY ${SETUP_PY}.tmp || true

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
  echo -e "${BLUE}Updating key packages to their latest versions...${NC}"
  pip install --upgrade ${PACKAGES[@]}

  # Regenerate requirements.txt using pip-compile
  echo -e "${BLUE}Regenerating requirements.txt with updated dependencies...${NC}"
  pip-compile --upgrade --constraint=$CONSTRAINTS_TXT --output-file=$REQUIREMENTS_TXT

  # Clean up temporary files
  rm -f ${REQUIREMENTS_TXT}.tmp ${SETUP_PY}.tmp

  # Sync versions
  sync_versions

  echo -e "${GREEN}Dependencies updated successfully!${NC}"
  echo -e "${YELLOW}Run 'pip install -r requirements.txt' to install updated dependencies${NC}"
  echo -e "${YELLOW}Run 'pip install -e \".[dev]\"' to install development dependencies${NC}"
}

# Sync versions between requirements.txt and setup.py
sync_versions() {
  echo -e "${BLUE}Synchronizing package versions between setup.py and requirements.txt...${NC}"

  # Check if files exist
  if [ ! -f "$SETUP_PY" ]; then
    echo -e "${RED}Error: $SETUP_PY not found${NC}"
    exit 1
  fi

  if [ ! -f "$REQUIREMENTS_TXT" ]; then
    echo -e "${RED}Error: $REQUIREMENTS_TXT not found${NC}"
    exit 1
  fi

  # Create a temp file
  TEMP_FILE=$(mktemp)

  # Extract package versions from requirements.txt - only direct lines with ==
  echo -e "${BLUE}Extracting package versions from requirements.txt...${NC}"
  grep -E "^[a-zA-Z0-9_-]+==.*$" "$REQUIREMENTS_TXT" | sort > "$TEMP_FILE"

  # Update packages in setup.py
  echo -e "${BLUE}Updating packages in setup.py...${NC}"

  UPDATED=0

  # Read through each line in temp file
  while read -r line; do
    # Split the line into package name and version
    PKG_NAME=$(echo "$line" | cut -d'=' -f1)
    PKG_VERSION=$(echo "$line" | cut -d'=' -f3)

    # Skip if either is empty
    if [ -z "$PKG_NAME" ] || [ -z "$PKG_VERSION" ]; then
      continue
    fi

    # Look for the package in setup.py with >= format
    if grep -q "\"$PKG_NAME>=.*\"" "$SETUP_PY"; then
      # Update the version
      sed -i "s/\"$PKG_NAME>=.*\"/\"$PKG_NAME>=$PKG_VERSION\"/" "$SETUP_PY"
      UPDATED=1
    fi
  done < "$TEMP_FILE"

  # Clean up
  rm "$TEMP_FILE"

  # If we made changes, report it
  if [ $UPDATED -eq 1 ]; then
      echo -e "${BLUE}Changes made to setup.py based on requirements.txt.${NC}"
  else
      echo -e "${BLUE}No version changes needed in setup.py.${NC}"
  fi

  echo -e "${GREEN}Version synchronization complete!${NC}"
  echo -e "${BLUE}Next steps:${NC}"
  echo -e "1. Review changes to setup.py"
  echo -e "2. Commit changes if they look good:${NC}"
  echo -e "   git add $SETUP_PY"
  echo -e "   git commit -m \\"Update package versions in setup.py\\""
}

# Update Pinecone SDK specifically
update_pinecone() {
  echo -e "${BLUE}Updating Pinecone SDK...${NC}"

  # Uninstall any previous versions of pinecone-client or pinecone
  echo -e "${BLUE}Uninstalling previous pinecone packages...${NC}"
  pip uninstall -y pinecone-client pinecone || true

  # Install Pinecone SDK v6.0.2
  echo -e "${BLUE}Installing Pinecone SDK v6.0.2...${NC}"
  pip install pinecone==6.0.2

  # Update requirements.txt
  pip-compile --constraint=$CONSTRAINTS_TXT --output-file=$REQUIREMENTS_TXT

  echo -e "${GREEN}Pinecone SDK updated successfully!${NC}"
}

# Check for outdated packages
check_outdated() {
  echo -e "${BLUE}Checking for outdated packages...${NC}"
  pip list --outdated
}

# Main functionality
main() {
  # Ensure we have a command
  if [ $# -eq 0 ]; then
    show_help
    exit 0
  fi

  # Process the command
  case "$1" in
    update)
      ensure_venv
      update_packages
      ;;
    sync)
      ensure_venv
      sync_versions
      ;;
    pinecone)
      ensure_venv
      update_pinecone
      ;;
    check)
      ensure_venv
      check_outdated
      ;;
    help|--help|-h)
      show_help
      ;;
    *)
      echo -e "${RED}Unknown command: $1${NC}"
      show_help
      exit 1
      ;;
  esac
}

# Run the script
main "$@"
