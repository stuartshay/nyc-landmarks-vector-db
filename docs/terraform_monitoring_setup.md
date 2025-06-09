# Terraform Monitoring Setup

This configuration provisions monitoring resources for the NYC Landmarks Vector DB project using the Google Cloud provider.

## Quick Start

### First-Time Setup

1. **Automated setup** (recommended):

   ```bash
   cd infrastructure
   ./setup_terraform.sh
   ```

1. **Manual setup**:

   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details
   terraform init
   terraform plan
   ```

### Deploy Dashboard

1. **Using deployment script**:

   ```bash
   cd infrastructure
   ./deploy_dashboard.sh apply
   ```

1. **Manual deployment**:

   ```bash
   cd infrastructure/terraform
   terraform apply
   ```

## Prerequisites

- Terraform >= 1.0 installed
- GCP service account key at `.gcp/service-account-key.json` with permissions:
  - `roles/logging.configWriter`
  - `roles/monitoring.editor`
  - `roles/monitoring.metricWriter`
- GCP project with enabled APIs:
  - Cloud Logging API
  - Cloud Monitoring API
  - Cloud Resource Manager API

## Configuration

The setup automatically detects your GCP project from the service account key file. You can override settings in `terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"
credentials_file = "../../.gcp/service-account-key.json"
region = "us-central1"
log_name_prefix = "nyc-landmarks-vector-db"
```

## Resources Created

The module creates log-based metrics:

- `{log_name_prefix}.requests` - Total API requests
- `{log_name_prefix}.errors` - HTTP 5xx errors
- `{log_name_prefix}.latency` - Request duration
- `{log_name_prefix}.validation_warnings` - Validation warnings

A comprehensive monitoring dashboard with widgets for:

- Request count and rate
- Error rate
- Latency (average and 95th percentile)
- Validation warning rate

## Scripts

- `setup_terraform.sh`: First-time setup with validation
- `deploy_dashboard.sh`: Deploy, plan, destroy, and status commands

## Dashboard Access

After deployment, access your dashboard at:

```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
```

View resource details:

```bash
cd infrastructure/terraform
terraform output
```

For detailed instructions, see `infrastructure/README.md`.
