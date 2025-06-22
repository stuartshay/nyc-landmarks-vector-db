# NYC Landmarks Vector DB - Infrastructure

This directory contains Terraform configuration for deploying monitoring infrastructure for the NYC Landmarks Vector DB project.

## 🚀 Quick Start

### First-Time Setup

```bash
cd infrastructure
./setup_terraform.sh
```

### Deploy Dashboard

```bash
./deploy_dashboard.sh apply
```

### View Dashboard

```bash
./deploy_dashboard.sh output
# Visit the URL shown for your project
```

## 📋 Common Commands

| Command                            | Description                                 |
| ---------------------------------- | ------------------------------------------- |
| `./health_check.sh`                | Check if everything is configured correctly |
| `../utils/test_health_endpoint.sh` | Test service health endpoints               |
| `./setup_terraform.sh`             | Initialize Terraform (run once)             |
| `./deploy_dashboard.sh plan`       | See what will be created                    |
| `./deploy_dashboard.sh apply`      | Create the dashboard                        |
| `./deploy_dashboard.sh output`     | Show dashboard URL and details              |
| `./deploy_dashboard.sh destroy`    | Remove all resources                        |

## 📁 Key Files

- `terraform/main.tf` - Main Terraform configuration
- `terraform/terraform.tfvars` - Your project settings (auto-generated)
- `../../.gcp/service-account-key.json` - GCP authentication

## Overview

The Terraform configuration creates:

- **Log-based metrics** for monitoring API performance
- **Comprehensive monitoring dashboard** in Google Cloud Console
- **Uptime checks** with automated health monitoring
- **Cloud Scheduler jobs** for periodic health validation
- **Proper IAM and authentication** setup

### 📊 Dashboard Features

The monitoring dashboard includes:

- **🔗 Service Health Status** - Real-time uptime percentage with color-coded thresholds
- **📈 Service Uptime (24h)** - 24-hour trend of service availability
- **Request Count** - Total API requests
- **Request Rate** - Requests per second
- **Error Rate** - 5xx errors per second
- **Latency** - Average and 95th percentile response times
- **Validation Warnings** - Application validation issues

### 🎯 Health Monitoring

The dashboard includes comprehensive health monitoring:

- **Uptime Check**: Monitors `/health` endpoint every 60 seconds
- **Thresholds**:
  - 🟡 Yellow warning below 95% uptime
  - 🔴 Red alert below 90% uptime
- **Content Validation**: Ensures response contains `"status": "healthy"`
- **Endpoints Monitored**:
  - Primary: `https://vector-db.coredatastore.com/health`
  - Direct: `https://nyc-landmarks-vector-db-1052843754581.us-east4.run.app/health`

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
   - `roles/cloudscheduler.admin`
   - `roles/cloudscheduler.jobRunner`

1. **GCP Project**: A valid Google Cloud Project with the following APIs enabled:

   - Cloud Logging API
   - Cloud Monitoring API
   - Cloud Resource Manager API
   - Cloud Scheduler API

## 🔧 Configuration

### Variables

| Variable             | Description                                          | Default                            | Required |
| -------------------- | ---------------------------------------------------- | ---------------------------------- | -------- |
| `project_id`         | GCP project ID                                       | Auto-detected from service account | No       |
| `GOOGLE_CREDENTIALS` | Contents of the service account key JSON (sensitive) | _empty_                            | Yes      |
| `region`             | GCP region                                           | `us-central1`                      | No       |
| `log_name_prefix`    | Prefix for log metric names                          | `nyc-landmarks-vector-db`          | No       |

### terraform.tfvars Example

```hcl
project_id = "my-gcp-project"
GOOGLE_CREDENTIALS = file("../../.gcp/service-account-key.json")
region = "us-central1"
log_name_prefix = "nyc-landmarks-vector-db"
```

## ✅ Health Check

Run `./health_check.sh` to verify:

- ✓ All required files exist
- ✓ Scripts are executable
- ✓ Terraform is installed
- ✓ GCP credentials are valid
- ✓ Configuration is correct

## 🔗 Access Dashboard

After deployment, access at:

```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
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

### Health Monitoring Components

- **Uptime Checks**: Monitor service endpoints every 60 seconds
- **Cloud Scheduler Jobs**: Periodic health validation tasks
- **Alerting Policies**: Automated notifications for service issues

## 📁 File Structure

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
├── health_check.sh               # Infrastructure validation
└── README.md                    # This file
```

## 🔧 Scripts Reference

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

### health_check.sh

Infrastructure validation script that checks:

- Required files and permissions
- Terraform installation and configuration
- GCP authentication and API access
- Cross-references endpoint testing utility at `../utils/test_health_endpoint.sh`

## Running Terraform locally with HCP backend

1. Run `terraform login` to generate a user API token for Terraform Cloud.

1. Export the token for CLI use:

   ```bash
   export TF_TOKEN_app_terraform_io=YOUR_TOKEN
   export GOOGLE_CREDENTIALS=$(cat ../../.gcp/service-account-key.json)
   ```

1. Initialize and run Terraform with the backend:

   ```bash
   terraform -chdir=terraform init
   terraform -chdir=terraform plan
   ```

The state and runs will execute remotely in HCP Terraform.

## Token rotation & secret management

- Rotate the service account key and update the `GOOGLE_CREDENTIALS` variable in the workspace.
- Regenerate your `TF_TOKEN_app_terraform_io` with `terraform login` when expired.
- Store tokens in GitHub Secrets for CI workflows.

### Switching to OIDC authentication

Provision the workload identity pool using the `modules/gcp_oidc` module and set
the following variables in the Terraform Cloud workspace:

```
TFC_GCP_PROVIDER_AUTH=OIDC
TFC_GCP_WORKLOAD_IDENTITY_PROVIDER=<provider full name>
TFC_GCP_PROJECT_ID=<project_id>
```

## Enabling Cost Estimation & Drift Detection

Enable these features in the Terraform Cloud workspace settings. When enabled,
run plans or applies through HCP to automatically check for cost and drift.

## 🛠 Troubleshooting

### Common Issues

1. **Authentication Errors**:

   - Verify service account key file exists and is valid JSON
   - Check service account has required permissions
   - Ensure GCP APIs are enabled

1. **Permission Denied**:

   - Service account needs all required roles (see Prerequisites)
   - Check IAM permissions in GCP Console

1. **Project Not Found**:

   - Verify project ID in terraform.tfvars
   - Ensure project exists and is active

1. **API Not Enabled**:

   ```bash
   gcloud services enable logging.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable cloudresourcemanager.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   ```

1. **Cloud Scheduler Issues**:

   - Ensure App Engine application exists in your project
   - Verify Cloud Scheduler API is enabled
   - Check service account has scheduler permissions

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

# View detailed logs
terraform apply -var-file=terraform.tfvars -auto-approve -verbose
```

## 🔒 Security Considerations

- Service account key file contains sensitive credentials
- Never commit `terraform.tfvars` or `*.tfstate` files to version control
- **DO commit `.terraform.lock.hcl` files** for consistent provider versions
- Use least-privilege IAM roles
- Consider using Workload Identity instead of service account keys in production
- Regularly rotate service account keys
- Monitor access logs for unauthorized usage

## 🤝 Contributing

When making changes to the infrastructure:

1. Test changes in a development project first
1. Update documentation if adding new variables or resources
1. Validate Terraform configuration: `terraform validate`
1. Format code: `terraform fmt`
1. Update version constraints if needed
1. Test deployment and rollback procedures

## 📞 Support

For issues related to:

- **Terraform configuration**: Check the troubleshooting section above
- **GCP permissions**: Review IAM documentation and required roles
- **Application logging**: Check the main project documentation
- **Health monitoring**: Use `../utils/test_health_endpoint.sh` for endpoint testing
