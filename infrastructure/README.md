# NYC Landmarks Vector DB - Infrastructure

This directory contains Terraform configuration for deploying monitoring infrastructure for the NYC Landmarks Vector DB project.

## Overview

The Terraform configuration creates:

- Log-based metrics for monitoring API performance
- A comprehensive monitoring dashboard in Google Cloud Console
- Proper IAM and authentication setup

## Prerequisites

1. **Terraform**: Install Terraform >= 1.0

   **Using Devcontainer (Recommended):**

   - Terraform is automatically included in the devcontainer
   - Simply rebuild your devcontainer to get Terraform + VS Code extension
   - See `TERRAFORM_DEVCONTAINER.md` for details

   **Manual Installation:**

   ```bash
   # On Ubuntu/Debian
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

1. **GCP Service Account**: Ensure you have a service account key file at `../../.gcp/service-account-key.json` with the following roles:

   - `roles/logging.configWriter`
   - `roles/monitoring.editor`
   - `roles/monitoring.metricWriter`

1. **GCP Project**: A valid Google Cloud Project with the following APIs enabled:

   - Cloud Logging API
   - Cloud Monitoring API
   - Cloud Resource Manager API

## Quick Start

### First-Time Setup

1. **Run the setup script** (recommended):

   ```bash
   cd infrastructure
   ./setup_terraform.sh
   ```

   This script will:

   - Validate prerequisites
   - Initialize Terraform
   - Create `terraform.tfvars` from the example
   - Validate the configuration
   - Create a deployment plan

1. **Manual setup** (alternative):

   ```bash
   cd infrastructure/terraform

   # Copy and edit variables
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details

   # Initialize Terraform
   terraform init

   # Plan deployment
   terraform plan
   ```

### Deploy Dashboard

1. **Using the deployment script** (recommended):

   ```bash
   cd infrastructure
   ./deploy_dashboard.sh apply
   ```

1. **Manual deployment**:

   ```bash
   cd infrastructure/terraform
   terraform apply
   ```

### View Dashboard

After successful deployment, you can access your monitoring dashboard at:

```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
```

## Configuration

### Variables

| Variable           | Description                     | Default                               | Required |
| ------------------ | ------------------------------- | ------------------------------------- | -------- |
| `project_id`       | GCP project ID                  | Auto-detected from service account    | No       |
| `credentials_file` | Path to GCP service account key | `../../.gcp/service-account-key.json` | No       |
| `region`           | GCP region                      | `us-central1`                         | No       |
| `log_name_prefix`  | Prefix for log metric names     | `nyc-landmarks-vector-db`             | No       |

### terraform.tfvars Example

```hcl
project_id = "my-gcp-project"
credentials_file = "../../.gcp/service-account-key.json"
region = "us-central1"
log_name_prefix = "nyc-landmarks-vector-db"
```

## Resources Created

### Log-Based Metrics

1. **Requests**: `{log_name_prefix}.requests`

   - Tracks total API requests
   - Filter: Cloud Run revision logs with performance metrics

1. **Errors**: `{log_name_prefix}.errors`

   - Tracks HTTP 5xx errors
   - Filter: Performance logs with status_code >= 500

1. **Latency**: `{log_name_prefix}.latency`

   - Tracks request duration
   - Filter: Performance logs with duration_ms >= 0

1. **Validation Warnings**: `{log_name_prefix}.validation_warnings`

   - Tracks validation issues
   - Filter: WARNING level logs from validation module

### Monitoring Dashboard

The dashboard includes widgets for:

- **Total Request Count**: Bar chart showing request volume
- **Average Latency**: Scorecard with mean response time
- **Request Rate**: Line chart of requests per second
- **Error Rate**: Line chart of 5xx errors per second
- **Request Latency**: Combined view of average and 95th percentile latency
- **Validation Warning Rate**: Line chart of validation warnings per second

## Scripts

### setup_terraform.sh

Comprehensive first-time setup script that:

- Validates prerequisites (Terraform, service account key)
- Initializes Terraform workspace
- Creates configuration from templates
- Validates setup
- Creates deployment plan

### deploy_dashboard.sh

Deployment and management script with commands:

- `plan`: Show planned changes
- `apply`: Deploy resources (default)
- `destroy`: Remove all resources
- `output`: Show resource information
- `status`: Show current state

Usage examples:

```bash
# Plan deployment
./deploy_dashboard.sh plan

# Deploy with auto-approval
./deploy_dashboard.sh apply --auto-approve

# Destroy resources
./deploy_dashboard.sh destroy

# Show outputs
./deploy_dashboard.sh output
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:

   - Verify service account key file exists and is valid JSON
   - Check service account has required permissions
   - Ensure GCP APIs are enabled

1. **Permission Denied**:

   - Service account needs `roles/logging.configWriter` and `roles/monitoring.editor`
   - Check IAM permissions in GCP Console

1. **Project Not Found**:

   - Verify project ID in terraform.tfvars
   - Ensure project exists and is active

1. **API Not Enabled**:

   ```bash
   gcloud services enable logging.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable cloudresourcemanager.googleapis.com
   ```

### Debug Commands

```bash
# Check Terraform state
terraform show

# Validate configuration
terraform validate

# Check outputs
terraform output

# Force refresh state
terraform refresh
```

## Security Considerations

- Service account key file contains sensitive credentials
- Never commit `terraform.tfvars` or `*.tfstate` files to version control
- **DO commit `.terraform.lock.hcl` files** for consistent provider versions
- Use least-privilege IAM roles
- Consider using Workload Identity instead of service account keys in production

## File Structure

```
infrastructure/
├── terraform/
│   ├── main.tf                   # Main Terraform configuration
│   ├── variables.tf              # Variable definitions
│   ├── outputs.tf                # Output definitions
│   ├── dashboard.json.tpl        # Dashboard template
│   ├── .terraform.lock.hcl       # Provider version locks (tracked)
│   ├── terraform.tfvars.example  # Example variables
│   └── .gitignore               # Git ignore patterns
├── .terraform.lock.hcl           # Root provider locks (tracked)
├── setup_terraform.sh            # First-time setup script
├── deploy_dashboard.sh           # Deployment script
└── README.md                    # This file
```

## Contributing

When making changes to the infrastructure:

1. Test changes in a development project first
1. Update documentation if adding new variables or resources
1. Validate Terraform configuration: `terraform validate`
1. Format code: `terraform fmt`
1. Update version constraints if needed

## Support

For issues related to:

- **Terraform configuration**: Check the troubleshooting section above
- **GCP permissions**: Review IAM documentation
- **Application logging**: Check the main project documentation
