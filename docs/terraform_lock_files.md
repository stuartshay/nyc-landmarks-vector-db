# Terraform Lock Files - Why They Should Be Versioned

## Overview

Terraform lock files (`.terraform.lock.hcl`) **should be committed to version control** for consistency and reproducibility across environments.

## Current Lock Files

The project tracks these lock files:

- `infrastructure/.terraform.lock.hcl` - For the root infrastructure configuration
- `infrastructure/terraform/.terraform.lock.hcl` - For the main Terraform configuration

## Why Version Lock Files?

### 1. **Consistent Provider Versions**

Lock files ensure all team members and CI/CD systems use identical provider versions:

```hcl
provider "registry.terraform.io/hashicorp/google" {
  version     = "5.45.2"
  constraints = "~> 5.0"
  hashes = [
    "h1:k8taQAdfHrv2F/AiGV5BZBZfI+1uaq8g6O8dWzjx42c=",
    # ... additional hashes for verification
  ]
}
```

### 2. **Reproducible Deployments**

- Prevents "works on my machine" issues
- Ensures CI/CD uses same provider versions as local development
- Guarantees consistent behavior across environments

### 3. **Security and Integrity**

- Contains cryptographic hashes to verify provider authenticity
- Prevents supply chain attacks through provider tampering
- Ensures downloaded providers match expected checksums

### 4. **Dependency Management**

- Similar to `package-lock.json` (Node.js) or `requirements.txt` (Python)
- Locks transitive dependencies and their versions
- Prevents unexpected version drift

## Best Practices

### ✅ **Do Version Control**

```bash
git add .terraform.lock.hcl
git commit -m "Add/update Terraform provider locks"
```

### ✅ **Update Intentionally**

```bash
# Update all providers
terraform init -upgrade

# Update specific provider
terraform init -upgrade=hashicorp/google
```

### ✅ **Review Lock File Changes**

- Check provider version changes in pull requests
- Understand impact of version updates
- Test thoroughly when providers are upgraded

### ❌ **Don't Ignore Lock Files**

```gitignore
# ❌ Don't do this:
**/.terraform.lock.hcl

# ✅ Do this instead - only ignore the .terraform directory:
**/.terraform/
```

## Current .gitignore Configuration

The project correctly excludes provider binaries but includes lock files:

```gitignore
# Terraform
**/.terraform/                    # ✅ Ignore downloaded providers
**/terraform.tfstate             # ✅ Ignore state files
**/terraform.tfstate.backup      # ✅ Ignore state backups
**/terraform.tfvars              # ✅ Ignore variable files (may contain secrets)
# Note: .terraform.lock.hcl is NOT ignored (✅ Correct!)
```

## Team Workflow

### For Developers

1. **New checkout**: `terraform init` uses existing lock file
1. **Provider updates**: Run `terraform init -upgrade` deliberately
1. **Commit changes**: Include lock file updates in commits

### For CI/CD

1. **Consistent builds**: Uses locked provider versions
1. **Security**: Verifies provider integrity via hashes
1. **Reliability**: No surprise version updates during deployment

## Migration Notes

If lock files were previously ignored:

1. Remove from `.gitignore`
1. Run `terraform init` to generate current lock files
1. Commit the lock files
1. Ensure all team members pull the changes

## Example Lock File Structure

```hcl
# This file is maintained automatically by "terraform init".
# Manual edits may be lost in future updates.

provider "registry.terraform.io/hashicorp/google" {
  version     = "5.45.2"           # Exact version used
  constraints = "~> 5.0"           # Version constraint from config
  hashes = [                       # Cryptographic verification
    "h1:k8taQAdfHrv2F/AiGV5BZBZfI+1uaq8g6O8dWzjx42c=",
    # ... additional platform-specific hashes
  ]
}
```

## Conclusion

Versioning `.terraform.lock.hcl` files is a Terraform best practice that ensures:

- **Consistency** across environments
- **Security** through hash verification
- **Reproducibility** of deployments
- **Team collaboration** with shared dependencies

The project now correctly tracks these files for robust infrastructure management.
