#!/bin/bash

# Enhanced Python 3.13 Environment Setup Script for NYC Landmarks Vector DB
# This script sets up a complete development environment with Python 3.13
# and all required dependencies for the NYC Landmarks Vector DB project

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for better output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Configuration
readonly PYTHON_VERSION="3.13"
readonly PYTHON_FULL_VERSION="3.13.1"
readonly PROJECT_NAME="NYC Landmarks Vector DB"
readonly VENV_NAME="venv"
readonly GITLEAKS_VERSION="8.21.2"
readonly TERRAFORM_VERSION="1.10.3"

# Global variables
PROJECT_DIR=""
VENV_DIR=""
OS_TYPE=""
PACKAGE_MANAGER=""
FORCE_REINSTALL=false
SKIP_PYTHON=false
DEV_ONLY=false
MINIMAL=false
VERBOSE=false
SKIP_SECURITY_TOOLS=false

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")  echo -e "${BLUE}[INFO]${NC} ${timestamp} - $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} ${timestamp} - $message" ;;
        "DEBUG") [[ $VERBOSE == true ]] && echo -e "${PURPLE}[DEBUG]${NC} ${timestamp} - $message" ;;
    esac
}

# Progress indicator
show_progress() {
    local message="$1"
    echo -e "${CYAN}⏳ $message...${NC}"
}

# Success indicator
show_success() {
    local message="$1"
    echo -e "${GREEN}✅ $message${NC}"
}

# Error handler
error_exit() {
    log "ERROR" "$1"
    echo -e "${RED}❌ Setup failed. Check the error above.${NC}"
    exit 1
}

# Cleanup function for failed installations
cleanup_on_failure() {
    log "WARN" "Cleaning up failed installation..."
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
        log "INFO" "Removed incomplete virtual environment"
    fi
}

# Trap errors and cleanup
trap cleanup_on_failure ERR

# Display usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Enhanced Python 3.13 Environment Setup for $PROJECT_NAME

OPTIONS:
    --force-reinstall       Force reinstall Python 3.13 even if it exists
    --skip-python          Skip Python 3.13 installation (use existing)
    --skip-security-tools  Skip gitleaks and Terraform installation
    --dev-only             Install only development dependencies
    --minimal              Minimal installation without optional tools
    --verbose              Enable verbose output for debugging
    --help                 Show this help message

EXAMPLES:
    $0                              # Standard installation
    $0 --verbose                    # Verbose installation
    $0 --skip-python --dev-only     # Skip Python install, dev deps only
    $0 --skip-security-tools        # Skip gitleaks and Terraform
    $0 --force-reinstall            # Force complete reinstall

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-reinstall)
                FORCE_REINSTALL=true
                shift
                ;;
            --skip-python)
                SKIP_PYTHON=true
                shift
                ;;
            --skip-security-tools)
                SKIP_SECURITY_TOOLS=true
                shift
                ;;
            --dev-only)
                DEV_ONLY=true
                shift
                ;;
            --minimal)
                MINIMAL=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Detect operating system and package manager
detect_os() {
    show_progress "Detecting operating system"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            OS_TYPE="debian"
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            OS_TYPE="rhel"
            PACKAGE_MANAGER="yum"
        elif command -v dnf &> /dev/null; then
            OS_TYPE="fedora"
            PACKAGE_MANAGER="dnf"
        else
            OS_TYPE="linux"
            PACKAGE_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        PACKAGE_MANAGER="brew"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS_TYPE="windows"
        PACKAGE_MANAGER="unknown"
    else
        OS_TYPE="unknown"
        PACKAGE_MANAGER="unknown"
    fi

    log "INFO" "Detected OS: $OS_TYPE with package manager: $PACKAGE_MANAGER"
    show_success "Operating system detected"
}

# Check if Python 3.13 is installed
check_python313() {
    if command -v python3.13 &> /dev/null; then
        local version=$(python3.13 --version 2>&1 | cut -d' ' -f2)
        log "INFO" "Found Python 3.13: $version"
        return 0
    elif command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ $version == 3.13* ]]; then
            log "INFO" "Found Python 3.13 as python3: $version"
            return 0
        fi
    fi
    return 1
}

# Check if gitleaks is installed
check_gitleaks() {
    if command -v gitleaks &> /dev/null; then
        local version=$(gitleaks version 2>&1 | head -n1 | cut -d' ' -f2 || echo "unknown")
        log "INFO" "Found gitleaks: $version"
        return 0
    fi
    return 1
}

# Check if Terraform is installed
check_terraform() {
    if command -v terraform &> /dev/null; then
        local version=$(terraform version -json 2>/dev/null | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4 || terraform version | head -n1 | cut -d' ' -f2)
        log "INFO" "Found Terraform: $version"
        return 0
    fi
    return 1
}

# Install gitleaks
install_gitleaks() {
    show_progress "Installing gitleaks"

    case $PACKAGE_MANAGER in
        "brew")
            # macOS with Homebrew
            brew install gitleaks
            ;;
        "apt"|"yum"|"dnf"|*)
            # Linux - download from GitHub releases
            local temp_dir=$(mktemp -d)
            cd "$temp_dir"

            # Determine architecture
            local arch=""
            case $(uname -m) in
                x86_64) arch="x64" ;;
                aarch64|arm64) arch="arm64" ;;
                *) arch="x64" ;; # Default to x64
            esac

            # Download and install gitleaks
            local download_url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${arch}.tar.gz"
            log "DEBUG" "Downloading gitleaks from: $download_url"

            if wget -q "$download_url" -O gitleaks.tar.gz; then
                tar -xzf gitleaks.tar.gz
                sudo mv gitleaks /usr/local/bin/
                sudo chmod +x /usr/local/bin/gitleaks
                log "INFO" "Gitleaks installed to /usr/local/bin/gitleaks"
            else
                log "WARN" "Failed to download gitleaks from GitHub releases"
                return 1
            fi

            # Cleanup
            cd "$PROJECT_DIR"
            rm -rf "$temp_dir"
            ;;
    esac

    return 0
}

# Install Terraform
install_terraform() {
    show_progress "Installing Terraform"

    case $PACKAGE_MANAGER in
        "brew")
            # macOS with Homebrew
            brew install terraform
            ;;
        "apt")
            # Ubuntu/Debian - add HashiCorp repository
            wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
            echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
            sudo apt-get update
            sudo apt-get install -y terraform
            ;;
        "yum"|"dnf")
            # RHEL/CentOS/Fedora - add HashiCorp repository
            sudo $PACKAGE_MANAGER install -y yum-utils
            sudo $PACKAGE_MANAGER config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
            sudo $PACKAGE_MANAGER install -y terraform
            ;;
        *)
            # Fallback - download from HashiCorp releases
            local temp_dir=$(mktemp -d)
            cd "$temp_dir"

            # Determine architecture
            local arch=""
            case $(uname -m) in
                x86_64) arch="amd64" ;;
                aarch64|arm64) arch="arm64" ;;
                *) arch="amd64" ;; # Default to amd64
            esac

            # Download and install Terraform
            local download_url="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${arch}.zip"
            log "DEBUG" "Downloading Terraform from: $download_url"

            if wget -q "$download_url" -O terraform.zip; then
                unzip -q terraform.zip
                sudo mv terraform /usr/local/bin/
                sudo chmod +x /usr/local/bin/terraform
                log "INFO" "Terraform installed to /usr/local/bin/terraform"
            else
                log "WARN" "Failed to download Terraform from HashiCorp releases"
                return 1
            fi

            # Cleanup
            cd "$PROJECT_DIR"
            rm -rf "$temp_dir"
            ;;
    esac

    return 0
}

# Setup security tools (gitleaks and Terraform)
setup_security_tools() {
    if [[ $SKIP_SECURITY_TOOLS == true ]]; then
        log "INFO" "Skipping security tools installation as requested"
        return 0
    fi

    if [[ $MINIMAL == true ]]; then
        log "INFO" "Skipping security tools setup (minimal installation)"
        return 0
    fi

    show_progress "Setting up security and infrastructure tools"

    local errors=0

    # Install gitleaks
    if check_gitleaks; then
        log "INFO" "Gitleaks already installed"
    else
        if install_gitleaks; then
            show_success "Gitleaks installed successfully"
        else
            log "WARN" "Failed to install gitleaks"
            ((errors++))
        fi
    fi

    # Install Terraform
    if check_terraform; then
        log "INFO" "Terraform already installed"
    else
        if install_terraform; then
            show_success "Terraform installed successfully"
        else
            log "WARN" "Failed to install Terraform"
            ((errors++))
        fi
    fi

    if [[ $errors -eq 0 ]]; then
        show_success "Security tools configured"
    else
        log "WARN" "Some security tools failed to install but continuing setup"
    fi

    return 0
}

# Install system dependencies
install_system_dependencies() {
    show_progress "Installing system dependencies"

    case $PACKAGE_MANAGER in
        "apt")
            sudo apt-get update
            sudo apt-get install -y \
                software-properties-common \
                build-essential \
                libssl-dev \
                libffi-dev \
                libsqlite3-dev \
                libbz2-dev \
                libreadline-dev \
                libncurses5-dev \
                libncursesw5-dev \
                xz-utils \
                tk-dev \
                libxml2-dev \
                libxmlsec1-dev \
                liblzma-dev \
                git \
                curl \
                wget
            ;;
        "yum"|"dnf")
            sudo $PACKAGE_MANAGER groupinstall -y "Development Tools"
            sudo $PACKAGE_MANAGER install -y \
                openssl-devel \
                libffi-devel \
                sqlite-devel \
                bzip2-devel \
                readline-devel \
                ncurses-devel \
                xz-devel \
                tk-devel \
                libxml2-devel \
                xmlsec1-devel \
                git \
                curl \
                wget
            ;;
        "brew")
            brew install \
                openssl \
                readline \
                sqlite3 \
                xz \
                zlib \
                tcl-tk
            ;;
        *)
            log "WARN" "Unknown package manager. Skipping system dependencies."
            ;;
    esac

    show_success "System dependencies installed"
}

# Install Python 3.13 via system package manager
install_python313_system() {
    show_progress "Installing Python 3.13 via system package manager"

    case $PACKAGE_MANAGER in
        "apt")
            # Add deadsnakes PPA for Ubuntu/Debian
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt-get update
            sudo apt-get install -y python3.13 python3.13-venv python3.13-dev
            ;;
        "dnf")
            # Fedora usually has recent Python versions
            sudo dnf install -y python3.13 python3.13-devel python3.13-pip
            ;;
        "brew")
            # macOS with Homebrew
            brew install python@3.13
            ;;
        *)
            log "WARN" "System package installation not supported for $PACKAGE_MANAGER"
            return 1
            ;;
    esac

    return 0
}

# Install Python 3.13 via pyenv
install_python313_pyenv() {
    show_progress "Installing Python 3.13 via pyenv"

    # Install pyenv if not present
    if ! command -v pyenv &> /dev/null; then
        log "INFO" "Installing pyenv..."
        curl https://pyenv.run | bash

        # Add pyenv to PATH for current session
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    fi

    # Install Python 3.13 via pyenv
    pyenv install $PYTHON_FULL_VERSION
    pyenv global $PYTHON_FULL_VERSION

    return 0
}

# Install Python 3.13 from source (fallback)
install_python313_source() {
    show_progress "Installing Python 3.13 from source (this may take a while)"

    local temp_dir=$(mktemp -d)
    cd "$temp_dir"

    # Download Python source
    wget "https://www.python.org/ftp/python/$PYTHON_FULL_VERSION/Python-$PYTHON_FULL_VERSION.tgz"
    tar -xzf "Python-$PYTHON_FULL_VERSION.tgz"
    cd "Python-$PYTHON_FULL_VERSION"

    # Configure and compile
    ./configure --enable-optimizations --with-ensurepip=install
    make -j$(nproc)
    sudo make altinstall

    # Cleanup
    cd "$PROJECT_DIR"
    rm -rf "$temp_dir"

    return 0
}

# Main Python 3.13 installation function
install_python313() {
    if [[ $SKIP_PYTHON == true ]]; then
        log "INFO" "Skipping Python 3.13 installation as requested"
        return 0
    fi

    if check_python313 && [[ $FORCE_REINSTALL == false ]]; then
        log "INFO" "Python 3.13 already installed. Use --force-reinstall to reinstall."
        return 0
    fi

    log "INFO" "Installing Python 3.13..."

    # Install system dependencies first
    install_system_dependencies

    # Try different installation methods
    if install_python313_system; then
        show_success "Python 3.13 installed via system package manager"
    elif install_python313_pyenv; then
        show_success "Python 3.13 installed via pyenv"
    elif install_python313_source; then
        show_success "Python 3.13 installed from source"
    else
        error_exit "Failed to install Python 3.13 using all available methods"
    fi

    # Verify installation
    if ! check_python313; then
        error_exit "Python 3.13 installation verification failed"
    fi
}

# Get Python 3.13 executable path
get_python313_path() {
    if command -v python3.13 &> /dev/null; then
        echo "python3.13"
    elif command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ $version == 3.13* ]]; then
            echo "python3"
        fi
    else
        error_exit "Python 3.13 not found after installation"
    fi
}

# Create and setup virtual environment
setup_virtual_environment() {
    show_progress "Setting up Python virtual environment"

    local python_cmd=$(get_python313_path)

    # Remove existing virtual environment if force reinstall
    if [[ $FORCE_REINSTALL == true ]] && [[ -d "$VENV_DIR" ]]; then
        log "INFO" "Removing existing virtual environment"
        rm -rf "$VENV_DIR"
    fi

    # Create virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        log "INFO" "Creating virtual environment with $python_cmd"
        $python_cmd -m venv "$VENV_DIR"
    else
        log "INFO" "Virtual environment already exists"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Verify Python version in virtual environment
    local venv_version=$(python --version 2>&1 | cut -d' ' -f2)
    log "INFO" "Virtual environment Python version: $venv_version"

    show_success "Virtual environment created and activated"
}

# Upgrade pip and install pip-tools
setup_pip() {
    show_progress "Upgrading pip and installing pip-tools"

    # Upgrade pip
    python -m pip install --upgrade pip

    # Install pip-tools for dependency management
    pip install pip-tools wheel setuptools

    show_success "Pip and tools updated"
}

# Install project dependencies
install_dependencies() {
    show_progress "Installing project dependencies"

    if [[ $DEV_ONLY == true ]]; then
        log "INFO" "Installing development dependencies only"
        pip install -e ".[dev]"
    elif [[ $MINIMAL == true ]]; then
        log "INFO" "Installing minimal dependencies"
        pip install -e .
    else
        log "INFO" "Installing all dependencies from requirements.txt"
        pip install -r requirements.txt

        # Install the package in development mode
        pip install -e ".[dev]"
    fi

    show_success "Dependencies installed"
}

# Setup development tools
setup_development_tools() {
    if [[ $MINIMAL == true ]]; then
        log "INFO" "Skipping development tools setup (minimal installation)"
        return 0
    fi

    show_progress "Setting up development tools"

    # Install and setup pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        log "INFO" "Pre-commit hooks installed"
    else
        log "WARN" "pre-commit not found, skipping hooks setup"
    fi

    # Create test output directories
    mkdir -p test_output/notebooks
    log "INFO" "Created test output directories"

    # Setup Jupyter kernel
    if command -v jupyter &> /dev/null; then
        python -m ipykernel install --user --name="$VENV_NAME" --display-name="Python ($PROJECT_NAME)"
        log "INFO" "Jupyter kernel installed"
    fi

    show_success "Development tools configured"
}

# Validate installation
validate_installation() {
    show_progress "Validating installation"

    local errors=0

    # Check Python version
    local python_version=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ $python_version == 3.13* ]]; then
        log "SUCCESS" "Python version: $python_version ✓"
    else
        log "ERROR" "Wrong Python version: $python_version"
        ((errors++))
    fi

    # Check key packages
    local key_packages=("fastapi" "openai" "pinecone" "pandas" "numpy" "jupyter")
    for package in "${key_packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            log "SUCCESS" "Package $package: ✓"
        else
            log "ERROR" "Package $package: ✗"
            ((errors++))
        fi
    done

    # Check development tools
    if [[ $MINIMAL == false ]]; then
        local dev_tools=("black" "mypy" "pytest" "pre-commit")
        for tool in "${dev_tools[@]}"; do
            if command -v $tool &> /dev/null; then
                log "SUCCESS" "Tool $tool: ✓"
            else
                log "ERROR" "Tool $tool: ✗"
                ((errors++))
            fi
        done
    fi

    # Check security tools
    if [[ $SKIP_SECURITY_TOOLS == false ]] && [[ $MINIMAL == false ]]; then
        local security_tools=("gitleaks" "terraform")
        for tool in "${security_tools[@]}"; do
            if command -v $tool &> /dev/null; then
                log "SUCCESS" "Security tool $tool: ✓"
            else
                log "WARN" "Security tool $tool: ✗ (optional)"
            fi
        done
    fi

    if [[ $errors -eq 0 ]]; then
        show_success "All validation checks passed"
        return 0
    else
        log "ERROR" "Validation failed with $errors errors"
        return 1
    fi
}

# Display completion summary
show_completion_summary() {
    echo
    echo -e "${GREEN}🎉 Environment setup completed successfully!${NC}"
    echo
    echo -e "${BLUE}Project:${NC} $PROJECT_NAME"
    echo -e "${BLUE}Python Version:${NC} $(python --version 2>&1)"
    echo -e "${BLUE}Virtual Environment:${NC} $VENV_DIR"
    echo -e "${BLUE}Project Directory:${NC} $PROJECT_DIR"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Activate the environment: ${CYAN}source $VENV_DIR/bin/activate${NC}"
    echo -e "  2. Copy environment file: ${CYAN}cp .env.sample .env${NC}"
    echo -e "  3. Edit .env with your API keys"
    echo -e "  4. Start Jupyter: ${CYAN}jupyter lab${NC}"
    echo -e "  5. Run the application: ${CYAN}python -m nyc_landmarks.main${NC}"
    echo
    echo -e "${GREEN}Happy coding! 🚀${NC}"
}

# Main execution function
main() {
    echo -e "${BLUE}🏗️  Enhanced Python 3.13 Setup for $PROJECT_NAME${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo

    # Parse command line arguments
    parse_arguments "$@"

    # Set up project directories
    PROJECT_DIR="$(pwd)"
    VENV_DIR="$PROJECT_DIR/$VENV_NAME"

    log "INFO" "Starting setup in: $PROJECT_DIR"

    # Main setup steps
    detect_os
    install_python313
    setup_security_tools
    setup_virtual_environment
    setup_pip
    install_dependencies
    setup_development_tools

    # Validate and complete
    if validate_installation; then
        show_completion_summary
    else
        error_exit "Installation validation failed"
    fi
}

# Run main function with all arguments
main "$@"
