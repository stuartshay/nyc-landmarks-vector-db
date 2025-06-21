#!/bin/bash

# Script to deploy only the monitoring dashboard without affecting other resources
# This avoids conflicts with existing resources that may already exist in GCP

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

echo -e "${BLUE}NYC Landmarks Vector DB - Dashboard-Only Deployment${NC}"
echo "===================================================="
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

case "$ACTION" in
    "plan")
        print_status "Creating Terraform plan for dashboard only..."
        terraform plan -out=dashboard_only.plan -target=google_monitoring_dashboard.api_dashboard
        ;;
    "apply")
        print_status "Applying dashboard changes only..."
        terraform plan -out=dashboard_only.plan -target=google_monitoring_dashboard.api_dashboard
        terraform apply "dashboard_only.plan"

        if [[ $? -eq 0 ]]; then
            echo
            print_status "Dashboard deployment completed successfully!"
            echo
            print_status "Dashboard details:"
            terraform output dashboard_url
            echo
            print_status "You can view your monitoring dashboard in the Google Cloud Console:"
            PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || echo "")
            DASHBOARD_ID=$(terraform output -raw dashboard_id 2>/dev/null || echo "")
            if [[ ! -z "$PROJECT_ID" && ! -z "$DASHBOARD_ID" ]]; then
                echo "https://console.cloud.google.com/monitoring/dashboards/custom/$DASHBOARD_ID?project=$PROJECT_ID"
            fi
        fi
        ;;
    *)
        echo "Usage: $0 [plan|apply]"
        echo
        echo "Commands:"
        echo "  plan      - Show what changes will be made to the dashboard"
        echo "  apply     - Deploy only the monitoring dashboard (default)"
        exit 1
        ;;
esac
