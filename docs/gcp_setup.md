# Google Cloud Platform Setup

This document describes how to set up Google Cloud Platform (GCP) authentication for the NYC Landmarks Vector DB project.

## Overview

The project is configured to automatically authenticate with Google Cloud using a service account key stored in the `.gcp` directory. This setup allows seamless access to GCP services like Google Cloud Storage, Logging, and other APIs.

## Authentication Setup

### 1. Service Account Key

The project uses a service account key located at:

```
.gcp/service-account-key.json
```

This key file contains:

- **Project ID**: `velvety-byway-327718`
- **Service Account**: `gh-actions-navigator@velvety-byway-327718.iam.gserviceaccount.com`
- **Private Key**: Used for authentication

### 2. Automatic Setup

The devcontainer is configured to automatically set up GCP authentication when it starts:

1. **Environment Variables**: The `GOOGLE_APPLICATION_CREDENTIALS` environment variable is automatically set to point to the service account key
1. **gcloud CLI**: The Google Cloud CLI is authenticated using the service account key
1. **Default Project**: The project is automatically set as the default for gcloud commands

### 3. Manual Setup

If you need to manually set up or refresh the authentication, you can run:

```bash
# Run the setup script
./scripts/setup_gcp_auth.sh

# Or use the VS Code task
# Ctrl+Shift+P -> "Tasks: Run Task" -> "Setup GCP Authentication"
```

## Verification

To verify that GCP authentication is working correctly:

```bash
# Run the comprehensive environment check (includes GCP verification)
python utils/check_dev_env.py

# Or use the VS Code task
# Ctrl+Shift+P -> "Tasks: Run Task" -> "Verify GCP Authentication"
```

The verification script checks:

- ✅ Service account key exists and is valid
- ✅ Environment variables are properly set
- ✅ gcloud CLI is authenticated
- ✅ GCP API access is working
- ✅ Plus all other development environment requirements

## Available VS Code Tasks

The following VS Code tasks are available for GCP management:

1. **Setup GCP Authentication**: Runs the setup script to configure authentication
1. **Verify GCP Authentication**: Runs comprehensive checks to ensure everything is working

Access these tasks via:

- Command Palette: `Ctrl+Shift+P` → "Tasks: Run Task"
- Terminal menu: "Terminal" → "Run Task"

## Manual gcloud Commands

Once authenticated, you can use gcloud commands directly:

```bash
# Check authentication status
gcloud auth list

# Check current project
gcloud config get-value project

# List available projects
gcloud projects list

# Set a different project (if needed)
gcloud config set project PROJECT_ID
```

## Environment Variables

The following environment variables are automatically set:

- `GOOGLE_APPLICATION_CREDENTIALS`: Points to the service account key file
- Project configuration is handled by gcloud CLI

## Troubleshooting

### Common Issues

1. **Service account key not found**

   - Ensure the key file exists at `.gcp/service-account-key.json`
   - Check file permissions

1. **Authentication failed**

   - Verify the service account key is valid JSON
   - Check that the service account has necessary permissions

1. **Project not set**

   - Run `gcloud config set project velvety-byway-327718`

### Getting Help

Run the comprehensive environment check to get detailed diagnostics:

```bash
python utils/check_dev_env.py
```

This will show exactly what's working and what needs attention, including GCP setup.

## Security Notes

- The service account key is included in the repository for development purposes
- In production, use more secure methods like Workload Identity or IAM roles
- Never commit service account keys to public repositories
- Regularly rotate service account keys

## Files

- `.gcp/service-account-key.json`: Service account credentials
- `scripts/setup_gcp_auth.sh`: Authentication setup script
- `utils/check_dev_env.py`: Comprehensive environment verification (includes GCP)
- `.devcontainer/devcontainer.json`: Devcontainer configuration with GCP setup
- `.vscode/tasks.json`: VS Code tasks for GCP management
