# Terraform File Structure Cleanup

## Issue Addressed

Removed duplicate `infrastructure/terraform/dashboard.json` file that was causing confusion and potential configuration drift.

## Problem

- The Terraform configuration uses `dashboard.json.tpl` (template file) with variable substitution
- There was also a static `dashboard.json` file that was not being used
- This created confusion about which file was the source of truth
- Could lead to configuration drift if someone edited the wrong file

## Solution

### Files Removed

- `infrastructure/terraform/dashboard.json` - Static file (not used by Terraform)

### Files Retained

- `infrastructure/terraform/dashboard.json.tpl` - Template file used by Terraform with variable substitution

## Terraform Configuration

The main.tf file uses the template approach:

```hcl
resource "google_monitoring_dashboard" "api_dashboard" {
  dashboard_json = templatefile("${path.module}/dashboard.json.tpl", {
    project_id = local.project_id
  })
}
```

## Benefits

1. **Single Source of Truth**: Only the template file exists and is used
1. **Variable Substitution**: Dashboard configuration can use Terraform variables
1. **No Configuration Drift**: Can't accidentally edit the wrong file
1. **Cleaner Repository**: Removes unused duplicate files

## Verification

- ✅ Terraform validation passes
- ✅ Terraform plan works correctly
- ✅ Template file contains all dashboard configuration
- ✅ No functionality lost

The dashboard deployment continues to work exactly as before, but now with a cleaner, less confusing file structure.
