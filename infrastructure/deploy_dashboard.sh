#!/bin/bash

# Terraform Deployment Script for NYC Landmarks Vector DB Monitoring Dashboard
# This script deploys the monitoring infrastructure

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

echo -e "${BLUE}NYC Landmarks Vector DB - Dashboard Deployment${NC}"
echo "==============================================="
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

# Check if we're in the right directory
if [[ ! -d "$TERRAFORM_DIR" ]]; then
    print_error "Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Check if Terraform is initialized
if [[ ! -d ".terraform" ]]; then
    print_error "Terraform not initialized. Please run setup_terraform.sh first."
    exit 1
fi

# Check if terraform.tfvars exists
if [[ ! -f "terraform.tfvars" ]]; then
    print_error "terraform.tfvars not found. Please run setup_terraform.sh first."
    exit 1
fi

# Parse command line arguments
ACTION="${1:-apply}"
AUTO_APPROVE="${2:-}"

case "$ACTION" in
    "plan")
        print_status "Creating Terraform plan..."
        terraform plan
        ;;
    "apply")
        print_status "Applying Terraform configuration..."
        if [[ "$AUTO_APPROVE" == "--auto-approve" ]]; then
            terraform apply -auto-approve
        else
            terraform apply
        fi

        if [[ $? -eq 0 ]]; then
            echo
            print_status "Deployment completed successfully!"
            echo
            print_status "Dashboard details:"
            terraform output
            echo
            print_status "You can view your monitoring dashboard in the Google Cloud Console:"
            PROJECT_ID=$(terraform output -raw project_id)
            echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
        fi
        ;;
    "destroy")
        print_warning "This will destroy all monitoring resources!"
        echo "Are you sure you want to continue? (y/N)"
        read -r confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            print_status "Destroying Terraform resources..."
            terraform destroy
        else
            print_status "Destruction cancelled"
        fi
        ;;
    "output")
        print_status "Terraform outputs:"
        terraform output
        ;;
    "status")
        print_status "Terraform state:"
        terraform show
        ;;
    *)
        echo "Usage: $0 [plan|apply|destroy|output|status] [--auto-approve]"
        echo
        echo "Commands:"
        echo "  plan      - Show what changes will be made"
        echo "  apply     - Deploy the monitoring dashboard (default)"
        echo "  destroy   - Remove all monitoring resources"
        echo "  output    - Show information about deployed resources"
        echo "  status    - Show current Terraform state"
        echo
        echo "Options:"
        echo "  --auto-approve  - Skip confirmation prompts (for apply only)"
        exit 1
        ;;
esac
