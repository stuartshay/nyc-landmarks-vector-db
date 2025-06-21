#!/bin/bash

# Script to import existing resources into Terraform state
# This resolves "Error 409: Resource already exists" errors by importing the resources
# into Terraform state before applying changes

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

echo -e "${BLUE}NYC Landmarks Vector DB - Import Existing Resources${NC}"
echo "====================================================="
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

# Extract project_id from terraform.tfvars if it exists
PROJECT_ID="velvety-byway-327718"
if [[ -f "terraform.tfvars" ]]; then
    PROJECT_ID_LINE=$(grep "project_id" terraform.tfvars)
    if [[ ! -z "$PROJECT_ID_LINE" ]]; then
        PROJECT_ID=$(echo $PROJECT_ID_LINE | sed 's/project_id *= *"\(.*\)"/\1/')
    fi
fi

print_status "Using project ID: $PROJECT_ID"

# Import the existing logging metrics
print_status "Importing existing logging metrics..."

echo -e "${YELLOW}Importing requests metric...${NC}"
terraform import google_logging_metric.requests "nyc-landmarks-vector-db.requests" || print_warning "Failed to import requests metric"

echo -e "${YELLOW}Importing errors metric...${NC}"
terraform import google_logging_metric.errors "nyc-landmarks-vector-db.errors" || print_warning "Failed to import errors metric"

echo -e "${YELLOW}Importing latency metric...${NC}"
terraform import google_logging_metric.latency "nyc-landmarks-vector-db.latency" || print_warning "Failed to import latency metric"

echo -e "${YELLOW}Importing validation_warnings metric...${NC}"
terraform import google_logging_metric.validation_warnings "nyc-landmarks-vector-db.validation_warnings" || print_warning "Failed to import validation_warnings metric"

# Import the cloud scheduler job
print_status "Importing existing cloud scheduler job..."
terraform import google_cloud_scheduler_job.scheduler_health_check "projects/${PROJECT_ID}/locations/us-central1/jobs/nyc-landmarks-health-check" || print_warning "Failed to import cloud scheduler job"

print_status "Import operation completed."
print_status "You can now run ./deploy_dashboard.sh apply to apply changes without conflicts."
