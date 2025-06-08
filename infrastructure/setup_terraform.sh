#!/bin/bash

# Terraform First-Time Setup Script
# This script helps set up Terraform for the NYC Landmarks Vector DB monitoring dashboard

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

echo -e "${BLUE}NYC Landmarks Vector DB - Terraform Setup${NC}"
echo "=============================================="
echo

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    echo "Visit: https://www.terraform.io/downloads.html"
    exit 1
fi

print_status "Terraform found: $(terraform version | head -1)"

# Check if gcloud CLI is available (optional but recommended)
if command -v gcloud &> /dev/null; then
    print_status "Google Cloud CLI found: $(gcloud version | head -1 | cut -d' ' -f4)"
else
    print_warning "Google Cloud CLI not found. Authentication will rely on service account key file."
fi

# Navigate to Terraform directory
cd "$TERRAFORM_DIR"

# Check if service account key file exists
SERVICE_ACCOUNT_KEY="$PROJECT_ROOT/.gcp/service-account-key.json"
if [[ ! -f "$SERVICE_ACCOUNT_KEY" ]]; then
    print_error "Service account key file not found at: $SERVICE_ACCOUNT_KEY"
    echo "Please ensure you have a valid GCP service account key file."
    echo "The service account should have the following roles:"
    echo "  - roles/logging.configWriter"
    echo "  - roles/monitoring.editor"
    echo "  - roles/monitoring.metricWriter"
    exit 1
fi

print_status "Service account key file found"

# Validate service account key file
if ! python3 -c "import json; json.load(open('$SERVICE_ACCOUNT_KEY'))" 2>/dev/null; then
    print_error "Invalid JSON in service account key file"
    exit 1
fi

# Extract project ID from service account key
PROJECT_ID=$(python3 -c "import json; print(json.load(open('$SERVICE_ACCOUNT_KEY'))['project_id'])")
print_status "Detected GCP Project ID: $PROJECT_ID"

# Check if terraform.tfvars exists, if not create it from example
if [[ ! -f "terraform.tfvars" ]]; then
    print_status "Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars

    # Update project_id in terraform.tfvars
    if command -v sed &> /dev/null; then
        sed -i.bak "s/your-gcp-project-id/$PROJECT_ID/g" terraform.tfvars
        rm terraform.tfvars.bak 2>/dev/null || true
        print_status "Updated terraform.tfvars with project ID: $PROJECT_ID"
    else
        print_warning "Please manually update terraform.tfvars with your project ID: $PROJECT_ID"
    fi
else
    print_status "terraform.tfvars already exists"
fi

# Initialize Terraform
print_status "Initializing Terraform..."
if terraform init; then
    print_status "Terraform initialized successfully"
else
    print_error "Terraform initialization failed"
    exit 1
fi

# Validate Terraform configuration
print_status "Validating Terraform configuration..."
if terraform validate; then
    print_status "Terraform configuration is valid"
else
    print_error "Terraform configuration validation failed"
    exit 1
fi

# Plan the deployment
print_status "Creating Terraform plan..."
if terraform plan -out=tfplan; then
    print_status "Terraform plan created successfully"
    echo
    echo -e "${GREEN}Setup completed successfully!${NC}"
    echo
    echo "Next steps:"
    echo "1. Review the plan output above"
    echo "2. Run 'terraform apply tfplan' to deploy the monitoring dashboard"
    echo "3. Run 'terraform output' to see the created resources"
    echo
    echo "To clean up: run 'terraform destroy'"
else
    print_error "Terraform plan failed"
    exit 1
fi
