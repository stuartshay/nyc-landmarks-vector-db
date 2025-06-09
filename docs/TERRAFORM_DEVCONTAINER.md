# Terraform Integration in DevContainer

This document describes how Terraform is integrated into the NYC Landmarks Vector DB project's devcontainer for seamless infrastructure management.

## DevContainer Configuration

The devcontainer is fully configured for Terraform development with the following features:

### Terraform Feature

```json
"features": {
  "ghcr.io/devcontainers/features/terraform:1": {
    "version": "latest"
  }
}
```

This automatically installs Terraform CLI (currently v1.12.1) in the devcontainer.

### VS Code Extension

```json
"extensions": [
  "hashicorp.terraform"
]
```

The official HashiCorp Terraform extension provides:

- Syntax highlighting
- IntelliSense and auto-completion
- Terraform validation
- Format on save
- Error detection and linting

### VS Code Settings

```json
"terraform.experimentalFeatures.validateOnSave": true,
"terraform.experimentalFeatures.prefillRequiredFields": true,
"[terraform]": {
  "editor.formatOnSave": true
},
"[terraform-vars]": {
  "editor.formatOnSave": true
}
```

These settings enable:

- Automatic validation when saving Terraform files
- Auto-completion for required fields
- Automatic formatting for `.tf` and `.tfvars` files

## Infrastructure Setup

### Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf                    # Main Terraform configuration
│   ├── variables.tf              # Variable definitions
│   ├── outputs.tf                # Output definitions
│   ├── dashboard.json.tpl        # Dashboard template
│   ├── terraform.tfvars.example  # Example variables file
│   └── .gitignore               # Terraform-specific ignores
├── setup_terraform.sh           # First-time setup script
├── deploy_dashboard.sh          # Deployment script
├── health_check.sh             # Environment validation
├── README.md                   # Complete setup guide
└── QUICK_REFERENCE.md         # Quick command reference
```

### Quick Start

1. **First-time setup** (only needed once):

   ```bash
   cd infrastructure
   ./setup_terraform.sh
   ```

1. **Deploy infrastructure**:

   ```bash
   ./deploy_dashboard.sh apply
   ```

1. **Validate environment**:

   ```bash
   ./health_check.sh
   ```

### Environment Variables

The devcontainer automatically configures:

- `GOOGLE_APPLICATION_CREDENTIALS`: Points to the service account key
- GCP authentication is handled by the `postStartCommand`

## Features Available

### 1. Terraform CLI Commands

All standard Terraform commands work out of the box:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
terraform validate
terraform fmt
```

### 2. VS Code Integration

- **Command Palette**: Use `Ctrl+Shift+P` and search for "Terraform" commands
- **File Explorer**: Right-click on `.tf` files for Terraform-specific actions
- **Problems Panel**: Shows Terraform validation errors and warnings
- **IntelliSense**: Auto-completion for resources, data sources, and variables

### 3. Automated Scripts

- **health_check.sh**: Validates the entire infrastructure setup (13 checks)
- **setup_terraform.sh**: Handles first-time Terraform initialization
- **deploy_dashboard.sh**: Streamlined deployment with validation

### 4. Template Support

The dashboard configuration uses Terraform's `templatefile()` function:

- **dashboard.json.tpl**: Template with variable substitution
- Dynamic project ID and resource naming
- Environment-specific customization

## Best Practices Implemented

### 1. Security

- Service account key is gitignored
- Terraform state files are gitignored
- Sensitive variables are handled through `.tfvars` files

### 2. Code Quality

- Automatic formatting on save
- Validation on save
- Consistent indentation (2 spaces for Terraform)
- Pre-commit hooks integration

### 3. Documentation

- Comprehensive variable descriptions
- Output descriptions for reference
- Example configurations provided

### 4. Error Handling

- Health checks validate the entire setup
- Clear error messages and troubleshooting guides
- Graceful handling of missing dependencies

## Troubleshooting

### Common Issues

1. **"terraform: command not found"**

   - The devcontainer should auto-install Terraform
   - Rebuild the container if necessary: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

1. **GCP Authentication Errors**

   - Run `./health_check.sh` to validate the service account key
   - Ensure `.gcp/service-account-key.json` exists and is valid

1. **Terraform Validation Errors**

   - The VS Code extension will highlight errors in real-time
   - Use `terraform validate` for detailed error information

1. **Permission Errors**

   - Scripts should be executable by default
   - If needed: `chmod +x *.sh`

### Getting Help

1. **Health Check**: Always start with `./health_check.sh`
1. **Documentation**: Check `infrastructure/README.md` for detailed guides
1. **Quick Reference**: Use `infrastructure/QUICK_REFERENCE.md` for commands
1. **VS Code**: Use the built-in Terraform extension help and documentation

## Development Workflow

1. **Edit Terraform files** in VS Code with full IntelliSense support
1. **Validate changes** automatically on save
1. **Plan deployments** using `./deploy_dashboard.sh plan`
1. **Apply changes** using `./deploy_dashboard.sh apply`
1. **Monitor health** using `./health_check.sh`

The devcontainer provides a complete, ready-to-use Terraform development environment with no additional setup required.
