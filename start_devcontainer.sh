#!/usr/bin/env bash

# Development Container Script
# This script serves dual purposes:
# 1. When run from host: builds and starts the development container
# 2. When run inside container: sets up the development environment (postCreateCommand)

# Set colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Detect if we're running inside a container or on the host
if [ -f "/.dockerenv" ] || [ -n "${REMOTE_CONTAINERS}" ] || [ -n "${CODESPACES}" ]; then
    # We're inside a container - run setup mode
    CONTAINER_MODE=true
    PROJECT_DIR="/workspaces/nyc-landmarks-vector-db"
else
    # We're on the host - run build mode
    CONTAINER_MODE=false
    PROJECT_DIR="$(pwd)"
fi

if [ "$CONTAINER_MODE" = true ]; then
    echo -e "${GREEN}🚀 Setting up NYC Landmarks Vector DB development environment...${NC}"

    # Container setup logic
    set -e

    # Define paths
    WORKSPACE_ROOT="/workspaces/nyc-landmarks-vector-db"
    GCP_DIR="${WORKSPACE_ROOT}/.gcp"
    SERVICE_ACCOUNT_KEY_PATH="${GCP_DIR}/service-account-key.json"

    # Ensure necessary directories exist
    echo -e "${BLUE}📁 Creating necessary directories...${NC}"
    mkdir -p "${GCP_DIR}"
    mkdir -p "${WORKSPACE_ROOT}/test_output"
    mkdir -p "${WORKSPACE_ROOT}/.cache"

    # Create Python user directories with proper permissions
    echo -e "${BLUE}📁 Setting up Python user directories...${NC}"

    # Fix ownership of existing directories first
    if [ -d "${HOME}/.local" ]; then
        sudo chown -R vscode:vscode "${HOME}/.local"
    fi
    if [ -d "${HOME}/.cache" ]; then
        sudo chown -R vscode:vscode "${HOME}/.cache"
    fi

    # Now create the directories
    mkdir -p "${HOME}/.local/lib/python3.12/site-packages"
    mkdir -p "${HOME}/.local/bin"
    mkdir -p "${HOME}/.cache/pip"

    # Set proper permissions for directories
    chmod 755 "${GCP_DIR}"
    chmod 755 "${WORKSPACE_ROOT}/test_output"
    chmod -R 755 "${HOME}/.local"
    chmod -R 755 "${HOME}/.cache"

    # Verify Python installation and version
    echo -e "${BLUE}🐍 Checking Python installation...${NC}"
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version)
        echo -e "${GREEN}✅ ${PYTHON_VERSION} found${NC}"
    else
        echo -e "${RED}❌ Python not found${NC}"
        exit 1
    fi

    # Verify pip installation
    echo -e "${BLUE}📦 Checking pip installation...${NC}"
    if command -v pip &> /dev/null; then
        PIP_VERSION=$(pip --version)
        echo -e "${GREEN}✅ ${PIP_VERSION}${NC}"

        # Upgrade pip to latest version
        echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
        pip install --upgrade pip
    else
        echo -e "${RED}❌ pip not found${NC}"
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

    # Set up Git to use main as default branch
    git config --global init.defaultBranch main

    # Configure Git to be more permissive with safe directories in containers
    git config --global --add safe.directory /workspaces/nyc-landmarks-vector-db

    echo -e "${GREEN}✅ Git configured${NC}"

    # Set environment variables for the session
    echo -e "${BLUE}🌍 Setting up environment variables...${NC}"
    export PYTHONPATH="${WORKSPACE_ROOT}"
    export ENVIRONMENT="development"
    export LOG_LEVEL="INFO"
    export LOG_FORMAT="json"
    export DEBUG="false"

    # Add user's local bin directory to PATH for installed tools
    export PATH="${HOME}/.local/bin:${PATH}"
    echo -e "${GREEN}✅ Added ${HOME}/.local/bin to PATH${NC}"

    # Check if Google Cloud CLI is available and configure if needed
    echo -e "${BLUE}☁️  Checking Google Cloud CLI...${NC}"
    if command -v gcloud &> /dev/null; then
        echo -e "${GREEN}✅ Google Cloud CLI found${NC}"

        # Set up gcloud configuration directory
        GCLOUD_CONFIG_DIR="${HOME}/.config/gcloud"
        mkdir -p "${GCLOUD_CONFIG_DIR}"

        # Initialize gcloud configuration if service account key exists
        if [ -f "$SERVICE_ACCOUNT_KEY_PATH" ]; then
            echo -e "${BLUE}🔧 Found service account key, setting up authentication...${NC}"
            echo -e "${YELLOW}Service account authentication setup will be done separately${NC}"
        else
            echo -e "${YELLOW}⚠️  No service account key found at ${SERVICE_ACCOUNT_KEY_PATH}${NC}"
            echo -e "${YELLOW}   GCP authentication will need to be set up manually later${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Google Cloud CLI not found${NC}"
    fi

    # Check if required system tools are available
    echo -e "${BLUE}🔧 Checking system tools...${NC}"

    REQUIRED_TOOLS=("curl" "wget" "git" "make" "gcc")
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo -e "${GREEN}✅ $tool found${NC}"
        else
            echo -e "${YELLOW}⚠️  $tool not found${NC}"
        fi
    done

    # Install pyright for VS Code test discovery and type checking
    echo -e "${BLUE}📦 Installing pyright for VS Code integration...${NC}"
    if command -v npm &> /dev/null; then
        if ! command -v pyright &> /dev/null; then
            echo -e "${BLUE}Installing pyright globally...${NC}"
            npm install -g pyright
            echo -e "${GREEN}✅ pyright installed${NC}"
        else
            echo -e "${GREEN}✅ pyright already installed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  npm not found, skipping pyright installation${NC}"
    fi

    # Check if Docker is available (for Docker-in-Docker)
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker CLI found${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker CLI not found${NC}"
    fi

    # Check if Terraform is available
    if command -v terraform &> /dev/null; then
        echo -e "${GREEN}✅ Terraform found${NC}"
        terraform version
    else
        echo -e "${YELLOW}⚠️  Terraform not found${NC}"
    fi    # Set up shell configuration for zsh
    echo -e "${BLUE}🐚 Configuring shell environment...${NC}"
    if [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
        echo -e "${GREEN}✅ Zsh detected${NC}"

        # Add PYTHONPATH to .zshrc if not already present
        ZSHRC_FILE="${HOME}/.zshrc"
        if [ -f "$ZSHRC_FILE" ]; then
            if ! grep -q "PYTHONPATH.*nyc-landmarks-vector-db" "$ZSHRC_FILE"; then
                echo -e "${BLUE}Adding PYTHONPATH to .zshrc...${NC}"
                echo "" >> "$ZSHRC_FILE"
                echo "# NYC Landmarks Vector DB environment" >> "$ZSHRC_FILE"
                echo "export PYTHONPATH=\"/workspaces/nyc-landmarks-vector-db:\$PYTHONPATH\"" >> "$ZSHRC_FILE"
            fi

            # Add local bin directory to PATH in .zshrc if not already present
            if ! grep -q ".local/bin" "$ZSHRC_FILE"; then
                echo -e "${BLUE}Adding local bin directory to PATH in .zshrc...${NC}"
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$ZSHRC_FILE"
            fi
        fi
    fi

    # Log environment health check information
    echo -e "${BLUE}📝 Logging environment health check...${NC}"
    echo -e "${GREEN}DevContainer setup completed at: $(date)${NC}"
    echo -e "${GREEN}Python: $(python --version)${NC}"
    echo -e "${GREEN}Pip: $(pip --version)${NC}"
    echo -e "${GREEN}Git: $(git --version)${NC}"
    echo -e "${GREEN}Workspace: ${WORKSPACE_ROOT}${NC}"
    echo -e "${GREEN}User: $(whoami)${NC}"
    echo -e "${GREEN}Shell: ${SHELL}${NC}"

    echo -e "${GREEN}🎉 DevContainer environment setup complete!${NC}"
    echo -e "${BLUE}Next steps will be handled automatically:${NC}"
    echo -e "  1. Installing Python dependencies with: ${YELLOW}pip install -e .[dev]${NC}"
    echo -e "  2. Setting up pre-commit hooks with: ${YELLOW}pre-commit install${NC}"
    echo
    echo -e "${YELLOW}📦 Note: VS Code extensions are being downloaded and installed in the background.${NC}"
    echo -e "${YELLOW}   This may take a few minutes to complete. Extension features will be available once${NC}"
    echo -e "${YELLOW}   the installation finishes. You can check progress in the Extensions panel.${NC}"

    exit 0
else
    # Host mode - original container build functionality
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
fi
