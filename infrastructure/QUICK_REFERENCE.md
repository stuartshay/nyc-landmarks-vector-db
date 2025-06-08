# Quick Reference Guide - Infrastructure

## 🚀 Quick Start

### First Time Setup

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
# Then visit the URL shown for your project
```

## 📋 Common Commands

| Command                         | Description                                 |
| ------------------------------- | ------------------------------------------- |
| `./health_check.sh`             | Check if everything is configured correctly |
| `./setup_terraform.sh`          | Initialize Terraform (run once)             |
| `./deploy_dashboard.sh plan`    | See what will be created                    |
| `./deploy_dashboard.sh apply`   | Create the dashboard                        |
| `./deploy_dashboard.sh output`  | Show dashboard URL and details              |
| `./deploy_dashboard.sh destroy` | Remove all resources                        |

## 📁 Key Files

- `terraform/main.tf` - Main Terraform configuration
- `terraform/terraform.tfvars` - Your project settings (auto-generated)
- `.gcp/service-account-key.json` - GCP authentication

## 🔧 Configuration

Edit `terraform/terraform.tfvars` to customize:

```hcl
project_id = "your-gcp-project-id"
region = "us-central1"
log_name_prefix = "nyc-landmarks-vector-db"
```

## ✅ Health Check Results

Run `./health_check.sh` to verify:

- ✓ All required files exist
- ✓ Scripts are executable
- ✓ Terraform is installed
- ✓ GCP credentials are valid
- ✓ Configuration is correct

## 📊 Dashboard Features

The monitoring dashboard includes:

- **Request Count** - Total API requests
- **Request Rate** - Requests per second
- **Error Rate** - 5xx errors per second
- **Latency** - Average and 95th percentile response times
- **Validation Warnings** - Application validation issues

## 🔗 Access Dashboard

After deployment, access at:

```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
```

## 🛠 Troubleshooting

### Common Issues

1. **Permission denied**: Check service account has required roles
1. **Project not found**: Verify project ID in terraform.tfvars
1. **API not enabled**: Enable required GCP APIs

### Required GCP Permissions

- `roles/logging.configWriter`
- `roles/monitoring.editor`
- `roles/monitoring.metricWriter`

### Required GCP APIs

- Cloud Logging API
- Cloud Monitoring API
- Cloud Resource Manager API
