#!/bin/bash

# Infrastructure Health Check Script
# Validates the monitoring infrastructure setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}Infrastructure Health Check${NC}"
echo "=========================="
echo

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_count=0
pass_count=0

# Check if required files exist
echo "Checking file structure..."
required_files=(
    "$TERRAFORM_DIR/main.tf"
    "$TERRAFORM_DIR/variables.tf"
    "$TERRAFORM_DIR/outputs.tf"
    "$TERRAFORM_DIR/dashboard.json.tpl"
    "$TERRAFORM_DIR/terraform.tfvars.example"
    "$PROJECT_ROOT/.gcp/service-account-key.json"
)

for file in "${required_files[@]}"; do
    check_count=$((check_count + 1))
    if [[ -f "$file" ]]; then
        print_status "$(basename "$file") exists"
        pass_count=$((pass_count + 1))
    else
        print_error "$(basename "$file") missing at $file"
    fi
done

# Check if scripts are executable
echo
echo "Checking script permissions..."
scripts=(
    "$SCRIPT_DIR/setup_terraform.sh"
    "$SCRIPT_DIR/deploy_dashboard.sh"
)

for script in "${scripts[@]}"; do
    check_count=$((check_count + 1))
    if [[ -x "$script" ]]; then
        print_status "$(basename "$script") is executable"
        pass_count=$((pass_count + 1))
    else
        print_error "$(basename "$script") is not executable"
    fi
done

# Check Terraform installation
echo
echo "Checking prerequisites..."
check_count=$((check_count + 1))
if command -v terraform &> /dev/null; then
    version=$(terraform version | head -1)
    print_status "Terraform installed: $version"
    pass_count=$((pass_count + 1))
else
    print_error "Terraform not installed"
fi

# Check service account key validity
check_count=$((check_count + 1))
if [[ -f "$PROJECT_ROOT/.gcp/service-account-key.json" ]]; then
    if python3 -c "import json; json.load(open('$PROJECT_ROOT/.gcp/service-account-key.json'))" 2>/dev/null; then
        project_id=$(python3 -c "import json; print(json.load(open('$PROJECT_ROOT/.gcp/service-account-key.json'))['project_id'])")
        print_status "Service account key is valid (Project: $project_id)"
        pass_count=$((pass_count + 1))
    else
        print_error "Service account key is invalid JSON"
    fi
else
    print_error "Service account key file not found"
fi

# Check if Terraform is initialized
cd "$TERRAFORM_DIR"
echo
echo "Checking Terraform state..."
check_count=$((check_count + 1))
if [[ -d ".terraform" ]]; then
    print_status "Terraform is initialized"
    pass_count=$((pass_count + 1))
else
    print_warning "Terraform not initialized (run setup_terraform.sh)"
fi

# Check if terraform.tfvars exists
check_count=$((check_count + 1))
if [[ -f "terraform.tfvars" ]]; then
    print_status "terraform.tfvars configured"
    pass_count=$((pass_count + 1))
else
    print_warning "terraform.tfvars not found (run setup_terraform.sh)"
fi

# Validate Terraform configuration if initialized
if [[ -d ".terraform" ]]; then
    echo
    echo "Validating Terraform configuration..."
    check_count=$((check_count + 1))
    if terraform validate &>/dev/null; then
        print_status "Terraform configuration is valid"
        pass_count=$((pass_count + 1))
    else
        print_error "Terraform configuration validation failed"
    fi
fi

# Summary
echo
echo "=============="
echo "Health Check Summary:"
echo "Passed: $pass_count/$check_count checks"

if [[ $pass_count -eq $check_count ]]; then
    echo -e "${GREEN}All checks passed! Infrastructure is ready.${NC}"
    echo
    echo "To deploy: ./deploy_dashboard.sh apply"
    exit 0
elif [[ $pass_count -gt $((check_count * 3 / 4)) ]]; then
    echo -e "${YELLOW}Most checks passed. Review warnings above.${NC}"
    echo
    echo "To setup: ./setup_terraform.sh"
    exit 0
else
    echo -e "${RED}Multiple checks failed. Please address the errors above.${NC}"
    exit 1
fi
